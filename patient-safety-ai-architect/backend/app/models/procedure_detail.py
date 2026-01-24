"""
Procedure (검사/시술/치료) Detail Model

PSR 양식 V항 기반 검사/시술/치료 관련 사고 상세 기록
"""

import enum
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, Enum, Text, Boolean, ForeignKey

from app.database import Base


class ProcedureType(str, enum.Enum):
    """시술/검사 유형"""
    TREATMENT = "treatment"              # 치료
    EXAMINATION = "examination"          # 검사
    PROCEDURE = "procedure"              # 시술
    RESTRAINT_RELATED = "restraint_related"  # 억제대 관련
    DIET_RELATED = "diet_related"        # 식이 관련
    OTHER = "other"


class ProcedureErrorType(str, enum.Enum):
    """오류 유형"""
    WRONG_PATIENT = "wrong_patient"          # 환자 오류
    WRONG_SITE = "wrong_site"                # 부위 오류
    WRONG_PROCEDURE = "wrong_procedure"      # 시술/검사 오류
    WRONG_TIME = "wrong_time"                # 시간 오류
    TECHNIQUE_ERROR = "technique_error"      # 술기 오류
    EQUIPMENT_FAILURE = "equipment_failure"  # 장비 결함
    CONSENT_ISSUE = "consent_issue"          # 동의서 문제
    PREPARATION_ERROR = "preparation_error"  # 준비 오류 (금식 등)
    COMPLICATION = "complication"            # 합병증
    OTHER = "other"


class ProcedureOutcome(str, enum.Enum):
    """시술/검사 결과"""
    NO_HARM = "no_harm"                  # 해 없음
    MINOR_HARM = "minor_harm"            # 경미한 해
    MODERATE_HARM = "moderate_harm"      # 중등도 해
    SEVERE_HARM = "severe_harm"          # 중증 해
    DEATH = "death"                      # 사망


class ProcedureDetail(Base):
    """검사/시술/치료 관련 사고 상세 기록"""

    __tablename__ = "procedure_details"

    id = Column(Integer, primary_key=True, index=True)

    # 기본 사고 연결
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False, index=True)

    # 시술/검사 유형
    procedure_type = Column(Enum(ProcedureType), nullable=False, index=True)

    # 시술/검사명
    procedure_name = Column(String(200), nullable=False)

    # 시술/검사 상세 내용
    procedure_detail = Column(Text, nullable=True)

    # 오류 유형
    error_type = Column(Enum(ProcedureErrorType), nullable=False, index=True)
    error_type_detail = Column(Text, nullable=True)

    # 시술/검사 결과
    outcome = Column(Enum(ProcedureOutcome), nullable=True, index=True)
    outcome_detail = Column(Text, nullable=True)

    # 동의서 관련
    consent_obtained = Column(Boolean, default=True)
    consent_issue_detail = Column(Text, nullable=True)

    # 시술/검사 시간
    procedure_datetime = Column(DateTime(timezone=True), nullable=True)

    # 시술/검사 수행자
    performer_role = Column(String(100), nullable=True)  # 의사, 간호사 등

    # 환자 정보 (익명화)
    patient_code = Column(String(50), nullable=True, index=True)

    # 시술/검사 부위
    procedure_site = Column(String(200), nullable=True)

    # 준비 상태
    preparation_done = Column(Boolean, default=True)
    preparation_issue = Column(Text, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<ProcedureDetail {self.id} - {self.procedure_type.value}>"
