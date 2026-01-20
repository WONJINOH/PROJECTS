"""
Incident Model

Patient safety incident with required fields per CLAUDE.md:
- immediate_action: REQUIRED for all incidents
- reported_at: REQUIRED (datetime)
- reporter_name: Required except for NEAR_MISS grade
"""

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, Enum, Text, ForeignKey, Boolean, JSON
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


class IncidentCategory(str, enum.Enum):
    """Incident categories."""

    FALL = "fall"                          # 낙상
    MEDICATION = "medication"              # 투약
    PRESSURE_ULCER = "pressure_ulcer"      # 욕창
    INFECTION = "infection"                # 감염
    MEDICAL_DEVICE = "medical_device"      # 의료기기
    SURGERY = "surgery"                    # 수술
    TRANSFUSION = "transfusion"            # 수혈
    OTHER = "other"                        # 기타


class IncidentGrade(str, enum.Enum):
    """Incident severity grades."""

    NEAR_MISS = "near_miss"    # 근접오류 (reporter_name optional)
    NO_HARM = "no_harm"        # 위해없음
    MILD = "mild"              # 일시적 손상 - 경증
    MODERATE = "moderate"      # 일시적 손상 - 중등도
    SEVERE = "severe"          # 영구적 손상
    DEATH = "death"            # 사망


class Incident(Base):
    """Patient safety incident model."""

    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)

    # === Common Page Required Fields ===
    category = Column(Enum(IncidentCategory), nullable=False, index=True)
    grade = Column(Enum(IncidentGrade), nullable=False, index=True)
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
    outcome_impact = Column(Enum(IncidentOutcomeImpact), nullable=True, index=True)
    outcome_impact_detail = Column(Text, nullable=True)

    # 기여요인 (복수 선택) - JSON 배열로 저장
    # 예: ["human_communication", "system_workload", "facility_environment"]
    contributing_factors = Column(JSON, nullable=True)
    contributing_factors_detail = Column(Text, nullable=True)

    # 환자 신체적 손상 결과
    patient_physical_outcome = Column(Enum(PatientPhysicalOutcome), nullable=True, index=True)
    patient_physical_outcome_detail = Column(Text, nullable=True)

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
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    reporter = relationship("User", back_populates="incidents")
    attachments = relationship("Attachment", back_populates="incident")
    approvals = relationship("Approval", back_populates="incident")
    actions = relationship("Action", back_populates="incident")

    def __repr__(self) -> str:
        return f"<Incident {self.id} ({self.category.value}, {self.grade.value})>"
