"""
Pressure Ulcer Improvement Rate Calculator

욕창 호전율 자동 계산 서비스

정의:
- 분자: 당월 첫째주 호전 건수 (PUSH ≥1점↓ 또는 Grade↓)
- 분모: 전월말 활성 욕창 수 (사망/퇴원 제외)
- 호전율 = (분자 / 분모) × 100

계산 시점: 매월 2일 06:00 (전월 데이터 기반)
"""

import logging
from datetime import datetime, date, timedelta, timezone
from typing import TypedDict
from calendar import monthrange

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pressure_ulcer import (
    PressureUlcerRecord,
    PressureUlcerAssessment,
    PressureUlcerEndReason,
    PressureUlcerMonthlyStats,
)
from app.models.indicator import (
    IndicatorConfig,
    IndicatorValue,
    IndicatorCategory,
    IndicatorStatus,
)

logger = logging.getLogger(__name__)


class ImprovementResult(TypedDict):
    """호전율 계산 결과"""
    numerator: int      # 호전 건수
    denominator: int    # 전월말 활성 건수
    rate: float         # 호전율 (%)
    improved_push: int  # PUSH 점수 호전
    improved_grade: int # 등급 호전
    excluded_death: int # 사망 제외 건수
    excluded_discharge: int  # 퇴원 제외 건수
    details: list       # 상세 내역


# 욕창 호전율 지표 코드
IMPROVEMENT_RATE_INDICATOR_CODE = "PU-002"


async def get_active_ulcers_at_month_end(
    db: AsyncSession,
    year: int,
    month: int,
) -> list[PressureUlcerRecord]:
    """
    특정 월 말일 기준 활성 욕창 목록 조회.

    활성 조건:
    - is_active = True
    - end_date가 NULL이거나 해당 월 이후
    - end_reason이 사망/퇴원이 아님

    Args:
        year: 연도
        month: 월

    Returns:
        활성 욕창 레코드 목록
    """
    # 해당 월의 마지막 날
    _, last_day = monthrange(year, month)
    month_end = date(year, month, last_day)

    query = select(PressureUlcerRecord).where(
        and_(
            # 발견일이 해당 월말 이전
            PressureUlcerRecord.discovery_date <= month_end,
            # 활성 상태이거나, 종료일이 해당 월 이후
            or_(
                PressureUlcerRecord.is_active == True,
                PressureUlcerRecord.end_date > month_end,
                PressureUlcerRecord.end_date == None,
            ),
            # 사망/퇴원이 아닌 경우만 (종료 사유가 없거나 healed/transfer/other)
            or_(
                PressureUlcerRecord.end_reason == None,
                PressureUlcerRecord.end_reason.notin_([
                    PressureUlcerEndReason.DEATH,
                    PressureUlcerEndReason.DISCHARGE,
                ]),
            ),
        )
    )

    result = await db.execute(query)
    return list(result.scalars().all())


async def get_first_week_assessments(
    db: AsyncSession,
    year: int,
    month: int,
    ulcer_ids: list[int],
) -> list[PressureUlcerAssessment]:
    """
    특정 월 첫째주(1-7일) 평가 기록 조회.

    Args:
        year: 연도
        month: 월
        ulcer_ids: 대상 욕창 ID 목록

    Returns:
        첫째주 평가 기록 목록
    """
    if not ulcer_ids:
        return []

    first_day = date(year, month, 1)
    first_week_end = date(year, month, 7)

    query = select(PressureUlcerAssessment).where(
        and_(
            PressureUlcerAssessment.ulcer_record_id.in_(ulcer_ids),
            PressureUlcerAssessment.assessment_date >= first_day,
            PressureUlcerAssessment.assessment_date <= first_week_end,
        )
    ).order_by(
        PressureUlcerAssessment.ulcer_record_id,
        PressureUlcerAssessment.assessment_date.desc(),
    )

    result = await db.execute(query)
    return list(result.scalars().all())


async def get_previous_assessment(
    db: AsyncSession,
    ulcer_id: int,
    before_date: date,
) -> PressureUlcerAssessment | None:
    """
    특정 날짜 이전의 가장 최근 평가 기록 조회.

    Args:
        ulcer_id: 욕창 ID
        before_date: 기준 날짜

    Returns:
        이전 평가 기록 또는 None
    """
    query = (
        select(PressureUlcerAssessment)
        .where(
            and_(
                PressureUlcerAssessment.ulcer_record_id == ulcer_id,
                PressureUlcerAssessment.assessment_date < before_date,
            )
        )
        .order_by(PressureUlcerAssessment.assessment_date.desc())
        .limit(1)
    )

    result = await db.execute(query)
    return result.scalar_one_or_none()


# 등급 순서 (호전 판단용)
GRADE_ORDER = {
    "stage_4": 4,
    "stage_3": 3,
    "stage_2": 2,
    "stage_1": 1,
    "unstageable": 3,  # 미분류는 Stage 3과 동일하게 취급
    "dtpi": 2,         # DTPI는 Stage 2와 동일하게 취급
}


def is_improved(
    current_assessment: PressureUlcerAssessment,
    previous_assessment: PressureUlcerAssessment | None,
    ulcer_record: PressureUlcerRecord,
) -> tuple[bool, str]:
    """
    호전 여부 판단.

    호전 기준:
    1. PUSH 점수 1점 이상 감소
    2. Grade 호전 (예: Stage 3 → Stage 2)

    Args:
        current_assessment: 현재 평가
        previous_assessment: 이전 평가 (없으면 초기 기록 사용)
        ulcer_record: 욕창 기본 기록

    Returns:
        (호전 여부, 사유)
    """
    # 이전 PUSH 점수 결정
    if previous_assessment and previous_assessment.push_total is not None:
        prev_push = previous_assessment.push_total
    elif ulcer_record.push_total is not None:
        prev_push = ulcer_record.push_total
    else:
        prev_push = None

    # 현재 PUSH 점수
    curr_push = current_assessment.push_total

    # PUSH 점수 비교
    if prev_push is not None and curr_push is not None:
        if prev_push - curr_push >= 1:
            return True, f"PUSH {prev_push} → {curr_push} (↓{prev_push - curr_push}점)"

    # 이전 Grade 결정
    if previous_assessment and previous_assessment.grade:
        prev_grade = previous_assessment.grade.value
    elif ulcer_record.grade:
        prev_grade = ulcer_record.grade.value
    else:
        prev_grade = None

    # 현재 Grade
    curr_grade = current_assessment.grade.value if current_assessment.grade else None

    # Grade 비교
    if prev_grade and curr_grade:
        prev_order = GRADE_ORDER.get(prev_grade, 0)
        curr_order = GRADE_ORDER.get(curr_grade, 0)
        if curr_order < prev_order:
            return True, f"Grade {prev_grade} → {curr_grade}"

    return False, ""


async def calculate_pressure_ulcer_improvement_rate(
    db: AsyncSession,
    year: int,
    month: int,
) -> ImprovementResult:
    """
    욕창 호전율 계산.

    Args:
        year: 계산 대상 연도
        month: 계산 대상 월 (이 월의 첫째주 평가 기록을 사용)

    Returns:
        호전율 계산 결과
    """
    # 전월 계산
    if month == 1:
        prev_year = year - 1
        prev_month = 12
    else:
        prev_year = year
        prev_month = month - 1

    logger.info(f"Calculating improvement rate for {year}-{month:02d} (base: {prev_year}-{prev_month:02d})")

    # 1. 전월말 활성 욕창 조회
    active_ulcers = await get_active_ulcers_at_month_end(db, prev_year, prev_month)
    logger.info(f"Active ulcers at {prev_year}-{prev_month:02d} end: {len(active_ulcers)}")

    if not active_ulcers:
        return ImprovementResult(
            numerator=0,
            denominator=0,
            rate=0.0,
            improved_push=0,
            improved_grade=0,
            excluded_death=0,
            excluded_discharge=0,
            details=[],
        )

    # 욕창 ID → 레코드 매핑
    ulcer_map = {u.id: u for u in active_ulcers}
    ulcer_ids = list(ulcer_map.keys())

    # 2. 당월 첫째주 평가 기록 조회
    first_week_assessments = await get_first_week_assessments(db, year, month, ulcer_ids)
    logger.info(f"First week assessments in {year}-{month:02d}: {len(first_week_assessments)}")

    # 욕창별 최신 평가 (첫째주 내)
    latest_by_ulcer: dict[int, PressureUlcerAssessment] = {}
    for assessment in first_week_assessments:
        ulcer_id = assessment.ulcer_record_id
        if ulcer_id not in latest_by_ulcer:
            latest_by_ulcer[ulcer_id] = assessment

    # 3. 호전 건수 계산
    improved_count = 0
    improved_push_count = 0
    improved_grade_count = 0
    details = []

    for ulcer_id, assessment in latest_by_ulcer.items():
        ulcer_record = ulcer_map.get(ulcer_id)
        if not ulcer_record:
            continue

        # 이전 평가 조회 (당월 첫째주 이전)
        first_day = date(year, month, 1)
        prev_assessment = await get_previous_assessment(db, ulcer_id, first_day)

        # 호전 여부 판단
        improved, reason = is_improved(assessment, prev_assessment, ulcer_record)

        if improved:
            improved_count += 1
            if "PUSH" in reason:
                improved_push_count += 1
            elif "Grade" in reason:
                improved_grade_count += 1

            details.append({
                "ulcer_id": ulcer_id,
                "patient_code": ulcer_record.patient_code,
                "reason": reason,
                "assessment_date": assessment.assessment_date.isoformat(),
            })

    # 4. 제외 건수 계산 (정보 제공용)
    excluded_death = 0
    excluded_discharge = 0

    # 전월말 기준으로 사망/퇴원으로 종료된 건 수
    excluded_query = select(
        func.count(PressureUlcerRecord.id),
        PressureUlcerRecord.end_reason
    ).where(
        and_(
            PressureUlcerRecord.end_reason.in_([
                PressureUlcerEndReason.DEATH,
                PressureUlcerEndReason.DISCHARGE,
            ]),
            PressureUlcerRecord.end_date <= date(prev_year, prev_month, monthrange(prev_year, prev_month)[1]),
        )
    ).group_by(PressureUlcerRecord.end_reason)

    excluded_result = await db.execute(excluded_query)
    for count, reason in excluded_result.all():
        if reason == PressureUlcerEndReason.DEATH:
            excluded_death = count
        elif reason == PressureUlcerEndReason.DISCHARGE:
            excluded_discharge = count

    # 5. 호전율 계산
    denominator = len(active_ulcers)
    rate = round((improved_count / denominator * 100), 2) if denominator > 0 else 0.0

    logger.info(f"Improvement rate: {rate}% ({improved_count}/{denominator})")

    return ImprovementResult(
        numerator=improved_count,
        denominator=denominator,
        rate=rate,
        improved_push=improved_push_count,
        improved_grade=improved_grade_count,
        excluded_death=excluded_death,
        excluded_discharge=excluded_discharge,
        details=details,
    )


async def save_improvement_rate_to_indicator(
    db: AsyncSession,
    year: int,
    month: int,
    result: ImprovementResult,
) -> IndicatorValue:
    """
    계산된 호전율을 지표 값으로 저장.

    Args:
        year: 연도
        month: 월
        result: 계산 결과

    Returns:
        저장된 IndicatorValue
    """
    # 지표 설정 조회
    indicator_query = select(IndicatorConfig).where(
        IndicatorConfig.code == IMPROVEMENT_RATE_INDICATOR_CODE
    )
    indicator_result = await db.execute(indicator_query)
    indicator = indicator_result.scalar_one_or_none()

    if not indicator:
        logger.warning(f"Indicator {IMPROVEMENT_RATE_INDICATOR_CODE} not found, creating...")
        indicator = await create_improvement_rate_indicator(db)

    # 기간 설정
    period_start = datetime(year, month, 1, tzinfo=timezone.utc)
    _, last_day = monthrange(year, month)
    period_end = datetime(year, month, last_day, 23, 59, 59, tzinfo=timezone.utc)

    # 기존 값 확인 (덮어쓰기 방지)
    existing_query = select(IndicatorValue).where(
        and_(
            IndicatorValue.indicator_id == indicator.id,
            IndicatorValue.period_start == period_start,
        )
    )
    existing_result = await db.execute(existing_query)
    existing = existing_result.scalar_one_or_none()

    if existing:
        # 기존 값 업데이트
        existing.value = result["rate"]
        existing.numerator = float(result["numerator"])
        existing.denominator = float(result["denominator"])
        existing.notes = (
            f"PUSH 호전: {result['improved_push']}건, "
            f"Grade 호전: {result['improved_grade']}건"
        )
        await db.commit()
        await db.refresh(existing)
        return existing

    # 새 값 생성
    indicator_value = IndicatorValue(
        indicator_id=indicator.id,
        period_start=period_start,
        period_end=period_end,
        value=result["rate"],
        numerator=float(result["numerator"]),
        denominator=float(result["denominator"]),
        notes=(
            f"자동 계산. PUSH 호전: {result['improved_push']}건, "
            f"Grade 호전: {result['improved_grade']}건"
        ),
    )

    db.add(indicator_value)
    await db.commit()
    await db.refresh(indicator_value)

    return indicator_value


async def create_improvement_rate_indicator(db: AsyncSession) -> IndicatorConfig:
    """
    욕창호전율 지표 설정 자동 생성.

    Returns:
        생성된 IndicatorConfig
    """
    indicator = IndicatorConfig(
        code=IMPROVEMENT_RATE_INDICATOR_CODE,
        name="욕창호전율",
        description="월초 1주 내 호전 건수 / 전월말 활성 욕창 수 × 100",
        category=IndicatorCategory.PRESSURE_ULCER,
        calculation_formula="(호전 건수 / 전월말 활성 욕창 수) × 100",
        numerator_name="월초 1주 내 호전 건수 (PUSH↓1점+ 또는 Grade↓)",
        denominator_name="전월말 활성 욕창 수 (사망/퇴원 제외)",
        unit="%",
        target_value=50.0,  # 목표: 50% 이상
        warning_threshold=30.0,
        threshold_direction="higher_is_better",
        period_type="monthly",
        data_source="PSR 욕창 관리 시스템",
        auto_calculate=True,
        status=IndicatorStatus.ACTIVE,
    )

    db.add(indicator)
    await db.commit()
    await db.refresh(indicator)

    logger.info(f"Created indicator: {indicator.code} - {indicator.name}")

    return indicator
