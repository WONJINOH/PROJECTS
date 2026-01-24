"""
Security Details API

Category-specific detail management for security incidents.
"""

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.security_detail import SecurityDetail
from app.models.incident import Incident, IncidentCategory
from app.models.user import User, Role
from app.models.audit import AuditLog, AuditEventType
from app.schemas.security_detail import (
    SecurityDetailCreate,
    SecurityDetailUpdate,
    SecurityDetailResponse,
)
from app.security.dependencies import get_current_active_user

router = APIRouter()

# Security-related categories that can have security details
SECURITY_CATEGORIES = [
    IncidentCategory.SECURITY,
    IncidentCategory.ELOPEMENT,
    IncidentCategory.VIOLENCE,
    IncidentCategory.FIRE,
    IncidentCategory.SUICIDE,
    IncidentCategory.SELF_HARM,
]


async def log_security_detail_event(
    db: AsyncSession,
    user: User,
    detail_id: int | None,
    incident_id: int,
    event: str,
    result: str,
    details: dict | None = None,
) -> None:
    """Log security detail event for audit."""
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
        resource_type="security_detail",
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
    """Check if user can edit security details. QPS_STAFF+ required."""
    if user.role in [Role.QPS_STAFF, Role.VICE_CHAIR, Role.DIRECTOR, Role.MASTER]:
        if user.role == Role.QPS_STAFF:
            return incident.department == user.department
        return True
    return False


def can_delete_detail(user: User) -> bool:
    """Check if user can delete security details. DIRECTOR+ required."""
    return user.role in [Role.DIRECTOR, Role.MASTER]


@router.post(
    "/",
    response_model=SecurityDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create security detail",
)
async def create_security_detail(
    detail_data: SecurityDetailCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SecurityDetailResponse:
    """
    Create security detail record for a security incident.

    Business rules:
    - Incident must exist and not be deleted
    - Incident category must be SECURITY or related (elopement, violence, fire, suicide, self_harm)
    - Only one security detail per incident allowed
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

    if incident.category not in SECURITY_CATEGORIES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Incident category is '{incident.category.value}', expected one of security-related categories",
        )

    if not can_access_incident(current_user, incident):
        await log_security_detail_event(
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
        select(SecurityDetail).where(SecurityDetail.incident_id == detail_data.incident_id)
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Security detail already exists for this incident",
        )

    # Convert involved_parties to JSON-serializable format
    involved_parties_json = None
    if detail_data.involved_parties:
        involved_parties_json = [
            {"type": p.type.value, "code": p.code}
            for p in detail_data.involved_parties
        ]

    security_detail = SecurityDetail(
        incident_id=detail_data.incident_id,
        security_type=detail_data.security_type,
        security_type_detail=detail_data.security_type_detail,
        severity=detail_data.severity,
        involved_parties=involved_parties_json,
        involved_parties_count=detail_data.involved_parties_count,
        victim_type=detail_data.victim_type,
        victim_code=detail_data.victim_code,
        perpetrator_type=detail_data.perpetrator_type,
        perpetrator_code=detail_data.perpetrator_code,
        police_notified=detail_data.police_notified,
        police_report_number=detail_data.police_report_number,
        security_notified=detail_data.security_notified,
        injury_occurred=detail_data.injury_occurred,
        injury_detail=detail_data.injury_detail,
        property_damage=detail_data.property_damage,
        property_damage_detail=detail_data.property_damage_detail,
        stolen_items=detail_data.stolen_items,
        immediate_response=detail_data.immediate_response,
        restraint_applied=detail_data.restraint_applied,
        isolation_applied=detail_data.isolation_applied,
        duration_minutes=detail_data.duration_minutes,
        found_location=detail_data.found_location,
        method_used=detail_data.method_used,
        risk_assessment_done=detail_data.risk_assessment_done,
        suicide_risk_level=detail_data.suicide_risk_level,
    )

    db.add(security_detail)
    await db.flush()
    await db.refresh(security_detail)

    await log_security_detail_event(
        db=db,
        user=current_user,
        detail_id=security_detail.id,
        incident_id=detail_data.incident_id,
        event="create",
        result="success",
        details={"security_type": detail_data.security_type.value},
    )

    return SecurityDetailResponse.model_validate(security_detail)


@router.get(
    "/incident/{incident_id}",
    response_model=SecurityDetailResponse,
    summary="Get security detail by incident",
)
async def get_security_detail_by_incident(
    incident_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SecurityDetailResponse:
    """Get security detail for a specific incident."""
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
        await log_security_detail_event(
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
        select(SecurityDetail).where(SecurityDetail.incident_id == incident_id)
    )
    security_detail = result.scalar_one_or_none()

    if security_detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Security detail not found for this incident",
        )

    await log_security_detail_event(
        db=db,
        user=current_user,
        detail_id=security_detail.id,
        incident_id=incident_id,
        event="view",
        result="success",
    )

    return SecurityDetailResponse.model_validate(security_detail)


@router.get(
    "/{detail_id}",
    response_model=SecurityDetailResponse,
    summary="Get security detail by ID",
)
async def get_security_detail(
    detail_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SecurityDetailResponse:
    """Get security detail by its ID."""
    result = await db.execute(
        select(SecurityDetail).where(SecurityDetail.id == detail_id)
    )
    security_detail = result.scalar_one_or_none()

    if security_detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Security detail not found",
        )

    result = await db.execute(
        select(Incident).where(
            and_(Incident.id == security_detail.incident_id, Incident.is_deleted == False)
        )
    )
    incident = result.scalar_one_or_none()

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Linked incident not found",
        )

    if not can_access_incident(current_user, incident):
        await log_security_detail_event(
            db=db,
            user=current_user,
            detail_id=detail_id,
            incident_id=security_detail.incident_id,
            event="view",
            result="denied",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this incident",
        )

    await log_security_detail_event(
        db=db,
        user=current_user,
        detail_id=detail_id,
        incident_id=security_detail.incident_id,
        event="view",
        result="success",
    )

    return SecurityDetailResponse.model_validate(security_detail)


@router.put(
    "/{detail_id}",
    response_model=SecurityDetailResponse,
    summary="Update security detail",
)
async def update_security_detail(
    detail_id: int,
    detail_data: SecurityDetailUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SecurityDetailResponse:
    """Update a security detail record. QPS_STAFF or higher required."""
    result = await db.execute(
        select(SecurityDetail).where(SecurityDetail.id == detail_id)
    )
    security_detail = result.scalar_one_or_none()

    if security_detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Security detail not found",
        )

    result = await db.execute(
        select(Incident).where(
            and_(Incident.id == security_detail.incident_id, Incident.is_deleted == False)
        )
    )
    incident = result.scalar_one_or_none()

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Linked incident not found",
        )

    if not can_edit_detail(current_user, incident):
        await log_security_detail_event(
            db=db,
            user=current_user,
            detail_id=detail_id,
            incident_id=security_detail.incident_id,
            event="update",
            result="denied",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to edit this security detail",
        )

    changes = {}
    update_data = detail_data.model_dump(exclude_unset=True)

    # Handle involved_parties specially
    if "involved_parties" in update_data and update_data["involved_parties"] is not None:
        update_data["involved_parties"] = [
            {"type": p.type.value, "code": p.code}
            for p in update_data["involved_parties"]
        ]

    for field, new_value in update_data.items():
        old_value = getattr(security_detail, field)
        if old_value != new_value:
            old_str = old_value.value if hasattr(old_value, 'value') else str(old_value)
            new_str = new_value.value if hasattr(new_value, 'value') else str(new_value)
            changes[field] = {"old": old_str, "new": new_str}
            setattr(security_detail, field, new_value)

    if changes:
        await log_security_detail_event(
            db=db,
            user=current_user,
            detail_id=detail_id,
            incident_id=security_detail.incident_id,
            event="update",
            result="success",
            details={"changes": changes},
        )

    return SecurityDetailResponse.model_validate(security_detail)


@router.delete(
    "/{detail_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete security detail",
)
async def delete_security_detail(
    detail_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete a security detail record. DIRECTOR or higher required."""
    result = await db.execute(
        select(SecurityDetail).where(SecurityDetail.id == detail_id)
    )
    security_detail = result.scalar_one_or_none()

    if security_detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Security detail not found",
        )

    if not can_delete_detail(current_user):
        await log_security_detail_event(
            db=db,
            user=current_user,
            detail_id=detail_id,
            incident_id=security_detail.incident_id,
            event="delete",
            result="denied",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete security details",
        )

    incident_id = security_detail.incident_id

    await db.delete(security_detail)

    await log_security_detail_event(
        db=db,
        user=current_user,
        detail_id=detail_id,
        incident_id=incident_id,
        event="delete",
        result="success",
    )
