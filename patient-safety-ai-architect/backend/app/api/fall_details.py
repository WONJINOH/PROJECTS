"""
Fall Details API

Category-specific detail management for fall incidents.
"""

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.fall_detail import FallDetail
from app.models.incident import Incident, IncidentCategory
from app.models.user import User, Role
from app.models.audit import AuditLog, AuditEventType
from app.schemas.fall_detail import (
    FallDetailCreate,
    FallDetailUpdate,
    FallDetailResponse,
)
from app.security.dependencies import get_current_active_user, require_permission
from app.security.rbac import Permission

router = APIRouter()


async def log_fall_detail_event(
    db: AsyncSession,
    user: User,
    detail_id: int | None,
    incident_id: int,
    event: str,
    result: str,
    details: dict | None = None,
) -> None:
    """Log fall detail event for audit."""
    timestamp = datetime.now(timezone.utc)
    previous_hash = "genesis"

    entry_hash = AuditLog.calculate_hash(
        event_type=AuditEventType.INCIDENT_UPDATE.value,
        timestamp=timestamp,
        user_id=user.id,
        resource_id=str(detail_id) if detail_id else None,
        previous_hash=previous_hash,
    )

    audit_log = AuditLog(
        event_type=AuditEventType.INCIDENT_UPDATE,
        timestamp=timestamp,
        user_id=user.id,
        user_role=user.role.value,
        username=user.username,
        resource_type="fall_detail",
        resource_id=str(detail_id) if detail_id else None,
        action_detail={"event": event, "incident_id": incident_id, **(details or {})},
        result=result,
        previous_hash=previous_hash,
        entry_hash=entry_hash,
    )
    db.add(audit_log)


def can_access_incident(user: User, incident: Incident) -> bool:
    """Check row-level access to incident."""
    if user.role in [Role.VICE_CHAIR, Role.DIRECTOR, Role.MASTER]:
        return True
    if user.role == Role.QPS_STAFF:
        return incident.department == user.department
    if user.role == Role.REPORTER:
        return incident.reporter_id == user.id
    return False


def can_edit_detail(user: User, incident: Incident) -> bool:
    """Check if user can edit fall details. QPS_STAFF+ required."""
    if user.role in [Role.QPS_STAFF, Role.VICE_CHAIR, Role.DIRECTOR, Role.MASTER]:
        if user.role == Role.QPS_STAFF:
            return incident.department == user.department
        return True
    return False


def can_delete_detail(user: User) -> bool:
    """Check if user can delete fall details. DIRECTOR+ required."""
    return user.role in [Role.DIRECTOR, Role.MASTER]


@router.post(
    "/",
    response_model=FallDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create fall detail",
)
async def create_fall_detail(
    detail_data: FallDetailCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> FallDetailResponse:
    """
    Create fall detail record for a fall incident.

    Business rules:
    - Incident must exist and not be deleted
    - Incident category must be FALL
    - Only one fall detail per incident allowed
    """
    # Verify incident exists
    result = await db.execute(
        select(Incident).where(
            and_(Incident.id == detail_data.incident_id, Incident.is_deleted == False)
        )
    )
    incident = result.scalar_one_or_none()

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )

    # Verify incident category
    if incident.category != IncidentCategory.FALL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Incident category is '{incident.category.value}', expected 'fall'",
        )

    # Check access
    if not can_access_incident(current_user, incident):
        await log_fall_detail_event(
            db=db,
            user=current_user,
            detail_id=None,
            incident_id=detail_data.incident_id,
            event="create",
            result="denied",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this incident",
        )

    # Check for existing detail (only one per incident)
    existing = await db.execute(
        select(FallDetail).where(FallDetail.incident_id == detail_data.incident_id)
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Fall detail already exists for this incident",
        )

    # Create fall detail
    fall_detail = FallDetail(
        incident_id=detail_data.incident_id,
        patient_code=detail_data.patient_code,
        patient_age_group=detail_data.patient_age_group,
        patient_gender=detail_data.patient_gender,
        pre_fall_risk_level=detail_data.pre_fall_risk_level,
        morse_score=detail_data.morse_score,
        fall_location=detail_data.fall_location,
        fall_location_detail=detail_data.fall_location_detail,
        fall_cause=detail_data.fall_cause,
        fall_cause_detail=detail_data.fall_cause_detail,
        occurred_hour=detail_data.occurred_hour,
        shift=detail_data.shift,
        injury_level=detail_data.injury_level,
        injury_description=detail_data.injury_description,
        activity_at_fall=detail_data.activity_at_fall,
        was_supervised=detail_data.was_supervised,
        had_fall_prevention=detail_data.had_fall_prevention,
        department=detail_data.department,
        is_recurrence=detail_data.is_recurrence,
        previous_fall_count=detail_data.previous_fall_count,
    )

    db.add(fall_detail)
    await db.flush()
    await db.refresh(fall_detail)

    await log_fall_detail_event(
        db=db,
        user=current_user,
        detail_id=fall_detail.id,
        incident_id=detail_data.incident_id,
        event="create",
        result="success",
        details={"injury_level": detail_data.injury_level.value},
    )

    return FallDetailResponse.model_validate(fall_detail)


@router.get(
    "/incident/{incident_id}",
    response_model=FallDetailResponse,
    summary="Get fall detail by incident",
)
async def get_fall_detail_by_incident(
    incident_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> FallDetailResponse:
    """
    Get fall detail for a specific incident.

    Access controlled at row level via incident.
    """
    # Verify incident exists and get access info
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
        await log_fall_detail_event(
            db=db,
            user=current_user,
            detail_id=None,
            incident_id=incident_id,
            event="view",
            result="denied",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this incident",
        )

    # Get fall detail
    result = await db.execute(
        select(FallDetail).where(FallDetail.incident_id == incident_id)
    )
    fall_detail = result.scalar_one_or_none()

    if fall_detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fall detail not found for this incident",
        )

    await log_fall_detail_event(
        db=db,
        user=current_user,
        detail_id=fall_detail.id,
        incident_id=incident_id,
        event="view",
        result="success",
    )

    return FallDetailResponse.model_validate(fall_detail)


@router.get(
    "/{detail_id}",
    response_model=FallDetailResponse,
    summary="Get fall detail by ID",
)
async def get_fall_detail(
    detail_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> FallDetailResponse:
    """
    Get fall detail by its ID.

    Access controlled at row level via linked incident.
    """
    # Get fall detail
    result = await db.execute(
        select(FallDetail).where(FallDetail.id == detail_id)
    )
    fall_detail = result.scalar_one_or_none()

    if fall_detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fall detail not found",
        )

    # Get incident for access check
    result = await db.execute(
        select(Incident).where(
            and_(Incident.id == fall_detail.incident_id, Incident.is_deleted == False)
        )
    )
    incident = result.scalar_one_or_none()

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Linked incident not found",
        )

    # Check access
    if not can_access_incident(current_user, incident):
        await log_fall_detail_event(
            db=db,
            user=current_user,
            detail_id=detail_id,
            incident_id=fall_detail.incident_id,
            event="view",
            result="denied",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this incident",
        )

    await log_fall_detail_event(
        db=db,
        user=current_user,
        detail_id=detail_id,
        incident_id=fall_detail.incident_id,
        event="view",
        result="success",
    )

    return FallDetailResponse.model_validate(fall_detail)


@router.put(
    "/{detail_id}",
    response_model=FallDetailResponse,
    summary="Update fall detail",
)
async def update_fall_detail(
    detail_id: int,
    detail_data: FallDetailUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> FallDetailResponse:
    """
    Update a fall detail record.

    QPS_STAFF or higher required.
    """
    # Get fall detail
    result = await db.execute(
        select(FallDetail).where(FallDetail.id == detail_id)
    )
    fall_detail = result.scalar_one_or_none()

    if fall_detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fall detail not found",
        )

    # Get incident for permission check
    result = await db.execute(
        select(Incident).where(
            and_(Incident.id == fall_detail.incident_id, Incident.is_deleted == False)
        )
    )
    incident = result.scalar_one_or_none()

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Linked incident not found",
        )

    # Check edit permission
    if not can_edit_detail(current_user, incident):
        await log_fall_detail_event(
            db=db,
            user=current_user,
            detail_id=detail_id,
            incident_id=fall_detail.incident_id,
            event="update",
            result="denied",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to edit this fall detail",
        )

    # Update fields
    changes = {}
    update_data = detail_data.model_dump(exclude_unset=True)

    for field, new_value in update_data.items():
        old_value = getattr(fall_detail, field)
        if old_value != new_value:
            old_str = old_value.value if hasattr(old_value, 'value') else str(old_value)
            new_str = new_value.value if hasattr(new_value, 'value') else str(new_value)
            changes[field] = {"old": old_str, "new": new_str}
            setattr(fall_detail, field, new_value)

    if changes:
        await log_fall_detail_event(
            db=db,
            user=current_user,
            detail_id=detail_id,
            incident_id=fall_detail.incident_id,
            event="update",
            result="success",
            details={"changes": changes},
        )

    return FallDetailResponse.model_validate(fall_detail)


@router.delete(
    "/{detail_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete fall detail (soft delete)",
)
async def delete_fall_detail(
    detail_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """
    Soft delete a fall detail record.

    DIRECTOR or higher required.
    Note: FallDetail model doesn't have is_deleted field,
    so this performs actual deletion.
    """
    # Get fall detail
    result = await db.execute(
        select(FallDetail).where(FallDetail.id == detail_id)
    )
    fall_detail = result.scalar_one_or_none()

    if fall_detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fall detail not found",
        )

    # Check delete permission
    if not can_delete_detail(current_user):
        await log_fall_detail_event(
            db=db,
            user=current_user,
            detail_id=detail_id,
            incident_id=fall_detail.incident_id,
            event="delete",
            result="denied",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete fall details",
        )

    incident_id = fall_detail.incident_id

    await db.delete(fall_detail)

    await log_fall_detail_event(
        db=db,
        user=current_user,
        detail_id=detail_id,
        incident_id=incident_id,
        event="delete",
        result="success",
    )
