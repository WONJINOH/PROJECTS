"""
Transfusion Detail Schemas (Pydantic)

Schemas for transfusion incident details with validation rules.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.transfusion_detail import (
    BloodVerificationMethod,
    TransfusionErrorType,
    TransfusionReactionType,
)


class TransfusionDetailBase(BaseModel):
    """Base transfusion detail schema with shared fields."""

    blood_type_verified: bool = Field(True, description="혈액형 확인 여부")
    verification_method: Optional[BloodVerificationMethod] = Field(None, description="확인 방법")

    error_type: TransfusionErrorType = Field(..., description="오류 유형")
    error_type_detail: Optional[str] = Field(None, description="오류 상세")

    reaction_type: Optional[TransfusionReactionType] = Field(None, description="수혈 반응 유형")
    reaction_detail: Optional[str] = Field(None, description="반응 상세")

    blood_product_type: Optional[str] = Field(None, max_length=100, description="혈액제제 종류")
    blood_unit_id: Optional[str] = Field(None, max_length=50, description="혈액 단위 ID")

    infusion_volume_ml: Optional[int] = Field(None, ge=0, description="수혈량 (ml)")
    infusion_rate: Optional[str] = Field(None, max_length=50, description="수혈 속도")

    start_time: Optional[datetime] = Field(None, description="수혈 시작 시간")
    end_time: Optional[datetime] = Field(None, description="수혈 종료 시간")

    patient_code: Optional[str] = Field(None, max_length=50, description="환자 코드 (익명화)")
    patient_blood_type: Optional[str] = Field(None, max_length=10, description="환자 혈액형")

    pre_transfusion_check_done: bool = Field(True, description="수혈 전 확인 시행 여부")
    two_person_verification: bool = Field(True, description="2인 확인 시행 여부")


class TransfusionDetailCreate(TransfusionDetailBase):
    """Schema for creating a transfusion detail."""

    incident_id: int = Field(..., description="연결할 사고 ID")

    @model_validator(mode="after")
    def validate_reaction_detail(self) -> "TransfusionDetailCreate":
        """reaction_detail is required when reaction_type is not NONE."""
        if self.reaction_type and self.reaction_type != TransfusionReactionType.NONE:
            if not self.reaction_detail:
                raise ValueError(
                    "reaction_detail is required when reaction_type is not NONE"
                )
        return self


class TransfusionDetailUpdate(BaseModel):
    """Schema for updating a transfusion detail."""

    blood_type_verified: Optional[bool] = None
    verification_method: Optional[BloodVerificationMethod] = None

    error_type: Optional[TransfusionErrorType] = None
    error_type_detail: Optional[str] = None

    reaction_type: Optional[TransfusionReactionType] = None
    reaction_detail: Optional[str] = None

    blood_product_type: Optional[str] = Field(None, max_length=100)
    blood_unit_id: Optional[str] = Field(None, max_length=50)

    infusion_volume_ml: Optional[int] = Field(None, ge=0)
    infusion_rate: Optional[str] = Field(None, max_length=50)

    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    patient_code: Optional[str] = Field(None, max_length=50)
    patient_blood_type: Optional[str] = Field(None, max_length=10)

    pre_transfusion_check_done: Optional[bool] = None
    two_person_verification: Optional[bool] = None


class TransfusionDetailResponse(TransfusionDetailBase):
    """Schema for transfusion detail response."""

    id: int
    incident_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
