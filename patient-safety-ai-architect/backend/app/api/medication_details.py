"""
Medication Details API

Category-specific detail management for medication error incidents.
"""

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.medication_detail import MedicationErrorDetail
from app.models.incident import Incident, IncidentCategory
from app.models.user import User, Role
from app.models.audit import AuditLog, AuditEventType
from app.schemas.medication_detail import (
    MedicationDetailCreate,
    MedicationDetailUpdate,
    MedicationDetailResponse,
)
from app.security.dependencies import get_current_active_user, require_permission
from app.security.rbac import Permission

router = APIRouter()


async def log_medication_detail_event(
    db: AsyncSession,
    user: User,
    detail_id: int | None,
    incident_id: int,
    event: str,
    result: str,
    details: dict | None = None,
) -> None:
    """Log medication detail event for audit."""
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
        resource_type="medication_detail",
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
    """Check if user can edit medication details. QPS_STAFF+ required."""
    if user.role in [Role.QPS_STAFF, Role.VICE_CHAIR, Role.DIRECTOR, Role.MASTER]:
        if user.role == Role.QPS_STAFF:
            return incident.department == user.department
        return True
    return False


def can_delete_detail(user: User) -> bool:
    """Check if user can delete medication details. DIRECTOR+ required."""
    return user.role in [Role.DIRECTOR, Role.MASTER]


@router.post(
    "/",
    response_model=MedicationDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create medication detail",
)
async def create_medication_detail(
    detail_data: MedicationDetailCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MedicationDetailResponse:
    """
    Create medication detail record for a medication incident.

    Business rules:
    - Incident must exist and not be deleted
    - Incident category must be MEDICATION
    - Only one medication detail per incident allowed
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
    if incident.category != IncidentCategory.MEDICATION:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Incident category is '{incident.category.value}', expected 'medication'",
        )

    # Check access
    if not can_access_incident(current_user, incident):
        await log_medication_detail_event(
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
        select(MedicationErrorDetail).where(
            MedicationErrorDetail.incident_id == detail_data.incident_id
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Medication detail already exists for this incident",
        )

    # Create medication detail
    medication_detail = MedicationErrorDetail(
        incident_id=detail_data.incident_id,
        patient_code=detail_data.patient_code,
        patient_age_group=detail_data.patient_age_group,
        error_type=detail_data.error_type,
        error_stage=detail_data.error_stage,
        error_severity=detail_data.error_severity,
        is_near_miss=detail_data.is_near_miss,
        medication_category=detail_data.medication_category,
        is_high_alert=detail_data.is_high_alert,
        high_alert_type=detail_data.high_alert_type,
        intended_dose=detail_data.intended_dose,
        actual_dose=detail_data.actual_dose,
        intended_route=detail_data.intended_route,
        actual_route=detail_data.actual_route,
        discovered_by_role=detail_data.discovered_by_role,
        discovery_method=detail_data.discovery_method,
        department=detail_data.department,
        barcode_scanned=detail_data.barcode_scanned,
        contributing_factors=detail_data.contributing_factors,
    )

    db.add(medication_detail)
    await db.flush()
    await db.refresh(medication_detail)

    await log_medication_detail_event(
        db=db,
        user=current_user,
        detail_id=medication_detail.id,
        incident_id=detail_data.incident_id,
        event="create",
        result="success",
        details={
            "error_type": detail_data.error_type.value,
            "error_severity": detail_data.error_severity.value,
        },
    )

    return MedicationDetailResponse.model_validate(medication_detail)


@router.get(
    "/incident/{incident_id}",
    response_model=MedicationDetailResponse,
    summary="Get medication detail by incident",
)
async def get_medication_detail_by_incident(
    incident_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MedicationDetailResponse:
    """
    Get medication detail for a specific incident.

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
        await log_medication_detail_event(
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

    # Get medication detail
    result = await db.execute(
        select(MedicationErrorDetail).where(
            MedicationErrorDetail.incident_id == incident_id
        )
    )
    medication_detail = result.scalar_one_or_none()

    if medication_detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medication detail not found for this incident",
        )

    await log_medication_detail_event(
        db=db,
        user=current_user,
        detail_id=medication_detail.id,
        incident_id=incident_id,
        event="view",
        result="success",
    )

    return MedicationDetailResponse.model_validate(medication_detail)


@router.get(
    "/{detail_id}",
    response_model=MedicationDetailResponse,
    summary="Get medication detail by ID",
)
async def get_medication_detail(
    detail_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MedicationDetailResponse:
    """
    Get medication detail by its ID.

    Access controlled at row level via linked incident.
    """
    # Get medication detail
    result = await db.execute(
        select(MedicationErrorDetail).where(MedicationErrorDetail.id == detail_id)
    )
    medication_detail = result.scalar_one_or_none()

    if medication_detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medication detail not found",
        )

    # Get incident for access check
    result = await db.execute(
        select(Incident).where(
            and_(
                Incident.id == medication_detail.incident_id,
                Incident.is_deleted == False,
            )
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
        await log_medication_detail_event(
            db=db,
            user=current_user,
            detail_id=detail_id,
            incident_id=medication_detail.incident_id,
            event="view",
            result="denied",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this incident",
        )

    await log_medication_detail_event(
        db=db,
        user=current_user,
        detail_id=detail_id,
        incident_id=medication_detail.incident_id,
        event="view",
        result="success",
    )

    return MedicationDetailResponse.model_validate(medication_detail)


@router.put(
    "/{detail_id}",
    response_model=MedicationDetailResponse,
    summary="Update medication detail",
)
async def update_medication_detail(
    detail_id: int,
    detail_data: MedicationDetailUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MedicationDetailResponse:
    """
    Update a medication detail record.

    QPS_STAFF or higher required.
    """
    # Get medication detail
    result = await db.execute(
        select(MedicationErrorDetail).where(MedicationErrorDetail.id == detail_id)
    )
    medication_detail = result.scalar_one_or_none()

    if medication_detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medication detail not found",
        )

    # Get incident for permission check
    result = await db.execute(
        select(Incident).where(
            and_(
                Incident.id == medication_detail.incident_id,
                Incident.is_deleted == False,
            )
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
        await log_medication_detail_event(
            db=db,
            user=current_user,
            detail_id=detail_id,
            incident_id=medication_detail.incident_id,
            event="update",
            result="denied",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to edit this medication detail",
        )

    # Update fields
    changes = {}
    update_data = detail_data.model_dump(exclude_unset=True)

    for field, new_value in update_data.items():
        old_value = getattr(medication_detail, field)
        if old_value != new_value:
            old_str = old_value.value if hasattr(old_value, 'value') else str(old_value)
            new_str = new_value.value if hasattr(new_value, 'value') else str(new_value)
            changes[field] = {"old": old_str, "new": new_str}
            setattr(medication_detail, field, new_value)

    if changes:
        await log_medication_detail_event(
            db=db,
            user=current_user,
            detail_id=detail_id,
            incident_id=medication_detail.incident_id,
            event="update",
            result="success",
            details={"changes": changes},
        )

    return MedicationDetailResponse.model_validate(medication_detail)


@router.delete(
    "/{detail_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete medication detail (soft delete)",
)
async def delete_medication_detail(
    detail_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """
    Soft delete a medication detail record.

    DIRECTOR or higher required.
    Note: MedicationErrorDetail model doesn't have is_deleted field,
    so this performs actual deletion.
    """
    # Get medication detail
    result = await db.execute(
        select(MedicationErrorDetail).where(MedicationErrorDetail.id == detail_id)
    )
    medication_detail = result.scalar_one_or_none()

    if medication_detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medication detail not found",
        )

    # Check delete permission
    if not can_delete_detail(current_user):
        await log_medication_detail_event(
            db=db,
            user=current_user,
            detail_id=detail_id,
            incident_id=medication_detail.incident_id,
            event="delete",
            result="denied",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete medication details",
        )

    incident_id = medication_detail.incident_id

    await db.delete(medication_detail)

    await log_medication_detail_event(
        db=db,
        user=current_user,
        detail_id=detail_id,
        incident_id=incident_id,
        event="delete",
        result="success",
    )
