"""
Thermal Injury Detail Schemas (Pydantic)

Schemas for thermal injury incident details with validation rules.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.thermal_injury_detail import (
    ThermalInjurySource,
    ThermalInjurySeverity,
    ThermalInjuryBodyPart,
)


class ThermalInjuryDetailBase(BaseModel):
    """Base thermal injury detail schema with shared fields."""

    injury_source: ThermalInjurySource = Field(..., description="사고 원인 물질")
    injury_source_detail: Optional[str] = Field(None, max_length=200, description="원인 물질 상세")

    injury_severity: ThermalInjurySeverity = Field(..., description="손상 정도")

    body_part: ThermalInjuryBodyPart = Field(..., description="손상 부위")
    body_part_detail: Optional[str] = Field(None, max_length=200, description="부위 상세")

    injury_size: Optional[str] = Field(None, max_length=50, description="손상 범위 (예: 5x3cm)")

    application_duration_min: Optional[int] = Field(None, ge=0, description="적용 시간 (분)")

    temperature_celsius: Optional[str] = Field(None, max_length=20, description="온도 (℃)")

    patient_code: Optional[str] = Field(None, max_length=50, description="환자 코드 (익명화)")

    patient_sensory_intact: Optional[str] = Field(
        None,
        pattern=r"^(intact|impaired|absent)$",
        description="감각 상태 (intact/impaired/absent)"
    )

    treatment_provided: Optional[str] = Field(None, description="치료 내용")


class ThermalInjuryDetailCreate(ThermalInjuryDetailBase):
    """Schema for creating a thermal injury detail."""

    incident_id: int = Field(..., description="연결할 사고 ID")

    @model_validator(mode="after")
    def validate_severity_treatment(self) -> "ThermalInjuryDetailCreate":
        """treatment_provided is required when injury_severity is not NONE."""
        if self.injury_severity != ThermalInjurySeverity.NONE and not self.treatment_provided:
            raise ValueError(
                "treatment_provided is required when injury_severity is not NONE"
            )
        return self


class ThermalInjuryDetailUpdate(BaseModel):
    """Schema for updating a thermal injury detail."""

    injury_source: Optional[ThermalInjurySource] = None
    injury_source_detail: Optional[str] = Field(None, max_length=200)

    injury_severity: Optional[ThermalInjurySeverity] = None

    body_part: Optional[ThermalInjuryBodyPart] = None
    body_part_detail: Optional[str] = Field(None, max_length=200)

    injury_size: Optional[str] = Field(None, max_length=50)

    application_duration_min: Optional[int] = Field(None, ge=0)

    temperature_celsius: Optional[str] = Field(None, max_length=20)

    patient_code: Optional[str] = Field(None, max_length=50)

    patient_sensory_intact: Optional[str] = Field(None, pattern=r"^(intact|impaired|absent)$")

    treatment_provided: Optional[str] = None


class ThermalInjuryDetailResponse(ThermalInjuryDetailBase):
    """Schema for thermal injury detail response."""

    id: int
    incident_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
