"""
Infection Control (감염 관리) Models

감염 관리 지표:
- 비카테터성 요로감염
- 카테터 관련 요로감염 (CAUTI)
- 손씻기 수행률
- 항생제 사용 적정성 (추후)
"""

import enum
from datetime import datetime, date, timezone
from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, Enum, Text, Float, Date, Boolean, ForeignKey

from app.database import Base


class InfectionType(str, enum.Enum):
    """감염 유형"""
    UTI_NON_CATHETER = "uti_non_catheter"    # 비카테터성 요로감염
    CAUTI = "cauti"                          # 카테터 관련 요로감염
    PNEUMONIA = "pneumonia"                  # 폐렴
    VAP = "vap"                              # 인공호흡기 관련 폐렴
    CLABSI = "clabsi"                        # 중심정맥관 관련 혈류감염
    SSI = "ssi"                              # 수술부위 감염
    CDIFF = "cdiff"                          # 클로스트리디움 디피실 감염
    MRSA = "mrsa"                            # MRSA
    OTHER = "other"                          # 기타


class HandHygieneOpportunity(str, enum.Enum):
    """손위생 기회 (WHO 5 moments)"""
    BEFORE_PATIENT = "before_patient"        # 환자 접촉 전
    BEFORE_ASEPTIC = "before_aseptic"        # 청결/무균 처치 전
    AFTER_EXPOSURE = "after_exposure"        # 체액 노출 위험 후
    AFTER_PATIENT = "after_patient"          # 환자 접촉 후
    AFTER_ENVIRONMENT = "after_environment"  # 환자 주변 환경 접촉 후


class InfectionRecord(Base):
    """감염 발생 기록"""

    __tablename__ = "infection_records"

    id = Column(Integer, primary_key=True, index=True)

    # 환자 정보 (익명화)
    patient_code = Column(String(50), nullable=False, index=True)
    patient_age_group = Column(String(20), nullable=True)
    admission_date = Column(Date, nullable=True)

    # 감염 정보
    infection_type = Column(Enum(InfectionType), nullable=False, index=True)
    onset_date = Column(Date, nullable=False, index=True)
    diagnosis_date = Column(Date, nullable=True)

    # 의료기기 관련
    device_related = Column(Boolean, default=False)
    device_type = Column(String(100), nullable=True)  # 유치도뇨관, 중심정맥관 등
    device_days = Column(Integer, nullable=True)  # 기구 유치 일수

    # 원인균
    pathogen = Column(String(200), nullable=True)
    is_mdro = Column(Boolean, default=False)  # 다제내성균 여부

    # 부서
    department = Column(String(100), nullable=False, index=True)

    # 입원 시 보유 vs 재원 중 발생
    is_hospital_acquired = Column(Boolean, default=True)

    # 연결된 사고 보고
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<InfectionRecord {self.id} - {self.infection_type.value}>"


class HandHygieneObservation(Base):
    """손위생 관찰 기록"""

    __tablename__ = "hand_hygiene_observations"

    id = Column(Integer, primary_key=True, index=True)

    # 관찰 정보
    observation_date = Column(Date, nullable=False, index=True)
    observation_time = Column(DateTime, nullable=True)

    # 관찰 대상
    department = Column(String(100), nullable=False, index=True)
    staff_role = Column(String(50), nullable=True)  # 의사, 간호사, 간병인 등

    # 손위생 기회 (WHO 5 moments)
    opportunity_type = Column(Enum(HandHygieneOpportunity), nullable=False)

    # 수행 여부
    performed = Column(Boolean, nullable=False)
    method = Column(String(50), nullable=True)  # 물+비누, 손소독제

    # 관찰자
    observer_id = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<HandHygieneObs {self.observation_date} - {'Y' if self.performed else 'N'}>"


class InfectionMonthlyStats(Base):
    """감염 월간 통계"""

    __tablename__ = "infection_monthly_stats"

    id = Column(Integer, primary_key=True, index=True)

    # 기간
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)

    # 부서 (전체인 경우 NULL)
    department = Column(String(100), nullable=True, index=True)

    # 재원일수/기구일수
    total_patient_days = Column(Integer, default=0)
    catheter_days = Column(Integer, default=0)  # 도뇨관 일수
    ventilator_days = Column(Integer, default=0)  # 인공호흡기 일수
    central_line_days = Column(Integer, default=0)  # 중심정맥관 일수

    # 감염 건수
    uti_non_catheter = Column(Integer, default=0)
    cauti = Column(Integer, default=0)
    pneumonia = Column(Integer, default=0)
    vap = Column(Integer, default=0)
    clabsi = Column(Integer, default=0)

    # 감염률
    uti_rate = Column(Float, nullable=True)  # 1000재원일당
    cauti_rate = Column(Float, nullable=True)  # 1000도뇨관일당
    vap_rate = Column(Float, nullable=True)  # 1000인공호흡기일당
    clabsi_rate = Column(Float, nullable=True)  # 1000중심정맥관일당

    # 손위생
    hand_hygiene_opportunities = Column(Integer, default=0)
    hand_hygiene_performed = Column(Integer, default=0)
    hand_hygiene_rate = Column(Float, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<InfectionMonthlyStats {self.year}-{self.month}>"
