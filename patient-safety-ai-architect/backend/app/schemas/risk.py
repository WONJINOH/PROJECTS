"""
Risk Management Schemas (Pydantic)

Schemas for risk register and risk assessment with validation rules.
"""

from datetime import datetime, date
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.risk import (
    RiskSourceType,
    RiskCategory,
    RiskLevel,
    RiskStatus,
    RiskAssessmentType,
)


# === Risk Schemas ===

class RiskBase(BaseModel):
    """Base risk schema with shared fields."""

    title: str = Field(..., min_length=1, max_length=200, description="위험 제목")
    description: str = Field(..., min_length=10, description="위험 설명")

    source_type: RiskSourceType = Field(..., description="위험 식별 출처")
    source_incident_id: Optional[int] = Field(None, description="출처 PSR ID")
    source_detail: Optional[str] = Field(None, description="출처 상세")

    category: RiskCategory = Field(..., description="위험 분류")

    current_controls: Optional[str] = Field(None, description="현재 통제 방법")

    # P×S 평가
    probability: int = Field(..., ge=1, le=5, description="발생가능성 (1-5)")
    severity: int = Field(..., ge=1, le=5, description="심각도 (1-5)")

    target_date: Optional[date] = Field(None, description="목표 완료일")


class RiskCreate(RiskBase):
    """Schema for creating a risk."""

    owner_id: int = Field(..., description="책임자 ID")

    @model_validator(mode="after")
    def validate_source(self) -> "RiskCreate":
        """PSR 출처인 경우 source_incident_id 필수"""
        if self.source_type == RiskSourceType.PSR and not self.source_incident_id:
            raise ValueError(
                "source_incident_id is required when source_type is PSR"
            )
        return self


class RiskUpdate(BaseModel):
    """Schema for updating a risk."""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=10)

    source_detail: Optional[str] = None

    current_controls: Optional[str] = None

    probability: Optional[int] = Field(None, ge=1, le=5)
    severity: Optional[int] = Field(None, ge=1, le=5)

    # 잔여위험 (조치 후 재평가)
    residual_probability: Optional[int] = Field(None, ge=1, le=5)
    residual_severity: Optional[int] = Field(None, ge=1, le=5)

    owner_id: Optional[int] = None
    target_date: Optional[date] = None
    status: Optional[RiskStatus] = None


class RiskResponse(RiskBase):
    """Schema for risk response."""

    id: int
    risk_code: str

    risk_score: int  # P×S 자동 계산
    risk_level: RiskLevel

    residual_probability: Optional[int] = None
    residual_severity: Optional[int] = None
    residual_score: Optional[int] = None
    residual_level: Optional[RiskLevel] = None

    owner_id: int
    status: RiskStatus

    auto_escalated: bool
    escalation_reason: Optional[str] = None

    created_by_id: int
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None
    closed_by_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class RiskListResponse(BaseModel):
    """Schema for risk list response."""

    items: List[RiskResponse]
    total: int
    skip: int
    limit: int


class RiskMatrixCell(BaseModel):
    """5×5 Risk Matrix 셀 데이터"""
    probability: int
    severity: int
    count: int
    risk_ids: List[int]
    level: RiskLevel


class RiskMatrixResponse(BaseModel):
    """5×5 Risk Matrix 전체 응답"""
    matrix: List[List[RiskMatrixCell]]  # 5×5 matrix
    total_risks: int
    by_level: dict  # {"low": 10, "medium": 5, "high": 2, "critical": 1}


# === RiskAssessment Schemas ===

class RiskAssessmentBase(BaseModel):
    """Base risk assessment schema."""

    probability: int = Field(..., ge=1, le=5, description="발생가능성 (1-5)")
    severity: int = Field(..., ge=1, le=5, description="심각도 (1-5)")
    rationale: Optional[str] = Field(None, description="평가 근거")


class RiskAssessmentCreate(RiskAssessmentBase):
    """Schema for creating a risk assessment."""

    risk_id: int = Field(..., description="위험 ID")
    assessment_type: RiskAssessmentType = Field(..., description="평가 유형")


class RiskAssessmentResponse(RiskAssessmentBase):
    """Schema for risk assessment response."""

    id: int
    risk_id: int
    assessment_type: RiskAssessmentType

    score: int  # P×S 자동 계산
    level: RiskLevel

    assessed_at: datetime
    assessor_id: int

    model_config = ConfigDict(from_attributes=True)


# === Auto Escalation Schemas ===

class EscalationCandidate(BaseModel):
    """PSR → Risk 자동 승격 후보"""
    incident_id: int
    category: str
    grade: str
    occurred_at: datetime
    reason: str  # 승격 사유
    suggested_probability: int
    suggested_severity: int


class EscalationResult(BaseModel):
    """자동 승격 결과"""
    escalated_count: int
    candidates: List[EscalationCandidate]
    created_risks: List[RiskResponse]
