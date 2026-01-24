"""
Thermal Injury Details API

Category-specific detail management for thermal injury incidents.
"""

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.thermal_injury_detail import ThermalInjuryDetail
from app.models.incident import Incident, IncidentCategory
from app.models.user import User, Role
from app.models.audit import AuditLog, AuditEventType
from app.schemas.thermal_injury_detail import (
    ThermalInjuryDetailCreate,
    ThermalInjuryDetailUpdate,
    ThermalInjuryDetailResponse,
)
from app.security.dependencies import get_current_active_user

router = APIRouter()


async def log_thermal_injury_detail_event(
    db: AsyncSession,
    user: User,
    detail_id: int | None,
    incident_id: int,
    event: str,
    result: str,
    details: dict | None = None,
) -> None:
    """Log thermal injury detail event for audit."""
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
        resource_type="thermal_injury_detail",
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
    """Check if user can edit thermal injury details. QPS_STAFF+ required."""
    if user.role in [Role.QPS_STAFF, Role.VICE_CHAIR, Role.DIRECTOR, Role.MASTER]:
        if user.role == Role.QPS_STAFF:
            return incident.department == user.department
        return True
    return False


def can_delete_detail(user: User) -> bool:
    """Check if user can delete thermal injury details. DIRECTOR+ required."""
    return user.role in [Role.DIRECTOR, Role.MASTER]


@router.post(
    "/",
    response_model=ThermalInjuryDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create thermal injury detail",
)
async def create_thermal_injury_detail(
    detail_data: ThermalInjuryDetailCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ThermalInjuryDetailResponse:
    """
    Create thermal injury detail record for a thermal injury incident.

    Business rules:
    - Incident must exist and not be deleted
    - Incident category must be THERMAL_INJURY
    - Only one thermal injury detail per incident allowed
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

    if incident.category != IncidentCategory.THERMAL_INJURY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Incident category is '{incident.category.value}', expected 'thermal_injury'",
        )

    if not can_access_incident(current_user, incident):
        await log_thermal_injury_detail_event(
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
        select(ThermalInjuryDetail).where(ThermalInjuryDetail.incident_id == detail_data.incident_id)
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Thermal injury detail already exists for this incident",
        )

    thermal_injury_detail = ThermalInjuryDetail(
        incident_id=detail_data.incident_id,
        injury_source=detail_data.injury_source,
        injury_source_detail=detail_data.injury_source_detail,
        injury_severity=detail_data.injury_severity,
        body_part=detail_data.body_part,
        body_part_detail=detail_data.body_part_detail,
        injury_size=detail_data.injury_size,
        application_duration_min=detail_data.application_duration_min,
        temperature_celsius=detail_data.temperature_celsius,
        patient_code=detail_data.patient_code,
        patient_sensory_intact=detail_data.patient_sensory_intact,
        treatment_provided=detail_data.treatment_provided,
    )

    db.add(thermal_injury_detail)
    await db.flush()
    await db.refresh(thermal_injury_detail)

    await log_thermal_injury_detail_event(
        db=db,
        user=current_user,
        detail_id=thermal_injury_detail.id,
        incident_id=detail_data.incident_id,
        event="create",
        result="success",
        details={"injury_source": detail_data.injury_source.value},
    )

    return ThermalInjuryDetailResponse.model_validate(thermal_injury_detail)


@router.get(
    "/incident/{incident_id}",
    response_model=ThermalInjuryDetailResponse,
    summary="Get thermal injury detail by incident",
)
async def get_thermal_injury_detail_by_incident(
    incident_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ThermalInjuryDetailResponse:
    """Get thermal injury detail for a specific incident."""
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
        await log_thermal_injury_detail_event(
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
        select(ThermalInjuryDetail).where(ThermalInjuryDetail.incident_id == incident_id)
    )
    thermal_injury_detail = result.scalar_one_or_none()

    if thermal_injury_detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thermal injury detail not found for this incident",
        )

    await log_thermal_injury_detail_event(
        db=db,
        user=current_user,
        detail_id=thermal_injury_detail.id,
        incident_id=incident_id,
        event="view",
        result="success",
    )

    return ThermalInjuryDetailResponse.model_validate(thermal_injury_detail)


@router.get(
    "/{detail_id}",
    response_model=ThermalInjuryDetailResponse,
    summary="Get thermal injury detail by ID",
)
async def get_thermal_injury_detail(
    detail_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ThermalInjuryDetailResponse:
    """Get thermal injury detail by its ID."""
    result = await db.execute(
        select(ThermalInjuryDetail).where(ThermalInjuryDetail.id == detail_id)
    )
    thermal_injury_detail = result.scalar_one_or_none()

    if thermal_injury_detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thermal injury detail not found",
        )

    result = await db.execute(
        select(Incident).where(
            and_(Incident.id == thermal_injury_detail.incident_id, Incident.is_deleted == False)
        )
    )
    incident = result.scalar_one_or_none()

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Linked incident not found",
        )

    if not can_access_incident(current_user, incident):
        await log_thermal_injury_detail_event(
            db=db,
            user=current_user,
            detail_id=detail_id,
            incident_id=thermal_injury_detail.incident_id,
            event="view",
            result="denied",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this incident",
        )

    await log_thermal_injury_detail_event(
        db=db,
        user=current_user,
        detail_id=detail_id,
        incident_id=thermal_injury_detail.incident_id,
        event="view",
        result="success",
    )

    return ThermalInjuryDetailResponse.model_validate(thermal_injury_detail)


@router.put(
    "/{detail_id}",
    response_model=ThermalInjuryDetailResponse,
    summary="Update thermal injury detail",
)
async def update_thermal_injury_detail(
    detail_id: int,
    detail_data: ThermalInjuryDetailUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ThermalInjuryDetailResponse:
    """Update a thermal injury detail record. QPS_STAFF or higher required."""
    result = await db.execute(
        select(ThermalInjuryDetail).where(ThermalInjuryDetail.id == detail_id)
    )
    thermal_injury_detail = result.scalar_one_or_none()

    if thermal_injury_detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thermal injury detail not found",
        )

    result = await db.execute(
        select(Incident).where(
            and_(Incident.id == thermal_injury_detail.incident_id, Incident.is_deleted == False)
        )
    )
    incident = result.scalar_one_or_none()

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Linked incident not found",
        )

    if not can_edit_detail(current_user, incident):
        await log_thermal_injury_detail_event(
            db=db,
            user=current_user,
            detail_id=detail_id,
            incident_id=thermal_injury_detail.incident_id,
            event="update",
            result="denied",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to edit this thermal injury detail",
        )

    changes = {}
    update_data = detail_data.model_dump(exclude_unset=True)

    for field, new_value in update_data.items():
        old_value = getattr(thermal_injury_detail, field)
        if old_value != new_value:
            old_str = old_value.value if hasattr(old_value, 'value') else str(old_value)
            new_str = new_value.value if hasattr(new_value, 'value') else str(new_value)
            changes[field] = {"old": old_str, "new": new_str}
            setattr(thermal_injury_detail, field, new_value)

    if changes:
        await log_thermal_injury_detail_event(
            db=db,
            user=current_user,
            detail_id=detail_id,
            incident_id=thermal_injury_detail.incident_id,
            event="update",
            result="success",
            details={"changes": changes},
        )

    return ThermalInjuryDetailResponse.model_validate(thermal_injury_detail)


@router.delete(
    "/{detail_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete thermal injury detail",
)
async def delete_thermal_injury_detail(
    detail_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete a thermal injury detail record. DIRECTOR or higher required."""
    result = await db.execute(
        select(ThermalInjuryDetail).where(ThermalInjuryDetail.id == detail_id)
    )
    thermal_injury_detail = result.scalar_one_or_none()

    if thermal_injury_detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thermal injury detail not found",
        )

    if not can_delete_detail(current_user):
        await log_thermal_injury_detail_event(
            db=db,
            user=current_user,
            detail_id=detail_id,
            incident_id=thermal_injury_detail.incident_id,
            event="delete",
            result="denied",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete thermal injury details",
        )

    incident_id = thermal_injury_detail.incident_id

    await db.delete(thermal_injury_detail)

    await log_thermal_injury_detail_event(
        db=db,
        user=current_user,
        detail_id=detail_id,
        incident_id=incident_id,
        event="delete",
        result="success",
    )
