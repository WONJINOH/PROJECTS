"""
Actions API

CAPA (Corrective and Preventive Action) management.
Tracks actions with owner/due-date/DoD and evidence attachments.
"""

from datetime import datetime, timezone, date
from typing import Annotated, Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.action import Action, ActionStatus, ActionPriority
from app.models.incident import Incident
from app.models.attachment import Attachment
from app.models.user import User, Role
from app.models.audit import AuditLog, AuditEventType
from app.schemas.action import (
    ActionCreate,
    ActionUpdate,
    ActionComplete,
    ActionVerify,
    ActionResponse,
    ActionListResponse,
)
from app.security.dependencies import get_current_active_user, require_permission
from app.security.rbac import Permission

router = APIRouter()


async def log_action_event(
    db: AsyncSession,
    user: User,
    action_id: int | None,
    incident_id: int,
    event: str,
    result: str,
    details: dict | None = None,
) -> None:
    """Log action event for audit."""
    timestamp = datetime.now(timezone.utc)
    previous_hash = "genesis"

    entry_hash = AuditLog.calculate_hash(
        event_type=AuditEventType.INCIDENT_UPDATE.value,  # Using incident update for actions
        timestamp=timestamp,
        user_id=user.id,
        resource_id=str(action_id) if action_id else None,
        previous_hash=previous_hash,
    )

    audit_log = AuditLog(
        event_type=AuditEventType.INCIDENT_UPDATE,
        timestamp=timestamp,
        user_id=user.id,
        user_role=user.role.value,
        username=user.username,
        resource_type="action",
        resource_id=str(action_id) if action_id else None,
        action_detail={"event": event, "incident_id": incident_id, **(details or {})},
        result=result,
        previous_hash=previous_hash,
        entry_hash=entry_hash,
    )
    db.add(audit_log)


def can_manage_actions(user: User, incident: Incident) -> bool:
    """Check if user can manage actions for an incident."""
    if user.role in [Role.QPS_STAFF, Role.VICE_CHAIR, Role.DIRECTOR, Role.MASTER]:
        return True
    return False


def can_complete_action(user: User, action: Action) -> bool:
    """Check if user can complete an action."""
    # Action owner or higher roles
    if user.role in [Role.QPS_STAFF, Role.VICE_CHAIR, Role.DIRECTOR, Role.MASTER]:
        return True
    return False


def can_verify_action(user: User) -> bool:
    """Check if user can verify actions."""
    # Only QPS_STAFF or higher can verify
    return user.role in [Role.QPS_STAFF, Role.VICE_CHAIR, Role.DIRECTOR, Role.MASTER]


def action_to_response(action: Action) -> ActionResponse:
    """Convert Action model to response schema."""
    return ActionResponse(
        id=action.id,
        incident_id=action.incident_id,
        title=action.title,
        description=action.description,
        owner=action.owner,
        due_date=action.due_date,
        definition_of_done=action.definition_of_done,
        priority=action.priority,
        status=action.status,
        evidence_attachment_id=action.evidence_attachment_id,
        completed_at=action.completed_at,
        completed_by_id=action.completed_by_id,
        completion_notes=action.completion_notes,
        verified_at=action.verified_at,
        verified_by_id=action.verified_by_id,
        verification_notes=action.verification_notes,
        created_by_id=action.created_by_id,
        created_at=action.created_at,
        updated_at=action.updated_at,
        is_overdue=action.is_overdue(),
    )


@router.post(
    "/",
    response_model=ActionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new CAPA action",
)
async def create_action(
    action_data: ActionCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ActionResponse:
    """
    Create a new CAPA action for an incident.

    Required fields:
    - title: Action title
    - owner: Person responsible (담당자)
    - due_date: Deadline (기한)
    - definition_of_done: Completion criteria (DoD)
    """
    # Verify incident exists
    result = await db.execute(
        select(Incident).where(
            and_(Incident.id == action_data.incident_id, Incident.is_deleted == False)
        )
    )
    incident = result.scalar_one_or_none()

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )

    if not can_manage_actions(current_user, incident):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create actions for this incident",
        )

    # Create action
    action = Action(
        incident_id=action_data.incident_id,
        title=action_data.title,
        description=action_data.description,
        owner=action_data.owner,
        due_date=action_data.due_date,
        definition_of_done=action_data.definition_of_done,
        priority=action_data.priority,
        status=ActionStatus.OPEN,
        created_by_id=current_user.id,
    )

    db.add(action)
    await db.flush()
    await db.refresh(action)

    await log_action_event(
        db=db,
        user=current_user,
        action_id=action.id,
        incident_id=action_data.incident_id,
        event="create",
        result="success",
        details={"title": action_data.title, "owner": action_data.owner},
    )

    return action_to_response(action)


@router.get(
    "/incident/{incident_id}",
    response_model=ActionListResponse,
    summary="List actions for incident",
)
async def list_actions_for_incident(
    incident_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status_filter: Optional[ActionStatus] = Query(None, alias="status"),
) -> ActionListResponse:
    """
    List all actions for a specific incident.
    """
    # Verify incident exists and user has access
    result = await db.execute(
        select(Incident).where(
            and_(Incident.id == incident_id, Incident.is_deleted == False)
        )
    )
    incident = result.scalar_one_or_none()

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )

    # Build query
    filters = [Action.incident_id == incident_id, Action.is_deleted == False]
    if status_filter:
        filters.append(Action.status == status_filter)

    # Count
    count_query = select(func.count(Action.id)).where(and_(*filters))
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Get items
    query = (
        select(Action)
        .where(and_(*filters))
        .order_by(Action.due_date.asc(), Action.created_at.asc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    actions = result.scalars().all()

    return ActionListResponse(
        items=[action_to_response(a) for a in actions],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{action_id}",
    response_model=ActionResponse,
    summary="Get action details",
)
async def get_action(
    action_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ActionResponse:
    """
    Get details of a specific action.
    """
    result = await db.execute(
        select(Action).where(
            and_(Action.id == action_id, Action.is_deleted == False)
        )
    )
    action = result.scalar_one_or_none()

    if action is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Action not found",
        )

    return action_to_response(action)


@router.put(
    "/{action_id}",
    response_model=ActionResponse,
    summary="Update action",
)
async def update_action(
    action_id: int,
    action_data: ActionUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ActionResponse:
    """
    Update an action's details.

    Cannot update completed or verified actions.
    """
    result = await db.execute(
        select(Action).where(
            and_(Action.id == action_id, Action.is_deleted == False)
        )
    )
    action = result.scalar_one_or_none()

    if action is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Action not found",
        )

    if action.status in [ActionStatus.COMPLETED, ActionStatus.VERIFIED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update completed or verified actions",
        )

    # Get incident for permission check
    result = await db.execute(
        select(Incident).where(Incident.id == action.incident_id)
    )
    incident = result.scalar_one_or_none()

    if not can_manage_actions(current_user, incident):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this action",
        )

    # Update fields
    changes = {}
    update_data = action_data.model_dump(exclude_unset=True)

    for field, new_value in update_data.items():
        old_value = getattr(action, field)
        if old_value != new_value:
            changes[field] = {"old": str(old_value), "new": str(new_value)}
            setattr(action, field, new_value)

    if changes:
        action.updated_at = datetime.now(timezone.utc)
        await log_action_event(
            db=db,
            user=current_user,
            action_id=action_id,
            incident_id=action.incident_id,
            event="update",
            result="success",
            details={"changes": changes},
        )

    return action_to_response(action)


@router.post(
    "/{action_id}/start",
    response_model=ActionResponse,
    summary="Start working on action",
)
async def start_action(
    action_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ActionResponse:
    """
    Mark an action as in progress.
    """
    result = await db.execute(
        select(Action).where(
            and_(Action.id == action_id, Action.is_deleted == False)
        )
    )
    action = result.scalar_one_or_none()

    if action is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Action not found",
        )

    if action.status != ActionStatus.OPEN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot start action with status '{action.status.value}'",
        )

    action.status = ActionStatus.IN_PROGRESS
    action.updated_at = datetime.now(timezone.utc)

    await log_action_event(
        db=db,
        user=current_user,
        action_id=action_id,
        incident_id=action.incident_id,
        event="start",
        result="success",
    )

    return action_to_response(action)


@router.post(
    "/{action_id}/complete",
    response_model=ActionResponse,
    summary="Complete action",
)
async def complete_action(
    action_id: int,
    complete_data: ActionComplete,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ActionResponse:
    """
    Mark an action as completed.

    Optionally attach evidence and completion notes.
    Action moves to COMPLETED status, awaiting verification.
    """
    result = await db.execute(
        select(Action).where(
            and_(Action.id == action_id, Action.is_deleted == False)
        )
    )
    action = result.scalar_one_or_none()

    if action is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Action not found",
        )

    if not action.can_complete():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot complete action with status '{action.status.value}'",
        )

    if not can_complete_action(current_user, action):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to complete this action",
        )

    # Verify evidence attachment if provided
    if complete_data.evidence_attachment_id:
        result = await db.execute(
            select(Attachment).where(
                and_(
                    Attachment.id == complete_data.evidence_attachment_id,
                    Attachment.incident_id == action.incident_id,
                    Attachment.is_deleted == False,
                )
            )
        )
        if result.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Evidence attachment not found or not linked to this incident",
            )
        action.evidence_attachment_id = complete_data.evidence_attachment_id

    action.status = ActionStatus.COMPLETED
    action.completed_at = datetime.now(timezone.utc)
    action.completed_by_id = current_user.id
    action.completion_notes = complete_data.completion_notes
    action.updated_at = datetime.now(timezone.utc)

    await log_action_event(
        db=db,
        user=current_user,
        action_id=action_id,
        incident_id=action.incident_id,
        event="complete",
        result="success",
        details={"evidence_id": complete_data.evidence_attachment_id},
    )

    return action_to_response(action)


@router.post(
    "/{action_id}/verify",
    response_model=ActionResponse,
    summary="Verify completed action",
)
async def verify_action(
    action_id: int,
    verify_data: ActionVerify,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ActionResponse:
    """
    Verify a completed action.

    Only QPS staff or higher can verify.
    Final status indicating action is fully closed.
    """
    result = await db.execute(
        select(Action).where(
            and_(Action.id == action_id, Action.is_deleted == False)
        )
    )
    action = result.scalar_one_or_none()

    if action is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Action not found",
        )

    if not action.can_verify():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot verify action with status '{action.status.value}'",
        )

    if not can_verify_action(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to verify actions",
        )

    # Cannot verify own completion
    if action.completed_by_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot verify your own completed action",
        )

    action.status = ActionStatus.VERIFIED
    action.verified_at = datetime.now(timezone.utc)
    action.verified_by_id = current_user.id
    action.verification_notes = verify_data.verification_notes
    action.updated_at = datetime.now(timezone.utc)

    await log_action_event(
        db=db,
        user=current_user,
        action_id=action_id,
        incident_id=action.incident_id,
        event="verify",
        result="success",
    )

    return action_to_response(action)


@router.post(
    "/{action_id}/cancel",
    response_model=ActionResponse,
    summary="Cancel action",
)
async def cancel_action(
    action_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ActionResponse:
    """
    Cancel an action.

    Only OPEN or IN_PROGRESS actions can be cancelled.
    """
    result = await db.execute(
        select(Action).where(
            and_(Action.id == action_id, Action.is_deleted == False)
        )
    )
    action = result.scalar_one_or_none()

    if action is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Action not found",
        )

    if action.status not in [ActionStatus.OPEN, ActionStatus.IN_PROGRESS]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel action with status '{action.status.value}'",
        )

    # Only QPS_STAFF or higher can cancel
    if current_user.role not in [Role.QPS_STAFF, Role.VICE_CHAIR, Role.DIRECTOR, Role.MASTER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to cancel actions",
        )

    action.status = ActionStatus.CANCELLED
    action.updated_at = datetime.now(timezone.utc)

    await log_action_event(
        db=db,
        user=current_user,
        action_id=action_id,
        incident_id=action.incident_id,
        event="cancel",
        result="success",
    )

    return action_to_response(action)


@router.get(
    "/overdue",
    response_model=List[ActionResponse],
    summary="List overdue actions",
)
async def list_overdue_actions(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> List[ActionResponse]:
    """
    List all overdue actions (past due date, not completed/verified).
    """
    today = date.today()

    result = await db.execute(
        select(Action).where(
            and_(
                Action.is_deleted == False,
                Action.status.in_([ActionStatus.OPEN, ActionStatus.IN_PROGRESS]),
                Action.due_date < today,
            )
        ).order_by(Action.due_date.asc())
    )
    actions = result.scalars().all()

    return [action_to_response(a) for a in actions]
