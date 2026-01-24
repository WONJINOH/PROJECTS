"""
Environment (환경) Detail Model

PSR 양식 VI항 기반 환경 관련 사고 상세 기록
"""

import enum
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, Enum, Text, Boolean, ForeignKey, JSON

from app.database import Base


class EnvironmentType(str, enum.Enum):
    """환경 사고 유형"""
    FIRE = "fire"                        # 화재
    FACILITY = "facility"                # 시설 (건물, 바닥, 벽 등)
    WASTE = "waste"                      # 폐기물 관련
    MEDICAL_EQUIPMENT = "medical_equipment"  # 의료장비
    WATER = "water"                      # 상하수도
    ELECTRICAL = "electrical"            # 전기
    GAS = "gas"                          # 가스
    HVAC = "hvac"                        # 냉난방/환기
    OTHER = "other"


class EnvironmentSeverity(str, enum.Enum):
    """환경 사고 심각도"""
    MINOR = "minor"                      # 경미 (즉시 해결 가능)
    MODERATE = "moderate"                # 중등도 (업무에 영향)
    MAJOR = "major"                      # 중증 (환자/직원 위험)
    CRITICAL = "critical"                # 위급 (대피 필요)


class EnvironmentDetail(Base):
    """환경 관련 사고 상세 기록"""

    __tablename__ = "environment_details"

    id = Column(Integer, primary_key=True, index=True)

    # 기본 사고 연결
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False, index=True)

    # 환경 사고 유형
    environment_type = Column(Enum(EnvironmentType), nullable=False, index=True)
    environment_type_detail = Column(Text, nullable=True)

    # 심각도
    severity = Column(Enum(EnvironmentSeverity), nullable=False, index=True)

    # 구체적 장소
    location_specific = Column(String(200), nullable=True)
    location_floor = Column(String(50), nullable=True)  # 층
    location_room = Column(String(50), nullable=True)   # 호실

    # 관련 장비/시설
    equipment_involved = Column(String(200), nullable=True)
    equipment_id = Column(String(50), nullable=True)  # 장비 ID

    # 피해 범위
    damage_extent = Column(Text, nullable=True)

    # 인명 피해
    injury_occurred = Column(Boolean, default=False)
    injury_count = Column(Integer, default=0)
    injury_detail = Column(Text, nullable=True)

    # 재산 피해
    property_damage = Column(Boolean, default=False)
    property_damage_detail = Column(Text, nullable=True)
    estimated_cost = Column(String(50), nullable=True)

    # 대응 조치
    immediate_response = Column(Text, nullable=True)
    evacuation_required = Column(Boolean, default=False)
    external_help_called = Column(Boolean, default=False)  # 소방서, 전기안전공사 등

    # 원인
    cause_identified = Column(Boolean, default=False)
    cause_detail = Column(Text, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<EnvironmentDetail {self.id} - {self.environment_type.value}>"
