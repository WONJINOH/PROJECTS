"""
Indicator Configuration Model

동적 지표 관리 시스템 - 병원 정책에 따라 지표 추가/삭제/수정 가능

지표 카테고리:
1. PSR (환자안전사건보고)
2. 욕창 관리
3. 낙상 관리
4. 투약 안전
5. 신체보호대 사용
6. 감염 관리
7. 직원 안전
8. 검사 TAT
9. 종합 환자안전 지표
"""

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, Enum, Text, Boolean, Float, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class IndicatorCategory(str, enum.Enum):
    """지표 카테고리"""
    PSR = "psr"                          # 환자안전사건보고
    PRESSURE_ULCER = "pressure_ulcer"    # 욕창 관리
    FALL = "fall"                        # 낙상 관리
    MEDICATION = "medication"            # 투약 안전
    RESTRAINT = "restraint"              # 신체보호대 사용
    INFECTION = "infection"              # 감염 관리
    STAFF_SAFETY = "staff_safety"        # 직원 안전
    LAB_TAT = "lab_tat"                  # 검사 TAT
    COMPOSITE = "composite"              # 종합 환자안전 지표


class ThresholdDirection(str, enum.Enum):
    """임계값 방향"""
    HIGHER_IS_BETTER = "higher_is_better"
    LOWER_IS_BETTER = "lower_is_better"


class PeriodType(str, enum.Enum):
    """집계 주기"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class ChartType(str, enum.Enum):
    """차트 유형"""
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    AREA = "area"


class IndicatorStatus(str, enum.Enum):
    """지표 상태"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PLANNED = "planned"  # 추후 도입 예정


class IndicatorConfig(Base):
    """지표 설정 - 동적으로 추가/삭제 가능"""

    __tablename__ = "indicator_configs"

    id = Column(Integer, primary_key=True, index=True)

    # 기본 정보
    code = Column(String(50), unique=True, nullable=False, index=True)  # 예: PSR-001, FALL-001
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # 분류
    category = Column(Enum(IndicatorCategory), nullable=False, index=True)

    # 계산 방식
    calculation_formula = Column(Text, nullable=True)  # 계산 공식 설명
    numerator_name = Column(String(500), nullable=True)  # 분자 설명
    denominator_name = Column(String(500), nullable=True)  # 분모 설명
    unit = Column(String(50), default="건")  # 단위 (%, ‰, 건, 점 등)

    # 목표값 및 기준
    target_value = Column(Float, nullable=True)  # 목표값
    warning_threshold = Column(Float, nullable=True)  # 경고 기준
    critical_threshold = Column(Float, nullable=True)  # 위험 기준
    threshold_direction = Column(Enum(ThresholdDirection), nullable=True)  # 높을수록/낮을수록 좋음

    # 표시 설정
    period_type = Column(Enum(PeriodType), default=PeriodType.MONTHLY)  # 집계 주기
    chart_type = Column(Enum(ChartType), default=ChartType.LINE)  # 차트 유형
    is_key_indicator = Column(Boolean, default=False)  # 핵심 지표 여부 (★ 표시)
    display_order = Column(Integer, default=0)  # 표시 순서

    # 데이터 소스
    data_source = Column(String(200), nullable=True)  # 데이터 출처 (PSR 시스템, EMR 등)
    auto_calculate = Column(Boolean, default=False)  # 자동 계산 여부

    # 상태
    status = Column(Enum(IndicatorStatus), default=IndicatorStatus.ACTIVE)

    # 메타데이터
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = Column(Integer, nullable=True)

    # Relationships
    values = relationship("IndicatorValue", back_populates="indicator", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Indicator {self.code}: {self.name}>"


class IndicatorValue(Base):
    """지표 실측값 - 기간별 데이터 저장"""

    __tablename__ = "indicator_values"

    id = Column(Integer, primary_key=True, index=True)

    # 지표 연결
    indicator_id = Column(Integer, ForeignKey("indicator_configs.id", ondelete="CASCADE"), nullable=False, index=True)

    # 기간
    period_start = Column(DateTime, nullable=False, index=True)
    period_end = Column(DateTime, nullable=False)

    # 값
    value = Column(Float, nullable=False)  # 계산된 지표값
    numerator = Column(Float, nullable=True)  # 분자
    denominator = Column(Float, nullable=True)  # 분모

    # 메타데이터
    notes = Column(Text, nullable=True)  # 비고
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = Column(Integer, nullable=True)

    # 검증
    is_verified = Column(Boolean, default=False)
    verified_by_id = Column(Integer, nullable=True)
    verified_at = Column(DateTime, nullable=True)

    # Relationships
    indicator = relationship("IndicatorConfig", back_populates="values")

    def __repr__(self) -> str:
        return f"<IndicatorValue {self.indicator_id} @ {self.period_start}: {self.value}>"
