"""Add missing detail tables (fall, medication, indicator)

Revision ID: 005
Revises: 004
Create Date: 2026-01-26 10:00:00

Creates tables that were defined in models but missing from migrations:
- fall_details: 낙상 상세 기록
- fall_monthly_stats: 낙상 월간 통계
- medication_error_details: 투약 오류 상세 기록
- medication_monthly_stats: 투약 월간 통계
- indicator_configs: 지표 설정
- indicator_values: 지표 실측값
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '005'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create missing detail tables."""

    # === Fall-related Enum Types ===
    fall_injury_level_enum = postgresql.ENUM(
        'none', 'minor', 'moderate', 'major', 'death',
        name='fallinjurylevel', create_type=False
    )
    fall_injury_level_enum.create(op.get_bind(), checkfirst=True)

    fall_risk_level_enum = postgresql.ENUM(
        'low', 'moderate', 'high',
        name='fallrisklevel', create_type=False
    )
    fall_risk_level_enum.create(op.get_bind(), checkfirst=True)

    fall_location_enum = postgresql.ENUM(
        'bed', 'bathroom', 'hallway', 'wheelchair', 'chair', 'rehabilitation', 'other',
        name='falllocation', create_type=False
    )
    fall_location_enum.create(op.get_bind(), checkfirst=True)

    fall_cause_enum = postgresql.ENUM(
        'slip', 'trip', 'loss_of_balance', 'fainting', 'weakness',
        'cognitive', 'medication', 'environment', 'other',
        name='fallcause', create_type=False
    )
    fall_cause_enum.create(op.get_bind(), checkfirst=True)

    fall_consciousness_level_enum = postgresql.ENUM(
        'alert', 'drowsy', 'stupor', 'semicoma', 'coma',
        name='fallconsciousnesslevel', create_type=False
    )
    fall_consciousness_level_enum.create(op.get_bind(), checkfirst=True)

    fall_activity_level_enum = postgresql.ENUM(
        'independent', 'needs_assistance', 'dependent',
        name='fallactivitylevel', create_type=False
    )
    fall_activity_level_enum.create(op.get_bind(), checkfirst=True)

    fall_mobility_aid_enum = postgresql.ENUM(
        'none', 'wheelchair', 'walker', 'cane', 'crutch', 'other',
        name='fallmobilityaid', create_type=False
    )
    fall_mobility_aid_enum.create(op.get_bind(), checkfirst=True)

    fall_type_enum = postgresql.ENUM(
        'bed_fall', 'standing_fall', 'sitting_fall', 'walking_fall', 'transfer_fall', 'other',
        name='falltype', create_type=False
    )
    fall_type_enum.create(op.get_bind(), checkfirst=True)

    fall_physical_injury_enum = postgresql.ENUM(
        'none', 'abrasion', 'contusion', 'laceration', 'hematoma',
        'fracture', 'head_injury', 'other',
        name='fallphysicalinjury', create_type=False
    )
    fall_physical_injury_enum.create(op.get_bind(), checkfirst=True)

    fall_treatment_enum = postgresql.ENUM(
        'observation', 'dressing', 'suture', 'cast_splint',
        'imaging', 'surgery', 'transfer', 'other',
        name='falltreatment', create_type=False
    )
    fall_treatment_enum.create(op.get_bind(), checkfirst=True)

    # === Medication-related Enum Types ===
    medication_error_type_enum = postgresql.ENUM(
        'wrong_patient', 'wrong_drug', 'wrong_dose', 'wrong_route',
        'wrong_time', 'wrong_rate', 'omission', 'unauthorized',
        'deteriorated', 'monitoring', 'other',
        name='medicationerrortype', create_type=False
    )
    medication_error_type_enum.create(op.get_bind(), checkfirst=True)

    medication_error_stage_enum = postgresql.ENUM(
        'prescribing', 'transcribing', 'dispensing', 'administering', 'monitoring',
        name='medicationerrorstage', create_type=False
    )
    medication_error_stage_enum.create(op.get_bind(), checkfirst=True)

    medication_error_severity_enum = postgresql.ENUM(
        'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I',
        name='medicationerrorseverity', create_type=False
    )
    medication_error_severity_enum.create(op.get_bind(), checkfirst=True)

    high_alert_medication_enum = postgresql.ENUM(
        'anticoagulant', 'insulin', 'opioid', 'chemotherapy',
        'sedative', 'potassium', 'neuromuscular', 'other',
        name='highalertmedication', create_type=False
    )
    high_alert_medication_enum.create(op.get_bind(), checkfirst=True)

    medication_discovery_timing_enum = postgresql.ENUM(
        'pre_administration', 'post_administration',
        name='medicationdiscoverytiming', create_type=False
    )
    medication_discovery_timing_enum.create(op.get_bind(), checkfirst=True)

    medication_error_cause_enum = postgresql.ENUM(
        'communication', 'name_confusion', 'labeling', 'storage',
        'standardization', 'device_design', 'distraction', 'workload',
        'staff_shortage', 'training', 'patient_education',
        'verification_failure', 'prescription_error', 'transcription_error',
        'dispensing_error', 'other',
        name='medicationerrorcause', create_type=False
    )
    medication_error_cause_enum.create(op.get_bind(), checkfirst=True)

    # === Indicator-related Enum Types ===
    indicator_category_enum = postgresql.ENUM(
        'psr', 'pressure_ulcer', 'fall', 'medication', 'restraint',
        'infection', 'staff_safety', 'lab_tat', 'composite',
        name='indicatorcategory', create_type=False
    )
    indicator_category_enum.create(op.get_bind(), checkfirst=True)

    threshold_direction_enum = postgresql.ENUM(
        'higher_is_better', 'lower_is_better',
        name='thresholddirection', create_type=False
    )
    threshold_direction_enum.create(op.get_bind(), checkfirst=True)

    period_type_enum = postgresql.ENUM(
        'daily', 'weekly', 'monthly', 'quarterly', 'yearly',
        name='periodtype', create_type=False
    )
    period_type_enum.create(op.get_bind(), checkfirst=True)

    chart_type_enum = postgresql.ENUM(
        'line', 'bar', 'pie', 'area',
        name='charttype', create_type=False
    )
    chart_type_enum.create(op.get_bind(), checkfirst=True)

    indicator_status_enum = postgresql.ENUM(
        'active', 'inactive', 'planned',
        name='indicatorstatus', create_type=False
    )
    indicator_status_enum.create(op.get_bind(), checkfirst=True)

    # === Create fall_details Table ===
    op.create_table(
        'fall_details',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('incident_id', sa.Integer(), sa.ForeignKey('incidents.id'), nullable=False),
        # Patient info
        sa.Column('patient_code', sa.String(50), nullable=False, index=True),
        sa.Column('patient_age_group', sa.String(20), nullable=True),
        sa.Column('patient_gender', sa.String(10), nullable=True),
        # Pre-fall risk
        sa.Column('pre_fall_risk_level', fall_risk_level_enum, nullable=True),
        sa.Column('morse_score', sa.Integer(), nullable=True),
        # PSR fields
        sa.Column('consciousness_level', fall_consciousness_level_enum, nullable=True, index=True),
        sa.Column('activity_level', fall_activity_level_enum, nullable=True, index=True),
        sa.Column('uses_mobility_aid', sa.Boolean(), default=False),
        sa.Column('mobility_aid_type', fall_mobility_aid_enum, nullable=True),
        sa.Column('risk_factors', sa.JSON(), nullable=True),
        sa.Column('related_medications', sa.JSON(), nullable=True),
        sa.Column('fall_type', fall_type_enum, nullable=True, index=True),
        # Fall details
        sa.Column('fall_location', fall_location_enum, nullable=False),
        sa.Column('fall_location_detail', sa.String(200), nullable=True),
        sa.Column('fall_cause', fall_cause_enum, nullable=False),
        sa.Column('fall_cause_detail', sa.Text(), nullable=True),
        # Time
        sa.Column('occurred_hour', sa.Integer(), nullable=True),
        sa.Column('shift', sa.String(20), nullable=True),
        # Injury
        sa.Column('injury_level', fall_injury_level_enum, nullable=False, index=True),
        sa.Column('injury_description', sa.Text(), nullable=True),
        sa.Column('physical_injury_type', fall_physical_injury_enum, nullable=True, index=True),
        sa.Column('physical_injury_detail', sa.String(200), nullable=True),
        # Treatment
        sa.Column('treatments_provided', sa.JSON(), nullable=True),
        sa.Column('treatment_detail', sa.Text(), nullable=True),
        # Activity
        sa.Column('activity_at_fall', sa.String(200), nullable=True),
        sa.Column('was_supervised', sa.Boolean(), default=False),
        sa.Column('had_fall_prevention', sa.Boolean(), default=False),
        # Department
        sa.Column('department', sa.String(100), nullable=False, index=True),
        # Recurrence
        sa.Column('is_recurrence', sa.Boolean(), default=False),
        sa.Column('previous_fall_count', sa.Integer(), default=0),
        # Metadata
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_fall_details_incident_id', 'fall_details', ['incident_id'])

    # === Create fall_monthly_stats Table ===
    op.create_table(
        'fall_monthly_stats',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('month', sa.Integer(), nullable=False),
        sa.Column('department', sa.String(100), nullable=True, index=True),
        sa.Column('total_patient_days', sa.Integer(), default=0),
        sa.Column('total_falls', sa.Integer(), default=0),
        sa.Column('falls_no_injury', sa.Integer(), default=0),
        sa.Column('falls_minor_injury', sa.Integer(), default=0),
        sa.Column('falls_moderate_injury', sa.Integer(), default=0),
        sa.Column('falls_major_injury', sa.Integer(), default=0),
        sa.Column('falls_death', sa.Integer(), default=0),
        sa.Column('fall_rate', sa.Float(), nullable=True),
        sa.Column('fall_with_injury_rate', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # === Create medication_error_details Table ===
    op.create_table(
        'medication_error_details',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('incident_id', sa.Integer(), sa.ForeignKey('incidents.id'), nullable=False),
        # Patient info
        sa.Column('patient_code', sa.String(50), nullable=False, index=True),
        sa.Column('patient_age_group', sa.String(20), nullable=True),
        # Error info
        sa.Column('error_type', medication_error_type_enum, nullable=False, index=True),
        sa.Column('error_stage', medication_error_stage_enum, nullable=False, index=True),
        sa.Column('error_severity', medication_error_severity_enum, nullable=False, index=True),
        # Near miss
        sa.Column('is_near_miss', sa.Boolean(), default=False, index=True),
        # Medication info
        sa.Column('medication_category', sa.String(100), nullable=True),
        sa.Column('is_high_alert', sa.Boolean(), default=False),
        sa.Column('high_alert_type', high_alert_medication_enum, nullable=True),
        # Intended vs actual
        sa.Column('intended_dose', sa.String(100), nullable=True),
        sa.Column('actual_dose', sa.String(100), nullable=True),
        sa.Column('intended_route', sa.String(50), nullable=True),
        sa.Column('actual_route', sa.String(50), nullable=True),
        # Discovery
        sa.Column('discovered_by_role', sa.String(50), nullable=True),
        sa.Column('discovery_method', sa.String(100), nullable=True),
        sa.Column('discovery_timing', medication_discovery_timing_enum, nullable=True, index=True),
        # Causes
        sa.Column('error_causes', sa.JSON(), nullable=True),
        sa.Column('error_cause_detail', sa.Text(), nullable=True),
        # Department
        sa.Column('department', sa.String(100), nullable=False, index=True),
        # Barcode
        sa.Column('barcode_scanned', sa.Boolean(), nullable=True),
        # Contributing factors
        sa.Column('contributing_factors', sa.Text(), nullable=True),
        # Metadata
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_medication_error_details_incident_id', 'medication_error_details', ['incident_id'])

    # === Create medication_monthly_stats Table ===
    op.create_table(
        'medication_monthly_stats',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('month', sa.Integer(), nullable=False),
        sa.Column('department', sa.String(100), nullable=True, index=True),
        sa.Column('total_administrations', sa.Integer(), default=0),
        sa.Column('total_errors', sa.Integer(), default=0),
        sa.Column('near_miss_count', sa.Integer(), default=0),
        sa.Column('actual_error_count', sa.Integer(), default=0),
        sa.Column('prescribing_errors', sa.Integer(), default=0),
        sa.Column('transcribing_errors', sa.Integer(), default=0),
        sa.Column('dispensing_errors', sa.Integer(), default=0),
        sa.Column('administering_errors', sa.Integer(), default=0),
        sa.Column('high_alert_errors', sa.Integer(), default=0),
        sa.Column('error_rate', sa.Float(), nullable=True),
        sa.Column('near_miss_capture_rate', sa.Float(), nullable=True),
        sa.Column('barcode_scan_rate', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # === Create indicator_configs Table ===
    op.create_table(
        'indicator_configs',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('code', sa.String(50), unique=True, nullable=False, index=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', indicator_category_enum, nullable=False, index=True),
        sa.Column('calculation_formula', sa.Text(), nullable=True),
        sa.Column('numerator_name', sa.String(500), nullable=True),
        sa.Column('denominator_name', sa.String(500), nullable=True),
        sa.Column('unit', sa.String(50), default='건'),
        sa.Column('target_value', sa.Float(), nullable=True),
        sa.Column('warning_threshold', sa.Float(), nullable=True),
        sa.Column('critical_threshold', sa.Float(), nullable=True),
        sa.Column('threshold_direction', threshold_direction_enum, nullable=True),
        sa.Column('period_type', period_type_enum, default='monthly'),
        sa.Column('chart_type', chart_type_enum, default='line'),
        sa.Column('is_key_indicator', sa.Boolean(), default=False),
        sa.Column('display_order', sa.Integer(), default=0),
        sa.Column('data_source', sa.String(200), nullable=True),
        sa.Column('auto_calculate', sa.Boolean(), default=False),
        sa.Column('status', indicator_status_enum, default='active'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
    )

    # === Create indicator_values Table ===
    op.create_table(
        'indicator_values',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('indicator_id', sa.Integer(), sa.ForeignKey('indicator_configs.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('period_start', sa.DateTime(), nullable=False, index=True),
        sa.Column('period_end', sa.DateTime(), nullable=False),
        sa.Column('value', sa.Float(), nullable=False),
        sa.Column('numerator', sa.Float(), nullable=True),
        sa.Column('denominator', sa.Float(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('is_verified', sa.Boolean(), default=False),
        sa.Column('verified_by_id', sa.Integer(), nullable=True),
        sa.Column('verified_at', sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    """Drop created tables and enum types."""
    # Drop tables
    op.drop_table('indicator_values')
    op.drop_table('indicator_configs')
    op.drop_table('medication_monthly_stats')
    op.drop_table('medication_error_details')
    op.drop_table('fall_monthly_stats')
    op.drop_table('fall_details')

    # Drop indicator enum types
    op.execute('DROP TYPE IF EXISTS indicatorstatus')
    op.execute('DROP TYPE IF EXISTS charttype')
    op.execute('DROP TYPE IF EXISTS periodtype')
    op.execute('DROP TYPE IF EXISTS thresholddirection')
    op.execute('DROP TYPE IF EXISTS indicatorcategory')

    # Drop medication enum types
    op.execute('DROP TYPE IF EXISTS medicationerrorcause')
    op.execute('DROP TYPE IF EXISTS medicationdiscoverytiming')
    op.execute('DROP TYPE IF EXISTS highalertmedication')
    op.execute('DROP TYPE IF EXISTS medicationerrorseverity')
    op.execute('DROP TYPE IF EXISTS medicationerrorstage')
    op.execute('DROP TYPE IF EXISTS medicationerrortype')

    # Drop fall enum types
    op.execute('DROP TYPE IF EXISTS falltreatment')
    op.execute('DROP TYPE IF EXISTS fallphysicalinjury')
    op.execute('DROP TYPE IF EXISTS falltype')
    op.execute('DROP TYPE IF EXISTS fallmobilityaid')
    op.execute('DROP TYPE IF EXISTS fallactivitylevel')
    op.execute('DROP TYPE IF EXISTS fallconsciousnesslevel')
    op.execute('DROP TYPE IF EXISTS fallcause')
    op.execute('DROP TYPE IF EXISTS falllocation')
    op.execute('DROP TYPE IF EXISTS fallrisklevel')
    op.execute('DROP TYPE IF EXISTS fallinjurylevel')
