"""
Auto-Escalation Service

PSR (Patient Safety Report) → Risk Register 자동 승격 서비스

승격 기준:
1. Grade 기반: SEVERE 또는 DEATH 등급
2. 반복 발생: 동일 카테고리 + 부서에서 설정 기간 내 N건 이상
3. 수동 요청: QPS_STAFF 이상이 명시적 승격 요청

승격 시 동작:
1. Risk 레코드 자동 생성 (source_type=PSR)
2. 초기 P×S 값 설정 (기본값 또는 룰 기반)
3. Audit 로그 기록
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, List

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.incident import Incident, IncidentGrade, IncidentCategory
from app.models.risk import (
    Risk,
    RiskAssessment,
    RiskSourceType,
    RiskCategory,
    RiskStatus,
    RiskAssessmentType,
)
from app.models.user import User
from app.models.audit import AuditLog, AuditEventType
from app.schemas.risk import EscalationCandidate, EscalationResult, RiskResponse


# Grade → Suggested Probability/Severity 매핑
GRADE_PS_MAPPING = {
    IncidentGrade.DEATH: (5, 5),       # 사망: 최고 P×S
    IncidentGrade.SEVERE: (4, 5),      # 영구손상: 높은 P, 최고 S
    IncidentGrade.MODERATE: (3, 4),    # 중등도: 중간 P, 높은 S
    IncidentGrade.MILD: (2, 3),        # 경증: 낮은 P, 중간 S
    IncidentGrade.NO_HARM: (2, 2),     # 위해없음: 낮은 P/S
    IncidentGrade.NEAR_MISS: (3, 2),   # 근접오류: 중간 P, 낮은 S (잠재위험)
}

# Incident Category → Risk Category 매핑
CATEGORY_MAPPING = {
    IncidentCategory.FALL: RiskCategory.FALL,
    IncidentCategory.MEDICATION: RiskCategory.MEDICATION,
    IncidentCategory.PRESSURE_ULCER: RiskCategory.PRESSURE_ULCER,
    IncidentCategory.INFECTION: RiskCategory.INFECTION,
    IncidentCategory.MEDICAL_DEVICE: RiskCategory.OTHER,
    IncidentCategory.SURGERY: RiskCategory.PROCEDURE,
    IncidentCategory.TRANSFUSION: RiskCategory.TRANSFUSION,
    IncidentCategory.THERMAL_INJURY: RiskCategory.OTHER,
    IncidentCategory.PROCEDURE: RiskCategory.PROCEDURE,
    IncidentCategory.ENVIRONMENT: RiskCategory.ENVIRONMENT,
    IncidentCategory.SECURITY: RiskCategory.SECURITY,
    IncidentCategory.ELOPEMENT: RiskCategory.OTHER,
    IncidentCategory.VIOLENCE: RiskCategory.SECURITY,
    IncidentCategory.FIRE: RiskCategory.ENVIRONMENT,
    IncidentCategory.SUICIDE: RiskCategory.OTHER,
    IncidentCategory.SELF_HARM: RiskCategory.OTHER,
    IncidentCategory.OTHER: RiskCategory.OTHER,
}

# 반복 발생 기준
REPEAT_THRESHOLD = 3  # 동일 카테고리에서 N건 이상
REPEAT_WINDOW_DAYS = 90  # 최근 N일 이내


async def generate_risk_code(db: AsyncSession) -> str:
    """Generate unique risk code: R-YYYY-NNN"""
    from sqlalchemy import desc
    year = datetime.now().year
    prefix = f"R-{year}-"

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


async def log_escalation_event(
    db: AsyncSession,
    user: User,
    incident_id: int,
    risk_id: int,
    reason: str,
) -> None:
    """Log escalation event for audit."""
    timestamp = datetime.now(timezone.utc)
    previous_hash = "genesis"

    entry_hash = AuditLog.calculate_hash(
        event_type=AuditEventType.RISK_ESCALATE.value,
        timestamp=timestamp,
        user_id=user.id,
        resource_id=str(risk_id),
        previous_hash=previous_hash,
    )

    audit_log = AuditLog(
        event_type=AuditEventType.RISK_ESCALATE,
        timestamp=timestamp,
        user_id=user.id,
        user_role=user.role.value,
        username=user.username,
        resource_type="risk",
        resource_id=str(risk_id),
        action_detail={
            "action": "auto_escalation",
            "source_incident_id": incident_id,
            "reason": reason,
        },
        result="success",
        previous_hash=previous_hash,
        entry_hash=entry_hash,
    )
    db.add(audit_log)


def should_auto_escalate_by_grade(incident: Incident) -> tuple[bool, str]:
    """
    Grade 기반 자동 승격 여부 판단.

    Returns:
        (should_escalate, reason)
    """
    if incident.grade == IncidentGrade.DEATH:
        return True, "사망 사건 (Grade: DEATH)"
    if incident.grade == IncidentGrade.SEVERE:
        return True, "영구 손상 사건 (Grade: SEVERE)"
    return False, ""


async def check_repeat_pattern(
    db: AsyncSession,
    incident: Incident,
) -> tuple[bool, str, int]:
    """
    반복 발생 패턴 확인.

    Returns:
        (should_escalate, reason, repeat_count)
    """
    window_start = datetime.now(timezone.utc) - timedelta(days=REPEAT_WINDOW_DAYS)

    # 동일 카테고리 + 부서에서 최근 N일 이내 건수
    count_result = await db.execute(
        select(func.count(Incident.id))
        .where(
            and_(
                Incident.category == incident.category,
                Incident.department == incident.department,
                Incident.created_at >= window_start,
                Incident.is_deleted == False,
            )
        )
    )
    count = count_result.scalar_one()

    if count >= REPEAT_THRESHOLD:
        return (
            True,
            f"반복 발생 패턴 ({incident.department} 부서, {incident.category.value} 카테고리, {REPEAT_WINDOW_DAYS}일 내 {count}건)",
            count,
        )

    return False, "", count


async def find_escalation_candidates(
    db: AsyncSession,
    days: int = 30,
    already_escalated: bool = False,
) -> List[EscalationCandidate]:
    """
    자동 승격 후보 PSR 목록 조회.

    Args:
        days: 최근 N일 이내 건만 대상
        already_escalated: True면 이미 승격된 건도 포함

    Returns:
        승격 후보 목록
    """
    window_start = datetime.now(timezone.utc) - timedelta(days=days)

    # 이미 Risk로 연결된 incident_id 목록
    escalated_ids = []
    if not already_escalated:
        result = await db.execute(
            select(Risk.source_incident_id)
            .where(Risk.source_incident_id.isnot(None))
        )
        escalated_ids = [r for r in result.scalars().all()]

    # Grade 기준 승격 후보 조회
    query = (
        select(Incident)
        .where(
            and_(
                Incident.created_at >= window_start,
                Incident.is_deleted == False,
                Incident.grade.in_([IncidentGrade.DEATH, IncidentGrade.SEVERE]),
            )
        )
    )

    if escalated_ids:
        query = query.where(Incident.id.notin_(escalated_ids))

    result = await db.execute(query)
    incidents = result.scalars().all()

    candidates = []
    for incident in incidents:
        should_escalate, reason = should_auto_escalate_by_grade(incident)
        if should_escalate:
            p, s = GRADE_PS_MAPPING.get(incident.grade, (3, 3))
            candidates.append(EscalationCandidate(
                incident_id=incident.id,
                category=incident.category.value,
                grade=incident.grade.value,
                occurred_at=incident.occurred_at,
                reason=reason,
                suggested_probability=p,
                suggested_severity=s,
            ))

    return candidates


async def escalate_incident_to_risk(
    db: AsyncSession,
    incident_id: int,
    user: User,
    probability: Optional[int] = None,
    severity: Optional[int] = None,
    reason: Optional[str] = None,
) -> Risk:
    """
    단일 PSR을 Risk로 승격.

    Args:
        incident_id: 승격할 PSR ID
        user: 승격 요청자
        probability: 수동 지정 시 P 값 (1-5)
        severity: 수동 지정 시 S 값 (1-5)
        reason: 승격 사유 (자동/수동)

    Returns:
        생성된 Risk
    """
    # Get incident
    result = await db.execute(
        select(Incident).where(
            and_(Incident.id == incident_id, Incident.is_deleted == False)
        )
    )
    incident = result.scalar_one_or_none()

    if incident is None:
        raise ValueError(f"Incident {incident_id} not found")

    # Check if already escalated
    existing = await db.execute(
        select(Risk).where(Risk.source_incident_id == incident_id)
    )
    if existing.scalar_one_or_none():
        raise ValueError(f"Incident {incident_id} is already escalated to a risk")

    # Determine P×S values
    if probability is None or severity is None:
        default_p, default_s = GRADE_PS_MAPPING.get(incident.grade, (3, 3))
        probability = probability or default_p
        severity = severity or default_s

    # Determine risk category
    risk_category = CATEGORY_MAPPING.get(incident.category, RiskCategory.OTHER)

    # Determine reason
    if not reason:
        should_escalate, auto_reason = should_auto_escalate_by_grade(incident)
        if should_escalate:
            reason = auto_reason
        else:
            reason = "수동 승격 요청"

    # Generate risk code
    risk_code = await generate_risk_code(db)

    # Create risk
    risk = Risk(
        risk_code=risk_code,
        title=f"[PSR] {incident.category.value} - {incident.location}",
        description=incident.description,
        source_type=RiskSourceType.PSR,
        source_incident_id=incident_id,
        source_detail=f"PSR #{incident_id} 에서 자동 승격",
        category=risk_category,
        current_controls=incident.immediate_action,
        probability=probability,
        severity=severity,
        owner_id=user.id,  # 초기 책임자는 승격 요청자
        created_by_id=user.id,
        auto_escalated=True,
        escalation_reason=reason,
    )

    db.add(risk)
    await db.flush()
    await db.refresh(risk)

    # Create initial assessment
    initial_assessment = RiskAssessment(
        risk_id=risk.id,
        assessment_type=RiskAssessmentType.INITIAL,
        assessor_id=user.id,
        probability=probability,
        severity=severity,
        rationale=f"PSR #{incident_id} 승격 시 자동 생성된 초기 평가. 사유: {reason}",
    )
    db.add(initial_assessment)

    # Log audit
    await log_escalation_event(
        db=db,
        user=user,
        incident_id=incident_id,
        risk_id=risk.id,
        reason=reason,
    )

    # Commit all changes (risk + assessment + audit log)
    await db.commit()
    await db.refresh(risk)

    return risk


async def run_auto_escalation(
    db: AsyncSession,
    user: User,
    days: int = 30,
) -> EscalationResult:
    """
    자동 승격 배치 실행.

    Args:
        user: 배치 실행자 (시스템 또는 관리자)
        days: 최근 N일 이내 건만 대상

    Returns:
        승격 결과
    """
    # Find candidates
    candidates = await find_escalation_candidates(db, days=days)

    created_risks = []
    for candidate in candidates:
        try:
            risk = await escalate_incident_to_risk(
                db=db,
                incident_id=candidate.incident_id,
                user=user,
                probability=candidate.suggested_probability,
                severity=candidate.suggested_severity,
                reason=candidate.reason,
            )
            created_risks.append(RiskResponse.model_validate(risk))
        except ValueError:
            # Skip if already escalated or not found
            continue

    return EscalationResult(
        escalated_count=len(created_risks),
        candidates=candidates,
        created_risks=created_risks,
    )
