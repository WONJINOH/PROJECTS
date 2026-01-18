"""
Approval Workflow API

Implements 3-level approval flow:
1. QPS (L1) - QI담당자
2. Vice Chair (L2) - 부원장
3. Director (L3) - 원장
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.approval import ApprovalAction, ApprovalResponse
from app.security.dependencies import get_current_user, require_permission
from app.security.rbac import Permission
from app.models.user import User

router = APIRouter()


@router.post(
    "/incidents/{incident_id}/approve",
    response_model=ApprovalResponse,
    summary="Approve incident",
)
async def approve_incident(
    incident_id: int,
    action: ApprovalAction,
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApprovalResponse:
    """
    Approve or reject an incident at the appropriate level.

    Approval flow:
    1. QPS Staff → L1 Approval
    2. Vice Chair → L2 Approval
    3. Director → L3 Approval (final)

    Each level requires previous level approval.
    """
    # Determine required permission based on current approval state
    # TODO: Check incident's current approval level
    # and verify user has appropriate permission
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Approval not yet implemented",
    )


@router.get(
    "/incidents/{incident_id}/status",
    response_model=ApprovalResponse,
    summary="Get approval status",
)
async def get_approval_status(
    incident_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    _: Annotated[None, Depends(require_permission(Permission.VIEW_INCIDENT))],
) -> ApprovalResponse:
    """
    Get current approval status of an incident.

    Returns:
    - Current approval level (L1/L2/L3/NONE)
    - Approval history
    - Next required approver role
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Approval status not yet implemented",
    )


@router.post(
    "/incidents/{incident_id}/reject",
    response_model=ApprovalResponse,
    summary="Reject incident",
)
async def reject_incident(
    incident_id: int,
    action: ApprovalAction,
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApprovalResponse:
    """
    Reject an incident with reason.

    Rejection resets approval to previous level or NONE.
    Reason is required and logged.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Rejection not yet implemented",
    )
