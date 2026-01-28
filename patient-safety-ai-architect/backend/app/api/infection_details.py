"""
Infection Details API

Category-specific detail management for infection incidents.
"""

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.infection import InfectionRecord
from app.models.incident import Incident, IncidentCategory
from app.models.user import User, Role
from app.models.audit import AuditLog, AuditEventType
from app.schemas.infection_detail import (
    InfectionDetailCreate,
    InfectionDetailUpdate,
    InfectionDetailResponse,
)
from app.security.dependencies import get_current_active_user

router = APIRouter()


async def log_infection_detail_event(
    db: AsyncSession,
    user: User,
    detail_id: int | None,
    incident_id: int,
    event: str,
    result: str,
    details: dict | None = None,
) -> None:
    """Log infection detail event for audit."""
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
        resource_type="infection_detail",
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
    """Check if user can edit infection details. QPS_STAFF+ required."""
    if user.role in [Role.QPS_STAFF, Role.VICE_CHAIR, Role.DIRECTOR, Role.MASTER]:
        if user.role == Role.QPS_STAFF:
            return incident.department == user.department
        return True
    return False


def can_delete_detail(user: User) -> bool:
    """Check if user can delete infection details. DIRECTOR+ required."""
    return user.role in [Role.DIRECTOR, Role.MASTER]


@router.post(
    "/",
    response_model=InfectionDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create infection detail",
)
async def create_infection_detail(
    detail_data: InfectionDetailCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InfectionDetailResponse:
    """
    Create infection detail record for an infection incident.

    Business rules:
    - Incident must exist and not be deleted
    - Incident category must be INFECTION
    - Only one infection detail per incident allowed
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
    if incident.category != IncidentCategory.INFECTION:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Incident category is '{incident.category.value}', expected 'infection'",
        )

    # Check access
    if not can_access_incident(current_user, incident):
        await log_infection_detail_event(
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
        select(InfectionRecord).where(InfectionRecord.incident_id == detail_data.incident_id)
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Infection detail already exists for this incident",
        )

    # Create infection detail
    infection_detail = InfectionRecord(
        incident_id=detail_data.incident_id,
        patient_code=detail_data.patient_code,
        patient_name=detail_data.patient_name,
        patient_age_group=detail_data.patient_age_group,
        patient_gender=detail_data.patient_gender,
        room_number=detail_data.room_number,
        department_id=detail_data.department_id,
        physician_id=detail_data.physician_id,
        diagnosis=detail_data.diagnosis,
        infection_type=detail_data.infection_type,
        infection_site=detail_data.infection_site,
        infection_site_detail=detail_data.infection_site_detail,
        onset_date=detail_data.onset_date,
        diagnosis_date=detail_data.diagnosis_date,
        pathogen=detail_data.pathogen,
        is_mdro=detail_data.is_mdro,
        pathogen_culture_result=detail_data.pathogen_culture_result,
        device_related=detail_data.device_related,
        device_type=detail_data.device_type,
        device_insertion_date=detail_data.device_insertion_date,
        device_days=detail_data.device_days,
        is_hospital_acquired=detail_data.is_hospital_acquired,
        admission_date=detail_data.admission_date,
        department=detail_data.department,
        antibiotic_used=detail_data.antibiotic_used,
        treatment_notes=detail_data.treatment_notes,
    )

    db.add(infection_detail)
    await db.flush()
    await db.refresh(infection_detail)

    await log_infection_detail_event(
        db=db,
        user=current_user,
        detail_id=infection_detail.id,
        incident_id=detail_data.incident_id,
        event="create",
        result="success",
        details={"infection_type": detail_data.infection_type.value},
    )

    return InfectionDetailResponse.model_validate(infection_detail)


@router.get(
    "/incident/{incident_id}",
    response_model=InfectionDetailResponse,
    summary="Get infection detail by incident",
)
async def get_infection_detail_by_incident(
    incident_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InfectionDetailResponse:
    """
    Get infection detail for a specific incident.

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
        await log_infection_detail_event(
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

    # Get infection detail
    result = await db.execute(
        select(InfectionRecord).where(InfectionRecord.incident_id == incident_id)
    )
    infection_detail = result.scalar_one_or_none()

    if infection_detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Infection detail not found for this incident",
        )

    await log_infection_detail_event(
        db=db,
        user=current_user,
        detail_id=infection_detail.id,
        incident_id=incident_id,
        event="view",
        result="success",
    )

    return InfectionDetailResponse.model_validate(infection_detail)


@router.get(
    "/{detail_id}",
    response_model=InfectionDetailResponse,
    summary="Get infection detail by ID",
)
async def get_infection_detail(
    detail_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InfectionDetailResponse:
    """Get a specific infection detail by ID."""
    result = await db.execute(
        select(InfectionRecord).where(InfectionRecord.id == detail_id)
    )
    infection_detail = result.scalar_one_or_none()

    if infection_detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Infection detail not found",
        )

    # Get incident for access check
    result = await db.execute(
        select(Incident).where(Incident.id == infection_detail.incident_id)
    )
    incident = result.scalar_one_or_none()

    if incident is None or not can_access_incident(current_user, incident):
        await log_infection_detail_event(
            db=db,
            user=current_user,
            detail_id=detail_id,
            incident_id=infection_detail.incident_id,
            event="view",
            result="denied",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    await log_infection_detail_event(
        db=db,
        user=current_user,
        detail_id=detail_id,
        incident_id=infection_detail.incident_id,
        event="view",
        result="success",
    )

    return InfectionDetailResponse.model_validate(infection_detail)


@router.put(
    "/{detail_id}",
    response_model=InfectionDetailResponse,
    summary="Update infection detail",
)
async def update_infection_detail(
    detail_id: int,
    update_data: InfectionDetailUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InfectionDetailResponse:
    """Update an existing infection detail."""
    result = await db.execute(
        select(InfectionRecord).where(InfectionRecord.id == detail_id)
    )
    infection_detail = result.scalar_one_or_none()

    if infection_detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Infection detail not found",
        )

    # Get incident for access check
    result = await db.execute(
        select(Incident).where(Incident.id == infection_detail.incident_id)
    )
    incident = result.scalar_one_or_none()

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )

    # Check edit permission
    if not can_edit_detail(current_user, incident):
        await log_infection_detail_event(
            db=db,
            user=current_user,
            detail_id=detail_id,
            incident_id=infection_detail.incident_id,
            event="update",
            result="denied",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Edit permission denied",
        )

    # Update fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(infection_detail, field, value)

    await db.flush()
    await db.refresh(infection_detail)

    await log_infection_detail_event(
        db=db,
        user=current_user,
        detail_id=detail_id,
        incident_id=infection_detail.incident_id,
        event="update",
        result="success",
        details={"updated_fields": list(update_dict.keys())},
    )

    return InfectionDetailResponse.model_validate(infection_detail)


@router.delete(
    "/{detail_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete infection detail",
)
async def delete_infection_detail(
    detail_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete an infection detail. Requires DIRECTOR+ role."""
    if not can_delete_detail(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Delete permission denied. DIRECTOR+ role required.",
        )

    result = await db.execute(
        select(InfectionRecord).where(InfectionRecord.id == detail_id)
    )
    infection_detail = result.scalar_one_or_none()

    if infection_detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Infection detail not found",
        )

    incident_id = infection_detail.incident_id

    await db.delete(infection_detail)

    await log_infection_detail_event(
        db=db,
        user=current_user,
        detail_id=detail_id,
        incident_id=incident_id,
        event="delete",
        result="success",
    )
