"""
Staff Safety & Lab TAT Models

직원 안전:
- 직원 감염 노출

검사 TAT (Turn Around Time):
- 영상검사 TAT
- 임상병리검사 TAT
"""

import enum
from datetime import datetime, date
from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, Enum, Text, Float, Date, Boolean, ForeignKey

from app.database import Base


class ExposureType(str, enum.Enum):
    """감염 노출 유형"""
    NEEDLESTICK = "needlestick"              # 주사침 자상
    SHARP_INJURY = "sharp_injury"            # 날카로운 기구 손상
    SPLASH = "splash"                        # 점막/피부 노출
    RESPIRATORY = "respiratory"              # 호흡기 노출
    OTHER = "other"                          # 기타


class ExposureSource(str, enum.Enum):
    """노출원"""
    BLOOD = "blood"                  # 혈액
    BODY_FLUID = "body_fluid"        # 체액
    RESPIRATORY = "respiratory"      # 호흡기 분비물
    UNKNOWN = "unknown"              # 불명


class LabTestType(str, enum.Enum):
    """검사 종류"""
    # 영상검사
    XRAY = "xray"                    # X-ray
    CT = "ct"                        # CT
    MRI = "mri"                      # MRI
    ULTRASOUND = "ultrasound"        # 초음파

    # 임상병리검사
    CBC = "cbc"                      # 일반혈액검사
    CHEMISTRY = "chemistry"          # 생화학검사
    URINALYSIS = "urinalysis"        # 뇨검사
    COAGULATION = "coagulation"      # 응고검사
    BLOOD_GAS = "blood_gas"          # 혈액가스검사
    CULTURE = "culture"              # 배양검사


class StaffExposureRecord(Base):
    """직원 감염 노출 기록"""

    __tablename__ = "staff_exposure_records"

    id = Column(Integer, primary_key=True, index=True)

    # 노출 직원 (익명화)
    staff_code = Column(String(50), nullable=False, index=True)
    staff_role = Column(String(50), nullable=True)  # 의사, 간호사, 청소원 등
    department = Column(String(100), nullable=False, index=True)

    # 노출 정보
    exposure_datetime = Column(DateTime, nullable=False, index=True)
    exposure_type = Column(Enum(ExposureType), nullable=False, index=True)
    exposure_source = Column(Enum(ExposureSource), nullable=False)
    exposure_detail = Column(Text, nullable=True)

    # 발생 상황
    activity_at_exposure = Column(String(200), nullable=True)  # 주사, 채혈 등
    device_involved = Column(String(100), nullable=True)  # 관련 기구

    # 환자 정보 (해당 시)
    source_patient_code = Column(String(50), nullable=True)
    source_patient_hiv = Column(Boolean, nullable=True)
    source_patient_hbv = Column(Boolean, nullable=True)
    source_patient_hcv = Column(Boolean, nullable=True)

    # 사후 조치
    immediate_action = Column(Text, nullable=True)
    pep_given = Column(Boolean, nullable=True)  # 예방적 처치 여부
    follow_up_scheduled = Column(Boolean, default=False)

    # 연결된 사고 보고
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<StaffExposure {self.id} - {self.exposure_type.value}>"


class LabTATRecord(Base):
    """검사 TAT 기록"""

    __tablename__ = "lab_tat_records"

    id = Column(Integer, primary_key=True, index=True)

    # 검사 정보
    test_type = Column(Enum(LabTestType), nullable=False, index=True)
    test_category = Column(String(50), nullable=False)  # imaging, laboratory

    # 시간 기록
    order_datetime = Column(DateTime, nullable=False)  # 처방 시간
    collection_datetime = Column(DateTime, nullable=True)  # 검체 채취/검사 시작
    result_datetime = Column(DateTime, nullable=False)  # 결과 보고 시간

    # TAT 계산 (분)
    tat_minutes = Column(Integer, nullable=False)  # Order to Result
    collection_tat_minutes = Column(Integer, nullable=True)  # Order to Collection
    analysis_tat_minutes = Column(Integer, nullable=True)  # Collection to Result

    # 목표 달성
    target_tat_minutes = Column(Integer, nullable=True)
    met_target = Column(Boolean, nullable=True)

    # 부서
    ordering_department = Column(String(100), nullable=True, index=True)

    # 긴급 여부
    is_stat = Column(Boolean, default=False)

    # 기간 (집계용)
    test_date = Column(Date, nullable=False, index=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<LabTAT {self.test_type.value} - {self.tat_minutes}min>"


class StaffSafetyMonthlyStats(Base):
    """직원 안전 월간 통계"""

    __tablename__ = "staff_safety_monthly_stats"

    id = Column(Integer, primary_key=True, index=True)

    # 기간
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)

    # 부서 (전체인 경우 NULL)
    department = Column(String(100), nullable=True, index=True)

    # 노출 건수
    total_exposures = Column(Integer, default=0)
    needlestick_count = Column(Integer, default=0)
    sharp_injury_count = Column(Integer, default=0)
    splash_count = Column(Integer, default=0)
    respiratory_count = Column(Integer, default=0)

    # 예방적 처치
    pep_given_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<StaffSafetyStats {self.year}-{self.month}>"


class LabTATMonthlyStats(Base):
    """검사 TAT 월간 통계"""

    __tablename__ = "lab_tat_monthly_stats"

    id = Column(Integer, primary_key=True, index=True)

    # 기간
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)

    # 검사 종류
    test_type = Column(Enum(LabTestType), nullable=False)
    test_category = Column(String(50), nullable=False)

    # 건수
    total_tests = Column(Integer, default=0)
    stat_tests = Column(Integer, default=0)

    # TAT 통계 (분)
    avg_tat = Column(Float, nullable=True)
    median_tat = Column(Float, nullable=True)
    percentile_90_tat = Column(Float, nullable=True)

    # 목표 달성률
    target_tat = Column(Integer, nullable=True)
    target_achievement_rate = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<LabTATStats {self.year}-{self.month} - {self.test_type.value}>"
