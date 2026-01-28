"""
Risk Management API

위험 등록부 (Risk Register) 및 위험 평가 관리
- CRUD for risks
- Risk assessment history
- 5×5 Risk Matrix visualization
- PSR → Risk auto-escalation
"""

from datetime import datetime, timezone, date
from typing import Annotated, Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, and_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.risk import (
    Risk,
    RiskAssessment,
    RiskSourceType,
    RiskCategory,
    RiskLevel,
    RiskStatus,
    RiskAssessmentType,
    calculate_risk_level,
)
from app.models.incident import Incident
from app.models.user import User, Role
from app.models.audit import AuditLog, AuditEventType
from app.schemas.risk import (
    RiskCreate,
    RiskUpdate,
    RiskResponse,
    RiskListResponse,
    RiskAssessmentCreate,
    RiskAssessmentResponse,
    RiskMatrixResponse,
    RiskMatrixCell,
    EscalationCandidate,
    EscalationResult,
)
from app.services.escalation import (
    find_escalation_candidates,
    escalate_incident_to_risk,
    run_auto_escalation,
)
from app.security.dependencies import get_current_active_user

router = APIRouter()


async def generate_risk_code(db: AsyncSession) -> str:
    """Generate unique risk code: R-YYYY-NNN"""
    year = datetime.now().year
    prefix = f"R-{year}-"

    # Find the highest number for this year
    result = await db.execute(
        select(Risk.risk_code)
        .where(Risk.risk_code.like(f"{prefix}%"))
        .order_by(desc(Risk.risk_code))
        .limit(1)
    )
    last_code = result.scalar_one_or_none()

    if last_code:
        last_num = int(last_code.split("-")[-1])
        new_num = last_num + 1
    else:
        new_num = 1

    return f"{prefix}{new_num:03d}"


async def log_risk_event(
    db: AsyncSession,
    user: User,
    risk_id: int | None,
    event: str,
    result: str,
    details: dict | None = None,
) -> None:
    """Log risk event for audit."""
    timestamp = datetime.now(timezone.utc)
    previous_hash = "genesis"

    # Map event string to AuditEventType
    event_type_map = {
        "create": AuditEventType.RISK_CREATE,
        "update": AuditEventType.RISK_UPDATE,
        "escalate": AuditEventType.RISK_ESCALATE,
        "assessment": AuditEventType.RISK_ASSESSMENT,
    }
    audit_event_type = event_type_map.get(event, AuditEventType.RISK_UPDATE)

    entry_hash = AuditLog.calculate_hash(
        event_type=audit_event_type.value,
        timestamp=timestamp,
        user_id=user.id,
        resource_id=str(risk_id) if risk_id else None,
        previous_hash=previous_hash,
    )

    audit_log = AuditLog(
        event_type=audit_event_type,
        timestamp=timestamp,
        user_id=user.id,
        user_role=user.role.value,
        username=user.username,
        resource_type="risk",
        resource_id=str(risk_id) if risk_id else None,
        action_detail={"event": event, **(details or {})},
        result=result,
        previous_hash=previous_hash,
        entry_hash=entry_hash,
    )
    db.add(audit_log)


def can_manage_risks(user: User) -> bool:
    """Check if user can manage risks. QPS_STAFF+ required."""
    return user.role in [Role.QPS_STAFF, Role.VICE_CHAIR, Role.DIRECTOR, Role.MASTER]


def can_close_risks(user: User) -> bool:
    """Check if user can close risks. DIRECTOR+ required."""
    return user.role in [Role.DIRECTOR, Role.MASTER]


@router.post(
    "",
    response_model=RiskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new risk",
)
async def create_risk(
    risk_data: RiskCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RiskResponse:
    """
    Create a new risk in the Risk Register.

    Business rules:
    - QPS_STAFF or higher required
    - If source is PSR, incident must exist
    - Risk code auto-generated
    """
    if not can_manage_risks(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create risks",
        )

    # Verify source incident if PSR
    if risk_data.source_type == RiskSourceType.PSR and risk_data.source_incident_id:
        result = await db.execute(
            select(Incident).where(
                and_(
                    Incident.id == risk_data.source_incident_id,
                    Incident.is_deleted == False
                )
            )
        )
        if result.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Source incident not found",
            )

    # Generate risk code
    risk_code = await generate_risk_code(db)

    risk = Risk(
        risk_code=risk_code,
        title=risk_data.title,
        description=risk_data.description,
        source_type=risk_data.source_type,
        source_incident_id=risk_data.source_incident_id,
        source_detail=risk_data.source_detail,
        category=risk_data.category,
        current_controls=risk_data.current_controls,
        probability=risk_data.probability,
        severity=risk_data.severity,
        owner_id=risk_data.owner_id,
        target_date=risk_data.target_date,
        created_by_id=current_user.id,
    )

    db.add(risk)
    await db.flush()
    await db.refresh(risk)

    # Create initial assessment
    initial_assessment = RiskAssessment(
        risk_id=risk.id,
        assessment_type=RiskAssessmentType.INITIAL,
        assessor_id=current_user.id,
        probability=risk_data.probability,
        severity=risk_data.severity,
        rationale="Initial risk assessment at creation",
    )
    db.add(initial_assessment)

    await log_risk_event(
        db=db,
        user=current_user,
        risk_id=risk.id,
        event="create",
        result="success",
        details={"risk_code": risk_code, "risk_level": risk.risk_level.value},
    )

    return RiskResponse.model_validate(risk)


@router.get(
    "",
    response_model=RiskListResponse,
    summary="List risks",
)
async def list_risks(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status_filter: Optional[RiskStatus] = None,
    level_filter: Optional[RiskLevel] = None,
    category_filter: Optional[RiskCategory] = None,
) -> RiskListResponse:
    """List risks with optional filters."""
    if not can_manage_risks(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view risks",
        )

    query = select(Risk)
    count_query = select(func.count(Risk.id))

    if status_filter:
        query = query.where(Risk.status == status_filter)
        count_query = count_query.where(Risk.status == status_filter)

    if level_filter:
        query = query.where(Risk.risk_level == level_filter)
        count_query = count_query.where(Risk.risk_level == level_filter)

    if category_filter:
        query = query.where(Risk.category == category_filter)
        count_query = count_query.where(Risk.category == category_filter)

    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Get paginated results
    query = query.order_by(desc(Risk.risk_score), desc(Risk.created_at))
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    risks = result.scalars().all()

    return RiskListResponse(
        items=[RiskResponse.model_validate(r) for r in risks],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/matrix",
    response_model=RiskMatrixResponse,
    summary="Get 5×5 Risk Matrix",
)
async def get_risk_matrix(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    status_filter: Optional[RiskStatus] = None,
) -> RiskMatrixResponse:
    """
    Get 5×5 Risk Matrix for visualization.

    Returns matrix[probability][severity] with risk counts and IDs.
    """
    if not can_manage_risks(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view risk matrix",
        )

    query = select(Risk.id, Risk.probability, Risk.severity, Risk.risk_level)

    if status_filter:
        query = query.where(Risk.status == status_filter)
    else:
        # Default: exclude closed risks
        query = query.where(Risk.status != RiskStatus.CLOSED)

    result = await db.execute(query)
    risks = result.fetchall()

    # Initialize 5×5 matrix
    matrix = []
    level_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}

    for p in range(1, 6):  # probability 1-5
        row = []
        for s in range(1, 6):  # severity 1-5
            cell_risks = [r for r in risks if r.probability == p and r.severity == s]
            level = calculate_risk_level(p, s)

            cell = RiskMatrixCell(
                probability=p,
                severity=s,
                count=len(cell_risks),
                risk_ids=[r.id for r in cell_risks],
                level=level,
            )
            row.append(cell)

            level_counts[level.value] += len(cell_risks)

        matrix.append(row)

    return RiskMatrixResponse(
        matrix=matrix,
        total_risks=len(risks),
        by_level=level_counts,
    )


@router.get(
    "/{risk_id}",
    response_model=RiskResponse,
    summary="Get risk by ID",
)
async def get_risk(
    risk_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RiskResponse:
    """Get a single risk by ID."""
    if not can_manage_risks(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view risks",
        )

    result = await db.execute(select(Risk).where(Risk.id == risk_id))
    risk = result.scalar_one_or_none()

    if risk is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Risk not found",
        )

    return RiskResponse.model_validate(risk)


@router.put(
    "/{risk_id}",
    response_model=RiskResponse,
    summary="Update risk",
)
async def update_risk(
    risk_id: int,
    risk_data: RiskUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RiskResponse:
    """Update a risk."""
    if not can_manage_risks(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update risks",
        )

    result = await db.execute(select(Risk).where(Risk.id == risk_id))
    risk = result.scalar_one_or_none()

    if risk is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Risk not found",
        )

    # Check if closing risk requires DIRECTOR+
    if risk_data.status == RiskStatus.CLOSED and not can_close_risks(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="DIRECTOR or higher required to close risks",
        )

    changes = {}
    update_data = risk_data.model_dump(exclude_unset=True)

    for field, new_value in update_data.items():
        old_value = getattr(risk, field)
        if old_value != new_value:
            old_str = old_value.value if hasattr(old_value, 'value') else str(old_value)
            new_str = new_value.value if hasattr(new_value, 'value') else str(new_value)
            changes[field] = {"old": old_str, "new": new_str}
            setattr(risk, field, new_value)

    # Recalculate risk score and level if P or S changed
    if "probability" in update_data or "severity" in update_data:
        risk.risk_score = risk.probability * risk.severity
        risk.risk_level = calculate_risk_level(risk.probability, risk.severity)

    # Handle closing
    if risk_data.status == RiskStatus.CLOSED:
        risk.closed_at = datetime.now(timezone.utc)
        risk.closed_by_id = current_user.id

    if changes:
        await log_risk_event(
            db=db,
            user=current_user,
            risk_id=risk_id,
            event="update",
            result="success",
            details={"changes": changes},
        )

    await db.commit()
    await db.refresh(risk)

    return RiskResponse.model_validate(risk)


@router.post(
    "/{risk_id}/assessments",
    response_model=RiskAssessmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add risk assessment (re-evaluate)",
)
async def create_risk_assessment(
    risk_id: int,
    assessment_data: RiskAssessmentCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RiskAssessmentResponse:
    """
    Add a new risk assessment (re-evaluation).

    Updates the risk's current P×S values based on this assessment.
    """
    if not can_manage_risks(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to assess risks",
        )

    result = await db.execute(select(Risk).where(Risk.id == risk_id))
    risk = result.scalar_one_or_none()

    if risk is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Risk not found",
        )

    assessment = RiskAssessment(
        risk_id=risk_id,
        assessment_type=assessment_data.assessment_type,
        assessor_id=current_user.id,
        probability=assessment_data.probability,
        severity=assessment_data.severity,
        rationale=assessment_data.rationale,
    )

    db.add(assessment)
    await db.flush()
    await db.refresh(assessment)

    # Update risk based on assessment type
    if assessment_data.assessment_type == RiskAssessmentType.POST_TREATMENT:
        # Post-treatment: update residual risk
        risk.residual_probability = assessment_data.probability
        risk.residual_severity = assessment_data.severity
    else:
        # Other types: update current risk
        risk.probability = assessment_data.probability
        risk.severity = assessment_data.severity

    await log_risk_event(
        db=db,
        user=current_user,
        risk_id=risk_id,
        event="assess",
        result="success",
        details={
            "type": assessment_data.assessment_type.value,
            "score": assessment.score,
        },
    )

    return RiskAssessmentResponse.model_validate(assessment)


@router.get(
    "/{risk_id}/assessments",
    response_model=List[RiskAssessmentResponse],
    summary="Get risk assessment history",
)
async def list_risk_assessments(
    risk_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> List[RiskAssessmentResponse]:
    """Get all assessments for a risk (history)."""
    if not can_manage_risks(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view risk assessments",
        )

    result = await db.execute(
        select(RiskAssessment)
        .where(RiskAssessment.risk_id == risk_id)
        .order_by(desc(RiskAssessment.assessed_at))
    )
    assessments = result.scalars().all()

    return [RiskAssessmentResponse.model_validate(a) for a in assessments]


# === Auto-Escalation Endpoints ===

@router.get(
    "/escalation/candidates",
    response_model=List[EscalationCandidate],
    summary="Get PSR escalation candidates",
)
async def get_escalation_candidates(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    days: int = Query(30, ge=1, le=365, description="최근 N일 이내 건"),
) -> List[EscalationCandidate]:
    """
    자동 승격 후보 PSR 목록 조회.

    Grade 기준 (SEVERE, DEATH)으로 승격 대상을 자동 식별합니다.
    """
    if not can_manage_risks(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view escalation candidates",
        )

    candidates = await find_escalation_candidates(db, days=days)
    return candidates


@router.post(
    "/escalation/run",
    response_model=EscalationResult,
    summary="Run auto-escalation batch",
)
async def run_escalation_batch(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    days: int = Query(30, ge=1, le=365, description="최근 N일 이내 건"),
) -> EscalationResult:
    """
    자동 승격 배치 실행.

    SEVERE/DEATH 등급의 PSR을 자동으로 Risk Register에 등록합니다.
    QPS_STAFF 이상 권한 필요.
    """
    if not can_manage_risks(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to run escalation",
        )

    result = await run_auto_escalation(db=db, user=current_user, days=days)
    return result


@router.post(
    "/escalation/{incident_id}",
    response_model=RiskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Manually escalate PSR to Risk",
)
async def escalate_single_incident(
    incident_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    probability: Optional[int] = Query(None, ge=1, le=5),
    severity: Optional[int] = Query(None, ge=1, le=5),
    reason: Optional[str] = Query(None, max_length=500),
) -> RiskResponse:
    """
    단일 PSR을 수동으로 Risk로 승격.

    자동 승격 기준에 해당하지 않는 PSR도 QPS 담당자가 판단하여
    수동으로 Risk Register에 등록할 수 있습니다.
    """
    if not can_manage_risks(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to escalate incidents",
        )

    try:
        risk = await escalate_incident_to_risk(
            db=db,
            incident_id=incident_id,
            user=current_user,
            probability=probability,
            severity=severity,
            reason=reason or "QPS 담당자 수동 승격",
        )
        return RiskResponse.model_validate(risk)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
