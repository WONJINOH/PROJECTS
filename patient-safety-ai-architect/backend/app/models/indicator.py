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

from sqlalchemy import Column, Integer, String, DateTime, Enum, Text, Boolean, JSON, Float
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
    OVERALL = "overall"                  # 종합 환자안전 지표


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
    name_en = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)

    # 분류
    category = Column(Enum(IndicatorCategory), nullable=False, index=True)
    subcategory = Column(String(100), nullable=True)  # 세부 분류

    # 계산 방식
    formula = Column(Text, nullable=True)  # 계산 공식 설명
    numerator_desc = Column(String(500), nullable=True)  # 분자 설명
    denominator_desc = Column(String(500), nullable=True)  # 분모 설명
    unit = Column(String(50), default="%")  # 단위 (%, ‰, 건, 점 등)

    # 목표값 및 기준
    target_value = Column(Float, nullable=True)  # 목표값
    threshold_good = Column(Float, nullable=True)  # 양호 기준
    threshold_warning = Column(Float, nullable=True)  # 주의 기준
    threshold_critical = Column(Float, nullable=True)  # 위험 기준

    # 표시 설정
    display_order = Column(Integer, default=0)  # 표시 순서
    chart_type = Column(String(50), default="line")  # line, bar, pie, heatmap, gauge
    color = Column(String(20), nullable=True)  # 차트 색상

    # 상태
    status = Column(Enum(IndicatorStatus), default=IndicatorStatus.ACTIVE)
    is_core = Column(Boolean, default=False)  # 핵심 지표 여부 (삭제 불가)

    # 데이터 소스
    data_source = Column(String(100), nullable=True)  # 데이터 출처 (manual, emr, external)
    collection_frequency = Column(String(50), default="monthly")  # daily, weekly, monthly, quarterly

    # 메타데이터
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, nullable=True)

    # 추가 설정 (JSON)
    extra_config = Column(JSON, nullable=True)  # 지표별 추가 설정

    def __repr__(self) -> str:
        return f"<Indicator {self.code}: {self.name}>"


class IndicatorValue(Base):
    """지표 실측값 - 기간별 데이터 저장"""

    __tablename__ = "indicator_values"

    id = Column(Integer, primary_key=True, index=True)

    # 지표 연결
    indicator_id = Column(Integer, nullable=False, index=True)

    # 기간
    period_type = Column(String(20), nullable=False)  # daily, weekly, monthly, quarterly, yearly
    period_start = Column(DateTime, nullable=False, index=True)
    period_end = Column(DateTime, nullable=False)

    # 값
    numerator = Column(Float, nullable=True)  # 분자
    denominator = Column(Float, nullable=True)  # 분모
    value = Column(Float, nullable=False)  # 계산된 지표값

    # 부서별 (선택)
    department = Column(String(100), nullable=True, index=True)

    # 메타데이터
    data_source = Column(String(100), nullable=True)  # 데이터 출처
    note = Column(Text, nullable=True)  # 비고
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, nullable=True)

    # 검증
    is_verified = Column(Boolean, default=False)
    verified_by = Column(Integer, nullable=True)
    verified_at = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<IndicatorValue {self.indicator_id} @ {self.period_start}: {self.value}>"
