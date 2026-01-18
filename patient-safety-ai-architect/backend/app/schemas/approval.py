"""
Approval Schemas (Pydantic)
"""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field

from app.models.approval import ApprovalLevel, ApprovalStatus


class ApprovalAction(BaseModel):
    """Schema for approval/rejection action."""

    action: str = Field(..., pattern="^(approve|reject)$")
    comment: Optional[str] = Field(None, max_length=1000)
    rejection_reason: Optional[str] = Field(None, max_length=1000)


class ApprovalRecord(BaseModel):
    """Single approval record."""

    level: ApprovalLevel
    status: ApprovalStatus
    approver_name: str
    comment: Optional[str]
    rejection_reason: Optional[str]
    decided_at: Optional[datetime]

    class Config:
        from_attributes = True


class ApprovalResponse(BaseModel):
    """Schema for approval status response."""

    incident_id: int
    current_level: Optional[ApprovalLevel]
    next_required_level: Optional[ApprovalLevel]
    is_fully_approved: bool
    history: List[ApprovalRecord]

    class Config:
        from_attributes = True
