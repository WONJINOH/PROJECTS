"""
Attachment Management API

Endpoints for uploading, downloading, and managing incident attachments.
Files stored locally under: uploads/incidents/{incident_id}/
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import FileResponse

from app.security.dependencies import get_current_user, require_permission
from app.security.rbac import Permission
from app.models.user import User

router = APIRouter()

# Maximum file size: 10MB
MAX_FILE_SIZE = 10 * 1024 * 1024

# Allowed file types
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".doc", ".docx"}


@router.post(
    "/incidents/{incident_id}/upload",
    status_code=status.HTTP_201_CREATED,
    summary="Upload attachment",
)
async def upload_attachment(
    incident_id: int,
    file: Annotated[UploadFile, File(description="File to upload")],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """
    Upload an attachment to an incident.

    Storage: uploads/incidents/{incident_id}/{filename}
    DB stores: file:// URI

    Constraints:
    - Max size: 10MB
    - Allowed types: PDF, JPG, PNG, DOC, DOCX
    """
    # TODO: Implement file upload
    # 1. Validate file type and size
    # 2. Verify user can access incident
    # 3. Save file to local storage
    # 4. Create attachment record with file:// URI
    # 5. Log audit event (ATTACHMENT_UPLOAD)
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Attachment upload not yet implemented",
    )


@router.get(
    "/{attachment_id}/download",
    summary="Download attachment",
)
async def download_attachment(
    attachment_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    _: Annotated[None, Depends(require_permission(Permission.VIEW_ATTACHMENT))],
) -> FileResponse:
    """
    Download an attachment.

    Access controlled based on incident permissions.
    Download event logged for audit.
    """
    # TODO: Implement file download
    # 1. Get attachment record
    # 2. Verify user can access parent incident
    # 3. Log audit event (ATTACHMENT_DOWNLOAD)
    # 4. Return file
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Attachment download not yet implemented",
    )


@router.delete(
    "/{attachment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete attachment",
)
async def delete_attachment(
    attachment_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    """
    Delete an attachment (soft delete).

    Only uploader or authorized roles can delete.
    """
    # TODO: Implement soft delete
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Attachment deletion not yet implemented",
    )
