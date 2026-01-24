"""
Transfusion Details API

Category-specific detail management for transfusion incidents.
"""

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.transfusion_detail import TransfusionDetail
from app.models.incident import Incident, IncidentCategory
from app.models.user import User, Role
from app.models.audit import AuditLog, AuditEventType
from app.schemas.transfusion_detail import (
    TransfusionDetailCreate,
    TransfusionDetailUpdate,
    TransfusionDetailResponse,
)
from app.security.dependencies import get_current_active_user

router = APIRouter()


async def log_transfusion_detail_event(
    db: AsyncSession,
    user: User,
    detail_id: int | None,
    incident_id: int,
    event: str,
    result: str,
    details: dict | None = None,
) -> None:
    """Log transfusion detail event for audit."""
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
        resource_type="transfusion_detail",
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
    """Check if user can edit transfusion details. QPS_STAFF+ required."""
    if user.role in [Role.QPS_STAFF, Role.VICE_CHAIR, Role.DIRECTOR, Role.MASTER]:
        if user.role == Role.QPS_STAFF:
            return incident.department == user.department
        return True
    return False


def can_delete_detail(user: User) -> bool:
    """Check if user can delete transfusion details. DIRECTOR+ required."""
    return user.role in [Role.DIRECTOR, Role.MASTER]


@router.post(
    "/",
    response_model=TransfusionDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create transfusion detail",
)
async def create_transfusion_detail(
    detail_data: TransfusionDetailCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TransfusionDetailResponse:
    """
    Create transfusion detail record for a transfusion incident.

    Business rules:
    - Incident must exist and not be deleted
    - Incident category must be TRANSFUSION
    - Only one transfusion detail per incident allowed
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

    if incident.category != IncidentCategory.TRANSFUSION:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Incident category is '{incident.category.value}', expected 'transfusion'",
        )

    if not can_access_incident(current_user, incident):
        await log_transfusion_detail_event(
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
        select(TransfusionDetail).where(TransfusionDetail.incident_id == detail_data.incident_id)
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Transfusion detail already exists for this incident",
        )

    transfusion_detail = TransfusionDetail(
        incident_id=detail_data.incident_id,
        blood_type_verified=detail_data.blood_type_verified,
        verification_method=detail_data.verification_method,
        error_type=detail_data.error_type,
        error_type_detail=detail_data.error_type_detail,
        reaction_type=detail_data.reaction_type,
        reaction_detail=detail_data.reaction_detail,
        blood_product_type=detail_data.blood_product_type,
        blood_unit_id=detail_data.blood_unit_id,
        infusion_volume_ml=detail_data.infusion_volume_ml,
        infusion_rate=detail_data.infusion_rate,
        start_time=detail_data.start_time,
        end_time=detail_data.end_time,
        patient_code=detail_data.patient_code,
        patient_blood_type=detail_data.patient_blood_type,
        pre_transfusion_check_done=detail_data.pre_transfusion_check_done,
        two_person_verification=detail_data.two_person_verification,
    )

    db.add(transfusion_detail)
    await db.flush()
    await db.refresh(transfusion_detail)

    await log_transfusion_detail_event(
        db=db,
        user=current_user,
        detail_id=transfusion_detail.id,
        incident_id=detail_data.incident_id,
        event="create",
        result="success",
        details={"error_type": detail_data.error_type.value},
    )

    return TransfusionDetailResponse.model_validate(transfusion_detail)


@router.get(
    "/incident/{incident_id}",
    response_model=TransfusionDetailResponse,
    summary="Get transfusion detail by incident",
)
async def get_transfusion_detail_by_incident(
    incident_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TransfusionDetailResponse:
    """Get transfusion detail for a specific incident."""
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
        await log_transfusion_detail_event(
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
        select(TransfusionDetail).where(TransfusionDetail.incident_id == incident_id)
    )
    transfusion_detail = result.scalar_one_or_none()

    if transfusion_detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transfusion detail not found for this incident",
        )

    await log_transfusion_detail_event(
        db=db,
        user=current_user,
        detail_id=transfusion_detail.id,
        incident_id=incident_id,
        event="view",
        result="success",
    )

    return TransfusionDetailResponse.model_validate(transfusion_detail)


@router.get(
    "/{detail_id}",
    response_model=TransfusionDetailResponse,
    summary="Get transfusion detail by ID",
)
async def get_transfusion_detail(
    detail_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TransfusionDetailResponse:
    """Get transfusion detail by its ID."""
    result = await db.execute(
        select(TransfusionDetail).where(TransfusionDetail.id == detail_id)
    )
    transfusion_detail = result.scalar_one_or_none()

    if transfusion_detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transfusion detail not found",
        )

    result = await db.execute(
        select(Incident).where(
            and_(Incident.id == transfusion_detail.incident_id, Incident.is_deleted == False)
        )
    )
    incident = result.scalar_one_or_none()

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Linked incident not found",
        )

    if not can_access_incident(current_user, incident):
        await log_transfusion_detail_event(
            db=db,
            user=current_user,
            detail_id=detail_id,
            incident_id=transfusion_detail.incident_id,
            event="view",
            result="denied",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this incident",
        )

    await log_transfusion_detail_event(
        db=db,
        user=current_user,
        detail_id=detail_id,
        incident_id=transfusion_detail.incident_id,
        event="view",
        result="success",
    )

    return TransfusionDetailResponse.model_validate(transfusion_detail)


@router.put(
    "/{detail_id}",
    response_model=TransfusionDetailResponse,
    summary="Update transfusion detail",
)
async def update_transfusion_detail(
    detail_id: int,
    detail_data: TransfusionDetailUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TransfusionDetailResponse:
    """Update a transfusion detail record. QPS_STAFF or higher required."""
    result = await db.execute(
        select(TransfusionDetail).where(TransfusionDetail.id == detail_id)
    )
    transfusion_detail = result.scalar_one_or_none()

    if transfusion_detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transfusion detail not found",
        )

    result = await db.execute(
        select(Incident).where(
            and_(Incident.id == transfusion_detail.incident_id, Incident.is_deleted == False)
        )
    )
    incident = result.scalar_one_or_none()

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Linked incident not found",
        )

    if not can_edit_detail(current_user, incident):
        await log_transfusion_detail_event(
            db=db,
            user=current_user,
            detail_id=detail_id,
            incident_id=transfusion_detail.incident_id,
            event="update",
            result="denied",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to edit this transfusion detail",
        )

    changes = {}
    update_data = detail_data.model_dump(exclude_unset=True)

    for field, new_value in update_data.items():
        old_value = getattr(transfusion_detail, field)
        if old_value != new_value:
            old_str = old_value.value if hasattr(old_value, 'value') else str(old_value)
            new_str = new_value.value if hasattr(new_value, 'value') else str(new_value)
            changes[field] = {"old": old_str, "new": new_str}
            setattr(transfusion_detail, field, new_value)

    if changes:
        await log_transfusion_detail_event(
            db=db,
            user=current_user,
            detail_id=detail_id,
            incident_id=transfusion_detail.incident_id,
            event="update",
            result="success",
            details={"changes": changes},
        )

    return TransfusionDetailResponse.model_validate(transfusion_detail)


@router.delete(
    "/{detail_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete transfusion detail",
)
async def delete_transfusion_detail(
    detail_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete a transfusion detail record. DIRECTOR or higher required."""
    result = await db.execute(
        select(TransfusionDetail).where(TransfusionDetail.id == detail_id)
    )
    transfusion_detail = result.scalar_one_or_none()

    if transfusion_detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transfusion detail not found",
        )

    if not can_delete_detail(current_user):
        await log_transfusion_detail_event(
            db=db,
            user=current_user,
            detail_id=detail_id,
            incident_id=transfusion_detail.incident_id,
            event="delete",
            result="denied",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete transfusion details",
        )

    incident_id = transfusion_detail.incident_id

    await db.delete(transfusion_detail)

    await log_transfusion_detail_event(
        db=db,
        user=current_user,
        detail_id=detail_id,
        incident_id=incident_id,
        event="delete",
        result="success",
    )
