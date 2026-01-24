"""
Fall Detail Schemas (Pydantic)

Schemas for fall incident details with validation rules.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.fall_detail import (
    FallInjuryLevel,
    FallRiskLevel,
    FallLocation,
    FallCause,
)


class FallDetailBase(BaseModel):
    """Base fall detail schema with shared fields."""

    patient_code: str = Field(..., min_length=1, max_length=50, description="환자 코드 (익명화)")
    patient_age_group: Optional[str] = Field(None, max_length=20, description="연령대")
    patient_gender: Optional[str] = Field(None, max_length=10, description="성별")

    pre_fall_risk_level: Optional[FallRiskLevel] = Field(None, description="사고 전 낙상 위험도")
    morse_score: Optional[int] = Field(None, ge=0, le=125, description="Morse Fall Scale 점수 (0-125)")

    fall_location: FallLocation = Field(..., description="낙상 발생 장소")
    fall_location_detail: Optional[str] = Field(None, max_length=200, description="장소 상세")
    fall_cause: FallCause = Field(..., description="낙상 원인")
    fall_cause_detail: Optional[str] = Field(None, description="원인 상세")

    occurred_hour: Optional[int] = Field(None, ge=0, le=23, description="발생 시간 (0-23)")
    shift: Optional[str] = Field(
        None,
        pattern=r"^(day|evening|night)$",
        description="근무 교대 (day/evening/night)"
    )

    injury_level: FallInjuryLevel = Field(..., description="손상 정도")
    injury_description: Optional[str] = Field(None, description="손상 설명")

    activity_at_fall: Optional[str] = Field(None, max_length=200, description="낙상 시 활동")
    was_supervised: bool = Field(False, description="감독 여부")
    had_fall_prevention: bool = Field(False, description="낙상예방조치 시행 여부")

    department: str = Field(..., min_length=1, max_length=100, description="부서")

    is_recurrence: bool = Field(False, description="재발 여부")
    previous_fall_count: int = Field(0, ge=0, description="이전 낙상 횟수")


class FallDetailCreate(FallDetailBase):
    """Schema for creating a fall detail."""

    incident_id: int = Field(..., description="연결할 사고 ID")

    @model_validator(mode="after")
    def validate_injury_description_required(self) -> "FallDetailCreate":
        """injury_description is required when injury_level is not NONE."""
        if self.injury_level != FallInjuryLevel.NONE and not self.injury_description:
            raise ValueError(
                "injury_description is required when injury_level is not NONE"
            )
        return self


class FallDetailUpdate(BaseModel):
    """Schema for updating a fall detail."""

    patient_code: Optional[str] = Field(None, min_length=1, max_length=50)
    patient_age_group: Optional[str] = Field(None, max_length=20)
    patient_gender: Optional[str] = Field(None, max_length=10)

    pre_fall_risk_level: Optional[FallRiskLevel] = None
    morse_score: Optional[int] = Field(None, ge=0, le=125)

    fall_location: Optional[FallLocation] = None
    fall_location_detail: Optional[str] = Field(None, max_length=200)
    fall_cause: Optional[FallCause] = None
    fall_cause_detail: Optional[str] = None

    occurred_hour: Optional[int] = Field(None, ge=0, le=23)
    shift: Optional[str] = Field(None, pattern=r"^(day|evening|night)$")

    injury_level: Optional[FallInjuryLevel] = None
    injury_description: Optional[str] = None

    activity_at_fall: Optional[str] = Field(None, max_length=200)
    was_supervised: Optional[bool] = None
    had_fall_prevention: Optional[bool] = None

    department: Optional[str] = Field(None, min_length=1, max_length=100)

    is_recurrence: Optional[bool] = None
    previous_fall_count: Optional[int] = Field(None, ge=0)


class FallDetailResponse(FallDetailBase):
    """Schema for fall detail response."""

    id: int
    incident_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
