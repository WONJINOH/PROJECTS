"""
Fall (낙상) Management Models

낙상 관리 지표:
- 낙상 발생률 (1000재원일당)
- 신체적 손상정도
"""

import enum
from datetime import datetime, date
from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, Enum, Text, Float, Date, Boolean, ForeignKey

from app.database import Base


class FallInjuryLevel(str, enum.Enum):
    """낙상 손상 정도"""
    NONE = "none"            # 손상 없음
    MINOR = "minor"          # 경미 (찰과상, 타박상)
    MODERATE = "moderate"    # 중등도 (봉합 필요, 골절 제외)
    MAJOR = "major"          # 중증 (골절, 의식 변화)
    DEATH = "death"          # 사망


class FallRiskLevel(str, enum.Enum):
    """낙상 위험도"""
    LOW = "low"              # 저위험
    MODERATE = "moderate"    # 중위험
    HIGH = "high"            # 고위험


class FallLocation(str, enum.Enum):
    """낙상 발생 장소"""
    BED = "bed"                  # 침대
    BATHROOM = "bathroom"        # 화장실
    HALLWAY = "hallway"          # 복도
    WHEELCHAIR = "wheelchair"    # 휠체어
    CHAIR = "chair"              # 의자
    REHABILITATION = "rehabilitation"  # 재활치료실
    OTHER = "other"              # 기타


class FallCause(str, enum.Enum):
    """낙상 원인"""
    SLIP = "slip"                # 미끄러짐
    TRIP = "trip"                # 걸려 넘어짐
    LOSS_OF_BALANCE = "loss_of_balance"  # 균형 상실
    FAINTING = "fainting"        # 실신/어지러움
    WEAKNESS = "weakness"        # 근력 약화
    COGNITIVE = "cognitive"      # 인지 장애
    MEDICATION = "medication"    # 약물 관련
    ENVIRONMENT = "environment"  # 환경 요인
    OTHER = "other"              # 기타


class FallDetail(Base):
    """낙상 상세 기록"""

    __tablename__ = "fall_details"

    id = Column(Integer, primary_key=True, index=True)

    # 기본 사고 연결
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False)

    # 환자 정보 (익명화)
    patient_code = Column(String(50), nullable=False, index=True)
    patient_age_group = Column(String(20), nullable=True)
    patient_gender = Column(String(10), nullable=True)

    # 낙상 위험도 (사고 전 평가)
    pre_fall_risk_level = Column(Enum(FallRiskLevel), nullable=True)
    morse_score = Column(Integer, nullable=True)  # Morse Fall Scale 점수

    # 발생 상황
    fall_location = Column(Enum(FallLocation), nullable=False)
    fall_location_detail = Column(String(200), nullable=True)
    fall_cause = Column(Enum(FallCause), nullable=False)
    fall_cause_detail = Column(Text, nullable=True)

    # 발생 시간대
    occurred_hour = Column(Integer, nullable=True)  # 0-23
    shift = Column(String(20), nullable=True)  # day, evening, night

    # 손상 정도
    injury_level = Column(Enum(FallInjuryLevel), nullable=False, index=True)
    injury_description = Column(Text, nullable=True)

    # 낙상 시 활동
    activity_at_fall = Column(String(200), nullable=True)  # 이동 중, 배변 중 등

    # 보호자/직원 유무
    was_supervised = Column(Boolean, default=False)
    had_fall_prevention = Column(Boolean, default=False)  # 낙상예방조치 시행 여부

    # 부서
    department = Column(String(100), nullable=False, index=True)

    # 재발
    is_recurrence = Column(Boolean, default=False)
    previous_fall_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<FallDetail {self.id} - {self.injury_level.value}>"


class FallMonthlyStats(Base):
    """낙상 월간 통계"""

    __tablename__ = "fall_monthly_stats"

    id = Column(Integer, primary_key=True, index=True)

    # 기간
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)

    # 부서 (전체인 경우 NULL)
    department = Column(String(100), nullable=True, index=True)

    # 재원일수
    total_patient_days = Column(Integer, default=0)

    # 낙상 건수
    total_falls = Column(Integer, default=0)

    # 손상 정도별
    falls_no_injury = Column(Integer, default=0)
    falls_minor_injury = Column(Integer, default=0)
    falls_moderate_injury = Column(Integer, default=0)
    falls_major_injury = Column(Integer, default=0)
    falls_death = Column(Integer, default=0)

    # 발생률 (1000재원일당)
    fall_rate = Column(Float, nullable=True)
    fall_with_injury_rate = Column(Float, nullable=True)  # 손상 동반 낙상률

    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<FallMonthlyStats {self.year}-{self.month}>"
