"""
Physical Restraint (신체보호대) Management Models

신체보호대 사용 지표:
- 월별 사용 건수
- 사용 사유별 분류 (사용 적절성)
- 신체보호대 관련 부작용 발생률
- 평균 사용 기간 (추후)
"""

import enum
from datetime import datetime, date
from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, Enum, Text, Float, Date, Boolean, ForeignKey

from app.database import Base


class RestraintType(str, enum.Enum):
    """신체보호대 종류"""
    WRIST = "wrist"              # 손목 억제대
    ANKLE = "ankle"              # 발목 억제대
    VEST = "vest"                # 조끼형 억제대
    MITTEN = "mitten"            # 손싸개
    BED_RAIL = "bed_rail"        # 침대 난간
    WHEELCHAIR_BELT = "wheelchair_belt"  # 휠체어 벨트
    OTHER = "other"              # 기타


class RestraintReason(str, enum.Enum):
    """신체보호대 사용 사유"""
    FALL_PREVENTION = "fall_prevention"      # 낙상 예방
    SELF_HARM = "self_harm"                  # 자해 예방
    TUBE_PROTECTION = "tube_protection"      # 튜브/카테터 보호
    AGITATION = "agitation"                  # 초조/불안 행동
    CONFUSION = "confusion"                  # 혼돈 상태
    WANDERING = "wandering"                  # 배회
    TREATMENT = "treatment"                  # 치료/처치 중
    OTHER = "other"                          # 기타


class RestraintAdverseEvent(str, enum.Enum):
    """신체보호대 관련 부작용"""
    SKIN_INJURY = "skin_injury"          # 피부 손상
    CIRCULATION = "circulation"          # 순환 장애
    NERVE_DAMAGE = "nerve_damage"        # 신경 손상
    STRANGULATION = "strangulation"      # 질식 위험
    PSYCHOLOGICAL = "psychological"      # 심리적 영향
    ASPIRATION = "aspiration"            # 흡인
    FALL = "fall"                        # 억제대 관련 낙상
    OTHER = "other"                      # 기타


class RestraintRecord(Base):
    """신체보호대 사용 기록"""

    __tablename__ = "restraint_records"

    id = Column(Integer, primary_key=True, index=True)

    # 환자 정보 (익명화)
    patient_code = Column(String(50), nullable=False, index=True)
    patient_age_group = Column(String(20), nullable=True)

    # 보호대 정보
    restraint_type = Column(Enum(RestraintType), nullable=False, index=True)
    reason = Column(Enum(RestraintReason), nullable=False, index=True)
    reason_detail = Column(Text, nullable=True)

    # 사용 기간
    start_datetime = Column(DateTime, nullable=False, index=True)
    end_datetime = Column(DateTime, nullable=True)
    duration_hours = Column(Float, nullable=True)  # 계산된 사용 시간

    # 동의
    consent_obtained = Column(Boolean, default=False)
    consent_from = Column(String(50), nullable=True)  # 환자, 보호자 등

    # 의사 지시
    physician_order = Column(Boolean, default=True)
    order_datetime = Column(DateTime, nullable=True)

    # 모니터링
    monitoring_frequency = Column(String(50), nullable=True)  # 2시간마다 등
    last_assessment = Column(DateTime, nullable=True)

    # 부서
    department = Column(String(100), nullable=False, index=True)

    # 적절성 검토
    appropriateness_reviewed = Column(Boolean, default=False)
    is_appropriate = Column(Boolean, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<RestraintRecord {self.id} - {self.restraint_type.value}>"


class RestraintAdverseEventRecord(Base):
    """신체보호대 부작용 기록"""

    __tablename__ = "restraint_adverse_events"

    id = Column(Integer, primary_key=True, index=True)

    # 보호대 기록 연결
    restraint_record_id = Column(Integer, ForeignKey("restraint_records.id"), nullable=False)

    # 부작용
    event_type = Column(Enum(RestraintAdverseEvent), nullable=False)
    event_datetime = Column(DateTime, nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(String(20), nullable=True)  # mild, moderate, severe

    # 조치
    action_taken = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<RestraintAdverseEvent {self.id} - {self.event_type.value}>"


class RestraintMonthlyStats(Base):
    """신체보호대 월간 통계"""

    __tablename__ = "restraint_monthly_stats"

    id = Column(Integer, primary_key=True, index=True)

    # 기간
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)

    # 부서 (전체인 경우 NULL)
    department = Column(String(100), nullable=True, index=True)

    # 사용 건수
    total_uses = Column(Integer, default=0)
    unique_patients = Column(Integer, default=0)

    # 사유별 건수
    fall_prevention_count = Column(Integer, default=0)
    self_harm_count = Column(Integer, default=0)
    tube_protection_count = Column(Integer, default=0)
    agitation_count = Column(Integer, default=0)
    other_count = Column(Integer, default=0)

    # 평균 사용 시간 (시간)
    avg_duration_hours = Column(Float, nullable=True)

    # 부작용
    adverse_event_count = Column(Integer, default=0)
    adverse_event_rate = Column(Float, nullable=True)

    # 적절성
    appropriate_use_rate = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<RestraintMonthlyStats {self.year}-{self.month}>"
