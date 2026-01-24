"""
Procedure Details API

Category-specific detail management for procedure incidents.
"""

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.procedure_detail import ProcedureDetail
from app.models.incident import Incident, IncidentCategory
from app.models.user import User, Role
from app.models.audit import AuditLog, AuditEventType
from app.schemas.procedure_detail import (
    ProcedureDetailCreate,
    ProcedureDetailUpdate,
    ProcedureDetailResponse,
)
from app.security.dependencies import get_current_active_user

router = APIRouter()


async def log_procedure_detail_event(
    db: AsyncSession,
    user: User,
    detail_id: int | None,
    incident_id: int,
    event: str,
    result: str,
    details: dict | None = None,
) -> None:
    """Log procedure detail event for audit."""
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
        resource_type="procedure_detail",
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
    """Check if user can edit procedure details. QPS_STAFF+ required."""
    if user.role in [Role.QPS_STAFF, Role.VICE_CHAIR, Role.DIRECTOR, Role.MASTER]:
        if user.role == Role.QPS_STAFF:
            return incident.department == user.department
        return True
    return False


def can_delete_detail(user: User) -> bool:
    """Check if user can delete procedure details. DIRECTOR+ required."""
    return user.role in [Role.DIRECTOR, Role.MASTER]


@router.post(
    "/",
    response_model=ProcedureDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create procedure detail",
)
async def create_procedure_detail(
    detail_data: ProcedureDetailCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProcedureDetailResponse:
    """
    Create procedure detail record for a procedure incident.

    Business rules:
    - Incident must exist and not be deleted
    - Incident category must be PROCEDURE
    - Only one procedure detail per incident allowed
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

    if incident.category != IncidentCategory.PROCEDURE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Incident category is '{incident.category.value}', expected 'procedure'",
        )

    if not can_access_incident(current_user, incident):
        await log_procedure_detail_event(
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
        select(ProcedureDetail).where(ProcedureDetail.incident_id == detail_data.incident_id)
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Procedure detail already exists for this incident",
        )

    procedure_detail = ProcedureDetail(
        incident_id=detail_data.incident_id,
        procedure_type=detail_data.procedure_type,
        procedure_name=detail_data.procedure_name,
        procedure_detail=detail_data.procedure_detail,
        error_type=detail_data.error_type,
        error_type_detail=detail_data.error_type_detail,
        outcome=detail_data.outcome,
        outcome_detail=detail_data.outcome_detail,
        consent_obtained=detail_data.consent_obtained,
        consent_issue_detail=detail_data.consent_issue_detail,
        procedure_datetime=detail_data.procedure_datetime,
        performer_role=detail_data.performer_role,
        patient_code=detail_data.patient_code,
        procedure_site=detail_data.procedure_site,
        preparation_done=detail_data.preparation_done,
        preparation_issue=detail_data.preparation_issue,
    )

    db.add(procedure_detail)
    await db.flush()
    await db.refresh(procedure_detail)

    await log_procedure_detail_event(
        db=db,
        user=current_user,
        detail_id=procedure_detail.id,
        incident_id=detail_data.incident_id,
        event="create",
        result="success",
        details={"procedure_type": detail_data.procedure_type.value},
    )

    return ProcedureDetailResponse.model_validate(procedure_detail)


@router.get(
    "/incident/{incident_id}",
    response_model=ProcedureDetailResponse,
    summary="Get procedure detail by incident",
)
async def get_procedure_detail_by_incident(
    incident_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProcedureDetailResponse:
    """Get procedure detail for a specific incident."""
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
        await log_procedure_detail_event(
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
        select(ProcedureDetail).where(ProcedureDetail.incident_id == incident_id)
    )
    procedure_detail = result.scalar_one_or_none()

    if procedure_detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Procedure detail not found for this incident",
        )

    await log_procedure_detail_event(
        db=db,
        user=current_user,
        detail_id=procedure_detail.id,
        incident_id=incident_id,
        event="view",
        result="success",
    )

    return ProcedureDetailResponse.model_validate(procedure_detail)


@router.get(
    "/{detail_id}",
    response_model=ProcedureDetailResponse,
    summary="Get procedure detail by ID",
)
async def get_procedure_detail(
    detail_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProcedureDetailResponse:
    """Get procedure detail by its ID."""
    result = await db.execute(
        select(ProcedureDetail).where(ProcedureDetail.id == detail_id)
    )
    procedure_detail = result.scalar_one_or_none()

    if procedure_detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Procedure detail not found",
        )

    result = await db.execute(
        select(Incident).where(
            and_(Incident.id == procedure_detail.incident_id, Incident.is_deleted == False)
        )
    )
    incident = result.scalar_one_or_none()

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Linked incident not found",
        )

    if not can_access_incident(current_user, incident):
        await log_procedure_detail_event(
            db=db,
            user=current_user,
            detail_id=detail_id,
            incident_id=procedure_detail.incident_id,
            event="view",
            result="denied",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this incident",
        )

    await log_procedure_detail_event(
        db=db,
        user=current_user,
        detail_id=detail_id,
        incident_id=procedure_detail.incident_id,
        event="view",
        result="success",
    )

    return ProcedureDetailResponse.model_validate(procedure_detail)


@router.put(
    "/{detail_id}",
    response_model=ProcedureDetailResponse,
    summary="Update procedure detail",
)
async def update_procedure_detail(
    detail_id: int,
    detail_data: ProcedureDetailUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProcedureDetailResponse:
    """Update a procedure detail record. QPS_STAFF or higher required."""
    result = await db.execute(
        select(ProcedureDetail).where(ProcedureDetail.id == detail_id)
    )
    procedure_detail = result.scalar_one_or_none()

    if procedure_detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Procedure detail not found",
        )

    result = await db.execute(
        select(Incident).where(
            and_(Incident.id == procedure_detail.incident_id, Incident.is_deleted == False)
        )
    )
    incident = result.scalar_one_or_none()

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Linked incident not found",
        )

    if not can_edit_detail(current_user, incident):
        await log_procedure_detail_event(
            db=db,
            user=current_user,
            detail_id=detail_id,
            incident_id=procedure_detail.incident_id,
            event="update",
            result="denied",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to edit this procedure detail",
        )

    changes = {}
    update_data = detail_data.model_dump(exclude_unset=True)

    for field, new_value in update_data.items():
        old_value = getattr(procedure_detail, field)
        if old_value != new_value:
            old_str = old_value.value if hasattr(old_value, 'value') else str(old_value)
            new_str = new_value.value if hasattr(new_value, 'value') else str(new_value)
            changes[field] = {"old": old_str, "new": new_str}
            setattr(procedure_detail, field, new_value)

    if changes:
        await log_procedure_detail_event(
            db=db,
            user=current_user,
            detail_id=detail_id,
            incident_id=procedure_detail.incident_id,
            event="update",
            result="success",
            details={"changes": changes},
        )

    return ProcedureDetailResponse.model_validate(procedure_detail)


@router.delete(
    "/{detail_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete procedure detail",
)
async def delete_procedure_detail(
    detail_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete a procedure detail record. DIRECTOR or higher required."""
    result = await db.execute(
        select(ProcedureDetail).where(ProcedureDetail.id == detail_id)
    )
    procedure_detail = result.scalar_one_or_none()

    if procedure_detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Procedure detail not found",
        )

    if not can_delete_detail(current_user):
        await log_procedure_detail_event(
            db=db,
            user=current_user,
            detail_id=detail_id,
            incident_id=procedure_detail.incident_id,
            event="delete",
            result="denied",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete procedure details",
        )

    incident_id = procedure_detail.incident_id

    await db.delete(procedure_detail)

    await log_procedure_detail_event(
        db=db,
        user=current_user,
        detail_id=detail_id,
        incident_id=incident_id,
        event="delete",
        result="success",
    )
