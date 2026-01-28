"""
Infection Detail Schemas (Pydantic)

Schemas for infection incident details with validation rules.
"""

from datetime import datetime, date
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field

from app.models.infection import InfectionType


class InfectionDetailBase(BaseModel):
    """Base infection detail schema with shared fields."""

    # 환자 정보 (PDF 양식 기준)
    patient_code: str = Field(..., min_length=1, max_length=50, description="환자등록번호")
    patient_name: Optional[str] = Field(None, max_length=100, description="환자명")
    patient_age_group: Optional[str] = Field(None, max_length=20, description="연령대")
    patient_gender: Optional[str] = Field(None, max_length=10, description="성별")
    room_number: Optional[str] = Field(None, max_length=50, description="병실")
    department_id: Optional[int] = Field(None, description="환자 진료과 ID")
    physician_id: Optional[int] = Field(None, description="담당 주치의 ID")
    diagnosis: Optional[str] = Field(None, max_length=500, description="진단명")

    # 감염 정보
    infection_type: InfectionType = Field(..., description="감염 유형")
    infection_site: Optional[str] = Field(None, max_length=100, description="감염 부위 (요로, 호흡기, 피부, 혈류 등)")
    infection_site_detail: Optional[str] = Field(None, max_length=200, description="감염 부위 상세")

    onset_date: Optional[date] = Field(None, description="발생일")
    diagnosis_date: Optional[date] = Field(None, description="진단일")

    # 원인균
    pathogen: Optional[str] = Field(None, max_length=200, description="원인균")
    is_mdro: bool = Field(False, description="다제내성균 여부")
    pathogen_culture_result: Optional[str] = Field(None, max_length=500, description="배양 결과")

    # 의료기기 관련
    device_related: bool = Field(False, description="기기 관련 여부")
    device_type: Optional[str] = Field(None, max_length=100, description="관련 기기 유형 (유치도뇨관, 중심정맥관 등)")
    device_insertion_date: Optional[date] = Field(None, description="기기 삽입일")
    device_days: Optional[int] = Field(None, ge=0, description="기구 유치 일수")

    # 원내 감염 여부
    is_hospital_acquired: bool = Field(True, description="원내 감염 여부 (입원 48시간 이후 발생)")
    admission_date: Optional[date] = Field(None, description="입원일")

    # 추가 정보
    department: str = Field(..., min_length=1, max_length=100, description="발생 부서")
    antibiotic_used: Optional[str] = Field(None, max_length=300, description="사용 항생제")
    treatment_notes: Optional[str] = Field(None, description="치료 내용")


class InfectionDetailCreate(InfectionDetailBase):
    """Schema for creating an infection detail."""

    incident_id: int = Field(..., description="연결할 사고 ID")


class InfectionDetailUpdate(BaseModel):
    """Schema for updating an infection detail."""

    # 환자 정보
    patient_code: Optional[str] = Field(None, min_length=1, max_length=50)
    patient_name: Optional[str] = Field(None, max_length=100)
    patient_age_group: Optional[str] = Field(None, max_length=20)
    patient_gender: Optional[str] = Field(None, max_length=10)
    room_number: Optional[str] = Field(None, max_length=50)
    department_id: Optional[int] = None
    physician_id: Optional[int] = None
    diagnosis: Optional[str] = Field(None, max_length=500)

    # 감염 정보
    infection_type: Optional[InfectionType] = None
    infection_site: Optional[str] = Field(None, max_length=100)
    infection_site_detail: Optional[str] = Field(None, max_length=200)
    onset_date: Optional[date] = None
    diagnosis_date: Optional[date] = None

    # 원인균
    pathogen: Optional[str] = Field(None, max_length=200)
    is_mdro: Optional[bool] = None
    pathogen_culture_result: Optional[str] = Field(None, max_length=500)

    # 의료기기 관련
    device_related: Optional[bool] = None
    device_type: Optional[str] = Field(None, max_length=100)
    device_insertion_date: Optional[date] = None
    device_days: Optional[int] = Field(None, ge=0)

    # 원내 감염 여부
    is_hospital_acquired: Optional[bool] = None
    admission_date: Optional[date] = None

    # 추가 정보
    department: Optional[str] = Field(None, min_length=1, max_length=100)
    antibiotic_used: Optional[str] = Field(None, max_length=300)
    treatment_notes: Optional[str] = None


class InfectionDetailResponse(InfectionDetailBase):
    """Schema for infection detail response."""

    id: int
    incident_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
