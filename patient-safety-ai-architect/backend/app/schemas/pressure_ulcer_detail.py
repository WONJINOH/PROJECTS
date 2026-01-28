"""
Pressure Ulcer Detail Schemas (Pydantic)

Schemas for pressure ulcer incident details with validation rules.
"""

from datetime import datetime, date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.pressure_ulcer import PressureUlcerGrade, PressureUlcerLocation, PressureUlcerOrigin


class PressureUlcerDetailBase(BaseModel):
    """Base pressure ulcer detail schema with shared fields."""

    # 환자 정보
    patient_code: str = Field(..., min_length=1, max_length=50, description="환자등록번호")
    patient_name: Optional[str] = Field(None, max_length=100, description="환자명")
    patient_age_group: Optional[str] = Field(None, max_length=20, description="연령대")
    patient_gender: Optional[str] = Field(None, max_length=10, description="성별")
    room_number: Optional[str] = Field(None, max_length=50, description="병실")
    admission_date: Optional[date] = Field(None, description="입원일")

    # 욕창 기본 정보
    ulcer_id: str = Field(..., min_length=1, max_length=50, description="욕창별 고유 ID")
    location: PressureUlcerLocation = Field(..., description="욕창 발생 부위")
    location_detail: Optional[str] = Field(None, max_length=100, description="발생 부위 상세 (기타인 경우)")
    origin: PressureUlcerOrigin = Field(..., description="발생 시점 (입원시/재원중)")
    discovery_date: date = Field(..., description="발견일")

    # 현재 상태 (초기 평가)
    grade: PressureUlcerGrade = Field(..., description="욕창 등급")

    # PUSH Score (선택적 - 초기 평가시)
    push_length_width: Optional[int] = Field(None, ge=0, le=10, description="PUSH 길이x너비 (0-10)")
    push_exudate: Optional[int] = Field(None, ge=0, le=3, description="PUSH 삼출물 (0-3)")
    push_tissue_type: Optional[int] = Field(None, ge=0, le=4, description="PUSH 조직유형 (0-4)")

    # 크기
    length_cm: Optional[float] = Field(None, ge=0, description="길이 (cm)")
    width_cm: Optional[float] = Field(None, ge=0, description="너비 (cm)")
    depth_cm: Optional[float] = Field(None, ge=0, description="깊이 (cm)")

    # 부서
    department: str = Field(..., min_length=1, max_length=100, description="발생 부서")

    # 추가 정보
    risk_factors: Optional[str] = Field(None, description="위험 요인")
    treatment_plan: Optional[str] = Field(None, description="치료 계획")
    note: Optional[str] = Field(None, description="비고")


class PressureUlcerDetailCreate(PressureUlcerDetailBase):
    """Schema for creating a pressure ulcer detail."""

    incident_id: int = Field(..., description="연결할 사고 ID")


class PressureUlcerDetailUpdate(BaseModel):
    """Schema for updating a pressure ulcer detail."""

    # 환자 정보
    patient_code: Optional[str] = Field(None, min_length=1, max_length=50)
    patient_name: Optional[str] = Field(None, max_length=100)
    patient_age_group: Optional[str] = Field(None, max_length=20)
    patient_gender: Optional[str] = Field(None, max_length=10)
    room_number: Optional[str] = Field(None, max_length=50)
    admission_date: Optional[date] = None

    # 욕창 기본 정보
    ulcer_id: Optional[str] = Field(None, min_length=1, max_length=50)
    location: Optional[PressureUlcerLocation] = None
    location_detail: Optional[str] = Field(None, max_length=100)
    origin: Optional[PressureUlcerOrigin] = None
    discovery_date: Optional[date] = None

    # 현재 상태
    grade: Optional[PressureUlcerGrade] = None

    # PUSH Score
    push_length_width: Optional[int] = Field(None, ge=0, le=10)
    push_exudate: Optional[int] = Field(None, ge=0, le=3)
    push_tissue_type: Optional[int] = Field(None, ge=0, le=4)

    # 크기
    length_cm: Optional[float] = Field(None, ge=0)
    width_cm: Optional[float] = Field(None, ge=0)
    depth_cm: Optional[float] = Field(None, ge=0)

    # 부서
    department: Optional[str] = Field(None, min_length=1, max_length=100)

    # 추가 정보
    risk_factors: Optional[str] = None
    treatment_plan: Optional[str] = None
    note: Optional[str] = None


class PressureUlcerDetailResponse(PressureUlcerDetailBase):
    """Schema for pressure ulcer detail response."""

    id: int
    incident_id: int
    push_total: Optional[float] = None
    is_healed: bool = False
    healed_date: Optional[date] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
