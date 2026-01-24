"""
Incident Schemas (Pydantic)

Validation rules per CLAUDE.md:
- immediate_action: REQUIRED for all incidents
- reported_at: REQUIRED (datetime)
- reporter_name: Required EXCEPT for NEAR_MISS grade
"""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.incident import (
    IncidentCategory,
    IncidentGrade,
    ImprovementType,
    PolicyFactorType,
    ManagementFactorType,
    BehaviorType,
)


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

    # 개선활동내역 (복수 선택)
    improvement_types: Optional[List[ImprovementType]] = Field(None, description="개선활동내역")

    # 인적요인 - 지침/규정/절차 관련
    policy_factor: Optional[PolicyFactorType] = Field(None, description="지침/규정/절차 관련 요인")
    policy_factor_detail: Optional[str] = Field(None, description="지침 관련 요인 상세")

    # 관리 관련 요인 (복수 선택)
    management_factors: Optional[List[ManagementFactorType]] = Field(None, description="관리 관련 요인")
    management_factors_detail: Optional[str] = Field(None, description="관리 요인 상세")

    # Just Culture 분류 (QPS 담당자가 분석 후 입력)
    behavior_type: Optional[BehaviorType] = Field(None, description="행동 유형 분류")
    behavior_type_rationale: Optional[str] = Field(None, description="분류 근거")


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
    improvement_types: Optional[List[ImprovementType]] = None
    policy_factor: Optional[PolicyFactorType] = None
    policy_factor_detail: Optional[str] = None
    management_factors: Optional[List[ManagementFactorType]] = None
    management_factors_detail: Optional[str] = None
    behavior_type: Optional[BehaviorType] = None
    behavior_type_rationale: Optional[str] = None


class IncidentResponse(IncidentBase):
    """Schema for incident response."""

    id: int
    reporter_id: int
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class IncidentListResponse(BaseModel):
    """Schema for incident list response."""

    items: List[IncidentResponse]
    total: int
    skip: int
    limit: int


# === Timeline Schemas (피드백 시각화) ===

class TimelineEvent(BaseModel):
    """사건 진행 타임라인 이벤트"""
    event_type: str  # submitted, under_review, action_created, approved, closed
    status: str
    occurred_at: datetime
    actor: Optional[str] = None  # 수행자 (익명화)
    detail: Optional[str] = None  # 상세 내용
    icon: Optional[str] = None  # 프론트엔드용 아이콘 힌트


class IncidentTimelineResponse(BaseModel):
    """사건 타임라인 전체 응답"""
    incident_id: int
    current_status: str
    events: List[TimelineEvent]
    next_expected_action: Optional[str] = None  # "승인 대기 중" 등
