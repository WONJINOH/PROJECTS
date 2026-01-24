"""
Environment Details API

Category-specific detail management for environment incidents.
"""

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.environment_detail import EnvironmentDetail
from app.models.incident import Incident, IncidentCategory
from app.models.user import User, Role
from app.models.audit import AuditLog, AuditEventType
from app.schemas.environment_detail import (
    EnvironmentDetailCreate,
    EnvironmentDetailUpdate,
    EnvironmentDetailResponse,
)
from app.security.dependencies import get_current_active_user

router = APIRouter()


async def log_environment_detail_event(
    db: AsyncSession,
    user: User,
    detail_id: int | None,
    incident_id: int,
    event: str,
    result: str,
    details: dict | None = None,
) -> None:
    """Log environment detail event for audit."""
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
        resource_type="environment_detail",
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
    """Check if user can edit environment details. QPS_STAFF+ required."""
    if user.role in [Role.QPS_STAFF, Role.VICE_CHAIR, Role.DIRECTOR, Role.MASTER]:
        if user.role == Role.QPS_STAFF:
            return incident.department == user.department
        return True
    return False


def can_delete_detail(user: User) -> bool:
    """Check if user can delete environment details. DIRECTOR+ required."""
    return user.role in [Role.DIRECTOR, Role.MASTER]


@router.post(
    "/",
    response_model=EnvironmentDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create environment detail",
)
async def create_environment_detail(
    detail_data: EnvironmentDetailCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> EnvironmentDetailResponse:
    """
    Create environment detail record for an environment incident.

    Business rules:
    - Incident must exist and not be deleted
    - Incident category must be ENVIRONMENT
    - Only one environment detail per incident allowed
    """
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

    if incident.category != IncidentCategory.ENVIRONMENT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Incident category is '{incident.category.value}', expected 'environment'",
        )

    if not can_access_incident(current_user, incident):
        await log_environment_detail_event(
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

    existing = await db.execute(
        select(EnvironmentDetail).where(EnvironmentDetail.incident_id == detail_data.incident_id)
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Environment detail already exists for this incident",
        )

    environment_detail = EnvironmentDetail(
        incident_id=detail_data.incident_id,
        environment_type=detail_data.environment_type,
        environment_type_detail=detail_data.environment_type_detail,
        severity=detail_data.severity,
        location_specific=detail_data.location_specific,
        location_floor=detail_data.location_floor,
        location_room=detail_data.location_room,
        equipment_involved=detail_data.equipment_involved,
        equipment_id=detail_data.equipment_id,
        damage_extent=detail_data.damage_extent,
        injury_occurred=detail_data.injury_occurred,
        injury_count=detail_data.injury_count,
        injury_detail=detail_data.injury_detail,
        property_damage=detail_data.property_damage,
        property_damage_detail=detail_data.property_damage_detail,
        estimated_cost=detail_data.estimated_cost,
        immediate_response=detail_data.immediate_response,
        evacuation_required=detail_data.evacuation_required,
        external_help_called=detail_data.external_help_called,
        cause_identified=detail_data.cause_identified,
        cause_detail=detail_data.cause_detail,
    )

    db.add(environment_detail)
    await db.flush()
    await db.refresh(environment_detail)

    await log_environment_detail_event(
        db=db,
        user=current_user,
        detail_id=environment_detail.id,
        incident_id=detail_data.incident_id,
        event="create",
        result="success",
        details={"environment_type": detail_data.environment_type.value},
    )

    return EnvironmentDetailResponse.model_validate(environment_detail)


@router.get(
    "/incident/{incident_id}",
    response_model=EnvironmentDetailResponse,
    summary="Get environment detail by incident",
)
async def get_environment_detail_by_incident(
    incident_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> EnvironmentDetailResponse:
    """Get environment detail for a specific incident."""
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

    if not can_access_incident(current_user, incident):
        await log_environment_detail_event(
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

    result = await db.execute(
        select(EnvironmentDetail).where(EnvironmentDetail.incident_id == incident_id)
    )
    environment_detail = result.scalar_one_or_none()

    if environment_detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Environment detail not found for this incident",
        )

    await log_environment_detail_event(
        db=db,
        user=current_user,
        detail_id=environment_detail.id,
        incident_id=incident_id,
        event="view",
        result="success",
    )

    return EnvironmentDetailResponse.model_validate(environment_detail)


@router.get(
    "/{detail_id}",
    response_model=EnvironmentDetailResponse,
    summary="Get environment detail by ID",
)
async def get_environment_detail(
    detail_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> EnvironmentDetailResponse:
    """Get environment detail by its ID."""
    result = await db.execute(
        select(EnvironmentDetail).where(EnvironmentDetail.id == detail_id)
    )
    environment_detail = result.scalar_one_or_none()

    if environment_detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Environment detail not found",
        )

    result = await db.execute(
        select(Incident).where(
            and_(Incident.id == environment_detail.incident_id, Incident.is_deleted == False)
        )
    )
    incident = result.scalar_one_or_none()

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Linked incident not found",
        )

    if not can_access_incident(current_user, incident):
        await log_environment_detail_event(
            db=db,
            user=current_user,
            detail_id=detail_id,
            incident_id=environment_detail.incident_id,
            event="view",
            result="denied",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this incident",
        )

    await log_environment_detail_event(
        db=db,
        user=current_user,
        detail_id=detail_id,
        incident_id=environment_detail.incident_id,
        event="view",
        result="success",
    )

    return EnvironmentDetailResponse.model_validate(environment_detail)


@router.put(
    "/{detail_id}",
    response_model=EnvironmentDetailResponse,
    summary="Update environment detail",
)
async def update_environment_detail(
    detail_id: int,
    detail_data: EnvironmentDetailUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> EnvironmentDetailResponse:
    """Update an environment detail record. QPS_STAFF or higher required."""
    result = await db.execute(
        select(EnvironmentDetail).where(EnvironmentDetail.id == detail_id)
    )
    environment_detail = result.scalar_one_or_none()

    if environment_detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Environment detail not found",
        )

    result = await db.execute(
        select(Incident).where(
            and_(Incident.id == environment_detail.incident_id, Incident.is_deleted == False)
        )
    )
    incident = result.scalar_one_or_none()

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Linked incident not found",
        )

    if not can_edit_detail(current_user, incident):
        await log_environment_detail_event(
            db=db,
            user=current_user,
            detail_id=detail_id,
            incident_id=environment_detail.incident_id,
            event="update",
            result="denied",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to edit this environment detail",
        )

    changes = {}
    update_data = detail_data.model_dump(exclude_unset=True)

    for field, new_value in update_data.items():
        old_value = getattr(environment_detail, field)
        if old_value != new_value:
            old_str = old_value.value if hasattr(old_value, 'value') else str(old_value)
            new_str = new_value.value if hasattr(new_value, 'value') else str(new_value)
            changes[field] = {"old": old_str, "new": new_str}
            setattr(environment_detail, field, new_value)

    if changes:
        await log_environment_detail_event(
            db=db,
            user=current_user,
            detail_id=detail_id,
            incident_id=environment_detail.incident_id,
            event="update",
            result="success",
            details={"changes": changes},
        )

    return EnvironmentDetailResponse.model_validate(environment_detail)


@router.delete(
    "/{detail_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete environment detail",
)
async def delete_environment_detail(
    detail_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete an environment detail record. DIRECTOR or higher required."""
    result = await db.execute(
        select(EnvironmentDetail).where(EnvironmentDetail.id == detail_id)
    )
    environment_detail = result.scalar_one_or_none()

    if environment_detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Environment detail not found",
        )

    if not can_delete_detail(current_user):
        await log_environment_detail_event(
            db=db,
            user=current_user,
            detail_id=detail_id,
            incident_id=environment_detail.incident_id,
            event="delete",
            result="denied",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete environment details",
        )

    incident_id = environment_detail.incident_id

    await db.delete(environment_detail)

    await log_environment_detail_event(
        db=db,
        user=current_user,
        detail_id=detail_id,
        incident_id=incident_id,
        event="delete",
        result="success",
    )
