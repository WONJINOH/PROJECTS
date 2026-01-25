"""
Dashboard API

환자안전 통합 대시보드 엔드포인트
- 요약 통계
- 카테고리별 지표
- 히트맵 데이터
- 추세 분석
- 최근 사고 목록
"""

from typing import Annotated, Optional, List
from datetime import date, datetime
import re

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.security.dependencies import get_current_user, require_permission
from app.security.rbac import Permission
from app.models.user import User, Role
from app.models.incident import Incident
from app.models.fall_detail import FallDetail
from app.models.medication_detail import MedicationErrorDetail
from app.database import get_db

router = APIRouter()


def generalize_location(location: str) -> str:
    """구체적인 장소를 일반화된 카테고리로 변환"""
    if not location:
        return "기타"

    location = location.strip()

    # 장소 패턴 매핑
    patterns = [
        (r"\d{2,3}(-\d)?호|병실", "병실"),
        (r"화장실|변기|욕실|샤워실", "화장실"),
        (r"복도|홀|로비|현관", "복도"),
        (r"간호(사)?실|스테이션|NS", "간호사실"),
        (r"처치실|드레싱룸", "처치실"),
        (r"물리치료|재활치료|PT실|OT실|치료실", "재활치료실"),
        (r"식당|급식|식사|카페", "식당"),
        (r"엘리베이터|승강기|EV", "엘리베이터"),
        (r"계단", "계단"),
        (r"야외|정원|옥상|테라스", "야외"),
    ]

    for pattern, label in patterns:
        if re.search(pattern, location, re.IGNORECASE):
            return label

    return "기타"


@router.get(
    "/summary",
    summary="대시보드 요약 통계",
)
async def get_dashboard_summary(
    current_user: Annotated[User, Depends(get_current_user)],
    year: int = Query(default=None, description="연도"),
    month: int = Query(default=None, ge=1, le=12, description="월"),
    department: Optional[str] = Query(default=None, description="부서"),
) -> dict:
    """
    대시보드 요약 통계 조회

    Returns:
        - 핵심 지표 요약 (KPI)
        - 카테고리별 요약
    """
    # TODO: 실제 DB 조회 구현
    return {
        "period": {
            "year": year or datetime.now().year,
            "month": month or datetime.now().month,
        },
        "kpi": {
            "total_incidents": 156,
            "fall_rate": 2.3,
            "pressure_ulcer_rate": 1.5,
            "medication_error_rate": 0.8,
            "infection_rate": 1.2,
            "hand_hygiene_rate": 87.5,
        },
        "by_category": {
            "psr": {"total": 156, "near_miss": 72, "harm": 15},
            "fall": {"total": 45, "with_injury": 12},
            "pressure_ulcer": {"new_cases": 8, "improved": 15, "worsened": 3},
            "medication": {"total_errors": 38, "near_miss": 28},
            "restraint": {"active_uses": 23, "adverse_events": 2},
            "infection": {"total": 12, "cauti": 4, "uti": 8},
        },
        "trends": {
            "direction": "improving",  # improving, stable, worsening
            "change_percent": -5.2,
        },
    }


@router.get(
    "/psr",
    summary="PSR(환자안전사건보고) 지표",
)
async def get_psr_dashboard(
    current_user: Annotated[User, Depends(get_current_user)],
    year: int = Query(default=None),
    month: int = Query(default=None, ge=1, le=12),
    department: Optional[str] = Query(default=None),
) -> dict:
    """
    PSR 대시보드 데이터
    - 사고분류별
    - 오류유형별
    - 부서별
    - 사건유형
    - 사고원인
    """
    return {
        "by_classification": [
            {"name": "낙상", "count": 45},
            {"name": "투약", "count": 38},
            {"name": "욕창", "count": 28},
            {"name": "감염", "count": 25},
            {"name": "기타", "count": 20},
        ],
        "by_severity": [
            {"name": "근접오류", "count": 72, "color": "#94a3b8"},
            {"name": "무해", "count": 45, "color": "#22c55e"},
            {"name": "위해", "count": 35, "color": "#f97316"},
            {"name": "적신호", "count": 4, "color": "#ef4444"},
        ],
        "by_department": [
            {"name": "301병동", "count": 32},
            {"name": "302병동", "count": 28},
            {"name": "401병동", "count": 24},
            {"name": "물리치료실", "count": 15},
            {"name": "기타", "count": 57},
        ],
        "by_cause": [
            {"name": "인적요인", "count": 65},
            {"name": "시스템요인", "count": 42},
            {"name": "환경요인", "count": 28},
            {"name": "의사소통", "count": 15},
            {"name": "기타", "count": 6},
        ],
        "recurrence_count": 12,
        "monthly_trend": [
            {"month": "1월", "count": 12},
            {"month": "2월", "count": 15},
            {"month": "3월", "count": 18},
            {"month": "4월", "count": 14},
            {"month": "5월", "count": 22},
            {"month": "6월", "count": 19},
        ],
    }


@router.get(
    "/psr/heatmap",
    summary="PSR 히트맵 데이터 (장소×시간)",
)
async def get_psr_heatmap(
    current_user: Annotated[User, Depends(get_current_user)],
    year: int = Query(default=None),
    month: int = Query(default=None, ge=1, le=12),
) -> dict:
    """
    사건장소 × 사건시간 히트맵 데이터
    """
    # 장소 목록
    locations = ["병실", "화장실", "복도", "간호사실", "처치실", "재활치료실", "기타"]
    # 시간대 (0-23)
    hours = list(range(24))

    # Mock 히트맵 데이터
    heatmap_data = []
    import random
    for loc_idx, location in enumerate(locations):
        for hour in hours:
            # 실제로는 DB에서 집계
            count = random.randint(0, 10) if 6 <= hour <= 22 else random.randint(0, 3)
            if count > 0:
                heatmap_data.append({
                    "location": location,
                    "hour": hour,
                    "count": count,
                })

    return {
        "locations": locations,
        "hours": hours,
        "data": heatmap_data,
        "peak_hours": [8, 14, 20],  # 피크 시간대
        "peak_locations": ["병실", "화장실"],  # 고위험 장소
    }


@router.get(
    "/pressure-ulcer",
    summary="욕창 관리 지표",
)
async def get_pressure_ulcer_dashboard(
    current_user: Annotated[User, Depends(get_current_user)],
    year: int = Query(default=None),
    month: int = Query(default=None, ge=1, le=12),
) -> dict:
    """
    욕창 관리 대시보드
    - 발생률
    - 호전율/악화율
    - 궤적분석
    """
    return {
        "summary": {
            "total_patient_days": 4500,
            "new_cases": 8,
            "incidence_rate": 1.78,  # 1000재원일당
            "target_rate": 2.0,
            "met_target": True,
        },
        "outcomes": {
            "improved": 15,
            "worsened": 3,
            "healed": 8,
            "improvement_rate": 71.4,
            "worsening_rate": 14.3,
        },
        "by_grade": [
            {"grade": "Stage 1", "count": 12},
            {"grade": "Stage 2", "count": 8},
            {"grade": "Stage 3", "count": 3},
            {"grade": "Stage 4", "count": 1},
            {"grade": "DTPI", "count": 2},
        ],
        "by_location": [
            {"location": "천골", "count": 10},
            {"location": "발뒤꿈치", "count": 7},
            {"location": "좌골", "count": 4},
            {"location": "대전자", "count": 3},
            {"location": "기타", "count": 2},
        ],
        "trajectory": [
            {"month": "1월", "incidence": 1.5, "improvement": 68},
            {"month": "2월", "incidence": 1.8, "improvement": 72},
            {"month": "3월", "incidence": 1.6, "improvement": 75},
            {"month": "4월", "incidence": 2.1, "improvement": 65},
            {"month": "5월", "incidence": 1.9, "improvement": 70},
            {"month": "6월", "incidence": 1.78, "improvement": 71},
        ],
    }


@router.get(
    "/fall",
    summary="낙상 관리 지표",
)
async def get_fall_dashboard(
    current_user: Annotated[User, Depends(get_current_user)],
    year: int = Query(default=None),
    month: int = Query(default=None, ge=1, le=12),
) -> dict:
    """
    낙상 관리 대시보드
    """
    return {
        "summary": {
            "total_patient_days": 4500,
            "total_falls": 45,
            "fall_rate": 10.0,  # 1000재원일당
            "target_rate": 12.0,
            "met_target": True,
        },
        "by_injury": [
            {"level": "손상없음", "count": 25, "color": "#22c55e"},
            {"level": "경미", "count": 12, "color": "#eab308"},
            {"level": "중등도", "count": 6, "color": "#f97316"},
            {"level": "중증", "count": 2, "color": "#ef4444"},
        ],
        "by_location": [
            {"location": "침대", "count": 18},
            {"location": "화장실", "count": 12},
            {"location": "복도", "count": 8},
            {"location": "휠체어", "count": 4},
            {"location": "기타", "count": 3},
        ],
        "by_cause": [
            {"cause": "균형상실", "count": 15},
            {"cause": "미끄러짐", "count": 12},
            {"cause": "근력약화", "count": 8},
            {"cause": "인지장애", "count": 6},
            {"cause": "기타", "count": 4},
        ],
        "monthly_trend": [
            {"month": "1월", "falls": 8, "with_injury": 3},
            {"month": "2월", "falls": 6, "with_injury": 2},
            {"month": "3월", "falls": 9, "with_injury": 4},
            {"month": "4월", "falls": 7, "with_injury": 2},
            {"month": "5월", "falls": 10, "with_injury": 5},
            {"month": "6월", "falls": 5, "with_injury": 2},
        ],
    }


@router.get(
    "/medication",
    summary="투약 안전 지표",
)
async def get_medication_dashboard(
    current_user: Annotated[User, Depends(get_current_user)],
    year: int = Query(default=None),
    month: int = Query(default=None, ge=1, le=12),
) -> dict:
    """
    투약 안전 대시보드
    """
    return {
        "summary": {
            "total_administrations": 45000,
            "total_errors": 38,
            "error_rate": 0.084,  # %
            "near_miss_count": 28,
            "near_miss_capture_rate": 73.7,
        },
        "by_stage": [
            {"stage": "처방", "count": 8},
            {"stage": "조제", "count": 12},
            {"stage": "투여", "count": 15},
            {"stage": "모니터링", "count": 3},
        ],
        "by_type": [
            {"type": "용량오류", "count": 12},
            {"type": "약물오류", "count": 8},
            {"type": "시간오류", "count": 6},
            {"type": "경로오류", "count": 4},
            {"type": "누락", "count": 5},
            {"type": "기타", "count": 3},
        ],
        "by_severity": [
            {"severity": "A-B (근접오류)", "count": 28},
            {"severity": "C-D (무해)", "count": 6},
            {"severity": "E-F (위해)", "count": 3},
            {"severity": "G-I (중증)", "count": 1},
        ],
        "high_alert_errors": 5,
        "monthly_trend": [
            {"month": "1월", "errors": 7, "near_miss": 5},
            {"month": "2월", "errors": 5, "near_miss": 4},
            {"month": "3월", "errors": 8, "near_miss": 6},
            {"month": "4월", "errors": 6, "near_miss": 4},
            {"month": "5월", "errors": 7, "near_miss": 5},
            {"month": "6월", "errors": 5, "near_miss": 4},
        ],
    }


@router.get(
    "/restraint",
    summary="신체보호대 지표",
)
async def get_restraint_dashboard(
    current_user: Annotated[User, Depends(get_current_user)],
    year: int = Query(default=None),
    month: int = Query(default=None, ge=1, le=12),
) -> dict:
    """
    신체보호대 사용 대시보드
    """
    return {
        "summary": {
            "total_uses": 156,
            "unique_patients": 45,
            "avg_duration_hours": 8.5,
            "adverse_events": 4,
            "adverse_event_rate": 2.56,
        },
        "by_reason": [
            {"reason": "낙상예방", "count": 78},
            {"reason": "튜브보호", "count": 42},
            {"reason": "초조행동", "count": 24},
            {"reason": "자해예방", "count": 8},
            {"reason": "기타", "count": 4},
        ],
        "by_type": [
            {"type": "손목억제대", "count": 65},
            {"type": "조끼형", "count": 42},
            {"type": "손싸개", "count": 28},
            {"type": "침대난간", "count": 15},
            {"type": "기타", "count": 6},
        ],
        "appropriateness": {
            "appropriate": 142,
            "inappropriate": 8,
            "not_reviewed": 6,
            "appropriate_rate": 94.7,
        },
        "monthly_trend": [
            {"month": "1월", "uses": 28, "adverse": 1},
            {"month": "2월", "uses": 25, "adverse": 0},
            {"month": "3월", "uses": 30, "adverse": 1},
            {"month": "4월", "uses": 22, "adverse": 0},
            {"month": "5월", "uses": 26, "adverse": 1},
            {"month": "6월", "uses": 25, "adverse": 1},
        ],
    }


@router.get(
    "/infection",
    summary="감염 관리 지표",
)
async def get_infection_dashboard(
    current_user: Annotated[User, Depends(get_current_user)],
    year: int = Query(default=None),
    month: int = Query(default=None, ge=1, le=12),
) -> dict:
    """
    감염 관리 대시보드
    """
    return {
        "summary": {
            "total_patient_days": 4500,
            "catheter_days": 1200,
            "total_infections": 12,
            "uti_non_catheter": 8,
            "cauti": 4,
        },
        "rates": {
            "uti_rate": 1.78,  # 1000재원일당
            "cauti_rate": 3.33,  # 1000도뇨관일당
        },
        "hand_hygiene": {
            "opportunities": 2500,
            "performed": 2188,
            "rate": 87.5,
            "target": 85.0,
            "met_target": True,
        },
        "by_type": [
            {"type": "비카테터 요로감염", "count": 8},
            {"type": "카테터 관련 요로감염", "count": 4},
        ],
        "hand_hygiene_by_role": [
            {"role": "간호사", "rate": 92.3},
            {"role": "의사", "rate": 85.2},
            {"role": "간병인", "rate": 78.5},
            {"role": "물리치료사", "rate": 88.1},
        ],
        "monthly_trend": [
            {"month": "1월", "infections": 2, "hand_hygiene": 85.2},
            {"month": "2월", "infections": 1, "hand_hygiene": 86.8},
            {"month": "3월", "infections": 3, "hand_hygiene": 84.5},
            {"month": "4월", "infections": 2, "hand_hygiene": 87.2},
            {"month": "5월", "infections": 2, "hand_hygiene": 88.1},
            {"month": "6월", "infections": 2, "hand_hygiene": 87.5},
        ],
    }


@router.get(
    "/staff-safety",
    summary="직원 안전 지표",
)
async def get_staff_safety_dashboard(
    current_user: Annotated[User, Depends(get_current_user)],
    year: int = Query(default=None),
    month: int = Query(default=None, ge=1, le=12),
) -> dict:
    """
    직원 안전 대시보드
    """
    return {
        "exposures": {
            "total": 8,
            "needlestick": 4,
            "sharp_injury": 2,
            "splash": 2,
            "pep_given": 3,
        },
        "by_role": [
            {"role": "간호사", "count": 5},
            {"role": "청소원", "count": 2},
            {"role": "의사", "count": 1},
        ],
        "monthly_trend": [
            {"month": "1월", "exposures": 1},
            {"month": "2월", "exposures": 2},
            {"month": "3월", "exposures": 1},
            {"month": "4월", "exposures": 1},
            {"month": "5월", "exposures": 2},
            {"month": "6월", "exposures": 1},
        ],
    }


@router.get(
    "/lab-tat",
    summary="검사 TAT 지표",
)
async def get_lab_tat_dashboard(
    current_user: Annotated[User, Depends(get_current_user)],
    year: int = Query(default=None),
    month: int = Query(default=None, ge=1, le=12),
) -> dict:
    """
    검사 TAT 대시보드
    """
    return {
        "imaging": [
            {"test": "X-ray", "avg_tat": 25, "target": 30, "achievement": 92.5},
            {"test": "CT", "avg_tat": 45, "target": 60, "achievement": 88.3},
            {"test": "MRI", "avg_tat": 120, "target": 180, "achievement": 95.2},
            {"test": "초음파", "avg_tat": 35, "target": 45, "achievement": 90.1},
        ],
        "laboratory": [
            {"test": "일반혈액검사", "avg_tat": 35, "target": 40, "achievement": 94.5},
            {"test": "생화학검사", "avg_tat": 45, "target": 60, "achievement": 96.2},
            {"test": "뇨검사", "avg_tat": 25, "target": 30, "achievement": 92.8},
            {"test": "응고검사", "avg_tat": 40, "target": 45, "achievement": 91.5},
        ],
        "overall": {
            "imaging_achievement": 91.5,
            "laboratory_achievement": 93.8,
        },
    }


@router.get(
    "/indicators",
    summary="활성 지표 목록",
)
async def get_active_indicators(
    current_user: Annotated[User, Depends(get_current_user)],
    category: Optional[str] = Query(default=None, description="카테고리 필터"),
) -> List[dict]:
    """
    활성화된 지표 목록 조회 (동적 관리용)
    """
    # TODO: DB에서 IndicatorConfig 조회
    return [
        {
            "id": 1,
            "code": "PSR-001",
            "name": "환자안전사건 총 보고건수",
            "category": "psr",
            "status": "active",
            "is_core": True,
        },
        {
            "id": 2,
            "code": "FALL-001",
            "name": "낙상 발생률",
            "category": "fall",
            "unit": "‰",
            "status": "active",
            "is_core": True,
        },
        {
            "id": 3,
            "code": "PU-001",
            "name": "욕창 발생률",
            "category": "pressure_ulcer",
            "unit": "‰",
            "status": "active",
            "is_core": True,
        },
        # ... 더 많은 지표
    ]


@router.get(
    "/recent-incidents",
    summary="최근 사고 보고 목록",
)
async def get_recent_incidents(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(default=10, ge=1, le=50, description="조회 개수"),
) -> List[dict]:
    """
    최근 사고 보고 목록 조회 (대시보드용)

    - REPORTER: 자신이 보고한 사고만 조회
    - QPS_STAFF/VICE_CHAIR/DIRECTOR/MASTER: 전체 사고 조회

    Returns:
        - id: 사고 ID
        - category: 사고 유형
        - grade: 등급
        - location: 장소 (일반화됨)
        - original_location: 원본 장소
        - occurred_at: 발생일시
        - status: 상태
        - has_analysis: 분석 완료 여부
        - analysis_type: 분석 유형 (fall_detail, medication_detail 등)
    """
    # 접근 필터 적용
    if current_user.role in [Role.QPS_STAFF, Role.VICE_CHAIR, Role.DIRECTOR, Role.MASTER]:
        access_filter = Incident.is_deleted == False
    else:
        access_filter = and_(
            Incident.is_deleted == False,
            Incident.reporter_id == current_user.id
        )

    # 최근 사고 조회
    query = (
        select(Incident)
        .where(access_filter)
        .order_by(Incident.occurred_at.desc())
        .limit(limit)
    )
    result = await db.execute(query)
    incidents = result.scalars().all()

    # 각 사고에 대해 분석 상태 확인
    incident_list = []
    for incident in incidents:
        # 분석 상태 확인
        has_analysis = False
        analysis_type = None

        # Get category value (handle both enum and string)
        cat_value = incident.category.value if hasattr(incident.category, 'value') else incident.category

        # Check for analysis records (handle missing tables gracefully)
        try:
            if cat_value == "fall":
                fall_query = select(FallDetail).where(FallDetail.incident_id == incident.id)
                fall_result = await db.execute(fall_query)
                if fall_result.scalar_one_or_none():
                    has_analysis = True
                    analysis_type = "fall_detail"

            elif cat_value == "medication":
                med_query = select(MedicationErrorDetail).where(MedicationErrorDetail.incident_id == incident.id)
                med_result = await db.execute(med_query)
                if med_result.scalar_one_or_none():
                    has_analysis = True
                    analysis_type = "medication_detail"
        except Exception:
            # Table might not exist - ignore and continue
            pass

        # 카테고리 라벨 매핑
        category_labels = {
            "fall": "낙상",
            "medication": "투약",
            "pressure_ulcer": "욕창",
            "infection": "감염",
            "medical_device": "의료기기",
            "surgery": "수술",
            "transfusion": "수혈",
            "other": "기타",
        }

        # Get grade value
        grade_value = incident.grade.value if hasattr(incident.grade, 'value') else incident.grade

        incident_list.append({
            "id": incident.id,
            "category": category_labels.get(cat_value, cat_value),
            "category_code": cat_value,
            "grade": grade_value,
            "location": generalize_location(incident.location),
            "original_location": incident.location,
            "occurred_at": incident.occurred_at.isoformat() if incident.occurred_at else None,
            "status": incident.status,  # status is already a string, not enum
            "has_analysis": has_analysis,
            "analysis_type": analysis_type,
        })

    return incident_list
