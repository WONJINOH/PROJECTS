"""
Action Schemas (Pydantic)

CAPA (Corrective and Preventive Action) schemas.
"""

from datetime import datetime, date
from typing import Optional, List

from pydantic import BaseModel, Field

from app.models.action import ActionStatus, ActionPriority


class ActionBase(BaseModel):
    """Base action schema."""

    title: str = Field(..., min_length=5, max_length=200)
    description: Optional[str] = None
    owner: str = Field(..., min_length=2, max_length=100, description="담당자")
    due_date: date = Field(..., description="기한")
    definition_of_done: str = Field(
        ..., min_length=10, description="완료 기준 (DoD)"
    )
    priority: ActionPriority = ActionPriority.MEDIUM


class ActionCreate(ActionBase):
    """Schema for creating an action."""

    incident_id: int


class ActionUpdate(BaseModel):
    """Schema for updating an action."""

    title: Optional[str] = Field(None, min_length=5, max_length=200)
    description: Optional[str] = None
    owner: Optional[str] = Field(None, min_length=2, max_length=100)
    due_date: Optional[date] = None
    definition_of_done: Optional[str] = Field(None, min_length=10)
    priority: Optional[ActionPriority] = None


class ActionComplete(BaseModel):
    """Schema for completing an action."""

    completion_notes: Optional[str] = None
    evidence_attachment_id: Optional[int] = None


class ActionVerify(BaseModel):
    """Schema for verifying an action."""

    verification_notes: Optional[str] = None


class ActionResponse(ActionBase):
    """Schema for action response."""

    id: int
    incident_id: int
    status: ActionStatus
    evidence_attachment_id: Optional[int]

    # Completion info
    completed_at: Optional[datetime]
    completed_by_id: Optional[int]
    completion_notes: Optional[str]

    # Verification info
    verified_at: Optional[datetime]
    verified_by_id: Optional[int]
    verification_notes: Optional[str]

    # Metadata
    created_by_id: int
    created_at: datetime
    updated_at: datetime
    is_overdue: bool

    class Config:
        from_attributes = True


class ActionListResponse(BaseModel):
    """Schema for action list response."""

    items: List[ActionResponse]
    total: int
    skip: int
    limit: int
