"""Risk Management Module - Phase 1.5

Revision ID: 003
Revises: 002
Create Date: 2026-01-24 12:00:00

Adds Risk Management features:
- risks table: Risk Register with P×S scoring
- risk_assessments table: Assessment history
- Just Culture behavior_type field in incidents
- risk_id foreign key in actions
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create Risk Management tables and update existing tables."""

    # === Step 1: Create New Enum Types ===

    # RiskSourceType
    risk_source_type_enum = postgresql.ENUM(
        'psr', 'rounding', 'audit', 'complaint', 'indicator', 'external', 'proactive', 'other',
        name='risksourcetype', create_type=False
    )
    risk_source_type_enum.create(op.get_bind(), checkfirst=True)

    # RiskCategory
    risk_category_enum = postgresql.ENUM(
        'fall', 'medication', 'pressure_ulcer', 'infection', 'transfusion',
        'procedure', 'restraint', 'environment', 'security', 'communication',
        'handoff', 'identification', 'other',
        name='riskcategory', create_type=False
    )
    risk_category_enum.create(op.get_bind(), checkfirst=True)

    # RiskLevel
    risk_level_enum = postgresql.ENUM(
        'low', 'medium', 'high', 'critical',
        name='risklevel', create_type=False
    )
    risk_level_enum.create(op.get_bind(), checkfirst=True)

    # RiskStatus
    risk_status_enum = postgresql.ENUM(
        'open', 'in_progress', 'mitigating', 'monitoring', 'closed',
        name='riskstatus', create_type=False
    )
    risk_status_enum.create(op.get_bind(), checkfirst=True)

    # RiskAssessmentType
    risk_assessment_type_enum = postgresql.ENUM(
        'initial', 'periodic', 'post_treatment', 'final',
        name='riskassessmenttype', create_type=False
    )
    risk_assessment_type_enum.create(op.get_bind(), checkfirst=True)

    # BehaviorType (Just Culture)
    behavior_type_enum = postgresql.ENUM(
        'human_error', 'at_risk', 'reckless', 'system_induced', 'not_applicable', 'pending_review',
        name='behaviortype', create_type=False
    )
    behavior_type_enum.create(op.get_bind(), checkfirst=True)

    # === Step 2: Create risks table ===
    op.create_table(
        'risks',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('risk_code', sa.String(20), unique=True, nullable=False, index=True),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),

        # Source
        sa.Column('source_type', postgresql.ENUM(name='risksourcetype', create_type=False), nullable=False, index=True),
        sa.Column('source_incident_id', sa.Integer(), sa.ForeignKey('incidents.id'), nullable=True),
        sa.Column('source_detail', sa.Text(), nullable=True),

        # Category
        sa.Column('category', postgresql.ENUM(name='riskcategory', create_type=False), nullable=False, index=True),

        # Controls
        sa.Column('current_controls', sa.Text(), nullable=True),

        # Current Risk (P×S)
        sa.Column('probability', sa.Integer(), nullable=False, default=1),
        sa.Column('severity', sa.Integer(), nullable=False, default=1),
        sa.Column('risk_score', sa.Integer(), nullable=False, default=1),
        sa.Column('risk_level', postgresql.ENUM(name='risklevel', create_type=False), nullable=False, index=True),

        # Residual Risk (after treatment)
        sa.Column('residual_probability', sa.Integer(), nullable=True),
        sa.Column('residual_severity', sa.Integer(), nullable=True),
        sa.Column('residual_score', sa.Integer(), nullable=True),
        sa.Column('residual_level', postgresql.ENUM(name='risklevel', create_type=False), nullable=True),

        # Ownership
        sa.Column('owner_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('target_date', sa.Date(), nullable=True),

        # Status
        sa.Column('status', postgresql.ENUM(name='riskstatus', create_type=False), nullable=False, default='open', index=True),

        # Auto-escalation
        sa.Column('auto_escalated', sa.Boolean(), default=False),
        sa.Column('escalation_reason', sa.Text(), nullable=True),

        # Metadata
        sa.Column('created_by_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('closed_by_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
    )

    # Create indexes for risks table
    op.create_index('ix_risks_created_at', 'risks', ['created_at'])
    op.create_index('ix_risks_owner_id', 'risks', ['owner_id'])

    # === Step 3: Create risk_assessments table ===
    op.create_table(
        'risk_assessments',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('risk_id', sa.Integer(), sa.ForeignKey('risks.id'), nullable=False, index=True),
        sa.Column('assessment_type', postgresql.ENUM(name='riskassessmenttype', create_type=False), nullable=False),

        # Assessment values
        sa.Column('probability', sa.Integer(), nullable=False),
        sa.Column('severity', sa.Integer(), nullable=False),
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('level', postgresql.ENUM(name='risklevel', create_type=False), nullable=False),
        sa.Column('rationale', sa.Text(), nullable=True),

        # Metadata
        sa.Column('assessor_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('assessed_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Create index for risk_assessments
    op.create_index('ix_risk_assessments_assessed_at', 'risk_assessments', ['assessed_at'])

    # === Step 4: Add Just Culture field to incidents table ===
    op.add_column('incidents', sa.Column('behavior_type', postgresql.ENUM(name='behaviortype', create_type=False), nullable=True))
    op.add_column('incidents', sa.Column('behavior_type_rationale', sa.Text(), nullable=True))

    # Create index for behavior_type
    op.create_index('ix_incidents_behavior_type', 'incidents', ['behavior_type'])

    # === Step 5: Add risk_id to actions table ===
    op.add_column('actions', sa.Column('risk_id', sa.Integer(), sa.ForeignKey('risks.id'), nullable=True))

    # Create index for risk_id in actions
    op.create_index('ix_actions_risk_id', 'actions', ['risk_id'])


def downgrade() -> None:
    """Remove Risk Management tables and fields."""

    # Remove index and column from actions
    op.drop_index('ix_actions_risk_id', table_name='actions')
    op.drop_column('actions', 'risk_id')

    # Remove index and columns from incidents
    op.drop_index('ix_incidents_behavior_type', table_name='incidents')
    op.drop_column('incidents', 'behavior_type_rationale')
    op.drop_column('incidents', 'behavior_type')

    # Drop risk_assessments table
    op.drop_index('ix_risk_assessments_assessed_at', table_name='risk_assessments')
    op.drop_table('risk_assessments')

    # Drop risks table
    op.drop_index('ix_risks_owner_id', table_name='risks')
    op.drop_index('ix_risks_created_at', table_name='risks')
    op.drop_table('risks')

    # Drop enum types (in reverse order of dependency)
    op.execute("DROP TYPE IF EXISTS behaviortype")
    op.execute("DROP TYPE IF EXISTS riskassessmenttype")
    op.execute("DROP TYPE IF EXISTS riskstatus")
    op.execute("DROP TYPE IF EXISTS risklevel")
    op.execute("DROP TYPE IF EXISTS riskcategory")
    op.execute("DROP TYPE IF EXISTS risksourcetype")
