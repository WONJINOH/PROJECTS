"""
Attachment Management API

Endpoints for uploading, downloading, and managing incident attachments.
Files stored locally under: uploads/incidents/{incident_id}/
"""

import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import FileResponse
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.attachment import Attachment
from app.models.incident import Incident
from app.models.user import User, Role
from app.models.audit import AuditLog, AuditEventType
from app.security.dependencies import get_current_user, get_current_active_user, require_permission
from app.security.rbac import Permission

router = APIRouter()

# Maximum file size: 10MB
MAX_FILE_SIZE = 10 * 1024 * 1024

# Allowed file types
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".doc", ".docx", ".gif", ".bmp"}
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/bmp",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


async def log_attachment_event(
    db: AsyncSession,
    event_type: AuditEventType,
    user: User,
    attachment_id: int | None,
    incident_id: int,
    result: str,
    details: dict | None = None,
) -> None:
    """Log attachment event for PIPA compliance."""
    timestamp = datetime.now(timezone.utc)
    previous_hash = "genesis"

    entry_hash = AuditLog.calculate_hash(
        event_type=event_type.value,
        timestamp=timestamp,
        user_id=user.id,
        resource_id=str(attachment_id) if attachment_id else None,
        previous_hash=previous_hash,
    )

    audit_log = AuditLog(
        event_type=event_type,
        timestamp=timestamp,
        user_id=user.id,
        user_role=user.role.value,
        username=user.username,
        resource_type="attachment",
        resource_id=str(attachment_id) if attachment_id else None,
        action_detail={"incident_id": incident_id, **(details or {})},
        result=result,
        previous_hash=previous_hash,
        entry_hash=entry_hash,
    )
    db.add(audit_log)


def can_access_attachment(user: User, incident: Incident) -> bool:
    """Check if user can access attachments for an incident."""
    if user.role in [Role.VICE_CHAIR, Role.DIRECTOR, Role.MASTER]:
        return True
    if user.role == Role.QPS_STAFF:
        return incident.department == user.department
    if user.role == Role.REPORTER:
        return incident.reporter_id == user.id
    return False


def get_file_extension(filename: str) -> str:
    """Get lowercase file extension."""
    return Path(filename).suffix.lower()


def generate_safe_filename(original_filename: str) -> str:
    """Generate a safe unique filename."""
    ext = get_file_extension(original_filename)
    return f"{uuid.uuid4().hex}{ext}"


@router.post(
    "/incidents/{incident_id}/upload",
    status_code=status.HTTP_201_CREATED,
    summary="Upload attachment",
)
async def upload_attachment(
    incident_id: int,
    file: Annotated[UploadFile, File(description="File to upload")],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """
    Upload an attachment to an incident.

    Storage: uploads/incidents/{incident_id}/{filename}
    DB stores: file:// URI

    Constraints:
    - Max size: 10MB
    - Allowed types: PDF, JPG, PNG, DOC, DOCX
    """
    # Get incident and verify access
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

    if not can_access_attachment(current_user, incident):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this incident",
        )

    # Validate file
    if file.filename is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required",
        )

    ext = get_file_extension(file.filename)
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Read file content to check size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB",
        )

    # Reset file pointer
    await file.seek(0)

    # Create storage directory
    upload_dir = Path(settings.UPLOAD_DIR) / "incidents" / str(incident_id)
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Generate safe filename
    safe_filename = generate_safe_filename(file.filename)
    file_path = upload_dir / safe_filename

    # Save file
    with open(file_path, "wb") as f:
        f.write(content)

    # Create storage URI
    storage_uri = f"file://{file_path.as_posix()}"

    # Create attachment record
    attachment = Attachment(
        filename=safe_filename,
        original_filename=file.filename,
        content_type=file.content_type or "application/octet-stream",
        file_size=len(content),
        storage_uri=storage_uri,
        incident_id=incident_id,
        uploaded_by_id=current_user.id,
    )

    db.add(attachment)
    await db.flush()
    await db.refresh(attachment)

    # Log event
    await log_attachment_event(
        db=db,
        event_type=AuditEventType.ATTACHMENT_UPLOAD,
        user=current_user,
        attachment_id=attachment.id,
        incident_id=incident_id,
        result="success",
        details={
            "original_filename": file.filename,
            "size": len(content),
            "content_type": file.content_type,
        },
    )

    return {
        "id": attachment.id,
        "filename": attachment.original_filename,
        "size": attachment.file_size,
        "content_type": attachment.content_type,
        "created_at": attachment.created_at.isoformat(),
    }


@router.get(
    "/incidents/{incident_id}",
    response_model=List[dict],
    summary="List attachments for incident",
)
async def list_attachments(
    incident_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> List[dict]:
    """
    List all attachments for an incident.
    """
    # Get incident and verify access
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

    if not can_access_attachment(current_user, incident):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this incident",
        )

    # Get attachments
    result = await db.execute(
        select(Attachment).where(
            and_(
                Attachment.incident_id == incident_id,
                Attachment.is_deleted == False,
            )
        ).order_by(Attachment.created_at.desc())
    )
    attachments = result.scalars().all()

    return [
        {
            "id": a.id,
            "filename": a.original_filename,
            "size": a.file_size,
            "content_type": a.content_type,
            "created_at": a.created_at.isoformat(),
            "uploaded_by_id": a.uploaded_by_id,
        }
        for a in attachments
    ]


@router.get(
    "/{attachment_id}/download",
    summary="Download attachment",
)
async def download_attachment(
    attachment_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> FileResponse:
    """
    Download an attachment.

    Access controlled based on incident permissions.
    Download event logged for audit.
    """
    # Get attachment
    result = await db.execute(
        select(Attachment).where(
            and_(
                Attachment.id == attachment_id,
                Attachment.is_deleted == False,
            )
        )
    )
    attachment = result.scalar_one_or_none()

    if attachment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment not found",
        )

    # Get incident and verify access
    result = await db.execute(
        select(Incident).where(Incident.id == attachment.incident_id)
    )
    incident = result.scalar_one_or_none()

    if incident is None or not can_access_attachment(current_user, incident):
        await log_attachment_event(
            db=db,
            event_type=AuditEventType.ATTACHMENT_DOWNLOAD,
            user=current_user,
            attachment_id=attachment_id,
            incident_id=attachment.incident_id,
            result="denied",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this attachment",
        )

    # Get file path from URI
    storage_uri = attachment.storage_uri
    if storage_uri.startswith("file://"):
        file_path = storage_uri[7:]  # Remove "file://" prefix
    else:
        file_path = storage_uri

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on storage",
        )

    # Log download
    await log_attachment_event(
        db=db,
        event_type=AuditEventType.ATTACHMENT_DOWNLOAD,
        user=current_user,
        attachment_id=attachment_id,
        incident_id=attachment.incident_id,
        result="success",
    )

    return FileResponse(
        path=file_path,
        filename=attachment.original_filename,
        media_type=attachment.content_type,
    )


@router.delete(
    "/{attachment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete attachment",
)
async def delete_attachment(
    attachment_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """
    Delete an attachment (soft delete).

    Only uploader or authorized roles can delete.
    """
    # Get attachment
    result = await db.execute(
        select(Attachment).where(
            and_(
                Attachment.id == attachment_id,
                Attachment.is_deleted == False,
            )
        )
    )
    attachment = result.scalar_one_or_none()

    if attachment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment not found",
        )

    # Check permission: uploader, QPS_STAFF (same dept), or higher
    can_delete = False
    if attachment.uploaded_by_id == current_user.id:
        can_delete = True
    elif current_user.role in [Role.VICE_CHAIR, Role.DIRECTOR, Role.MASTER]:
        can_delete = True
    elif current_user.role == Role.QPS_STAFF:
        # Check same department
        result = await db.execute(
            select(Incident).where(Incident.id == attachment.incident_id)
        )
        incident = result.scalar_one_or_none()
        if incident and incident.department == current_user.department:
            can_delete = True

    if not can_delete:
        await log_attachment_event(
            db=db,
            event_type=AuditEventType.ATTACHMENT_DELETE,
            user=current_user,
            attachment_id=attachment_id,
            incident_id=attachment.incident_id,
            result="denied",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this attachment",
        )

    # Soft delete
    attachment.is_deleted = True
    attachment.deleted_at = datetime.now(timezone.utc)

    # Log event
    await log_attachment_event(
        db=db,
        event_type=AuditEventType.ATTACHMENT_DELETE,
        user=current_user,
        attachment_id=attachment_id,
        incident_id=attachment.incident_id,
        result="success",
        details={"filename": attachment.original_filename},
    )
