"""Phase E: 욕창 관리 - 테이블 생성 및 종료 사유 필드 추가

Revision ID: 010
Revises: 009
Create Date: 2026-01-27 16:00:00.000000

Changes:
- Create PressureUlcerGrade enum type
- Create PressureUlcerLocation enum type
- Create PressureUlcerOrigin enum type
- Create PressureUlcerEndReason enum type
- Create pressure_ulcer_records table
- Create pressure_ulcer_assessments table
- Create pressure_ulcer_monthly_stats table
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '010'
down_revision = '009'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enums using raw SQL to avoid checkfirst issues with asyncpg
    op.execute("CREATE TYPE pressureulcergrade AS ENUM ('stage_1', 'stage_2', 'stage_3', 'stage_4', 'unstageable', 'dtpi')")
    op.execute("CREATE TYPE pressureulcerlocation AS ENUM ('sacrum', 'heel', 'ischium', 'trochanter', 'elbow', 'occiput', 'scapula', 'ear', 'other')")
    op.execute("CREATE TYPE pressureulcerorigin AS ENUM ('admission', 'acquired', 'unknown')")
    op.execute("CREATE TYPE pressureulcerendreason AS ENUM ('healed', 'death', 'discharge', 'transfer', 'other')")

    # Create pressure_ulcer_records table
    op.create_table(
        'pressure_ulcer_records',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('incident_id', sa.Integer(), sa.ForeignKey('incidents.id'), nullable=True, index=True),
        sa.Column('patient_code', sa.String(50), nullable=False, index=True),
        sa.Column('patient_name', sa.String(100), nullable=True),
        sa.Column('patient_gender', sa.String(10), nullable=True),
        sa.Column('room_number', sa.String(50), nullable=True),
        sa.Column('patient_age_group', sa.String(20), nullable=True),
        sa.Column('admission_date', sa.Date(), nullable=True),
        sa.Column('ulcer_id', sa.String(50), nullable=False),
        sa.Column('location', postgresql.ENUM('sacrum', 'heel', 'ischium', 'trochanter', 'elbow', 'occiput', 'scapula', 'ear', 'other', name='pressureulcerlocation', create_type=False), nullable=False),
        sa.Column('location_detail', sa.String(100), nullable=True),
        sa.Column('origin', postgresql.ENUM('admission', 'acquired', 'unknown', name='pressureulcerorigin', create_type=False), nullable=False, index=True),
        sa.Column('discovery_date', sa.Date(), nullable=False, index=True),
        sa.Column('grade', postgresql.ENUM('stage_1', 'stage_2', 'stage_3', 'stage_4', 'unstageable', 'dtpi', name='pressureulcergrade', create_type=False), nullable=True),
        sa.Column('push_length_width', sa.Integer(), nullable=True),
        sa.Column('push_exudate', sa.Integer(), nullable=True),
        sa.Column('push_tissue_type', sa.Integer(), nullable=True),
        sa.Column('push_total', sa.Float(), nullable=True),
        sa.Column('length_cm', sa.Float(), nullable=True),
        sa.Column('width_cm', sa.Float(), nullable=True),
        sa.Column('depth_cm', sa.Float(), nullable=True),
        sa.Column('department', sa.String(100), nullable=False, index=True),
        sa.Column('risk_factors', sa.Text(), nullable=True),
        sa.Column('treatment_plan', sa.Text(), nullable=True),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('is_healed', sa.Boolean(), default=False),
        sa.Column('healed_date', sa.Date(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('end_reason', postgresql.ENUM('healed', 'death', 'discharge', 'transfer', 'other', name='pressureulcerendreason', create_type=False), nullable=True),
        sa.Column('end_reason_detail', sa.String(200), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )

    # Create pressure_ulcer_assessments table
    op.create_table(
        'pressure_ulcer_assessments',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('ulcer_record_id', sa.Integer(), sa.ForeignKey('pressure_ulcer_records.id'), nullable=False),
        sa.Column('assessment_date', sa.Date(), nullable=False, index=True),
        sa.Column('grade', postgresql.ENUM('stage_1', 'stage_2', 'stage_3', 'stage_4', 'unstageable', 'dtpi', name='pressureulcergrade', create_type=False), nullable=False),
        sa.Column('previous_grade', postgresql.ENUM('stage_1', 'stage_2', 'stage_3', 'stage_4', 'unstageable', 'dtpi', name='pressureulcergrade', create_type=False), nullable=True),
        sa.Column('push_length_width', sa.Integer(), nullable=True),
        sa.Column('push_exudate', sa.Integer(), nullable=True),
        sa.Column('push_tissue_type', sa.Integer(), nullable=True),
        sa.Column('push_total', sa.Float(), nullable=True),
        sa.Column('length_cm', sa.Float(), nullable=True),
        sa.Column('width_cm', sa.Float(), nullable=True),
        sa.Column('depth_cm', sa.Float(), nullable=True),
        sa.Column('is_improved', sa.Boolean(), nullable=True),
        sa.Column('is_worsened', sa.Boolean(), nullable=True),
        sa.Column('assessed_by', sa.Integer(), nullable=True),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )

    # Create pressure_ulcer_monthly_stats table
    op.create_table(
        'pressure_ulcer_monthly_stats',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('month', sa.Integer(), nullable=False),
        sa.Column('department', sa.String(100), nullable=True, index=True),
        sa.Column('total_patient_days', sa.Integer(), default=0),
        sa.Column('new_cases', sa.Integer(), default=0),
        sa.Column('admission_cases', sa.Integer(), default=0),
        sa.Column('incidence_rate', sa.Float(), nullable=True),
        sa.Column('improved_count', sa.Integer(), default=0),
        sa.Column('worsened_count', sa.Integer(), default=0),
        sa.Column('healed_count', sa.Integer(), default=0),
        sa.Column('improvement_rate', sa.Float(), nullable=True),
        sa.Column('worsening_rate', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    # Drop tables
    op.drop_table('pressure_ulcer_monthly_stats')
    op.drop_table('pressure_ulcer_assessments')
    op.drop_table('pressure_ulcer_records')

    # Drop enums
    op.execute("DROP TYPE IF EXISTS pressureulcerendreason")
    op.execute("DROP TYPE IF EXISTS pressureulcerorigin")
    op.execute("DROP TYPE IF EXISTS pressureulcerlocation")
    op.execute("DROP TYPE IF EXISTS pressureulcergrade")
