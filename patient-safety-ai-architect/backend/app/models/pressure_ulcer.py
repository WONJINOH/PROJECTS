"""
Pressure Ulcer (욕창) Management Models

욕창 관리 지표:
- 재원시 욕창발생률 (1000재원일당)
- 호전율 (PUSH↓ + Grade↓)
- 악화율 (PUSH↑ + Grade↑)
- 궤적분석
"""

import enum
from datetime import datetime, date
from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Date, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import ENUM

from app.database import Base


# PostgreSQL native enums - use lowercase values matching migration
pressureulcergrade_enum = ENUM(
    'stage_1', 'stage_2', 'stage_3', 'stage_4', 'unstageable', 'dtpi',
    name='pressureulcergrade', create_type=False
)
pressureulcerlocation_enum = ENUM(
    'sacrum', 'heel', 'ischium', 'trochanter', 'elbow', 'occiput', 'scapula', 'ear', 'other',
    name='pressureulcerlocation', create_type=False
)
pressureulcerorigin_enum = ENUM(
    'admission', 'acquired', 'unknown',
    name='pressureulcerorigin', create_type=False
)
pressureulcerendreason_enum = ENUM(
    'healed', 'death', 'discharge', 'transfer', 'other',
    name='pressureulcerendreason', create_type=False
)


class PressureUlcerGrade(str, enum.Enum):
    """욕창 등급 (NPUAP/EPUAP)"""
    STAGE_1 = "stage_1"          # 1단계: 발적
    STAGE_2 = "stage_2"          # 2단계: 부분층 손실
    STAGE_3 = "stage_3"          # 3단계: 전층 손실
    STAGE_4 = "stage_4"          # 4단계: 전층 조직 손실
    UNSTAGEABLE = "unstageable"  # 미분류
    DTPI = "dtpi"                # 심부조직손상


class PressureUlcerLocation(str, enum.Enum):
    """욕창 발생 부위"""
    SACRUM = "sacrum"            # 천골
    HEEL = "heel"                # 발뒤꿈치
    ISCHIUM = "ischium"          # 좌골
    TROCHANTER = "trochanter"    # 대전자
    ELBOW = "elbow"              # 팔꿈치
    OCCIPUT = "occiput"          # 후두부
    SCAPULA = "scapula"          # 견갑골
    EAR = "ear"                  # 귀
    OTHER = "other"              # 기타


class PressureUlcerOrigin(str, enum.Enum):
    """욕창 발생 시점"""
    ADMISSION = "admission"      # 입원 시 보유
    ACQUIRED = "acquired"        # 재원 중 발생
    UNKNOWN = "unknown"          # 불명


class PressureUlcerEndReason(str, enum.Enum):
    """욕창 종료 사유"""
    HEALED = "healed"            # 치유
    DEATH = "death"              # 사망
    DISCHARGE = "discharge"      # 퇴원
    TRANSFER = "transfer"        # 전원
    OTHER = "other"              # 기타


class PressureUlcerRecord(Base):
    """욕창 기록"""

    __tablename__ = "pressure_ulcer_records"

    id = Column(Integer, primary_key=True, index=True)

    # 사고 연결 (PSR 시스템)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=True, index=True)

    # 환자 정보 (익명화)
    patient_code = Column(String(50), nullable=False, index=True)  # 익명 코드
    patient_name = Column(String(100), nullable=True)  # 환자명
    patient_gender = Column(String(10), nullable=True)  # 성별
    room_number = Column(String(50), nullable=True)  # 병실
    patient_age_group = Column(String(20), nullable=True)
    admission_date = Column(Date, nullable=True)

    # 욕창 정보
    ulcer_id = Column(String(50), nullable=False)  # 욕창별 고유 ID
    location = Column(pressureulcerlocation_enum, nullable=False)
    location_detail = Column(String(100), nullable=True)  # 발생 부위 상세 (기타인 경우)
    origin = Column(pressureulcerorigin_enum, nullable=False, index=True)
    discovery_date = Column(Date, nullable=False, index=True)

    # 초기 등급
    grade = Column(pressureulcergrade_enum, nullable=True)

    # 초기 PUSH Score (발견 시)
    push_length_width = Column(Integer, nullable=True)  # 0-10
    push_exudate = Column(Integer, nullable=True)       # 0-3
    push_tissue_type = Column(Integer, nullable=True)   # 0-4
    push_total = Column(Float, nullable=True)           # 총점 0-17

    # 크기
    length_cm = Column(Float, nullable=True)
    width_cm = Column(Float, nullable=True)
    depth_cm = Column(Float, nullable=True)

    # 부서
    department = Column(String(100), nullable=False, index=True)

    # 추가 정보
    risk_factors = Column(Text, nullable=True)  # 위험 요인
    treatment_plan = Column(Text, nullable=True)  # 치료 계획
    note = Column(Text, nullable=True)  # 비고

    # FMEA 위험 분류 (재원 중 발생 시에만 사용)
    fmea_severity = Column(Integer, nullable=True)  # 심각도: 1, 3, 5, 6, 8, 10
    fmea_probability = Column(Integer, nullable=True)  # 발생 가능성: 1, 3, 5, 7, 9
    fmea_detectability = Column(Integer, nullable=True)  # 발견 가능성: 1, 3, 5, 7, 9
    fmea_rpn = Column(Integer, nullable=True)  # RPN = S x O x D

    # 보고자 정보
    reporter_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    reporter_name = Column(String(100), nullable=True)
    reported_at = Column(DateTime, nullable=True)

    # 상태
    is_healed = Column(Boolean, default=False)
    healed_date = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True)

    # 종료 사유 (Feature 12)
    end_date = Column(Date, nullable=True)
    end_reason = Column(pressureulcerendreason_enum, nullable=True)
    end_reason_detail = Column(String(200), nullable=True)  # 기타인 경우 상세

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<PressureUlcer {self.ulcer_id} - {self.location}>"


class PressureUlcerAssessment(Base):
    """욕창 평가 기록 (PUSH Score 등)"""

    __tablename__ = "pressure_ulcer_assessments"

    id = Column(Integer, primary_key=True, index=True)

    # 욕창 연결
    ulcer_record_id = Column(Integer, ForeignKey("pressure_ulcer_records.id"), nullable=False)

    # 평가일
    assessment_date = Column(Date, nullable=False, index=True)

    # 등급
    grade = Column(pressureulcergrade_enum, nullable=False)
    previous_grade = Column(pressureulcergrade_enum, nullable=True)

    # PUSH Score (Pressure Ulcer Scale for Healing)
    push_length_width = Column(Integer, nullable=True)  # 0-10
    push_exudate = Column(Integer, nullable=True)       # 0-3
    push_tissue_type = Column(Integer, nullable=True)   # 0-4
    push_total = Column(Float, nullable=True)           # 총점 0-17

    # 크기
    length_cm = Column(Float, nullable=True)
    width_cm = Column(Float, nullable=True)
    depth_cm = Column(Float, nullable=True)

    # 상태 변화
    is_improved = Column(Boolean, nullable=True)   # 호전
    is_worsened = Column(Boolean, nullable=True)   # 악화

    # 평가자
    assessed_by = Column(Integer, nullable=True)
    note = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<PUAssessment {self.assessment_date} - Grade {self.grade.value}>"


class PressureUlcerMonthlyStats(Base):
    """욕창 월간 통계"""

    __tablename__ = "pressure_ulcer_monthly_stats"

    id = Column(Integer, primary_key=True, index=True)

    # 기간
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)

    # 부서 (전체인 경우 NULL)
    department = Column(String(100), nullable=True, index=True)

    # 재원일수
    total_patient_days = Column(Integer, default=0)

    # 발생 건수
    new_cases = Column(Integer, default=0)          # 신규 발생
    admission_cases = Column(Integer, default=0)    # 입원 시 보유

    # 발생률 (1000재원일당)
    incidence_rate = Column(Float, nullable=True)

    # 호전/악화
    improved_count = Column(Integer, default=0)     # 호전
    worsened_count = Column(Integer, default=0)     # 악화
    healed_count = Column(Integer, default=0)       # 치유

    # 호전율/악화율
    improvement_rate = Column(Float, nullable=True)
    worsening_rate = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<PUMonthlyStats {self.year}-{self.month}>"
