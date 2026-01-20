"""
Incident Management API

Endpoints for creating, reading, updating incident reports.
Implements RBAC and audit logging per PIPA requirements.
"""

from datetime import datetime, timezone
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.incident import Incident, IncidentCategory, IncidentGrade
from app.models.user import User, Role
from app.models.audit import AuditLog, AuditEventType
from app.schemas.incident import (
    IncidentCreate,
    IncidentResponse,
    IncidentUpdate,
    IncidentListResponse,
)
from app.security.dependencies import get_current_user, get_current_active_user, require_permission
from app.security.rbac import Permission

router = APIRouter()


async def log_incident_event(
    db: AsyncSession,
    event_type: AuditEventType,
    user: User,
    incident_id: int | None,
    result: str,
    details: dict | None = None,
) -> None:
    """Log incident event for PIPA compliance."""
    timestamp = datetime.now(timezone.utc)
    previous_hash = "genesis"  # Simplified - in production, get last hash

    entry_hash = AuditLog.calculate_hash(
        event_type=event_type.value,
        timestamp=timestamp,
        user_id=user.id,
        resource_id=str(incident_id) if incident_id else None,
        previous_hash=previous_hash,
    )

    audit_log = AuditLog(
        event_type=event_type,
        timestamp=timestamp,
        user_id=user.id,
        user_role=user.role.value,
        username=user.username,
        resource_type="incident",
        resource_id=str(incident_id) if incident_id else None,
        action_detail=details,
        result=result,
        previous_hash=previous_hash,
        entry_hash=entry_hash,
    )
    db.add(audit_log)


def can_access_incident(user: User, incident: Incident) -> bool:
    """
    Check if user can access a specific incident (row-level security).

    Rules:
    - REPORTER: Own incidents only
    - QPS_STAFF: Same department
    - VICE_CHAIR, DIRECTOR, MASTER: All incidents
    """
    if user.role in [Role.VICE_CHAIR, Role.DIRECTOR, Role.MASTER]:
        return True
    if user.role == Role.QPS_STAFF:
        return incident.department == user.department
    if user.role == Role.REPORTER:
        return incident.reporter_id == user.id
    return False


def can_edit_incident(user: User, incident: Incident) -> bool:
    """
    Check if user can edit a specific incident.

    Rules:
    - REPORTER: Own drafts only
    - QPS_STAFF: Same department
    - VICE_CHAIR, DIRECTOR, MASTER: Any incident
    """
    if user.role in [Role.VICE_CHAIR, Role.DIRECTOR, Role.MASTER]:
        return True
    if user.role == Role.QPS_STAFF:
        return incident.department == user.department
    if user.role == Role.REPORTER:
        return incident.reporter_id == user.id and incident.status == "draft"
    return False


def build_access_filter(user: User):
    """Build SQLAlchemy filter for row-level access control."""
    if user.role in [Role.VICE_CHAIR, Role.DIRECTOR, Role.MASTER]:
        return Incident.is_deleted == False
    if user.role == Role.QPS_STAFF:
        return and_(
            Incident.is_deleted == False,
            Incident.department == user.department,
        )
    # REPORTER or ADMIN
    return and_(
        Incident.is_deleted == False,
        Incident.reporter_id == user.id,
    )


@router.post(
    "/",
    response_model=IncidentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new incident report",
)
async def create_incident(
    incident_data: IncidentCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> IncidentResponse:
    """
    Create a new patient safety incident report.

    Required fields (Common page):
    - category: Incident category (FALL, MEDICATION, PRESSURE_ULCER, etc.)
    - grade: Severity grade (NEAR_MISS, NO_HARM, MILD, MODERATE, SEVERE, DEATH)
    - occurred_at: When the incident occurred
    - location: Where the incident occurred
    - description: What happened
    - immediate_action: REQUIRED - What was done immediately
    - reported_at: REQUIRED - When this report was created
    - reporter_name: Required except for NEAR_MISS grade
    """
    # Create incident record
    incident = Incident(
        category=incident_data.category,
        grade=incident_data.grade,
        occurred_at=incident_data.occurred_at,
        location=incident_data.location,
        description=incident_data.description,
        immediate_action=incident_data.immediate_action,
        reported_at=incident_data.reported_at,
        reporter_name=incident_data.reporter_name,
        root_cause=incident_data.root_cause,
        improvements=incident_data.improvements,
        department=incident_data.department or current_user.department,
        reporter_id=current_user.id,
        status="draft",
    )

    db.add(incident)
    await db.flush()
    await db.refresh(incident)

    # Log audit event
    await log_incident_event(
        db=db,
        event_type=AuditEventType.INCIDENT_CREATE,
        user=current_user,
        incident_id=incident.id,
        result="success",
        details={
            "category": incident_data.category.value,
            "grade": incident_data.grade.value,
        },
    )

    return IncidentResponse.model_validate(incident)


@router.get(
    "/",
    response_model=IncidentListResponse,
    summary="List incidents",
)
async def list_incidents(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    category: Optional[IncidentCategory] = None,
    grade: Optional[IncidentGrade] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    department: Optional[str] = None,
) -> IncidentListResponse:
    """
    List incidents visible to the current user.

    Access rules:
    - REPORTER: Own incidents only
    - QPS_STAFF: Department incidents
    - VICE_CHAIR, DIRECTOR, MASTER: All incidents
    """
    # Build base query with row-level access control
    base_filter = build_access_filter(current_user)
    filters = [base_filter]

    # Apply optional filters
    if category:
        filters.append(Incident.category == category)
    if grade:
        filters.append(Incident.grade == grade)
    if status_filter:
        filters.append(Incident.status == status_filter)
    if department and current_user.role in [Role.VICE_CHAIR, Role.DIRECTOR, Role.MASTER]:
        filters.append(Incident.department == department)

    # Count total
    count_query = select(func.count(Incident.id)).where(and_(*filters))
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Get items
    query = (
        select(Incident)
        .where(and_(*filters))
        .order_by(Incident.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    incidents = result.scalars().all()

    return IncidentListResponse(
        items=[IncidentResponse.model_validate(i) for i in incidents],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{incident_id}",
    response_model=IncidentResponse,
    summary="Get incident details",
)
async def get_incident(
    incident_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> IncidentResponse:
    """
    Get details of a specific incident.

    Access is verified at row level.
    Audit log entry created for each access.
    """
    # Get incident
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

    # Check access
    if not can_access_incident(current_user, incident):
        await log_incident_event(
            db=db,
            event_type=AuditEventType.INCIDENT_VIEW,
            user=current_user,
            incident_id=incident_id,
            result="denied",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this incident",
        )

    # Log access
    await log_incident_event(
        db=db,
        event_type=AuditEventType.INCIDENT_VIEW,
        user=current_user,
        incident_id=incident_id,
        result="success",
    )

    return IncidentResponse.model_validate(incident)


@router.put(
    "/{incident_id}",
    response_model=IncidentResponse,
    summary="Update incident",
)
async def update_incident(
    incident_id: int,
    incident_data: IncidentUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> IncidentResponse:
    """
    Update an existing incident.

    Changes are logged with old/new values for audit trail.
    """
    # Get incident
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

    # Check edit permission
    if not can_edit_incident(current_user, incident):
        await log_incident_event(
            db=db,
            event_type=AuditEventType.INCIDENT_UPDATE,
            user=current_user,
            incident_id=incident_id,
            result="denied",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot edit this incident",
        )

    # Track changes for audit
    changes = {}
    update_data = incident_data.model_dump(exclude_unset=True)

    for field, new_value in update_data.items():
        old_value = getattr(incident, field)
        if old_value != new_value:
            # Convert enums to string for JSON serialization
            changes[field] = {
                "old": old_value.value if hasattr(old_value, 'value') else str(old_value),
                "new": new_value.value if hasattr(new_value, 'value') else str(new_value),
            }
            setattr(incident, field, new_value)

    if changes:
        incident.updated_at = datetime.now(timezone.utc)

        # Log update with changes
        await log_incident_event(
            db=db,
            event_type=AuditEventType.INCIDENT_UPDATE,
            user=current_user,
            incident_id=incident_id,
            result="success",
            details={"changes": changes},
        )

    return IncidentResponse.model_validate(incident)


@router.post(
    "/{incident_id}/submit",
    response_model=IncidentResponse,
    summary="Submit incident for approval",
)
async def submit_incident(
    incident_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> IncidentResponse:
    """
    Submit a draft incident for approval.

    Changes status from 'draft' to 'submitted'.
    """
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

    # Check ownership for submission
    if incident.reporter_id != current_user.id and current_user.role not in [Role.MASTER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the reporter can submit this incident",
        )

    if incident.status != "draft":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot submit incident with status '{incident.status}'",
        )

    incident.status = "submitted"
    incident.updated_at = datetime.now(timezone.utc)

    await log_incident_event(
        db=db,
        event_type=AuditEventType.INCIDENT_UPDATE,
        user=current_user,
        incident_id=incident_id,
        result="success",
        details={"action": "submit", "old_status": "draft", "new_status": "submitted"},
    )

    return IncidentResponse.model_validate(incident)


@router.delete(
    "/{incident_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete incident (soft delete)",
)
async def delete_incident(
    incident_id: int,
    current_user: Annotated[User, Depends(require_permission(Permission.DELETE_INCIDENT))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """
    Soft delete an incident (DIRECTOR/MASTER only).

    Sets is_deleted flag instead of removing record.
    """
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

    incident.is_deleted = True
    incident.updated_at = datetime.now(timezone.utc)

    await log_incident_event(
        db=db,
        event_type=AuditEventType.INCIDENT_DELETE,
        user=current_user,
        incident_id=incident_id,
        result="success",
        details={"category": incident.category.value, "grade": incident.grade.value},
    )
