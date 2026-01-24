"""
Thermal Injury (열냉사고) Detail Model

PSR 양식 IV항 기반 열냉사고 상세 기록
"""

import enum
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, Enum, Text, ForeignKey

from app.database import Base


class ThermalInjurySource(str, enum.Enum):
    """열냉사고 원인 물질"""
    ICE_BAG = "ice_bag"                  # 아이스백
    HOT_BAG = "hot_bag"                  # 핫백/온열팩
    HOT_WATER = "hot_water"              # 온수
    COLD_WATER = "cold_water"            # 냉수
    HEATING_PAD = "heating_pad"          # 전기장판/온열패드
    HOT_BEVERAGE = "hot_beverage"        # 뜨거운 음료
    HOT_FOOD = "hot_food"                # 뜨거운 음식
    STEAM = "steam"                      # 증기
    LAMP = "lamp"                        # 조명/적외선 램프
    OTHER = "other"


class ThermalInjurySeverity(str, enum.Enum):
    """열냉 손상 정도"""
    NONE = "none"                # 손상 없음 (근접오류)
    GRADE_1 = "grade_1"          # 1도 화상 (표피)
    GRADE_2 = "grade_2"          # 2도 화상 (진피)
    GRADE_3 = "grade_3"          # 3도 화상 (전층)
    FROSTBITE_1 = "frostbite_1"  # 1도 동상
    FROSTBITE_2 = "frostbite_2"  # 2도 동상
    FROSTBITE_3 = "frostbite_3"  # 3도 동상


class ThermalInjuryBodyPart(str, enum.Enum):
    """손상 부위"""
    HEAD = "head"                # 머리
    FACE = "face"                # 얼굴
    NECK = "neck"                # 목
    CHEST = "chest"              # 가슴
    BACK = "back"                # 등
    ABDOMEN = "abdomen"          # 복부
    UPPER_ARM = "upper_arm"      # 상완
    FOREARM = "forearm"          # 전완
    HAND = "hand"                # 손
    THIGH = "thigh"              # 대퇴
    LOWER_LEG = "lower_leg"      # 하퇴
    FOOT = "foot"                # 발
    OTHER = "other"


class ThermalInjuryDetail(Base):
    """열냉사고 상세 기록"""

    __tablename__ = "thermal_injury_details"

    id = Column(Integer, primary_key=True, index=True)

    # 기본 사고 연결
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False, index=True)

    # 사고 원인 물질
    injury_source = Column(Enum(ThermalInjurySource), nullable=False, index=True)
    injury_source_detail = Column(String(200), nullable=True)

    # 손상 정도
    injury_severity = Column(Enum(ThermalInjurySeverity), nullable=False, index=True)

    # 손상 부위
    body_part = Column(Enum(ThermalInjuryBodyPart), nullable=False)
    body_part_detail = Column(String(200), nullable=True)

    # 손상 범위 (예: "5x3cm")
    injury_size = Column(String(50), nullable=True)

    # 적용 시간 (분)
    application_duration_min = Column(Integer, nullable=True)

    # 온도 정보 (가능한 경우)
    temperature_celsius = Column(String(20), nullable=True)

    # 환자 정보 (익명화)
    patient_code = Column(String(50), nullable=True, index=True)

    # 감각 상태 (열냉 인지 가능 여부)
    patient_sensory_intact = Column(String(50), nullable=True)  # "intact", "impaired", "absent"

    # 치료 내용
    treatment_provided = Column(Text, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<ThermalInjuryDetail {self.id} - {self.injury_source.value}>"
