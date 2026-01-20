"""
Approval Workflow API

Implements 3-level approval flow:
1. QPS (L1) - QI담당자
2. Vice Chair (L2) - 부원장
3. Director (L3) - 원장
"""

from datetime import datetime, timezone
from typing import Annotated, Optional, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.incident import Incident
from app.models.approval import Approval, ApprovalLevel, ApprovalStatus
from app.models.user import User, Role
from app.models.audit import AuditLog, AuditEventType
from app.schemas.approval import ApprovalAction, ApprovalResponse, ApprovalRecord
from app.security.dependencies import get_current_user, get_current_active_user, require_permission
from app.security.rbac import Permission

router = APIRouter()


# Mapping of roles to approval levels they can perform
ROLE_TO_APPROVAL_LEVEL = {
    Role.QPS_STAFF: ApprovalLevel.L1_QPS,
    Role.VICE_CHAIR: ApprovalLevel.L2_VICE_CHAIR,
    Role.DIRECTOR: ApprovalLevel.L3_DIRECTOR,
    Role.MASTER: None,  # MASTER can approve any level
}

# Approval level sequence
APPROVAL_SEQUENCE = [
    ApprovalLevel.L1_QPS,
    ApprovalLevel.L2_VICE_CHAIR,
    ApprovalLevel.L3_DIRECTOR,
]


async def log_approval_event(
    db: AsyncSession,
    user: User,
    incident_id: int,
    action: str,
    level: ApprovalLevel,
    result: str,
    details: dict | None = None,
) -> None:
    """Log approval event for PIPA compliance."""
    timestamp = datetime.now(timezone.utc)
    previous_hash = "genesis"

    entry_hash = AuditLog.calculate_hash(
        event_type=AuditEventType.APPROVAL_ACTION.value,
        timestamp=timestamp,
        user_id=user.id,
        resource_id=str(incident_id),
        previous_hash=previous_hash,
    )

    audit_log = AuditLog(
        event_type=AuditEventType.APPROVAL_ACTION,
        timestamp=timestamp,
        user_id=user.id,
        user_role=user.role.value,
        username=user.username,
        resource_type="approval",
        resource_id=str(incident_id),
        action_detail={"action": action, "level": level.value, **(details or {})},
        result=result,
        previous_hash=previous_hash,
        entry_hash=entry_hash,
    )
    db.add(audit_log)


def get_next_required_level(approvals: List[Approval]) -> Optional[ApprovalLevel]:
    """Determine the next required approval level."""
    approved_levels = {
        a.level for a in approvals
        if a.status == ApprovalStatus.APPROVED
    }

    for level in APPROVAL_SEQUENCE:
        if level not in approved_levels:
            return level

    return None  # Fully approved


def get_current_level(approvals: List[Approval]) -> Optional[ApprovalLevel]:
    """Get the highest approved level."""
    approved_levels = [
        a.level for a in approvals
        if a.status == ApprovalStatus.APPROVED
    ]

    if not approved_levels:
        return None

    # Return highest level in sequence
    for level in reversed(APPROVAL_SEQUENCE):
        if level in approved_levels:
            return level

    return None


def can_approve_level(user: User, level: ApprovalLevel) -> bool:
    """Check if user can approve at a specific level."""
    if user.role == Role.MASTER:
        return True

    user_level = ROLE_TO_APPROVAL_LEVEL.get(user.role)
    if user_level is None:
        return False

    # VICE_CHAIR can approve L1 and L2
    if user.role == Role.VICE_CHAIR:
        return level in [ApprovalLevel.L1_QPS, ApprovalLevel.L2_VICE_CHAIR]

    # DIRECTOR can approve all levels
    if user.role == Role.DIRECTOR:
        return True

    # QPS_STAFF can only approve L1
    return user_level == level


async def get_incident_with_approvals(
    db: AsyncSession,
    incident_id: int,
) -> tuple[Incident, List[Approval]]:
    """Get incident and its approvals."""
    result = await db.execute(
        select(Incident)
        .where(and_(Incident.id == incident_id, Incident.is_deleted == False))
        .options(selectinload(Incident.approvals))
    )
    incident = result.scalar_one_or_none()

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )

    # Filter out cancelled/deleted approvals
    active_approvals = [
        a for a in incident.approvals
        if a.status != ApprovalStatus.REJECTED or True  # Keep all for history
    ]

    return incident, active_approvals


def build_approval_response(
    incident_id: int,
    approvals: List[Approval],
) -> ApprovalResponse:
    """Build approval response from approvals list."""
    current_level = get_current_level(approvals)
    next_level = get_next_required_level(approvals)

    history = []
    for approval in sorted(approvals, key=lambda a: a.created_at):
        # Get approver name (would need join in production)
        history.append(ApprovalRecord(
            level=approval.level,
            status=approval.status,
            approver_name=f"User {approval.approver_id}",  # Simplified
            comment=approval.comment,
            rejection_reason=approval.rejection_reason,
            decided_at=approval.decided_at,
        ))

    return ApprovalResponse(
        incident_id=incident_id,
        current_level=current_level,
        next_required_level=next_level,
        is_fully_approved=next_level is None,
        history=history,
    )


@router.get(
    "/incidents/{incident_id}/status",
    response_model=ApprovalResponse,
    summary="Get approval status",
)
async def get_approval_status(
    incident_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApprovalResponse:
    """
    Get current approval status of an incident.

    Returns:
    - Current approval level (L1/L2/L3/NONE)
    - Approval history
    - Next required approver role
    """
    incident, approvals = await get_incident_with_approvals(db, incident_id)
    return build_approval_response(incident_id, approvals)


@router.post(
    "/incidents/{incident_id}/approve",
    response_model=ApprovalResponse,
    summary="Approve incident",
)
async def approve_incident(
    incident_id: int,
    action: ApprovalAction,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApprovalResponse:
    """
    Approve an incident at the appropriate level.

    Approval flow:
    1. QPS Staff → L1 Approval
    2. Vice Chair → L2 Approval
    3. Director → L3 Approval (final)

    Each level requires previous level approval.
    """
    if action.action != "approve":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Use /reject endpoint for rejection",
        )

    incident, approvals = await get_incident_with_approvals(db, incident_id)

    # Check incident is submitted
    if incident.status not in ["submitted", "approved"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot approve incident with status '{incident.status}'",
        )

    # Determine next required level
    next_level = get_next_required_level(approvals)

    if next_level is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incident is already fully approved",
        )

    # Check user permission
    if not can_approve_level(current_user, next_level):
        await log_approval_event(
            db=db,
            user=current_user,
            incident_id=incident_id,
            action="approve",
            level=next_level,
            result="denied",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Not authorized to approve at level {next_level.value}",
        )

    # Check if user already approved at this level
    existing = [a for a in approvals if a.level == next_level and a.approver_id == current_user.id]
    if existing and existing[0].status == ApprovalStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already approved at this level",
        )

    # Create approval record
    approval = Approval(
        incident_id=incident_id,
        approver_id=current_user.id,
        level=next_level,
        status=ApprovalStatus.APPROVED,
        comment=action.comment,
        decided_at=datetime.now(timezone.utc),
    )
    db.add(approval)

    # Update incident status if fully approved
    updated_approvals = approvals + [approval]
    if get_next_required_level(updated_approvals) is None:
        incident.status = "approved"

    await db.flush()

    # Log event
    await log_approval_event(
        db=db,
        user=current_user,
        incident_id=incident_id,
        action="approve",
        level=next_level,
        result="success",
        details={"comment": action.comment},
    )

    return build_approval_response(incident_id, updated_approvals)


@router.post(
    "/incidents/{incident_id}/reject",
    response_model=ApprovalResponse,
    summary="Reject incident",
)
async def reject_incident(
    incident_id: int,
    action: ApprovalAction,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApprovalResponse:
    """
    Reject an incident with reason.

    Rejection returns incident to 'submitted' status for revision.
    Reason is required and logged.
    """
    if action.action != "reject":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Use /approve endpoint for approval",
        )

    if not action.rejection_reason:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rejection reason is required",
        )

    incident, approvals = await get_incident_with_approvals(db, incident_id)

    # Check incident is submitted or partially approved
    if incident.status not in ["submitted", "approved"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot reject incident with status '{incident.status}'",
        )

    # Determine next required level (user must be able to approve at this level to reject)
    next_level = get_next_required_level(approvals)

    if next_level is None:
        # Allow rejection of fully approved incidents by DIRECTOR/MASTER
        if current_user.role not in [Role.DIRECTOR, Role.MASTER]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only Director can reject fully approved incidents",
            )
        next_level = ApprovalLevel.L3_DIRECTOR

    # Check user permission
    if not can_approve_level(current_user, next_level):
        await log_approval_event(
            db=db,
            user=current_user,
            incident_id=incident_id,
            action="reject",
            level=next_level,
            result="denied",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Not authorized to reject at level {next_level.value}",
        )

    # Create rejection record
    rejection = Approval(
        incident_id=incident_id,
        approver_id=current_user.id,
        level=next_level,
        status=ApprovalStatus.REJECTED,
        comment=action.comment,
        rejection_reason=action.rejection_reason,
        decided_at=datetime.now(timezone.utc),
    )
    db.add(rejection)

    # Reset incident status to submitted for revision
    incident.status = "submitted"
    incident.updated_at = datetime.now(timezone.utc)

    await db.flush()

    # Log event
    await log_approval_event(
        db=db,
        user=current_user,
        incident_id=incident_id,
        action="reject",
        level=next_level,
        result="success",
        details={"reason": action.rejection_reason},
    )

    updated_approvals = approvals + [rejection]
    return build_approval_response(incident_id, updated_approvals)


@router.get(
    "/pending",
    response_model=List[dict],
    summary="List incidents pending approval",
)
async def list_pending_approvals(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> List[dict]:
    """
    List incidents pending approval by the current user's level.

    Returns incidents where:
    - Status is 'submitted'
    - Current user can approve the next required level
    """
    # Determine what level current user can approve
    if current_user.role == Role.QPS_STAFF:
        approvable_levels = [ApprovalLevel.L1_QPS]
    elif current_user.role == Role.VICE_CHAIR:
        approvable_levels = [ApprovalLevel.L1_QPS, ApprovalLevel.L2_VICE_CHAIR]
    elif current_user.role in [Role.DIRECTOR, Role.MASTER]:
        approvable_levels = list(ApprovalLevel)
    else:
        return []

    # Get submitted incidents
    result = await db.execute(
        select(Incident)
        .where(and_(
            Incident.status.in_(["submitted"]),
            Incident.is_deleted == False,
        ))
        .options(selectinload(Incident.approvals))
        .order_by(Incident.created_at.desc())
    )
    incidents = result.scalars().all()

    pending = []
    for incident in incidents:
        next_level = get_next_required_level(list(incident.approvals))
        if next_level and next_level in approvable_levels:
            pending.append({
                "incident_id": incident.id,
                "category": incident.category.value,
                "grade": incident.grade.value,
                "created_at": incident.created_at.isoformat(),
                "next_required_level": next_level.value,
            })

    return pending
