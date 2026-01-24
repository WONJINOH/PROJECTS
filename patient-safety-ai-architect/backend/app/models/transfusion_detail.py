"""
Transfusion (수혈) Detail Model

PSR 양식 III항 기반 수혈사고 상세 기록
"""

import enum
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, Enum, Text, Boolean, ForeignKey

from app.database import Base


class BloodVerificationMethod(str, enum.Enum):
    """혈액형 확인 방법"""
    LAB_RESULT = "lab_result"        # 검사결과지
    PATIENT_STATEMENT = "patient_statement"  # 환자진술
    BOTH = "both"                    # 둘 다


class TransfusionErrorType(str, enum.Enum):
    """수혈 오류 유형"""
    PATIENT_ID_ERROR = "patient_id_error"        # 환자오류 (잘못된 환자에게 수혈)
    CROSSMATCH_ERROR = "crossmatch_error"        # X-matching 오류
    BLOOD_TYPE_ERROR = "blood_type_error"        # 혈액형 오류
    PRODUCT_ERROR = "product_error"              # 혈액제제 오류
    ADMINISTRATION_ERROR = "administration_error"  # 투여 오류 (속도, 양 등)
    STORAGE_ERROR = "storage_error"              # 보관 오류
    DOCUMENTATION_ERROR = "documentation_error"  # 기록 오류
    REACTION = "reaction"                        # 수혈 반응
    OTHER = "other"


class TransfusionReactionType(str, enum.Enum):
    """수혈 반응 유형"""
    NONE = "none"                    # 없음
    FEBRILE = "febrile"              # 발열성 반응
    ALLERGIC_MILD = "allergic_mild"  # 경증 알레르기 반응
    ALLERGIC_SEVERE = "allergic_severe"  # 중증 알레르기/아나필락시스
    HEMOLYTIC_ACUTE = "hemolytic_acute"  # 급성 용혈 반응
    HEMOLYTIC_DELAYED = "hemolytic_delayed"  # 지연성 용혈 반응
    TACO = "taco"                    # 수혈관련 순환과부하
    TRALI = "trali"                  # 수혈관련 급성폐손상
    OTHER = "other"


class TransfusionDetail(Base):
    """수혈사고 상세 기록"""

    __tablename__ = "transfusion_details"

    id = Column(Integer, primary_key=True, index=True)

    # 기본 사고 연결
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False, index=True)

    # 혈액형 확인 여부
    blood_type_verified = Column(Boolean, default=True)
    verification_method = Column(Enum(BloodVerificationMethod), nullable=True)

    # 오류 유형
    error_type = Column(Enum(TransfusionErrorType), nullable=False, index=True)
    error_type_detail = Column(Text, nullable=True)

    # 수혈 반응
    reaction_type = Column(Enum(TransfusionReactionType), nullable=True, index=True)
    reaction_detail = Column(Text, nullable=True)

    # 혈액제제 정보
    blood_product_type = Column(String(100), nullable=True)  # 전혈, 농축적혈구, FFP 등
    blood_unit_id = Column(String(50), nullable=True)  # 혈액 단위 ID

    # 수혈량 및 속도
    infusion_volume_ml = Column(Integer, nullable=True)
    infusion_rate = Column(String(50), nullable=True)  # 예: "20 gtt/min"

    # 수혈 시작/종료 시간
    start_time = Column(DateTime(timezone=True), nullable=True)
    end_time = Column(DateTime(timezone=True), nullable=True)

    # 환자 정보 (익명화)
    patient_code = Column(String(50), nullable=True, index=True)
    patient_blood_type = Column(String(10), nullable=True)  # A+, B-, O+, AB- 등

    # 수혈 전 확인 사항
    pre_transfusion_check_done = Column(Boolean, default=True)
    two_person_verification = Column(Boolean, default=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<TransfusionDetail {self.id} - {self.error_type.value}>"
