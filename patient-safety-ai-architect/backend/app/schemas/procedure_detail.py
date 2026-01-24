"""
Procedure Detail Schemas (Pydantic)

Schemas for procedure incident details with validation rules.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.procedure_detail import (
    ProcedureType,
    ProcedureErrorType,
    ProcedureOutcome,
)


class ProcedureDetailBase(BaseModel):
    """Base procedure detail schema with shared fields."""

    procedure_type: ProcedureType = Field(..., description="시술/검사 유형")

    procedure_name: str = Field(..., min_length=1, max_length=200, description="시술/검사명")

    procedure_detail: Optional[str] = Field(None, description="시술/검사 상세 내용")

    error_type: ProcedureErrorType = Field(..., description="오류 유형")
    error_type_detail: Optional[str] = Field(None, description="오류 상세")

    outcome: Optional[ProcedureOutcome] = Field(None, description="시술/검사 결과")
    outcome_detail: Optional[str] = Field(None, description="결과 상세")

    consent_obtained: bool = Field(True, description="동의서 취득 여부")
    consent_issue_detail: Optional[str] = Field(None, description="동의서 문제 상세")

    procedure_datetime: Optional[datetime] = Field(None, description="시술/검사 시간")

    performer_role: Optional[str] = Field(None, max_length=100, description="수행자 역할")

    patient_code: Optional[str] = Field(None, max_length=50, description="환자 코드 (익명화)")

    procedure_site: Optional[str] = Field(None, max_length=200, description="시술/검사 부위")

    preparation_done: bool = Field(True, description="준비 상태 완료 여부")
    preparation_issue: Optional[str] = Field(None, description="준비 문제 상세")


class ProcedureDetailCreate(ProcedureDetailBase):
    """Schema for creating a procedure detail."""

    incident_id: int = Field(..., description="연결할 사고 ID")

    @model_validator(mode="after")
    def validate_consent_issue(self) -> "ProcedureDetailCreate":
        """consent_issue_detail is required when consent_obtained is False."""
        if not self.consent_obtained and not self.consent_issue_detail:
            raise ValueError(
                "consent_issue_detail is required when consent_obtained is False"
            )
        return self


class ProcedureDetailUpdate(BaseModel):
    """Schema for updating a procedure detail."""

    procedure_type: Optional[ProcedureType] = None

    procedure_name: Optional[str] = Field(None, min_length=1, max_length=200)

    procedure_detail: Optional[str] = None

    error_type: Optional[ProcedureErrorType] = None
    error_type_detail: Optional[str] = None

    outcome: Optional[ProcedureOutcome] = None
    outcome_detail: Optional[str] = None

    consent_obtained: Optional[bool] = None
    consent_issue_detail: Optional[str] = None

    procedure_datetime: Optional[datetime] = None

    performer_role: Optional[str] = Field(None, max_length=100)

    patient_code: Optional[str] = Field(None, max_length=50)

    procedure_site: Optional[str] = Field(None, max_length=200)

    preparation_done: Optional[bool] = None
    preparation_issue: Optional[str] = None


class ProcedureDetailResponse(ProcedureDetailBase):
    """Schema for procedure detail response."""

    id: int
    incident_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
