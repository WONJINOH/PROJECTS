"""
Security Detail Schemas (Pydantic)

Schemas for security incident details with validation rules.
"""

from datetime import datetime
from typing import Optional, List, Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.security_detail import (
    SecurityType,
    SecuritySeverity,
    InvolvedPartyType,
)


class InvolvedParty(BaseModel):
    """관련자 정보 (익명화)"""
    type: InvolvedPartyType
    code: str = Field(..., max_length=50)


class SecurityDetailBase(BaseModel):
    """Base security detail schema with shared fields."""

    security_type: SecurityType = Field(..., description="보안 사고 유형")
    security_type_detail: Optional[str] = Field(None, description="사고 유형 상세")

    severity: SecuritySeverity = Field(..., description="심각도")

    involved_parties: Optional[List[InvolvedParty]] = Field(None, description="관련자 목록")
    involved_parties_count: int = Field(1, ge=1, description="관련자 수")

    victim_type: Optional[InvolvedPartyType] = Field(None, description="피해자 유형")
    victim_code: Optional[str] = Field(None, max_length=50, description="피해자 코드")

    perpetrator_type: Optional[InvolvedPartyType] = Field(None, description="가해자 유형")
    perpetrator_code: Optional[str] = Field(None, max_length=50, description="가해자 코드")

    police_notified: bool = Field(False, description="경찰 신고 여부")
    police_report_number: Optional[str] = Field(None, max_length=50, description="신고 접수 번호")
    security_notified: bool = Field(False, description="보안팀 통보 여부")

    injury_occurred: bool = Field(False, description="부상 발생 여부")
    injury_detail: Optional[str] = Field(None, description="부상 상세")
    property_damage: bool = Field(False, description="재산 피해 여부")
    property_damage_detail: Optional[str] = Field(None, description="재산 피해 상세")
    stolen_items: Optional[str] = Field(None, description="도난 물품")

    immediate_response: Optional[str] = Field(None, description="즉각 대응 조치")
    restraint_applied: bool = Field(False, description="제지 적용 여부")
    isolation_applied: bool = Field(False, description="격리 적용 여부")

    duration_minutes: Optional[int] = Field(None, ge=0, description="이탈 시간 (분)")
    found_location: Optional[str] = Field(None, max_length=200, description="발견 장소")
    method_used: Optional[str] = Field(None, max_length=200, description="자해/자살 방법")

    risk_assessment_done: bool = Field(False, description="위험도 평가 시행 여부")
    suicide_risk_level: Optional[str] = Field(
        None,
        pattern=r"^(low|moderate|high)$",
        description="자살 위험도 (low/moderate/high)"
    )


class SecurityDetailCreate(SecurityDetailBase):
    """Schema for creating a security detail."""

    incident_id: int = Field(..., description="연결할 사고 ID")

    @model_validator(mode="after")
    def validate_police_report(self) -> "SecurityDetailCreate":
        """police_report_number is recommended when police_notified is True."""
        # Not strictly required, just a recommendation
        return self

    @model_validator(mode="after")
    def validate_injury_detail(self) -> "SecurityDetailCreate":
        """injury_detail is required when injury_occurred is True."""
        if self.injury_occurred and not self.injury_detail:
            raise ValueError(
                "injury_detail is required when injury_occurred is True"
            )
        return self


class SecurityDetailUpdate(BaseModel):
    """Schema for updating a security detail."""

    security_type: Optional[SecurityType] = None
    security_type_detail: Optional[str] = None

    severity: Optional[SecuritySeverity] = None

    involved_parties: Optional[List[InvolvedParty]] = None
    involved_parties_count: Optional[int] = Field(None, ge=1)

    victim_type: Optional[InvolvedPartyType] = None
    victim_code: Optional[str] = Field(None, max_length=50)

    perpetrator_type: Optional[InvolvedPartyType] = None
    perpetrator_code: Optional[str] = Field(None, max_length=50)

    police_notified: Optional[bool] = None
    police_report_number: Optional[str] = Field(None, max_length=50)
    security_notified: Optional[bool] = None

    injury_occurred: Optional[bool] = None
    injury_detail: Optional[str] = None
    property_damage: Optional[bool] = None
    property_damage_detail: Optional[str] = None
    stolen_items: Optional[str] = None

    immediate_response: Optional[str] = None
    restraint_applied: Optional[bool] = None
    isolation_applied: Optional[bool] = None

    duration_minutes: Optional[int] = Field(None, ge=0)
    found_location: Optional[str] = Field(None, max_length=200)
    method_used: Optional[str] = Field(None, max_length=200)

    risk_assessment_done: Optional[bool] = None
    suicide_risk_level: Optional[str] = Field(None, pattern=r"^(low|moderate|high)$")


class SecurityDetailResponse(SecurityDetailBase):
    """Schema for security detail response."""

    id: int
    incident_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
