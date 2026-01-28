"""
Pressure Ulcer Management API (Feature 12)

독립적인 욕창 관리 기능:
- 환자 목록 조회 (활성 욕창 환자)
- PUSH 평가 기록 추가
- 월별 추이 조회
- 통계 요약
"""

from datetime import datetime, timezone, date, timedelta
from typing import Annotated, Optional
from calendar import monthrange

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select, func, and_, or_, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.pressure_ulcer import (
    PressureUlcerRecord,
    PressureUlcerAssessment,
    PressureUlcerGrade,
    PressureUlcerLocation,
    PressureUlcerOrigin,
    PressureUlcerEndReason,
)
from app.models.user import User, Role
from app.security.dependencies import get_current_active_user

router = APIRouter()


# ============ Schemas ============

class PressureUlcerPatientSummary(BaseModel):
    """환자별 욕창 요약"""
    id: int
    patient_code: str
    patient_name: Optional[str] = None
    patient_gender: Optional[str] = None
    room_number: Optional[str] = None
    department: str
    ulcer_id: str
    location: str
    location_label: str
    origin: str
    origin_label: str
    grade: Optional[str] = None
    grade_label: Optional[str] = None
    discovery_date: date
    push_total: Optional[float] = None
    latest_assessment_date: Optional[date] = None
    latest_push_total: Optional[float] = None
    is_active: bool
    end_reason: Optional[str] = None
    end_date: Optional[date] = None

    class Config:
        from_attributes = True


class PressureUlcerPatientListResponse(BaseModel):
    """환자 목록 응답"""
    items: list[PressureUlcerPatientSummary]
    total: int
    active_count: int
    healed_count: int


class PressureUlcerPatientDetail(BaseModel):
    """환자 상세 정보"""
    id: int
    incident_id: Optional[int] = None
    patient_code: str
    patient_name: Optional[str] = None
    patient_gender: Optional[str] = None
    room_number: Optional[str] = None
    patient_age_group: Optional[str] = None
    admission_date: Optional[date] = None
    department: str
    ulcer_id: str
    location: str
    location_detail: Optional[str] = None
    origin: str
    discovery_date: date
    grade: Optional[str] = None
    push_length_width: Optional[int] = None
    push_exudate: Optional[int] = None
    push_tissue_type: Optional[int] = None
    push_total: Optional[float] = None
    length_cm: Optional[float] = None
    width_cm: Optional[float] = None
    depth_cm: Optional[float] = None
    risk_factors: Optional[str] = None
    treatment_plan: Optional[str] = None
    note: Optional[str] = None
    is_active: bool
    is_healed: bool
    healed_date: Optional[date] = None
    end_date: Optional[date] = None
    end_reason: Optional[str] = None
    end_reason_detail: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    assessments: list["PushAssessmentResponse"] = []

    class Config:
        from_attributes = True


class PushAssessmentResponse(BaseModel):
    """PUSH 평가 응답"""
    id: int
    assessment_date: date
    grade: str
    grade_label: str
    previous_grade: Optional[str] = None
    push_length_width: Optional[int] = None
    push_exudate: Optional[int] = None
    push_tissue_type: Optional[int] = None
    push_total: Optional[float] = None
    length_cm: Optional[float] = None
    width_cm: Optional[float] = None
    depth_cm: Optional[float] = None
    is_improved: Optional[bool] = None
    is_worsened: Optional[bool] = None
    note: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PushAssessmentCreate(BaseModel):
    """PUSH 평가 생성"""
    assessment_date: date
    grade: PressureUlcerGrade
    push_length_width: int = Field(ge=0, le=10)
    push_exudate: int = Field(ge=0, le=3)
    push_tissue_type: int = Field(ge=0, le=4)
    length_cm: Optional[float] = None
    width_cm: Optional[float] = None
    depth_cm: Optional[float] = None
    note: Optional[str] = None


class CloseUlcerRequest(BaseModel):
    """욕창 종료 요청"""
    end_date: date
    end_reason: PressureUlcerEndReason
    end_reason_detail: Optional[str] = None


class PressureUlcerRecordCreate(BaseModel):
    """욕창 발생보고서 생성"""
    # 환자 정보
    patient_code: str = Field(..., description="환자 등록번호")
    patient_name: str = Field(..., description="환자명")
    patient_gender: str = Field(..., description="성별 (M/F)")
    room_number: str = Field(..., description="병실")
    patient_age_group: Optional[str] = Field(None, description="연령대")
    admission_date: Optional[date] = Field(None, description="입원일")

    # 욕창 정보
    location: PressureUlcerLocation = Field(..., description="발생 부위")
    location_detail: Optional[str] = Field(None, description="발생 부위 상세 (기타인 경우)")
    origin: PressureUlcerOrigin = Field(..., description="발생 시점")
    discovery_date: date = Field(..., description="발견일")
    grade: PressureUlcerGrade = Field(..., description="등급")

    # PUSH 점수
    push_length_width: int = Field(..., ge=0, le=10, description="Length x Width (0-10)")
    push_exudate: int = Field(..., ge=0, le=3, description="삼출물양 (0-3)")
    push_tissue_type: int = Field(..., ge=0, le=4, description="조직유형 (0-4)")
    length_cm: Optional[float] = Field(None, description="길이 (cm)")
    width_cm: Optional[float] = Field(None, description="너비 (cm)")
    depth_cm: Optional[float] = Field(None, description="깊이 (cm)")

    # 부서
    department: str = Field(..., description="병동")

    # 추가 정보
    risk_factors: Optional[str] = Field(None, description="위험 요인")
    treatment_plan: Optional[str] = Field(None, description="치료 계획")
    note: Optional[str] = Field(None, description="비고")

    # FMEA 위험 분류 (재원 중 발생 시에만 필수)
    fmea_severity: Optional[int] = Field(None, description="심각도 (1, 3, 5, 6, 8, 10)")
    fmea_probability: Optional[int] = Field(None, description="발생 가능성 (1, 3, 5, 7, 9)")
    fmea_detectability: Optional[int] = Field(None, description="발견 가능성 (1, 3, 5, 7, 9)")

    # 보고자 정보
    reporter_name: Optional[str] = Field(None, description="보고자명")


class TrendDataPoint(BaseModel):
    """추이 데이터 포인트"""
    date: date
    push_total: Optional[float] = None
    grade: Optional[str] = None
    grade_value: Optional[int] = None  # 숫자 표현 (시각화용)


class PressureUlcerTrendResponse(BaseModel):
    """추이 데이터 응답"""
    ulcer_id: str
    patient_code: str
    data_points: list[TrendDataPoint]


class PressureUlcerStatsResponse(BaseModel):
    """통계 요약 응답"""
    total_active: int
    total_healed: int
    total_closed: int
    acquired_count: int  # 재원 중 발생
    admission_count: int  # 입원 시 보유
    by_grade: dict[str, int]
    by_location: dict[str, int]
    by_department: dict[str, int]
    improvement_rate: Optional[float] = None  # 호전율


# ============ Labels ============

GRADE_LABELS = {
    "stage_1": "1단계",
    "stage_2": "2단계",
    "stage_3": "3단계",
    "stage_4": "4단계",
    "unstageable": "미분류",
    "dtpi": "심부조직손상",
}

LOCATION_LABELS = {
    "sacrum": "천골",
    "heel": "발뒤꿈치",
    "ischium": "좌골",
    "trochanter": "대전자",
    "elbow": "팔꿈치",
    "occiput": "후두부",
    "scapula": "견갑골",
    "ear": "귀",
    "other": "기타",
}

ORIGIN_LABELS = {
    "admission": "입원 시 보유",
    "acquired": "재원 중 발생",
    "unknown": "불명",
}

END_REASON_LABELS = {
    "healed": "치유",
    "death": "사망",
    "discharge": "퇴원",
    "transfer": "전원",
    "other": "기타",
}

GRADE_VALUES = {
    "stage_1": 1,
    "stage_2": 2,
    "stage_3": 3,
    "stage_4": 4,
    "unstageable": 0,
    "dtpi": 5,
}


# ============ Helper Functions ============

def can_access_management(user: User) -> bool:
    """Check if user can access pressure ulcer management."""
    return user.role in [Role.QPS_STAFF, Role.VICE_CHAIR, Role.DIRECTOR, Role.MASTER]


def calculate_push_total(length_width: int, exudate: int, tissue_type: int) -> float:
    """Calculate PUSH total score."""
    return float(length_width + exudate + tissue_type)


# ============ API Endpoints ============

@router.get(
    "/patients",
    response_model=PressureUlcerPatientListResponse,
    summary="Get pressure ulcer patient list",
)
async def list_pressure_ulcer_patients(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    active_only: bool = Query(True, description="활성 환자만 조회"),
    department: Optional[str] = Query(None, description="부서 필터"),
    origin: Optional[PressureUlcerOrigin] = Query(None, description="발생 시점 필터"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> PressureUlcerPatientListResponse:
    """
    Get list of pressure ulcer patients.

    - 활성 욕창 환자 목록 조회
    - 부서별, 발생 시점별 필터링 가능
    """
    if not can_access_management(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. QPS_STAFF+ role required.",
        )

    # Build query
    base_query = select(PressureUlcerRecord)

    if active_only:
        base_query = base_query.where(PressureUlcerRecord.is_active == True)

    if department:
        base_query = base_query.where(PressureUlcerRecord.department == department)

    if origin:
        base_query = base_query.where(PressureUlcerRecord.origin == origin)

    # Get total count
    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Get active/healed counts
    active_result = await db.execute(
        select(func.count()).where(PressureUlcerRecord.is_active == True)
    )
    active_count = active_result.scalar() or 0

    healed_result = await db.execute(
        select(func.count()).where(
            and_(
                PressureUlcerRecord.is_active == False,
                PressureUlcerRecord.end_reason == PressureUlcerEndReason.HEALED,
            )
        )
    )
    healed_count = healed_result.scalar() or 0

    # Get records with pagination
    query = base_query.order_by(
        PressureUlcerRecord.is_active.desc(),
        PressureUlcerRecord.discovery_date.desc(),
    ).offset(skip).limit(limit)

    result = await db.execute(query)
    records = result.scalars().all()

    # Get latest assessments for each record
    items = []
    for record in records:
        # Get latest assessment
        assessment_result = await db.execute(
            select(PressureUlcerAssessment)
            .where(PressureUlcerAssessment.ulcer_record_id == record.id)
            .order_by(PressureUlcerAssessment.assessment_date.desc())
            .limit(1)
        )
        latest_assessment = assessment_result.scalar_one_or_none()

        items.append(PressureUlcerPatientSummary(
            id=record.id,
            patient_code=record.patient_code,
            patient_name=record.patient_name,
            patient_gender=record.patient_gender,
            room_number=record.room_number,
            department=record.department,
            ulcer_id=record.ulcer_id,
            location=record.location.value,
            location_label=LOCATION_LABELS.get(record.location.value, record.location.value),
            origin=record.origin.value,
            origin_label=ORIGIN_LABELS.get(record.origin.value, record.origin.value),
            grade=record.grade.value if record.grade else None,
            grade_label=GRADE_LABELS.get(record.grade.value, "") if record.grade else None,
            discovery_date=record.discovery_date,
            push_total=record.push_total,
            latest_assessment_date=latest_assessment.assessment_date if latest_assessment else None,
            latest_push_total=latest_assessment.push_total if latest_assessment else None,
            is_active=record.is_active,
            end_reason=record.end_reason.value if record.end_reason else None,
            end_date=record.end_date,
        ))

    return PressureUlcerPatientListResponse(
        items=items,
        total=total,
        active_count=active_count,
        healed_count=healed_count,
    )


@router.post(
    "/patients",
    response_model=PressureUlcerPatientSummary,
    status_code=status.HTTP_201_CREATED,
    summary="Create pressure ulcer record (욕창발생보고서)",
)
async def create_pressure_ulcer_record(
    data: PressureUlcerRecordCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PressureUlcerPatientSummary:
    """
    Create a new pressure ulcer occurrence report (욕창발생보고서).

    - 입원 시 보유/재원 중 발생 모두 등록 가능
    - 재원 중 발생 시 FMEA 위험 분류 입력 필수
    """
    # Validate FMEA for acquired origin
    if data.origin == PressureUlcerOrigin.ACQUIRED:
        if not all([data.fmea_severity, data.fmea_probability, data.fmea_detectability]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="FMEA 위험 분류는 재원 중 발생 시 필수입니다 (심각도, 발생 가능성, 발견 가능성)",
            )
        # Validate FMEA values
        valid_severity = [1, 3, 5, 6, 8, 10]
        valid_probability = [1, 3, 5, 7, 9]
        valid_detectability = [1, 3, 5, 7, 9]
        if data.fmea_severity not in valid_severity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"심각도는 {valid_severity} 중 하나여야 합니다",
            )
        if data.fmea_probability not in valid_probability:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"발생 가능성은 {valid_probability} 중 하나여야 합니다",
            )
        if data.fmea_detectability not in valid_detectability:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"발견 가능성은 {valid_detectability} 중 하나여야 합니다",
            )

    # Generate ulcer_id (format: PU-YYYYMMDD-NNN)
    today_str = data.discovery_date.strftime("%Y%m%d")
    count_result = await db.execute(
        select(func.count())
        .where(PressureUlcerRecord.ulcer_id.like(f"PU-{today_str}-%"))
    )
    count = count_result.scalar() or 0
    ulcer_id = f"PU-{today_str}-{(count + 1):03d}"

    # Calculate PUSH total
    push_total = calculate_push_total(
        data.push_length_width,
        data.push_exudate,
        data.push_tissue_type,
    )

    # Calculate RPN if FMEA values provided
    fmea_rpn = None
    if data.fmea_severity and data.fmea_probability and data.fmea_detectability:
        fmea_rpn = data.fmea_severity * data.fmea_probability * data.fmea_detectability

    # Create record
    record = PressureUlcerRecord(
        patient_code=data.patient_code,
        patient_name=data.patient_name,
        patient_gender=data.patient_gender,
        room_number=data.room_number,
        patient_age_group=data.patient_age_group,
        admission_date=data.admission_date,
        ulcer_id=ulcer_id,
        location=data.location,
        location_detail=data.location_detail,
        origin=data.origin,
        discovery_date=data.discovery_date,
        grade=data.grade,
        push_length_width=data.push_length_width,
        push_exudate=data.push_exudate,
        push_tissue_type=data.push_tissue_type,
        push_total=push_total,
        length_cm=data.length_cm,
        width_cm=data.width_cm,
        depth_cm=data.depth_cm,
        department=data.department,
        risk_factors=data.risk_factors,
        treatment_plan=data.treatment_plan,
        note=data.note,
        fmea_severity=data.fmea_severity,
        fmea_probability=data.fmea_probability,
        fmea_detectability=data.fmea_detectability,
        fmea_rpn=fmea_rpn,
        reporter_id=current_user.id,
        reporter_name=data.reporter_name or current_user.name,
        reported_at=datetime.now(timezone.utc),
        is_active=True,
        is_healed=False,
    )

    db.add(record)
    await db.flush()
    await db.refresh(record)

    return PressureUlcerPatientSummary(
        id=record.id,
        patient_code=record.patient_code,
        patient_name=record.patient_name,
        patient_gender=record.patient_gender,
        room_number=record.room_number,
        department=record.department,
        ulcer_id=record.ulcer_id,
        location=record.location.value,
        location_label=LOCATION_LABELS.get(record.location.value, record.location.value),
        origin=record.origin.value,
        origin_label=ORIGIN_LABELS.get(record.origin.value, record.origin.value),
        grade=record.grade.value if record.grade else None,
        grade_label=GRADE_LABELS.get(record.grade.value, "") if record.grade else None,
        discovery_date=record.discovery_date,
        push_total=record.push_total,
        latest_assessment_date=None,
        latest_push_total=None,
        is_active=record.is_active,
        end_reason=None,
        end_date=None,
    )


@router.get(
    "/patients/{record_id}",
    response_model=PressureUlcerPatientDetail,
    summary="Get pressure ulcer patient detail",
)
async def get_pressure_ulcer_patient(
    record_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PressureUlcerPatientDetail:
    """
    Get detailed pressure ulcer patient information with all assessments.
    """
    if not can_access_management(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. QPS_STAFF+ role required.",
        )

    result = await db.execute(
        select(PressureUlcerRecord).where(PressureUlcerRecord.id == record_id)
    )
    record = result.scalar_one_or_none()

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pressure ulcer record not found",
        )

    # Get all assessments
    assessments_result = await db.execute(
        select(PressureUlcerAssessment)
        .where(PressureUlcerAssessment.ulcer_record_id == record_id)
        .order_by(PressureUlcerAssessment.assessment_date.desc())
    )
    assessments = assessments_result.scalars().all()

    assessment_responses = [
        PushAssessmentResponse(
            id=a.id,
            assessment_date=a.assessment_date,
            grade=a.grade.value,
            grade_label=GRADE_LABELS.get(a.grade.value, a.grade.value),
            previous_grade=a.previous_grade.value if a.previous_grade else None,
            push_length_width=a.push_length_width,
            push_exudate=a.push_exudate,
            push_tissue_type=a.push_tissue_type,
            push_total=a.push_total,
            length_cm=a.length_cm,
            width_cm=a.width_cm,
            depth_cm=a.depth_cm,
            is_improved=a.is_improved,
            is_worsened=a.is_worsened,
            note=a.note,
            created_at=a.created_at,
        )
        for a in assessments
    ]

    return PressureUlcerPatientDetail(
        id=record.id,
        incident_id=record.incident_id,
        patient_code=record.patient_code,
        patient_name=record.patient_name,
        patient_gender=record.patient_gender,
        room_number=record.room_number,
        patient_age_group=record.patient_age_group,
        admission_date=record.admission_date,
        department=record.department,
        ulcer_id=record.ulcer_id,
        location=record.location.value,
        location_detail=record.location_detail,
        origin=record.origin.value,
        discovery_date=record.discovery_date,
        grade=record.grade.value if record.grade else None,
        push_length_width=record.push_length_width,
        push_exudate=record.push_exudate,
        push_tissue_type=record.push_tissue_type,
        push_total=record.push_total,
        length_cm=record.length_cm,
        width_cm=record.width_cm,
        depth_cm=record.depth_cm,
        risk_factors=record.risk_factors,
        treatment_plan=record.treatment_plan,
        note=record.note,
        is_active=record.is_active,
        is_healed=record.is_healed,
        healed_date=record.healed_date,
        end_date=record.end_date,
        end_reason=record.end_reason.value if record.end_reason else None,
        end_reason_detail=record.end_reason_detail,
        created_at=record.created_at,
        updated_at=record.updated_at,
        assessments=assessment_responses,
    )


@router.post(
    "/patients/{record_id}/assessments",
    response_model=PushAssessmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add PUSH assessment",
)
async def create_push_assessment(
    record_id: int,
    data: PushAssessmentCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PushAssessmentResponse:
    """
    Add a new PUSH assessment for a pressure ulcer.

    PUSH Score components:
    - Length × Width (0-10)
    - Exudate Amount (0-3)
    - Tissue Type (0-4)
    """
    if not can_access_management(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. QPS_STAFF+ role required.",
        )

    # Get the record
    result = await db.execute(
        select(PressureUlcerRecord).where(PressureUlcerRecord.id == record_id)
    )
    record = result.scalar_one_or_none()

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pressure ulcer record not found",
        )

    if not record.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot add assessment to closed record",
        )

    # Get previous assessment
    prev_result = await db.execute(
        select(PressureUlcerAssessment)
        .where(PressureUlcerAssessment.ulcer_record_id == record_id)
        .order_by(PressureUlcerAssessment.assessment_date.desc())
        .limit(1)
    )
    prev_assessment = prev_result.scalar_one_or_none()

    # Calculate PUSH total
    push_total = calculate_push_total(
        data.push_length_width,
        data.push_exudate,
        data.push_tissue_type,
    )

    # Determine improvement/worsening
    is_improved = None
    is_worsened = None
    previous_grade = None

    if prev_assessment:
        previous_grade = prev_assessment.grade
        prev_push = prev_assessment.push_total or 0
        prev_grade_val = GRADE_VALUES.get(prev_assessment.grade.value, 0)
        curr_grade_val = GRADE_VALUES.get(data.grade.value, 0)

        # Improved: PUSH decreased by 1+ OR grade improved
        if push_total < prev_push - 0.5 or curr_grade_val < prev_grade_val:
            is_improved = True
            is_worsened = False
        # Worsened: PUSH increased by 1+ OR grade worsened
        elif push_total > prev_push + 0.5 or curr_grade_val > prev_grade_val:
            is_improved = False
            is_worsened = True
        else:
            is_improved = False
            is_worsened = False
    else:
        # First assessment - use initial record values
        if record.push_total:
            prev_push = record.push_total
            if push_total < prev_push - 0.5:
                is_improved = True
                is_worsened = False
            elif push_total > prev_push + 0.5:
                is_improved = False
                is_worsened = True

        if record.grade:
            previous_grade = record.grade

    # Create assessment
    assessment = PressureUlcerAssessment(
        ulcer_record_id=record_id,
        assessment_date=data.assessment_date,
        grade=data.grade,
        previous_grade=previous_grade,
        push_length_width=data.push_length_width,
        push_exudate=data.push_exudate,
        push_tissue_type=data.push_tissue_type,
        push_total=push_total,
        length_cm=data.length_cm,
        width_cm=data.width_cm,
        depth_cm=data.depth_cm,
        is_improved=is_improved,
        is_worsened=is_worsened,
        assessed_by=current_user.id,
        note=data.note,
    )

    db.add(assessment)
    await db.flush()
    await db.refresh(assessment)

    return PushAssessmentResponse(
        id=assessment.id,
        assessment_date=assessment.assessment_date,
        grade=assessment.grade.value,
        grade_label=GRADE_LABELS.get(assessment.grade.value, assessment.grade.value),
        previous_grade=assessment.previous_grade.value if assessment.previous_grade else None,
        push_length_width=assessment.push_length_width,
        push_exudate=assessment.push_exudate,
        push_tissue_type=assessment.push_tissue_type,
        push_total=assessment.push_total,
        length_cm=assessment.length_cm,
        width_cm=assessment.width_cm,
        depth_cm=assessment.depth_cm,
        is_improved=assessment.is_improved,
        is_worsened=assessment.is_worsened,
        note=assessment.note,
        created_at=assessment.created_at,
    )


@router.post(
    "/patients/{record_id}/close",
    response_model=PressureUlcerPatientSummary,
    summary="Close pressure ulcer record",
)
async def close_pressure_ulcer(
    record_id: int,
    data: CloseUlcerRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PressureUlcerPatientSummary:
    """
    Close a pressure ulcer record with end reason.

    End reasons:
    - healed: 치유
    - death: 사망
    - discharge: 퇴원
    - transfer: 전원
    - other: 기타
    """
    if not can_access_management(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. QPS_STAFF+ role required.",
        )

    result = await db.execute(
        select(PressureUlcerRecord).where(PressureUlcerRecord.id == record_id)
    )
    record = result.scalar_one_or_none()

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pressure ulcer record not found",
        )

    if not record.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Record is already closed",
        )

    # Update record
    record.is_active = False
    record.end_date = data.end_date
    record.end_reason = data.end_reason
    record.end_reason_detail = data.end_reason_detail

    if data.end_reason == PressureUlcerEndReason.HEALED:
        record.is_healed = True
        record.healed_date = data.end_date

    await db.flush()
    await db.refresh(record)

    return PressureUlcerPatientSummary(
        id=record.id,
        patient_code=record.patient_code,
        patient_name=record.patient_name,
        patient_gender=record.patient_gender,
        room_number=record.room_number,
        department=record.department,
        ulcer_id=record.ulcer_id,
        location=record.location.value,
        location_label=LOCATION_LABELS.get(record.location.value, record.location.value),
        origin=record.origin.value,
        origin_label=ORIGIN_LABELS.get(record.origin.value, record.origin.value),
        grade=record.grade.value if record.grade else None,
        grade_label=GRADE_LABELS.get(record.grade.value, "") if record.grade else None,
        discovery_date=record.discovery_date,
        push_total=record.push_total,
        latest_assessment_date=None,
        latest_push_total=None,
        is_active=record.is_active,
        end_reason=record.end_reason.value if record.end_reason else None,
        end_date=record.end_date,
    )


@router.get(
    "/patients/{record_id}/trend",
    response_model=PressureUlcerTrendResponse,
    summary="Get pressure ulcer trend data",
)
async def get_pressure_ulcer_trend(
    record_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PressureUlcerTrendResponse:
    """
    Get PUSH score and grade trend data for a pressure ulcer.
    """
    if not can_access_management(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. QPS_STAFF+ role required.",
        )

    result = await db.execute(
        select(PressureUlcerRecord).where(PressureUlcerRecord.id == record_id)
    )
    record = result.scalar_one_or_none()

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pressure ulcer record not found",
        )

    # Get all assessments ordered by date
    assessments_result = await db.execute(
        select(PressureUlcerAssessment)
        .where(PressureUlcerAssessment.ulcer_record_id == record_id)
        .order_by(PressureUlcerAssessment.assessment_date.asc())
    )
    assessments = assessments_result.scalars().all()

    # Build data points
    data_points = []

    # Add initial point from record
    if record.push_total is not None or record.grade is not None:
        data_points.append(TrendDataPoint(
            date=record.discovery_date,
            push_total=record.push_total,
            grade=record.grade.value if record.grade else None,
            grade_value=GRADE_VALUES.get(record.grade.value, None) if record.grade else None,
        ))

    # Add assessment points
    for a in assessments:
        data_points.append(TrendDataPoint(
            date=a.assessment_date,
            push_total=a.push_total,
            grade=a.grade.value,
            grade_value=GRADE_VALUES.get(a.grade.value, None),
        ))

    return PressureUlcerTrendResponse(
        ulcer_id=record.ulcer_id,
        patient_code=record.patient_code,
        data_points=data_points,
    )


@router.get(
    "/stats",
    response_model=PressureUlcerStatsResponse,
    summary="Get pressure ulcer statistics",
)
async def get_pressure_ulcer_stats(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    department: Optional[str] = Query(None, description="부서 필터"),
) -> PressureUlcerStatsResponse:
    """
    Get pressure ulcer statistics summary.
    """
    if not can_access_management(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. QPS_STAFF+ role required.",
        )

    base_query = select(PressureUlcerRecord)
    if department:
        base_query = base_query.where(PressureUlcerRecord.department == department)

    # Active count
    active_result = await db.execute(
        select(func.count())
        .select_from(PressureUlcerRecord)
        .where(
            and_(
                PressureUlcerRecord.is_active == True,
                PressureUlcerRecord.department == department if department else True,
            )
        )
    )
    total_active = active_result.scalar() or 0

    # Healed count
    healed_result = await db.execute(
        select(func.count())
        .select_from(PressureUlcerRecord)
        .where(
            and_(
                PressureUlcerRecord.end_reason == PressureUlcerEndReason.HEALED,
                PressureUlcerRecord.department == department if department else True,
            )
        )
    )
    total_healed = healed_result.scalar() or 0

    # Total closed
    closed_result = await db.execute(
        select(func.count())
        .select_from(PressureUlcerRecord)
        .where(
            and_(
                PressureUlcerRecord.is_active == False,
                PressureUlcerRecord.department == department if department else True,
            )
        )
    )
    total_closed = closed_result.scalar() or 0

    # By origin
    acquired_result = await db.execute(
        select(func.count())
        .select_from(PressureUlcerRecord)
        .where(
            and_(
                PressureUlcerRecord.origin == PressureUlcerOrigin.ACQUIRED,
                PressureUlcerRecord.department == department if department else True,
            )
        )
    )
    acquired_count = acquired_result.scalar() or 0

    admission_result = await db.execute(
        select(func.count())
        .select_from(PressureUlcerRecord)
        .where(
            and_(
                PressureUlcerRecord.origin == PressureUlcerOrigin.ADMISSION,
                PressureUlcerRecord.department == department if department else True,
            )
        )
    )
    admission_count = admission_result.scalar() or 0

    # By grade (active only)
    by_grade = {}
    for grade in PressureUlcerGrade:
        grade_result = await db.execute(
            select(func.count())
            .select_from(PressureUlcerRecord)
            .where(
                and_(
                    PressureUlcerRecord.is_active == True,
                    PressureUlcerRecord.grade == grade,
                    PressureUlcerRecord.department == department if department else True,
                )
            )
        )
        count = grade_result.scalar() or 0
        if count > 0:
            by_grade[GRADE_LABELS.get(grade.value, grade.value)] = count

    # By location (active only)
    by_location = {}
    for location in PressureUlcerLocation:
        loc_result = await db.execute(
            select(func.count())
            .select_from(PressureUlcerRecord)
            .where(
                and_(
                    PressureUlcerRecord.is_active == True,
                    PressureUlcerRecord.location == location,
                    PressureUlcerRecord.department == department if department else True,
                )
            )
        )
        count = loc_result.scalar() or 0
        if count > 0:
            by_location[LOCATION_LABELS.get(location.value, location.value)] = count

    # By department (active only)
    dept_result = await db.execute(
        select(
            PressureUlcerRecord.department,
            func.count(PressureUlcerRecord.id),
        )
        .where(PressureUlcerRecord.is_active == True)
        .group_by(PressureUlcerRecord.department)
    )
    by_department = {row[0]: row[1] for row in dept_result.all()}

    # Calculate improvement rate (this month's improved / last month's active)
    today = date.today()
    first_day_this_month = today.replace(day=1)
    last_month_end = first_day_this_month - timedelta(days=1)
    first_week_end = first_day_this_month + timedelta(days=6)

    # Get improved count in first week of this month
    improved_result = await db.execute(
        select(func.count())
        .select_from(PressureUlcerAssessment)
        .where(
            and_(
                PressureUlcerAssessment.assessment_date >= first_day_this_month,
                PressureUlcerAssessment.assessment_date <= first_week_end,
                PressureUlcerAssessment.is_improved == True,
            )
        )
    )
    improved_count = improved_result.scalar() or 0

    # Get active count at end of last month (excluding death/discharge)
    # This is an approximation - we count records that were active and not closed with death/discharge before month end
    last_month_active_result = await db.execute(
        select(func.count())
        .select_from(PressureUlcerRecord)
        .where(
            and_(
                PressureUlcerRecord.discovery_date <= last_month_end,
                or_(
                    PressureUlcerRecord.is_active == True,
                    PressureUlcerRecord.end_date > last_month_end,
                ),
                or_(
                    PressureUlcerRecord.end_reason.is_(None),
                    PressureUlcerRecord.end_reason.not_in([
                        PressureUlcerEndReason.DEATH,
                        PressureUlcerEndReason.DISCHARGE,
                    ]),
                ),
            )
        )
    )
    last_month_active = last_month_active_result.scalar() or 0

    improvement_rate = None
    if last_month_active > 0:
        improvement_rate = round((improved_count / last_month_active) * 100, 1)

    return PressureUlcerStatsResponse(
        total_active=total_active,
        total_healed=total_healed,
        total_closed=total_closed,
        acquired_count=acquired_count,
        admission_count=admission_count,
        by_grade=by_grade,
        by_location=by_location,
        by_department=by_department,
        improvement_rate=improvement_rate,
    )


# ============ Feature 13: Improvement Rate Calculation ============

class ImprovementRateRequest(BaseModel):
    """호전율 계산 요청"""
    year: int = Field(..., ge=2020, le=2100, description="계산 대상 연도")
    month: int = Field(..., ge=1, le=12, description="계산 대상 월")


class ImprovementRateResponse(BaseModel):
    """호전율 계산 결과"""
    year: int
    month: int
    numerator: int  # 호전 건수
    denominator: int  # 전월말 활성 건수
    rate: float  # 호전율 (%)
    improved_push: int  # PUSH 점수 호전
    improved_grade: int  # 등급 호전
    excluded_death: int  # 사망 제외 건수
    excluded_discharge: int  # 퇴원 제외 건수
    saved_to_indicator: bool  # 지표 저장 여부


@router.post(
    "/improvement-rate/calculate",
    response_model=ImprovementRateResponse,
    summary="Calculate improvement rate manually",
)
async def calculate_improvement_rate_manual(
    data: ImprovementRateRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ImprovementRateResponse:
    """
    수동으로 특정 월의 욕창 호전율을 계산합니다.

    - **year**: 계산 대상 연도
    - **month**: 계산 대상 월 (이 월의 첫째주 평가 기록 사용)

    호전 기준:
    - PUSH 점수 1점 이상 감소
    - Grade 호전 (예: Stage 3 → Stage 2)

    분모: 전월말 활성 욕창 수 (사망/퇴원 제외)
    분자: 당월 첫째주 호전 건수
    """
    # Admin/QPS only
    if current_user.role not in [Role.ADMIN, Role.MASTER, Role.QPS_STAFF, Role.DIRECTOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only QPS_STAFF, DIRECTOR, ADMIN, or MASTER can calculate improvement rate",
        )

    from app.tasks.pressure_ulcer_calculator import (
        calculate_pressure_ulcer_improvement_rate,
        save_improvement_rate_to_indicator,
    )

    # Calculate
    result = await calculate_pressure_ulcer_improvement_rate(
        db=db,
        year=data.year,
        month=data.month,
    )

    # Save to indicator
    saved = False
    try:
        await save_improvement_rate_to_indicator(
            db=db,
            year=data.year,
            month=data.month,
            result=result,
        )
        saved = True
    except Exception as e:
        # Log error but don't fail
        import logging
        logging.getLogger(__name__).warning(f"Failed to save indicator value: {e}")

    return ImprovementRateResponse(
        year=data.year,
        month=data.month,
        numerator=result["numerator"],
        denominator=result["denominator"],
        rate=result["rate"],
        improved_push=result["improved_push"],
        improved_grade=result["improved_grade"],
        excluded_death=result["excluded_death"],
        excluded_discharge=result["excluded_discharge"],
        saved_to_indicator=saved,
    )
