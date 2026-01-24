"""
Environment Detail Schemas (Pydantic)

Schemas for environment incident details with validation rules.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.environment_detail import (
    EnvironmentType,
    EnvironmentSeverity,
)


class EnvironmentDetailBase(BaseModel):
    """Base environment detail schema with shared fields."""

    environment_type: EnvironmentType = Field(..., description="환경 사고 유형")
    environment_type_detail: Optional[str] = Field(None, description="사고 유형 상세")

    severity: EnvironmentSeverity = Field(..., description="심각도")

    location_specific: Optional[str] = Field(None, max_length=200, description="구체적 장소")
    location_floor: Optional[str] = Field(None, max_length=50, description="층")
    location_room: Optional[str] = Field(None, max_length=50, description="호실")

    equipment_involved: Optional[str] = Field(None, max_length=200, description="관련 장비/시설")
    equipment_id: Optional[str] = Field(None, max_length=50, description="장비 ID")

    damage_extent: Optional[str] = Field(None, description="피해 범위")

    injury_occurred: bool = Field(False, description="인명 피해 발생 여부")
    injury_count: int = Field(0, ge=0, description="부상자 수")
    injury_detail: Optional[str] = Field(None, description="부상 상세")

    property_damage: bool = Field(False, description="재산 피해 발생 여부")
    property_damage_detail: Optional[str] = Field(None, description="재산 피해 상세")
    estimated_cost: Optional[str] = Field(None, max_length=50, description="추정 비용")

    immediate_response: Optional[str] = Field(None, description="즉각 대응 조치")
    evacuation_required: bool = Field(False, description="대피 필요 여부")
    external_help_called: bool = Field(False, description="외부 도움 요청 여부")

    cause_identified: bool = Field(False, description="원인 파악 여부")
    cause_detail: Optional[str] = Field(None, description="원인 상세")


class EnvironmentDetailCreate(EnvironmentDetailBase):
    """Schema for creating an environment detail."""

    incident_id: int = Field(..., description="연결할 사고 ID")

    @model_validator(mode="after")
    def validate_injury_detail(self) -> "EnvironmentDetailCreate":
        """injury_detail is required when injury_occurred is True."""
        if self.injury_occurred and not self.injury_detail:
            raise ValueError(
                "injury_detail is required when injury_occurred is True"
            )
        return self


class EnvironmentDetailUpdate(BaseModel):
    """Schema for updating an environment detail."""

    environment_type: Optional[EnvironmentType] = None
    environment_type_detail: Optional[str] = None

    severity: Optional[EnvironmentSeverity] = None

    location_specific: Optional[str] = Field(None, max_length=200)
    location_floor: Optional[str] = Field(None, max_length=50)
    location_room: Optional[str] = Field(None, max_length=50)

    equipment_involved: Optional[str] = Field(None, max_length=200)
    equipment_id: Optional[str] = Field(None, max_length=50)

    damage_extent: Optional[str] = None

    injury_occurred: Optional[bool] = None
    injury_count: Optional[int] = Field(None, ge=0)
    injury_detail: Optional[str] = None

    property_damage: Optional[bool] = None
    property_damage_detail: Optional[str] = None
    estimated_cost: Optional[str] = Field(None, max_length=50)

    immediate_response: Optional[str] = None
    evacuation_required: Optional[bool] = None
    external_help_called: Optional[bool] = None

    cause_identified: Optional[bool] = None
    cause_detail: Optional[str] = None


class EnvironmentDetailResponse(EnvironmentDetailBase):
    """Schema for environment detail response."""

    id: int
    incident_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
