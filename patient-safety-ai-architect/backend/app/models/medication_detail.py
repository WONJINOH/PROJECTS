"""
Medication Safety (투약 안전) Models

투약 안전 지표:
- 투약오류 발생률
- 오류 발견 단계별 비율
- 고위험 약물 오류 (추후)
- 근접오류 포착률
- 바코드 스캔 이행률 (추후)
"""

import enum
from datetime import datetime, date
from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, Enum, Text, Float, Date, Boolean, ForeignKey

from app.database import Base


class MedicationErrorType(str, enum.Enum):
    """투약 오류 유형"""
    WRONG_PATIENT = "wrong_patient"          # 환자 오류
    WRONG_DRUG = "wrong_drug"                # 약물 오류
    WRONG_DOSE = "wrong_dose"                # 용량 오류
    WRONG_ROUTE = "wrong_route"              # 경로 오류
    WRONG_TIME = "wrong_time"                # 시간 오류
    WRONG_RATE = "wrong_rate"                # 속도 오류 (주사)
    OMISSION = "omission"                    # 누락
    UNAUTHORIZED = "unauthorized"            # 무허가 투약
    DETERIORATED = "deteriorated"            # 변질 약물
    MONITORING = "monitoring"                # 모니터링 오류
    OTHER = "other"                          # 기타


class MedicationErrorStage(str, enum.Enum):
    """오류 발견 단계"""
    PRESCRIBING = "prescribing"              # 처방 단계
    TRANSCRIBING = "transcribing"            # 전사 단계
    DISPENSING = "dispensing"                # 조제 단계
    ADMINISTERING = "administering"          # 투여 단계
    MONITORING = "monitoring"                # 모니터링 단계


class MedicationErrorSeverity(str, enum.Enum):
    """투약 오류 심각도 (NCC MERP)"""
    CATEGORY_A = "A"  # 오류 가능성 있는 상황
    CATEGORY_B = "B"  # 오류 발생했으나 환자에게 도달 안 함
    CATEGORY_C = "C"  # 환자에게 도달, 해 없음
    CATEGORY_D = "D"  # 환자에게 도달, 모니터링 필요
    CATEGORY_E = "E"  # 일시적 해, 중재 필요
    CATEGORY_F = "F"  # 일시적 해, 입원/연장 필요
    CATEGORY_G = "G"  # 영구적 해
    CATEGORY_H = "H"  # 생명 위협 중재 필요
    CATEGORY_I = "I"  # 사망


class HighAlertMedication(str, enum.Enum):
    """고위험 약물 분류"""
    ANTICOAGULANT = "anticoagulant"          # 항응고제
    INSULIN = "insulin"                      # 인슐린
    OPIOID = "opioid"                        # 마약성 진통제
    CHEMOTHERAPY = "chemotherapy"            # 항암제
    SEDATIVE = "sedative"                    # 진정제
    POTASSIUM = "potassium"                  # 고농도 칼륨
    NEUROMUSCULAR = "neuromuscular"          # 신경근차단제
    OTHER = "other"                          # 기타


class MedicationErrorDetail(Base):
    """투약 오류 상세 기록"""

    __tablename__ = "medication_error_details"

    id = Column(Integer, primary_key=True, index=True)

    # 기본 사고 연결
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False)

    # 환자 정보 (익명화)
    patient_code = Column(String(50), nullable=False, index=True)
    patient_age_group = Column(String(20), nullable=True)

    # 오류 정보
    error_type = Column(Enum(MedicationErrorType), nullable=False, index=True)
    error_stage = Column(Enum(MedicationErrorStage), nullable=False, index=True)
    error_severity = Column(Enum(MedicationErrorSeverity), nullable=False, index=True)

    # 근접오류 여부
    is_near_miss = Column(Boolean, default=False, index=True)

    # 약물 정보 (익명화/일반화)
    medication_category = Column(String(100), nullable=True)  # 약물 분류
    is_high_alert = Column(Boolean, default=False)
    high_alert_type = Column(Enum(HighAlertMedication), nullable=True)

    # 의도한 것 vs 실제
    intended_dose = Column(String(100), nullable=True)
    actual_dose = Column(String(100), nullable=True)
    intended_route = Column(String(50), nullable=True)
    actual_route = Column(String(50), nullable=True)

    # 발견
    discovered_by_role = Column(String(50), nullable=True)
    discovery_method = Column(String(100), nullable=True)

    # 부서
    department = Column(String(100), nullable=False, index=True)

    # 바코드 스캔 관련 (추후)
    barcode_scanned = Column(Boolean, nullable=True)

    # 원인 분석
    contributing_factors = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<MedicationError {self.id} - {self.error_type.value}>"


class MedicationMonthlyStats(Base):
    """투약 월간 통계"""

    __tablename__ = "medication_monthly_stats"

    id = Column(Integer, primary_key=True, index=True)

    # 기간
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)

    # 부서 (전체인 경우 NULL)
    department = Column(String(100), nullable=True, index=True)

    # 총 투약 건수 (분모)
    total_administrations = Column(Integer, default=0)

    # 오류 건수
    total_errors = Column(Integer, default=0)
    near_miss_count = Column(Integer, default=0)
    actual_error_count = Column(Integer, default=0)

    # 단계별 오류
    prescribing_errors = Column(Integer, default=0)
    transcribing_errors = Column(Integer, default=0)
    dispensing_errors = Column(Integer, default=0)
    administering_errors = Column(Integer, default=0)

    # 고위험 약물 오류
    high_alert_errors = Column(Integer, default=0)

    # 비율
    error_rate = Column(Float, nullable=True)  # 투약오류 발생률
    near_miss_capture_rate = Column(Float, nullable=True)  # 근접오류 포착률

    # 바코드 스캔 (추후)
    barcode_scan_rate = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<MedicationMonthlyStats {self.year}-{self.month}>"
