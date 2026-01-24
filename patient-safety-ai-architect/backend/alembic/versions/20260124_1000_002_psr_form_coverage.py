"""PSR Form Coverage - Extended categories and detail tables

Revision ID: 002
Revises: 001
Create Date: 2026-01-24 10:00:00

Extends PSR (Patient Safety Report) form coverage:
- Add new incident categories (thermal_injury, procedure, environment, security, etc.)
- Add new fields to incidents table (improvement_types, policy_factor, management_factors)
- Create 5 new detail tables:
  - transfusion_details: 수혈사고 상세
  - thermal_injury_details: 열냉사고 상세
  - procedure_details: 검사/시술/치료 상세
  - environment_details: 환경 사고 상세
  - security_details: 보안 사고 상세
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create PSR form coverage tables and update existing tables."""

    # === Step 1: Extend IncidentCategory Enum ===
    # Note: PostgreSQL doesn't support ALTER TYPE ADD VALUE in transactions easily
    # We need to add each value separately
    op.execute("ALTER TYPE incidentcategory ADD VALUE IF NOT EXISTS 'thermal_injury'")
    op.execute("ALTER TYPE incidentcategory ADD VALUE IF NOT EXISTS 'procedure'")
    op.execute("ALTER TYPE incidentcategory ADD VALUE IF NOT EXISTS 'environment'")
    op.execute("ALTER TYPE incidentcategory ADD VALUE IF NOT EXISTS 'security'")
    op.execute("ALTER TYPE incidentcategory ADD VALUE IF NOT EXISTS 'elopement'")
    op.execute("ALTER TYPE incidentcategory ADD VALUE IF NOT EXISTS 'violence'")
    op.execute("ALTER TYPE incidentcategory ADD VALUE IF NOT EXISTS 'fire'")
    op.execute("ALTER TYPE incidentcategory ADD VALUE IF NOT EXISTS 'suicide'")
    op.execute("ALTER TYPE incidentcategory ADD VALUE IF NOT EXISTS 'self_harm'")

    # === Step 2: Create New Enum Types ===

    # ImprovementType
    improvement_type_enum = postgresql.ENUM(
        'policy_update', 'process_improvement', 'training', 'facility_improvement',
        name='improvementtype', create_type=True
    )
    improvement_type_enum.create(op.get_bind(), checkfirst=True)

    # PolicyFactorType
    policy_factor_type_enum = postgresql.ENUM(
        'no_policy', 'not_trained', 'trained_not_followed', 'unavoidable', 'other',
        name='policyfactortype', create_type=True
    )
    policy_factor_type_enum.create(op.get_bind(), checkfirst=True)

    # ManagementFactorType
    management_factor_type_enum = postgresql.ENUM(
        'facility', 'equipment', 'medical_device',
        name='managementfactortype', create_type=True
    )
    management_factor_type_enum.create(op.get_bind(), checkfirst=True)

    # BloodVerificationMethod
    blood_verification_method_enum = postgresql.ENUM(
        'lab_result', 'patient_statement', 'both',
        name='bloodverificationmethod', create_type=True
    )
    blood_verification_method_enum.create(op.get_bind(), checkfirst=True)

    # TransfusionErrorType
    transfusion_error_type_enum = postgresql.ENUM(
        'patient_id_error', 'crossmatch_error', 'blood_type_error', 'product_error',
        'administration_error', 'storage_error', 'documentation_error', 'reaction', 'other',
        name='transfusionerrortype', create_type=True
    )
    transfusion_error_type_enum.create(op.get_bind(), checkfirst=True)

    # TransfusionReactionType
    transfusion_reaction_type_enum = postgresql.ENUM(
        'none', 'febrile', 'allergic_mild', 'allergic_severe',
        'hemolytic_acute', 'hemolytic_delayed', 'taco', 'trali', 'other',
        name='transfusionreactiontype', create_type=True
    )
    transfusion_reaction_type_enum.create(op.get_bind(), checkfirst=True)

    # ThermalInjurySource
    thermal_injury_source_enum = postgresql.ENUM(
        'ice_bag', 'hot_bag', 'hot_water', 'cold_water', 'heating_pad',
        'hot_beverage', 'hot_food', 'steam', 'lamp', 'other',
        name='thermalinjurysource', create_type=True
    )
    thermal_injury_source_enum.create(op.get_bind(), checkfirst=True)

    # ThermalInjurySeverity
    thermal_injury_severity_enum = postgresql.ENUM(
        'none', 'grade_1', 'grade_2', 'grade_3',
        'frostbite_1', 'frostbite_2', 'frostbite_3',
        name='thermalinjuryseverity', create_type=True
    )
    thermal_injury_severity_enum.create(op.get_bind(), checkfirst=True)

    # ThermalInjuryBodyPart
    thermal_injury_body_part_enum = postgresql.ENUM(
        'head', 'face', 'neck', 'chest', 'back', 'abdomen',
        'upper_arm', 'forearm', 'hand', 'thigh', 'lower_leg', 'foot', 'other',
        name='thermalinjurybodypart', create_type=True
    )
    thermal_injury_body_part_enum.create(op.get_bind(), checkfirst=True)

    # ProcedureType
    procedure_type_enum = postgresql.ENUM(
        'treatment', 'examination', 'procedure', 'restraint_related', 'diet_related', 'other',
        name='proceduretype', create_type=True
    )
    procedure_type_enum.create(op.get_bind(), checkfirst=True)

    # ProcedureErrorType
    procedure_error_type_enum = postgresql.ENUM(
        'wrong_patient', 'wrong_site', 'wrong_procedure', 'wrong_time',
        'technique_error', 'equipment_failure', 'consent_issue', 'preparation_error',
        'complication', 'other',
        name='procedureerrortype', create_type=True
    )
    procedure_error_type_enum.create(op.get_bind(), checkfirst=True)

    # ProcedureOutcome
    procedure_outcome_enum = postgresql.ENUM(
        'no_harm', 'minor_harm', 'moderate_harm', 'severe_harm', 'death',
        name='procedureoutcome', create_type=True
    )
    procedure_outcome_enum.create(op.get_bind(), checkfirst=True)

    # EnvironmentType
    environment_type_enum = postgresql.ENUM(
        'fire', 'facility', 'waste', 'medical_equipment',
        'water', 'electrical', 'gas', 'hvac', 'other',
        name='environmenttype', create_type=True
    )
    environment_type_enum.create(op.get_bind(), checkfirst=True)

    # EnvironmentSeverity
    environment_severity_enum = postgresql.ENUM(
        'minor', 'moderate', 'major', 'critical',
        name='environmentseverity', create_type=True
    )
    environment_severity_enum.create(op.get_bind(), checkfirst=True)

    # SecurityType
    security_type_enum = postgresql.ENUM(
        'theft', 'suicide', 'suicide_attempt', 'elopement', 'assault',
        'verbal_abuse', 'sexual_misconduct', 'arson', 'vandalism', 'trespassing', 'other',
        name='securitytype', create_type=True
    )
    security_type_enum.create(op.get_bind(), checkfirst=True)

    # SecuritySeverity
    security_severity_enum = postgresql.ENUM(
        'low', 'moderate', 'high', 'critical',
        name='securityseverity', create_type=True
    )
    security_severity_enum.create(op.get_bind(), checkfirst=True)

    # InvolvedPartyType
    involved_party_type_enum = postgresql.ENUM(
        'patient', 'visitor', 'staff', 'outsider', 'unknown',
        name='involvedpartytype', create_type=True
    )
    involved_party_type_enum.create(op.get_bind(), checkfirst=True)

    # === Step 3: Add New Columns to incidents Table ===
    op.add_column('incidents', sa.Column('improvement_types', sa.JSON(), nullable=True))
    op.add_column('incidents', sa.Column('policy_factor', policy_factor_type_enum, nullable=True))
    op.add_column('incidents', sa.Column('policy_factor_detail', sa.Text(), nullable=True))
    op.add_column('incidents', sa.Column('management_factors', sa.JSON(), nullable=True))
    op.add_column('incidents', sa.Column('management_factors_detail', sa.Text(), nullable=True))

    # === Step 4: Create transfusion_details Table ===
    op.create_table(
        'transfusion_details',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('incident_id', sa.Integer(), sa.ForeignKey('incidents.id'), nullable=False, index=True),
        sa.Column('blood_type_verified', sa.Boolean(), default=True),
        sa.Column('verification_method', blood_verification_method_enum, nullable=True),
        sa.Column('error_type', transfusion_error_type_enum, nullable=False, index=True),
        sa.Column('error_type_detail', sa.Text(), nullable=True),
        sa.Column('reaction_type', transfusion_reaction_type_enum, nullable=True, index=True),
        sa.Column('reaction_detail', sa.Text(), nullable=True),
        sa.Column('blood_product_type', sa.String(100), nullable=True),
        sa.Column('blood_unit_id', sa.String(50), nullable=True),
        sa.Column('infusion_volume_ml', sa.Integer(), nullable=True),
        sa.Column('infusion_rate', sa.String(50), nullable=True),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('patient_code', sa.String(50), nullable=True, index=True),
        sa.Column('patient_blood_type', sa.String(10), nullable=True),
        sa.Column('pre_transfusion_check_done', sa.Boolean(), default=True),
        sa.Column('two_person_verification', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # === Step 5: Create thermal_injury_details Table ===
    op.create_table(
        'thermal_injury_details',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('incident_id', sa.Integer(), sa.ForeignKey('incidents.id'), nullable=False, index=True),
        sa.Column('injury_source', thermal_injury_source_enum, nullable=False, index=True),
        sa.Column('injury_source_detail', sa.String(200), nullable=True),
        sa.Column('injury_severity', thermal_injury_severity_enum, nullable=False, index=True),
        sa.Column('body_part', thermal_injury_body_part_enum, nullable=False),
        sa.Column('body_part_detail', sa.String(200), nullable=True),
        sa.Column('injury_size', sa.String(50), nullable=True),
        sa.Column('application_duration_min', sa.Integer(), nullable=True),
        sa.Column('temperature_celsius', sa.String(20), nullable=True),
        sa.Column('patient_code', sa.String(50), nullable=True, index=True),
        sa.Column('patient_sensory_intact', sa.String(50), nullable=True),
        sa.Column('treatment_provided', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # === Step 6: Create procedure_details Table ===
    op.create_table(
        'procedure_details',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('incident_id', sa.Integer(), sa.ForeignKey('incidents.id'), nullable=False, index=True),
        sa.Column('procedure_type', procedure_type_enum, nullable=False, index=True),
        sa.Column('procedure_name', sa.String(200), nullable=False),
        sa.Column('procedure_detail', sa.Text(), nullable=True),
        sa.Column('error_type', procedure_error_type_enum, nullable=False, index=True),
        sa.Column('error_type_detail', sa.Text(), nullable=True),
        sa.Column('outcome', procedure_outcome_enum, nullable=True, index=True),
        sa.Column('outcome_detail', sa.Text(), nullable=True),
        sa.Column('consent_obtained', sa.Boolean(), default=True),
        sa.Column('consent_issue_detail', sa.Text(), nullable=True),
        sa.Column('procedure_datetime', sa.DateTime(timezone=True), nullable=True),
        sa.Column('performer_role', sa.String(100), nullable=True),
        sa.Column('patient_code', sa.String(50), nullable=True, index=True),
        sa.Column('procedure_site', sa.String(200), nullable=True),
        sa.Column('preparation_done', sa.Boolean(), default=True),
        sa.Column('preparation_issue', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # === Step 7: Create environment_details Table ===
    op.create_table(
        'environment_details',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('incident_id', sa.Integer(), sa.ForeignKey('incidents.id'), nullable=False, index=True),
        sa.Column('environment_type', environment_type_enum, nullable=False, index=True),
        sa.Column('environment_type_detail', sa.Text(), nullable=True),
        sa.Column('severity', environment_severity_enum, nullable=False, index=True),
        sa.Column('location_specific', sa.String(200), nullable=True),
        sa.Column('location_floor', sa.String(50), nullable=True),
        sa.Column('location_room', sa.String(50), nullable=True),
        sa.Column('equipment_involved', sa.String(200), nullable=True),
        sa.Column('equipment_id', sa.String(50), nullable=True),
        sa.Column('damage_extent', sa.Text(), nullable=True),
        sa.Column('injury_occurred', sa.Boolean(), default=False),
        sa.Column('injury_count', sa.Integer(), default=0),
        sa.Column('injury_detail', sa.Text(), nullable=True),
        sa.Column('property_damage', sa.Boolean(), default=False),
        sa.Column('property_damage_detail', sa.Text(), nullable=True),
        sa.Column('estimated_cost', sa.String(50), nullable=True),
        sa.Column('immediate_response', sa.Text(), nullable=True),
        sa.Column('evacuation_required', sa.Boolean(), default=False),
        sa.Column('external_help_called', sa.Boolean(), default=False),
        sa.Column('cause_identified', sa.Boolean(), default=False),
        sa.Column('cause_detail', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # === Step 8: Create security_details Table ===
    op.create_table(
        'security_details',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('incident_id', sa.Integer(), sa.ForeignKey('incidents.id'), nullable=False, index=True),
        sa.Column('security_type', security_type_enum, nullable=False, index=True),
        sa.Column('security_type_detail', sa.Text(), nullable=True),
        sa.Column('severity', security_severity_enum, nullable=False, index=True),
        sa.Column('involved_parties', sa.JSON(), nullable=True),
        sa.Column('involved_parties_count', sa.Integer(), default=1),
        sa.Column('victim_type', involved_party_type_enum, nullable=True),
        sa.Column('victim_code', sa.String(50), nullable=True),
        sa.Column('perpetrator_type', involved_party_type_enum, nullable=True),
        sa.Column('perpetrator_code', sa.String(50), nullable=True),
        sa.Column('police_notified', sa.Boolean(), default=False),
        sa.Column('police_report_number', sa.String(50), nullable=True),
        sa.Column('security_notified', sa.Boolean(), default=False),
        sa.Column('injury_occurred', sa.Boolean(), default=False),
        sa.Column('injury_detail', sa.Text(), nullable=True),
        sa.Column('property_damage', sa.Boolean(), default=False),
        sa.Column('property_damage_detail', sa.Text(), nullable=True),
        sa.Column('stolen_items', sa.Text(), nullable=True),
        sa.Column('immediate_response', sa.Text(), nullable=True),
        sa.Column('restraint_applied', sa.Boolean(), default=False),
        sa.Column('isolation_applied', sa.Boolean(), default=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=True),
        sa.Column('found_location', sa.String(200), nullable=True),
        sa.Column('method_used', sa.String(200), nullable=True),
        sa.Column('risk_assessment_done', sa.Boolean(), default=False),
        sa.Column('suicide_risk_level', sa.String(20), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade() -> None:
    """Drop PSR form coverage tables and columns."""

    # Drop tables
    op.drop_table('security_details')
    op.drop_table('environment_details')
    op.drop_table('procedure_details')
    op.drop_table('thermal_injury_details')
    op.drop_table('transfusion_details')

    # Drop columns from incidents
    op.drop_column('incidents', 'management_factors_detail')
    op.drop_column('incidents', 'management_factors')
    op.drop_column('incidents', 'policy_factor_detail')
    op.drop_column('incidents', 'policy_factor')
    op.drop_column('incidents', 'improvement_types')

    # Drop enum types (in reverse order of creation)
    op.execute('DROP TYPE IF EXISTS involvedpartytype')
    op.execute('DROP TYPE IF EXISTS securityseverity')
    op.execute('DROP TYPE IF EXISTS securitytype')
    op.execute('DROP TYPE IF EXISTS environmentseverity')
    op.execute('DROP TYPE IF EXISTS environmenttype')
    op.execute('DROP TYPE IF EXISTS procedureoutcome')
    op.execute('DROP TYPE IF EXISTS procedureerrortype')
    op.execute('DROP TYPE IF EXISTS proceduretype')
    op.execute('DROP TYPE IF EXISTS thermalinjurybodypart')
    op.execute('DROP TYPE IF EXISTS thermalinjuryseverity')
    op.execute('DROP TYPE IF EXISTS thermalinjurysource')
    op.execute('DROP TYPE IF EXISTS transfusionreactiontype')
    op.execute('DROP TYPE IF EXISTS transfusionerrortype')
    op.execute('DROP TYPE IF EXISTS bloodverificationmethod')
    op.execute('DROP TYPE IF EXISTS managementfactortype')
    op.execute('DROP TYPE IF EXISTS policyfactortype')
    op.execute('DROP TYPE IF EXISTS improvementtype')

    # Note: Removing enum values from incidentcategory is complex in PostgreSQL
    # In practice, you might need to recreate the enum type entirely
    # For this migration, we skip removing enum values in downgrade
