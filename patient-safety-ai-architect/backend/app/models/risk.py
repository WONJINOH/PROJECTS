"""
Risk Management Models

위험관리 모듈:
- Risk: 위험 등록부 (Risk Register)
- RiskAssessment: 위험 평가 이력 (초기/재평가/사후)

PSR → Risk 자동 승격 지원
P×S 기반 위험도 자동 계산
"""

import enum
from datetime import datetime, date, timezone
from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, Date, Enum, Text, Boolean, ForeignKey, JSON, event
from sqlalchemy.orm import relationship

from app.database import Base


class RiskSourceType(str, enum.Enum):
    """위험 식별 출처"""
    PSR = "psr"                      # 환자안전사건보고
    ROUNDING = "rounding"            # 안전 라운딩
    AUDIT = "audit"                  # 내부 감사
    COMPLAINT = "complaint"          # 민원/불만
    INDICATOR = "indicator"          # 지표 이상
    EXTERNAL = "external"            # 외부 정보 (타병원 사례 등)
    PROACTIVE = "proactive"          # 선제적 식별 (FMEA 등)
    OTHER = "other"


class RiskCategory(str, enum.Enum):
    """위험 분류 (Incident Category와 연계)"""
    FALL = "fall"                          # 낙상
    MEDICATION = "medication"              # 투약
    PRESSURE_ULCER = "pressure_ulcer"      # 욕창
    INFECTION = "infection"                # 감염
    TRANSFUSION = "transfusion"            # 수혈
    PROCEDURE = "procedure"                # 검사/시술
    RESTRAINT = "restraint"                # 신체보호대
    ENVIRONMENT = "environment"            # 환경/시설
    SECURITY = "security"                  # 보안
    COMMUNICATION = "communication"        # 의사소통
    HANDOFF = "handoff"                    # 인수인계
    IDENTIFICATION = "identification"      # 환자확인
    OTHER = "other"


class RiskLevel(str, enum.Enum):
    """위험 수준 (P×S 기반 자동 산출)"""
    LOW = "low"              # 1-4: 저위험 (녹색)
    MEDIUM = "medium"        # 5-9: 중위험 (황색)
    HIGH = "high"            # 10-16: 고위험 (주황)
    CRITICAL = "critical"    # 17-25: 극심 (적색)


class RiskStatus(str, enum.Enum):
    """위험 상태"""
    IDENTIFIED = "identified"      # 식별됨
    ASSESSING = "assessing"        # 평가 중
    TREATING = "treating"          # 조치 진행 중
    MONITORING = "monitoring"      # 모니터링 중
    CLOSED = "closed"              # 종결
    ACCEPTED = "accepted"          # 수용 (잔여위험 허용)


class RiskAssessmentType(str, enum.Enum):
    """위험 평가 유형"""
    INITIAL = "initial"            # 초기 평가
    PERIODIC = "periodic"          # 정기 재평가
    POST_TREATMENT = "post_treatment"  # 조치 후 재평가
    POST_INCIDENT = "post_incident"    # 사건 발생 후 재평가


def calculate_risk_level(probability: int, severity: int) -> RiskLevel:
    """P×S 점수로 위험 수준 자동 산출"""
    score = probability * severity
    if score <= 4:
        return RiskLevel.LOW
    elif score <= 9:
        return RiskLevel.MEDIUM
    elif score <= 16:
        return RiskLevel.HIGH
    else:
        return RiskLevel.CRITICAL


class Risk(Base):
    """위험 등록부 (Risk Register)"""

    __tablename__ = "risks"

    id = Column(Integer, primary_key=True, index=True)

    # 위험 식별
    risk_code = Column(String(20), unique=True, index=True, nullable=False)  # R-2026-001
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)

    # 출처 정보
    source_type = Column(Enum(RiskSourceType), nullable=False, index=True)
    source_incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=True)  # PSR 연결
    source_detail = Column(Text, nullable=True)  # 출처 상세 (라운딩 일자, 감사 번호 등)

    # 분류
    category = Column(Enum(RiskCategory), nullable=False, index=True)

    # 현재 통제 방법
    current_controls = Column(Text, nullable=True)

    # 위험 평가 (최신 값 - RiskAssessment에서 갱신)
    probability = Column(Integer, nullable=False, default=1)  # 1-5
    severity = Column(Integer, nullable=False, default=1)      # 1-5
    risk_score = Column(Integer, nullable=False, default=1)    # P×S (자동계산)
    risk_level = Column(Enum(RiskLevel), nullable=False, default=RiskLevel.LOW, index=True)

    # 잔여위험 (조치 후)
    residual_probability = Column(Integer, nullable=True)
    residual_severity = Column(Integer, nullable=True)
    residual_score = Column(Integer, nullable=True)
    residual_level = Column(Enum(RiskLevel), nullable=True)

    # 책임자 및 일정
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    target_date = Column(Date, nullable=True)

    # 상태
    status = Column(Enum(RiskStatus), nullable=False, default=RiskStatus.IDENTIFIED, index=True)

    # 자동 승격 여부
    auto_escalated = Column(Boolean, default=False)
    escalation_reason = Column(Text, nullable=True)  # "동일 카테고리 3건 이상" 등

    # 메타데이터
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    closed_at = Column(DateTime, nullable=True)
    closed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    owner = relationship("User", foreign_keys=[owner_id], backref="owned_risks")
    created_by = relationship("User", foreign_keys=[created_by_id], backref="created_risks")
    closed_by = relationship("User", foreign_keys=[closed_by_id], backref="closed_risks")
    source_incident = relationship("Incident", backref="escalated_risks")
    assessments = relationship("RiskAssessment", back_populates="risk", order_by="desc(RiskAssessment.assessed_at)")
    # Actions linked via Action.risk_id

    def __repr__(self) -> str:
        return f"<Risk {self.risk_code} - {self.risk_level.value}>"

    def update_risk_score(self) -> None:
        """P×S 점수 및 수준 자동 갱신"""
        self.risk_score = self.probability * self.severity
        self.risk_level = calculate_risk_level(self.probability, self.severity)

    def update_residual_score(self) -> None:
        """잔여위험 점수 및 수준 자동 갱신"""
        if self.residual_probability and self.residual_severity:
            self.residual_score = self.residual_probability * self.residual_severity
            self.residual_level = calculate_risk_level(
                self.residual_probability, self.residual_severity
            )


# Event listener to auto-calculate risk score before insert/update
@event.listens_for(Risk, "before_insert")
@event.listens_for(Risk, "before_update")
def calculate_scores(mapper, connection, target):
    target.update_risk_score()
    target.update_residual_score()


class RiskAssessment(Base):
    """위험 평가 이력"""

    __tablename__ = "risk_assessments"

    id = Column(Integer, primary_key=True, index=True)

    risk_id = Column(Integer, ForeignKey("risks.id"), nullable=False, index=True)

    # 평가 정보
    assessment_type = Column(Enum(RiskAssessmentType), nullable=False, index=True)
    assessed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    assessor_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # P×S 평가
    probability = Column(Integer, nullable=False)  # 1-5
    severity = Column(Integer, nullable=False)     # 1-5
    score = Column(Integer, nullable=False)        # P×S
    level = Column(Enum(RiskLevel), nullable=False)

    # 평가 근거
    rationale = Column(Text, nullable=True)

    # Relationships
    risk = relationship("Risk", back_populates="assessments")
    assessor = relationship("User", backref="risk_assessments")

    def __repr__(self) -> str:
        return f"<RiskAssessment {self.id} - {self.assessment_type.value}>"


# Event listener to auto-calculate assessment score before insert
@event.listens_for(RiskAssessment, "before_insert")
def calculate_assessment_score(mapper, connection, target):
    target.score = target.probability * target.severity
    target.level = calculate_risk_level(target.probability, target.severity)
