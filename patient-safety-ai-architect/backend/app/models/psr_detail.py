"""
PSR (Patient Safety Report) Detail Models

환자안전사건보고 상세 데이터:
- 사고분류별
- 오류유형별 (근접오류, 무해, 위해, 적신호)
- 부서별 발생
- 사건 유형
- 사고원인
- 재발 패턴
- 사건장소 × 사건시간 (히트맵용)
"""

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, Enum, Text, ForeignKey, Time
from sqlalchemy.orm import relationship

from app.database import Base


class ErrorSeverity(str, enum.Enum):
    """오류 유형/심각도"""
    NEAR_MISS = "near_miss"      # 근접오류 - 환자에게 도달하지 않음
    NO_HARM = "no_harm"          # 무해 - 환자에게 도달했으나 해 없음
    HARM = "harm"                # 위해 - 환자에게 해가 발생
    SENTINEL = "sentinel"        # 적신호 - 심각한 위해/사망


class IncidentType(str, enum.Enum):
    """사건 유형"""
    FALL = "fall"                        # 낙상
    MEDICATION = "medication"            # 투약오류
    PRESSURE_ULCER = "pressure_ulcer"    # 욕창
    INFECTION = "infection"              # 감염
    PROCEDURE = "procedure"              # 시술/처치
    EQUIPMENT = "equipment"              # 의료기기
    TRANSFUSION = "transfusion"          # 수혈
    SURGERY = "surgery"                  # 수술
    NUTRITION = "nutrition"              # 영양
    IDENTIFICATION = "identification"    # 환자확인
    COMMUNICATION = "communication"      # 의사소통
    OTHER = "other"                      # 기타


class IncidentLocation(str, enum.Enum):
    """사건 장소"""
    PATIENT_ROOM = "patient_room"        # 병실
    BATHROOM = "bathroom"                # 화장실
    HALLWAY = "hallway"                  # 복도
    NURSING_STATION = "nursing_station"  # 간호사실
    TREATMENT_ROOM = "treatment_room"    # 처치실
    REHABILITATION = "rehabilitation"    # 재활치료실
    RADIOLOGY = "radiology"              # 영상의학과
    LABORATORY = "laboratory"            # 검사실
    PHARMACY = "pharmacy"                # 약국
    DINING = "dining"                    # 식당/급식
    OUTDOOR = "outdoor"                  # 야외
    OTHER = "other"                      # 기타


class CauseCategory(str, enum.Enum):
    """사고 원인 카테고리"""
    HUMAN = "human"                      # 인적 요인
    SYSTEM = "system"                    # 시스템 요인
    ENVIRONMENT = "environment"          # 환경 요인
    EQUIPMENT = "equipment"              # 장비 요인
    COMMUNICATION = "communication"      # 의사소통
    POLICY = "policy"                    # 정책/절차
    PATIENT = "patient"                  # 환자 요인
    OTHER = "other"                      # 기타


class PSRDetail(Base):
    """환자안전사건보고 상세"""

    __tablename__ = "psr_details"

    id = Column(Integer, primary_key=True, index=True)

    # 기본 사고 연결
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False)

    # 오류 유형/심각도
    error_severity = Column(Enum(ErrorSeverity), nullable=False, index=True)

    # 사건 유형
    incident_type = Column(Enum(IncidentType), nullable=False, index=True)
    incident_subtype = Column(String(100), nullable=True)  # 세부 유형

    # 발생 장소 및 시간
    location = Column(Enum(IncidentLocation), nullable=False, index=True)
    location_detail = Column(String(200), nullable=True)  # 상세 장소 (301호 등)
    occurred_hour = Column(Integer, nullable=True)  # 발생 시간 (0-23)

    # 부서
    department = Column(String(100), nullable=False, index=True)
    unit = Column(String(100), nullable=True)  # 세부 단위 (병동 등)

    # 사고 원인
    cause_category = Column(Enum(CauseCategory), nullable=False)
    cause_detail = Column(Text, nullable=True)
    contributing_factors = Column(Text, nullable=True)  # 기여 요인

    # 환자 정보 (익명화)
    patient_age_group = Column(String(20), nullable=True)  # 10대, 20대, ... 80대 이상
    patient_gender = Column(String(10), nullable=True)
    patient_diagnosis_category = Column(String(100), nullable=True)  # 진단 카테고리

    # 재발 분석
    is_recurrence = Column(Integer, default=0)  # 재발 여부 (0: 최초, 1+: 재발 횟수)
    previous_incident_id = Column(Integer, nullable=True)  # 이전 관련 사고

    # 발견/보고
    discovered_by_role = Column(String(50), nullable=True)  # 발견자 역할
    discovery_method = Column(String(100), nullable=True)  # 발견 방법

    # 메타데이터
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<PSRDetail {self.id} - {self.incident_type.value}>"


class HeatmapData(Base):
    """히트맵 데이터 (장소 × 시간)"""

    __tablename__ = "psr_heatmap_data"

    id = Column(Integer, primary_key=True, index=True)

    # 기간
    period_start = Column(DateTime, nullable=False, index=True)
    period_end = Column(DateTime, nullable=False)

    # 장소 × 시간
    location = Column(Enum(IncidentLocation), nullable=False)
    hour = Column(Integer, nullable=False)  # 0-23

    # 집계
    incident_count = Column(Integer, default=0)
    near_miss_count = Column(Integer, default=0)
    harm_count = Column(Integer, default=0)

    # 부서별 (선택)
    department = Column(String(100), nullable=True, index=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<HeatmapData {self.location.value}@{self.hour}h: {self.incident_count}>"
