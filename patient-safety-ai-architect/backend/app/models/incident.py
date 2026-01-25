"""
Incident Model

Patient safety incident with required fields per CLAUDE.md:
- immediate_action: REQUIRED for all incidents
- reported_at: REQUIRED (datetime)
- reporter_name: Required except for NEAR_MISS grade
"""

import enum
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum, Text, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy_utils import EncryptedType
from sqlalchemy_utils.types.encrypted.encrypted_type import AesEngine

from app.database import Base
from app.config import settings


class IncidentOutcomeImpact(str, enum.Enum):
    """문제의 결과 - 환자에게 미친 영향 (PSR 공통)"""
    NONE = "none"                            # 영향 없음
    EXTENDED_STAY = "extended_stay"          # 입원 연장
    ADDITIONAL_TREATMENT = "additional_treatment"  # 추가 치료 필요
    READMISSION = "readmission"              # 재입원
    DISABILITY = "disability"                # 장애
    DEATH = "death"                          # 사망
    OTHER = "other"                          # 기타


class ContributingFactorType(str, enum.Enum):
    """기여요인 유형 (PSR 공통)"""
    # 인적요인
    HUMAN_COMMUNICATION = "human_communication"      # 의사소통 문제
    HUMAN_FATIGUE = "human_fatigue"                  # 피로/스트레스
    HUMAN_KNOWLEDGE = "human_knowledge"              # 지식/기술 부족
    HUMAN_SUPERVISION = "human_supervision"          # 감독 부재
    HUMAN_VERIFICATION = "human_verification"        # 확인 절차 미이행
    # 시스템요인
    SYSTEM_POLICY = "system_policy"                  # 정책/절차 미흡
    SYSTEM_WORKLOAD = "system_workload"              # 업무과중
    SYSTEM_STAFFING = "system_staffing"              # 인력 부족
    SYSTEM_TRAINING = "system_training"              # 교육/훈련 부족
    # 시설/장비요인
    FACILITY_EQUIPMENT = "facility_equipment"        # 장비 결함/부족
    FACILITY_ENVIRONMENT = "facility_environment"    # 환경 문제 (조명, 바닥 등)
    FACILITY_DESIGN = "facility_design"              # 설계/배치 문제
    # 기타
    OTHER = "other"                                  # 기타


class PatientPhysicalOutcome(str, enum.Enum):
    """환자 신체적 손상 결과 (PSR 공통)"""
    NONE = "none"                        # 손상 없음
    TEMPORARY_MILD = "temporary_mild"    # 일시적 경미
    TEMPORARY_MODERATE = "temporary_moderate"  # 일시적 중등도
    PERMANENT = "permanent"              # 영구적 손상
    DEATH = "death"                      # 사망


class ImprovementType(str, enum.Enum):
    """개선활동내역 (PSR 공통)"""
    POLICY_UPDATE = "policy_update"                # 업무지침수정
    PROCESS_IMPROVEMENT = "process_improvement"    # 업무과정개선
    TRAINING = "training"                          # 정기교육 및 재교육
    FACILITY_IMPROVEMENT = "facility_improvement"  # 시설보완


class PolicyFactorType(str, enum.Enum):
    """인적요인 - 지침/규정/절차 관련"""
    NO_POLICY = "no_policy"                        # 지침/규정/절차 없음
    NOT_TRAINED = "not_trained"                    # 있으나 교육 안받음
    TRAINED_NOT_FOLLOWED = "trained_not_followed"  # 교육 받았으나 미이행
    UNAVOIDABLE = "unavoidable"                    # 불가항력적
    OTHER = "other"


class ManagementFactorType(str, enum.Enum):
    """관리 관련 요인"""
    FACILITY = "facility"                # 시설
    EQUIPMENT = "equipment"              # 장비/비품
    MEDICAL_DEVICE = "medical_device"    # 의료기기


class BehaviorType(str, enum.Enum):
    """
    Just Culture 행동 유형 분류

    행동 유형에 따른 시스템 대응:
    - HUMAN_ERROR: 위로 + 시스템 개선 (징계 없음)
    - AT_RISK: 코칭 + 인센티브 재설계 (교육)
    - RECKLESS: 시스템 개선 + 징계 검토
    - SYSTEM_INDUCED: 시스템 개선 (개인 책임 없음)
    """
    HUMAN_ERROR = "human_error"          # 실수 (의도 없는 오류)
    AT_RISK = "at_risk"                  # 위험 감수 (규칙 위반이나 이유 있음)
    RECKLESS = "reckless"                # 무모한 행동 (의도적 무시)
    SYSTEM_INDUCED = "system_induced"    # 시스템이 유발한 오류
    NOT_APPLICABLE = "not_applicable"    # 해당 없음 (환경/장비 요인 등)
    PENDING_REVIEW = "pending_review"    # 검토 대기


class IncidentCategory(str, enum.Enum):
    """Incident categories."""

    FALL = "fall"                          # 낙상
    MEDICATION = "medication"              # 투약
    PRESSURE_ULCER = "pressure_ulcer"      # 욕창
    INFECTION = "infection"                # 감염
    MEDICAL_DEVICE = "medical_device"      # 의료기기
    SURGERY = "surgery"                    # 수술
    TRANSFUSION = "transfusion"            # 수혈
    THERMAL_INJURY = "thermal_injury"      # 열냉사고
    PROCEDURE = "procedure"                # 검사/시술/치료
    ENVIRONMENT = "environment"            # 환경
    SECURITY = "security"                  # 보안
    ELOPEMENT = "elopement"                # 무단이탈/탈원
    VIOLENCE = "violence"                  # 폭력
    FIRE = "fire"                          # 방화
    SUICIDE = "suicide"                    # 자살
    SELF_HARM = "self_harm"                # 자해
    OTHER = "other"                        # 기타


class IncidentGrade(str, enum.Enum):
    """Incident severity grades."""

    NEAR_MISS = "near_miss"    # 근접오류 (reporter_name optional)
    NO_HARM = "no_harm"        # 위해없음
    MILD = "mild"              # 일시적 손상 - 경증
    MODERATE = "moderate"      # 일시적 손상 - 중등도
    SEVERE = "severe"          # 영구적 손상
    DEATH = "death"            # 사망


def enum_values_callable(enum_class):
    """Return enum values for SQLAlchemy Enum type to ensure lowercase values are used."""
    return [e.value for e in enum_class]


class Incident(Base):
    """Patient safety incident model."""

    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)

    # === Common Page Required Fields ===
    # Use values_callable to ensure enum values (lowercase) are sent to PostgreSQL
    category = Column(
        SQLEnum(IncidentCategory, values_callable=lambda x: enum_values_callable(x)),
        nullable=False, index=True
    )
    grade = Column(
        SQLEnum(IncidentGrade, values_callable=lambda x: enum_values_callable(x)),
        nullable=False, index=True
    )
    occurred_at = Column(DateTime(timezone=True), nullable=False)
    location = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)

    # REQUIRED: immediate action taken
    immediate_action = Column(Text, nullable=False)

    # REQUIRED: when report was created
    reported_at = Column(DateTime(timezone=True), nullable=False)

    # Required EXCEPT for NEAR_MISS (validated in schema)
    reporter_name = Column(String(100), nullable=True)

    # === Optional Fields ===
    root_cause = Column(Text, nullable=True)
    improvements = Column(Text, nullable=True)

    # === PSR 공통 필드 (대시보드용) ===

    # 문제의 결과 - 환자에게 미친 영향
    outcome_impact = Column(
        SQLEnum(IncidentOutcomeImpact, values_callable=lambda x: enum_values_callable(x)),
        nullable=True, index=True
    )
    outcome_impact_detail = Column(Text, nullable=True)

    # 기여요인 (복수 선택) - JSON 배열로 저장
    # 예: ["human_communication", "system_workload", "facility_environment"]
    contributing_factors = Column(JSON, nullable=True)
    contributing_factors_detail = Column(Text, nullable=True)

    # 환자 신체적 손상 결과
    patient_physical_outcome = Column(
        SQLEnum(PatientPhysicalOutcome, values_callable=lambda x: enum_values_callable(x)),
        nullable=True, index=True
    )
    patient_physical_outcome_detail = Column(Text, nullable=True)

    # 개선활동내역 (복수 선택) - JSON 배열로 저장
    # 예: ["policy_update", "training"]
    improvement_types = Column(JSON, nullable=True)

    # 인적요인 - 지침/규정/절차 관련
    policy_factor = Column(
        SQLEnum(PolicyFactorType, values_callable=lambda x: enum_values_callable(x)),
        nullable=True
    )
    policy_factor_detail = Column(Text, nullable=True)

    # 관리 관련 요인 (복수 선택) - JSON 배열로 저장
    # 예: ["facility", "equipment"]
    management_factors = Column(JSON, nullable=True)
    management_factors_detail = Column(Text, nullable=True)

    # === Just Culture 분류 ===
    # 행동 유형 분류 (QPS 담당자가 분석 후 입력)
    behavior_type = Column(
        SQLEnum(BehaviorType, values_callable=lambda x: enum_values_callable(x)),
        nullable=True, index=True
    )
    behavior_type_rationale = Column(Text, nullable=True)  # 분류 근거

    # === Sensitive Patient Info (Encrypted) ===
    # Note: In production, use proper key management
    patient_info = Column(
        EncryptedType(Text, settings.DB_ENCRYPTION_KEY, AesEngine, "pkcs5"),
        nullable=True,
    )

    # === Metadata ===
    reporter_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    department = Column(String(100), nullable=True)
    status = Column(String(50), default="draft", index=True)  # draft, submitted, approved, closed
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    reporter = relationship("User", back_populates="incidents")
    attachments = relationship("Attachment", back_populates="incident")
    approvals = relationship("Approval", back_populates="incident")
    actions = relationship("Action", back_populates="incident")

    def __repr__(self) -> str:
        return f"<Incident {self.id} ({self.category.value}, {self.grade.value})>"
