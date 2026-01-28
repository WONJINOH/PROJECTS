"""
APScheduler Configuration

백그라운드 작업 스케줄러 설정
- 욕창 호전율 자동 계산 (매월 2일 06:00)
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.database import async_session_maker
from app.tasks.pressure_ulcer_calculator import (
    calculate_pressure_ulcer_improvement_rate,
    save_improvement_rate_to_indicator,
)

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler: Optional[AsyncIOScheduler] = None


async def monthly_pressure_ulcer_improvement_job():
    """
    월별 욕창 호전율 자동 계산 작업.

    매월 2일에 실행되어 전월 데이터를 계산합니다.
    """
    logger.info("Starting monthly pressure ulcer improvement rate calculation")

    # 전월 계산
    today = datetime.now()
    # 전월 첫째 날 구하기
    first_of_this_month = today.replace(day=1)
    last_day_of_prev_month = first_of_this_month - timedelta(days=1)

    target_year = last_day_of_prev_month.year
    target_month = last_day_of_prev_month.month

    async with async_session_maker() as db:
        try:
            # 호전율 계산
            result = await calculate_pressure_ulcer_improvement_rate(
                db=db,
                year=target_year,
                month=target_month
            )

            logger.info(
                f"Improvement rate calculated: {result['rate']}% "
                f"({result['numerator']}/{result['denominator']})"
            )

            # 지표 값으로 저장
            await save_improvement_rate_to_indicator(
                db=db,
                year=target_year,
                month=target_month,
                result=result
            )

            logger.info(f"Improvement rate saved to indicator for {target_year}-{target_month:02d}")

        except Exception as e:
            logger.error(f"Failed to calculate/save improvement rate: {e}", exc_info=True)
            raise


def start_scheduler():
    """스케줄러 시작"""
    global scheduler

    if scheduler is not None:
        logger.warning("Scheduler already running")
        return

    scheduler = AsyncIOScheduler()

    # 매월 2일 오전 6시에 욕창 호전율 계산
    scheduler.add_job(
        monthly_pressure_ulcer_improvement_job,
        trigger=CronTrigger(day=2, hour=6, minute=0),
        id="monthly_pu_improvement",
        name="Monthly Pressure Ulcer Improvement Rate",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("APScheduler started with jobs: monthly_pu_improvement")


def shutdown_scheduler():
    """스케줄러 종료"""
    global scheduler

    if scheduler is not None:
        scheduler.shutdown(wait=False)
        scheduler = None
        logger.info("APScheduler shutdown")


async def run_manual_calculation(year: int, month: int) -> dict:
    """
    수동으로 특정 월의 호전율 계산 실행.

    Args:
        year: 계산 대상 연도
        month: 계산 대상 월

    Returns:
        계산 결과 dict
    """
    async with async_session_maker() as db:
        result = await calculate_pressure_ulcer_improvement_rate(
            db=db,
            year=year,
            month=month
        )

        await save_improvement_rate_to_indicator(
            db=db,
            year=year,
            month=month,
            result=result
        )

        return result
