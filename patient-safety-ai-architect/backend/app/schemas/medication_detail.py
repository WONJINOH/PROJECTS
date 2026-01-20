"""
Medication Detail Schemas (Pydantic)

Schemas for medication error incident details with validation rules.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, model_validator

from app.models.medication_detail import (
    MedicationErrorType,
    MedicationErrorStage,
    MedicationErrorSeverity,
    HighAlertMedication,
)


class MedicationDetailBase(BaseModel):
    """Base medication detail schema with shared fields."""

    patient_code: str = Field(..., min_length=1, max_length=50, description="환자 코드 (익명화)")
    patient_age_group: Optional[str] = Field(None, max_length=20, description="연령대")

    error_type: MedicationErrorType = Field(..., description="투약 오류 유형")
    error_stage: MedicationErrorStage = Field(..., description="오류 발견 단계")
    error_severity: MedicationErrorSeverity = Field(..., description="심각도 (NCC MERP A-I)")

    is_near_miss: bool = Field(False, description="근접오류 여부")

    medication_category: Optional[str] = Field(None, max_length=100, description="약물 분류")
    is_high_alert: bool = Field(False, description="고위험 약물 여부")
    high_alert_type: Optional[HighAlertMedication] = Field(None, description="고위험 약물 유형")

    intended_dose: Optional[str] = Field(None, max_length=100, description="의도한 용량")
    actual_dose: Optional[str] = Field(None, max_length=100, description="실제 용량")
    intended_route: Optional[str] = Field(None, max_length=50, description="의도한 경로")
    actual_route: Optional[str] = Field(None, max_length=50, description="실제 경로")

    discovered_by_role: Optional[str] = Field(None, max_length=50, description="발견자 역할")
    discovery_method: Optional[str] = Field(None, max_length=100, description="발견 방법")

    department: str = Field(..., min_length=1, max_length=100, description="부서")

    barcode_scanned: Optional[bool] = Field(None, description="바코드 스캔 여부")
    contributing_factors: Optional[str] = Field(None, description="기여 요인")


class MedicationDetailCreate(MedicationDetailBase):
    """Schema for creating a medication detail."""

    incident_id: int = Field(..., description="연결할 사고 ID")

    @model_validator(mode="after")
    def validate_high_alert_type_required(self) -> "MedicationDetailCreate":
        """high_alert_type is required when is_high_alert is True."""
        if self.is_high_alert and not self.high_alert_type:
            raise ValueError(
                "high_alert_type is required when is_high_alert is True"
            )
        return self


class MedicationDetailUpdate(BaseModel):
    """Schema for updating a medication detail."""

    patient_code: Optional[str] = Field(None, min_length=1, max_length=50)
    patient_age_group: Optional[str] = Field(None, max_length=20)

    error_type: Optional[MedicationErrorType] = None
    error_stage: Optional[MedicationErrorStage] = None
    error_severity: Optional[MedicationErrorSeverity] = None

    is_near_miss: Optional[bool] = None

    medication_category: Optional[str] = Field(None, max_length=100)
    is_high_alert: Optional[bool] = None
    high_alert_type: Optional[HighAlertMedication] = None

    intended_dose: Optional[str] = Field(None, max_length=100)
    actual_dose: Optional[str] = Field(None, max_length=100)
    intended_route: Optional[str] = Field(None, max_length=50)
    actual_route: Optional[str] = Field(None, max_length=50)

    discovered_by_role: Optional[str] = Field(None, max_length=50)
    discovery_method: Optional[str] = Field(None, max_length=100)

    department: Optional[str] = Field(None, min_length=1, max_length=100)

    barcode_scanned: Optional[bool] = None
    contributing_factors: Optional[str] = None


class MedicationDetailResponse(MedicationDetailBase):
    """Schema for medication detail response."""

    id: int
    incident_id: int
    created_at: datetime

    class Config:
        from_attributes = True
