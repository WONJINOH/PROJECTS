"""
Security (보안) Detail Model

PSR 양식 VII항 기반 보안 관련 사고 상세 기록
"""

import enum
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, Enum, Text, Boolean, ForeignKey, JSON

from app.database import Base


class SecurityType(str, enum.Enum):
    """보안 사고 유형"""
    THEFT = "theft"                      # 도난
    SUICIDE = "suicide"                  # 자살
    SUICIDE_ATTEMPT = "suicide_attempt"  # 자살시도
    ELOPEMENT = "elopement"              # 무단이탈/탈원
    ASSAULT = "assault"                  # 폭행
    VERBAL_ABUSE = "verbal_abuse"        # 언어폭력
    SEXUAL_MISCONDUCT = "sexual_misconduct"  # 성적 비위
    ARSON = "arson"                      # 방화
    VANDALISM = "vandalism"              # 기물파손
    TRESPASSING = "trespassing"          # 무단침입
    OTHER = "other"


class SecuritySeverity(str, enum.Enum):
    """보안 사고 심각도"""
    LOW = "low"                  # 경미
    MODERATE = "moderate"        # 중등도
    HIGH = "high"                # 중증
    CRITICAL = "critical"        # 위급


class InvolvedPartyType(str, enum.Enum):
    """관련자 유형"""
    PATIENT = "patient"          # 환자
    VISITOR = "visitor"          # 보호자/방문객
    STAFF = "staff"              # 직원
    OUTSIDER = "outsider"        # 외부인
    UNKNOWN = "unknown"          # 불명


class SecurityDetail(Base):
    """보안 관련 사고 상세 기록"""

    __tablename__ = "security_details"

    id = Column(Integer, primary_key=True, index=True)

    # 기본 사고 연결
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False, index=True)

    # 보안 사고 유형
    security_type = Column(Enum(SecurityType), nullable=False, index=True)
    security_type_detail = Column(Text, nullable=True)

    # 심각도
    severity = Column(Enum(SecuritySeverity), nullable=False, index=True)

    # 관련자 정보 (JSON 배열) - 익명화된 정보만 저장
    # 예: [{"type": "patient", "code": "PT001"}, {"type": "staff", "code": "ST001"}]
    involved_parties = Column(JSON, nullable=True)
    involved_parties_count = Column(Integer, default=1)

    # 피해자 정보 (익명화)
    victim_type = Column(Enum(InvolvedPartyType), nullable=True)
    victim_code = Column(String(50), nullable=True)

    # 가해자 정보 (익명화)
    perpetrator_type = Column(Enum(InvolvedPartyType), nullable=True)
    perpetrator_code = Column(String(50), nullable=True)

    # 신고/보고
    police_notified = Column(Boolean, default=False)
    police_report_number = Column(String(50), nullable=True)
    security_notified = Column(Boolean, default=False)

    # 피해 내용
    injury_occurred = Column(Boolean, default=False)
    injury_detail = Column(Text, nullable=True)
    property_damage = Column(Boolean, default=False)
    property_damage_detail = Column(Text, nullable=True)
    stolen_items = Column(Text, nullable=True)

    # 대응 조치
    immediate_response = Column(Text, nullable=True)
    restraint_applied = Column(Boolean, default=False)
    isolation_applied = Column(Boolean, default=False)

    # 무단이탈/자살 관련 추가 정보
    duration_minutes = Column(Integer, nullable=True)  # 이탈 시간 (분)
    found_location = Column(String(200), nullable=True)  # 발견 장소
    method_used = Column(String(200), nullable=True)  # 자해/자살 방법

    # 위험도 평가
    risk_assessment_done = Column(Boolean, default=False)
    suicide_risk_level = Column(String(20), nullable=True)  # low, moderate, high

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<SecurityDetail {self.id} - {self.security_type.value}>"
