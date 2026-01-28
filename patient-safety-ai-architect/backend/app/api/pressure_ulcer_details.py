"""
Pressure Ulcer Details API

Category-specific detail management for pressure ulcer incidents.
"""

from datetime import datetime, timezone
from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.pressure_ulcer import PressureUlcerRecord
from app.models.incident import Incident, IncidentCategory
from app.models.user import User, Role
from app.models.audit import AuditLog, AuditEventType
from app.schemas.pressure_ulcer_detail import (
    PressureUlcerDetailCreate,
    PressureUlcerDetailUpdate,
    PressureUlcerDetailResponse,
)
from app.security.dependencies import get_current_active_user

router = APIRouter()


async def log_pressure_ulcer_detail_event(
    db: AsyncSession,
    user: User,
    detail_id: int | None,
    incident_id: int,
    event: str,
    result: str,
    details: dict | None = None,
) -> None:
    """Log pressure ulcer detail event for audit."""
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
        resource_type="pressure_ulcer_detail",
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
    """Check if user can edit pressure ulcer details. QPS_STAFF+ required."""
    if user.role in [Role.QPS_STAFF, Role.VICE_CHAIR, Role.DIRECTOR, Role.MASTER]:
        if user.role == Role.QPS_STAFF:
            return incident.department == user.department
        return True
    return False


def can_delete_detail(user: User) -> bool:
    """Check if user can delete pressure ulcer details. DIRECTOR+ required."""
    return user.role in [Role.DIRECTOR, Role.MASTER]


def calculate_push_total(length_width: int | None, exudate: int | None, tissue_type: int | None) -> float | None:
    """Calculate PUSH total score."""
    if length_width is not None and exudate is not None and tissue_type is not None:
        return float(length_width + exudate + tissue_type)
    return None


@router.post(
    "/",
    response_model=PressureUlcerDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create pressure ulcer detail",
)
async def create_pressure_ulcer_detail(
    detail_data: PressureUlcerDetailCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PressureUlcerDetailResponse:
    """
    Create pressure ulcer detail record for a pressure ulcer incident.

    Business rules:
    - Incident must exist and not be deleted
    - Incident category must be PRESSURE_ULCER
    - Only one pressure ulcer detail per incident allowed
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
    if incident.category != IncidentCategory.PRESSURE_ULCER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Incident category is '{incident.category.value}', expected 'pressure_ulcer'",
        )

    # Check access
    if not can_access_incident(current_user, incident):
        await log_pressure_ulcer_detail_event(
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
        select(PressureUlcerRecord).where(PressureUlcerRecord.incident_id == detail_data.incident_id)
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Pressure ulcer detail already exists for this incident",
        )

    # Calculate PUSH total
    push_total = calculate_push_total(
        detail_data.push_length_width,
        detail_data.push_exudate,
        detail_data.push_tissue_type,
    )

    # Create pressure ulcer detail
    pressure_ulcer_detail = PressureUlcerRecord(
        incident_id=detail_data.incident_id,
        patient_code=detail_data.patient_code,
        patient_name=detail_data.patient_name,
        patient_gender=detail_data.patient_gender,
        room_number=detail_data.room_number,
        patient_age_group=detail_data.patient_age_group,
        admission_date=detail_data.admission_date,
        ulcer_id=detail_data.ulcer_id,
        location=detail_data.location,
        location_detail=detail_data.location_detail,
        origin=detail_data.origin,
        discovery_date=detail_data.discovery_date,
        grade=detail_data.grade,
        push_length_width=detail_data.push_length_width,
        push_exudate=detail_data.push_exudate,
        push_tissue_type=detail_data.push_tissue_type,
        push_total=push_total,
        length_cm=detail_data.length_cm,
        width_cm=detail_data.width_cm,
        depth_cm=detail_data.depth_cm,
        department=detail_data.department,
        risk_factors=detail_data.risk_factors,
        treatment_plan=detail_data.treatment_plan,
        note=detail_data.note,
    )

    db.add(pressure_ulcer_detail)
    await db.flush()
    await db.refresh(pressure_ulcer_detail)

    await log_pressure_ulcer_detail_event(
        db=db,
        user=current_user,
        detail_id=pressure_ulcer_detail.id,
        incident_id=detail_data.incident_id,
        event="create",
        result="success",
        details={"location": detail_data.location.value, "grade": detail_data.grade.value if detail_data.grade else None},
    )

    return PressureUlcerDetailResponse.model_validate(pressure_ulcer_detail)


@router.get(
    "/incident/{incident_id}",
    response_model=PressureUlcerDetailResponse,
    summary="Get pressure ulcer detail by incident",
)
async def get_pressure_ulcer_detail_by_incident(
    incident_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PressureUlcerDetailResponse:
    """
    Get pressure ulcer detail for a specific incident.

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
        await log_pressure_ulcer_detail_event(
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

    # Get pressure ulcer detail
    result = await db.execute(
        select(PressureUlcerRecord).where(PressureUlcerRecord.incident_id == incident_id)
    )
    pressure_ulcer_detail = result.scalar_one_or_none()

    if pressure_ulcer_detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pressure ulcer detail not found for this incident",
        )

    await log_pressure_ulcer_detail_event(
        db=db,
        user=current_user,
        detail_id=pressure_ulcer_detail.id,
        incident_id=incident_id,
        event="view",
        result="success",
    )

    return PressureUlcerDetailResponse.model_validate(pressure_ulcer_detail)


@router.get(
    "/{detail_id}",
    response_model=PressureUlcerDetailResponse,
    summary="Get pressure ulcer detail by ID",
)
async def get_pressure_ulcer_detail(
    detail_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PressureUlcerDetailResponse:
    """Get a specific pressure ulcer detail by ID."""
    result = await db.execute(
        select(PressureUlcerRecord).where(PressureUlcerRecord.id == detail_id)
    )
    pressure_ulcer_detail = result.scalar_one_or_none()

    if pressure_ulcer_detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pressure ulcer detail not found",
        )

    # Get incident for access check
    if pressure_ulcer_detail.incident_id:
        result = await db.execute(
            select(Incident).where(Incident.id == pressure_ulcer_detail.incident_id)
        )
        incident = result.scalar_one_or_none()

        if incident is None or not can_access_incident(current_user, incident):
            await log_pressure_ulcer_detail_event(
                db=db,
                user=current_user,
                detail_id=detail_id,
                incident_id=pressure_ulcer_detail.incident_id,
                event="view",
                result="denied",
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

    await log_pressure_ulcer_detail_event(
        db=db,
        user=current_user,
        detail_id=detail_id,
        incident_id=pressure_ulcer_detail.incident_id or 0,
        event="view",
        result="success",
    )

    return PressureUlcerDetailResponse.model_validate(pressure_ulcer_detail)


@router.put(
    "/{detail_id}",
    response_model=PressureUlcerDetailResponse,
    summary="Update pressure ulcer detail",
)
async def update_pressure_ulcer_detail(
    detail_id: int,
    update_data: PressureUlcerDetailUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PressureUlcerDetailResponse:
    """Update an existing pressure ulcer detail."""
    result = await db.execute(
        select(PressureUlcerRecord).where(PressureUlcerRecord.id == detail_id)
    )
    pressure_ulcer_detail = result.scalar_one_or_none()

    if pressure_ulcer_detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pressure ulcer detail not found",
        )

    # Get incident for access check
    if pressure_ulcer_detail.incident_id:
        result = await db.execute(
            select(Incident).where(Incident.id == pressure_ulcer_detail.incident_id)
        )
        incident = result.scalar_one_or_none()

        if incident is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Incident not found",
            )

        # Check edit permission
        if not can_edit_detail(current_user, incident):
            await log_pressure_ulcer_detail_event(
                db=db,
                user=current_user,
                detail_id=detail_id,
                incident_id=pressure_ulcer_detail.incident_id,
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
        setattr(pressure_ulcer_detail, field, value)

    # Recalculate PUSH total if any PUSH field was updated
    if any(f in update_dict for f in ['push_length_width', 'push_exudate', 'push_tissue_type']):
        pressure_ulcer_detail.push_total = calculate_push_total(
            pressure_ulcer_detail.push_length_width,
            pressure_ulcer_detail.push_exudate,
            pressure_ulcer_detail.push_tissue_type,
        )

    await db.flush()
    await db.refresh(pressure_ulcer_detail)

    await log_pressure_ulcer_detail_event(
        db=db,
        user=current_user,
        detail_id=detail_id,
        incident_id=pressure_ulcer_detail.incident_id or 0,
        event="update",
        result="success",
        details={"updated_fields": list(update_dict.keys())},
    )

    return PressureUlcerDetailResponse.model_validate(pressure_ulcer_detail)


@router.delete(
    "/{detail_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete pressure ulcer detail",
)
async def delete_pressure_ulcer_detail(
    detail_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete a pressure ulcer detail. Requires DIRECTOR+ role."""
    if not can_delete_detail(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Delete permission denied. DIRECTOR+ role required.",
        )

    result = await db.execute(
        select(PressureUlcerRecord).where(PressureUlcerRecord.id == detail_id)
    )
    pressure_ulcer_detail = result.scalar_one_or_none()

    if pressure_ulcer_detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pressure ulcer detail not found",
        )

    incident_id = pressure_ulcer_detail.incident_id or 0

    await db.delete(pressure_ulcer_detail)

    await log_pressure_ulcer_detail_event(
        db=db,
        user=current_user,
        detail_id=detail_id,
        incident_id=incident_id,
        event="delete",
        result="success",
    )
