"""
Fall (낙상) Management Models

낙상 관리 지표:
- 낙상 발생률 (1000재원일당)
- 신체적 손상정도

PSR 양식 기반 필드 (대시보드용)
"""

import enum
from datetime import datetime, date, timezone
from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, Enum, Text, Float, Date, Boolean, ForeignKey, JSON

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


# PSR 양식 기반 추가 Enum들
class FallConsciousnessLevel(str, enum.Enum):
    """의식상태 (PSR I항)"""
    ALERT = "alert"              # 명료
    DROWSY = "drowsy"            # 기면
    STUPOR = "stupor"            # 혼미
    SEMICOMA = "semicoma"        # 반혼수
    COMA = "coma"                # 혼수


class FallActivityLevel(str, enum.Enum):
    """활동/기능 수준 (PSR I항)"""
    INDEPENDENT = "independent"          # 독립적
    NEEDS_ASSISTANCE = "needs_assistance"  # 부분 도움 필요
    DEPENDENT = "dependent"              # 전적 도움 필요


class FallMobilityAid(str, enum.Enum):
    """보행보조기구 종류 (PSR I항)"""
    NONE = "none"                # 없음
    WHEELCHAIR = "wheelchair"    # 휠체어
    WALKER = "walker"            # 워커
    CANE = "cane"                # 지팡이
    CRUTCH = "crutch"            # 목발
    OTHER = "other"              # 기타


class FallType(str, enum.Enum):
    """낙상 유형 (PSR I항)"""
    BED_FALL = "bed_fall"              # 침대에서 낙상
    STANDING_FALL = "standing_fall"    # 서있다가 낙상
    SITTING_FALL = "sitting_fall"      # 앉아있다가 낙상
    WALKING_FALL = "walking_fall"      # 보행 중 낙상
    TRANSFER_FALL = "transfer_fall"    # 이동 중 낙상
    OTHER = "other"                    # 기타


class FallPhysicalInjury(str, enum.Enum):
    """신체적 손상 유형 (PSR I항)"""
    NONE = "none"                # 없음
    ABRASION = "abrasion"        # 찰과상
    CONTUSION = "contusion"      # 타박상
    LACERATION = "laceration"    # 열상
    HEMATOMA = "hematoma"        # 혈종
    FRACTURE = "fracture"        # 골절
    HEAD_INJURY = "head_injury"  # 두부손상
    OTHER = "other"              # 기타


class FallTreatment(str, enum.Enum):
    """치료 내용 (PSR I항)"""
    OBSERVATION = "observation"      # 관찰
    DRESSING = "dressing"            # 드레싱
    SUTURE = "suture"                # 봉합
    CAST_SPLINT = "cast_splint"      # 부목/석고
    IMAGING = "imaging"              # 영상검사
    SURGERY = "surgery"              # 수술
    TRANSFER = "transfer"            # 전원
    OTHER = "other"                  # 기타


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

    # ===== PSR 양식 기반 필드 (대시보드용) =====

    # 의식상태 (PSR I항)
    consciousness_level = Column(Enum(FallConsciousnessLevel), nullable=True, index=True)

    # 활동/기능 수준 (PSR I항)
    activity_level = Column(Enum(FallActivityLevel), nullable=True, index=True)

    # 보행보조기구 (PSR I항)
    uses_mobility_aid = Column(Boolean, default=False)
    mobility_aid_type = Column(Enum(FallMobilityAid), nullable=True)

    # 환자 위험요인 (PSR I항) - JSON 배열로 저장
    # 예: ["medication", "cognitive_impairment", "visual_impairment", "history_of_fall"]
    risk_factors = Column(JSON, nullable=True)

    # 관련 투약 (PSR I항) - JSON 배열로 저장
    # 예: ["sedative", "diuretic", "antihypertensive", "hypoglycemic"]
    related_medications = Column(JSON, nullable=True)

    # 낙상 유형 (PSR I항)
    fall_type = Column(Enum(FallType), nullable=True, index=True)

    # ===== 기존 필드 =====

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

    # 신체적 손상 유형 (PSR I항) - 기존 injury_level 보완
    physical_injury_type = Column(Enum(FallPhysicalInjury), nullable=True, index=True)
    physical_injury_detail = Column(String(200), nullable=True)

    # 치료 내용 (PSR I항) - JSON 배열로 저장 (복수 선택 가능)
    # 예: ["observation", "dressing", "imaging"]
    treatments_provided = Column(JSON, nullable=True)
    treatment_detail = Column(Text, nullable=True)

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

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

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

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<FallMonthlyStats {self.year}-{self.month}>"
