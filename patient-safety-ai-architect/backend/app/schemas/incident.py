"""
Incident Schemas (Pydantic)

Validation rules per CLAUDE.md:
- immediate_action: REQUIRED for all incidents
- reported_at: REQUIRED (datetime)
- reporter_name: Required EXCEPT for NEAR_MISS grade
"""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field, field_validator, model_validator

from app.models.incident import IncidentCategory, IncidentGrade


class IncidentBase(BaseModel):
    """Base incident schema."""

    category: IncidentCategory
    grade: IncidentGrade
    occurred_at: datetime
    location: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=10)
    immediate_action: str = Field(..., min_length=5, description="REQUIRED: Immediate action taken")
    reported_at: datetime = Field(..., description="REQUIRED: When this report was created")
    reporter_name: Optional[str] = Field(None, max_length=100)
    root_cause: Optional[str] = None
    improvements: Optional[str] = None
    department: Optional[str] = Field(None, max_length=100)


class IncidentCreate(IncidentBase):
    """Schema for creating an incident."""

    @model_validator(mode="after")
    def validate_reporter_name(self) -> "IncidentCreate":
        """
        Validate reporter_name is provided except for NEAR_MISS.

        Per CLAUDE.md Form rules:
        - reporter_name: Optional ONLY if grade == NEAR_MISS
        - Required for all other grades
        """
        if self.grade != IncidentGrade.NEAR_MISS and not self.reporter_name:
            raise ValueError(
                "reporter_name is required for incidents with grade other than NEAR_MISS"
            )
        return self


class IncidentUpdate(BaseModel):
    """Schema for updating an incident."""

    category: Optional[IncidentCategory] = None
    grade: Optional[IncidentGrade] = None
    occurred_at: Optional[datetime] = None
    location: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=10)
    immediate_action: Optional[str] = Field(None, min_length=5)
    reporter_name: Optional[str] = Field(None, max_length=100)
    root_cause: Optional[str] = None
    improvements: Optional[str] = None


class IncidentResponse(IncidentBase):
    """Schema for incident response."""

    id: int
    reporter_id: int
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class IncidentListResponse(BaseModel):
    """Schema for incident list response."""

    items: List[IncidentResponse]
    total: int
    skip: int
    limit: int
