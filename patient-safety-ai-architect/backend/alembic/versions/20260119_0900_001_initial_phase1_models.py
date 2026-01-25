"""Initial Phase 1 models

Revision ID: 001
Revises:
Create Date: 2026-01-19 09:00:00

Creates core tables for Phase 1:
- users: User accounts with RBAC
- incidents: Patient safety incidents
- approvals: 3-level approval workflow
- attachments: File storage
- actions: CAPA tracking
- audit_logs: PIPA Art. 29 compliance
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create Phase 1 tables."""

    # === ENUM Types ===
    # Use create_type=False since we're manually calling .create()
    role_enum = postgresql.ENUM(
        'reporter', 'qps_staff', 'vice_chair', 'director', 'admin', 'master',
        name='role', create_type=False
    )
    role_enum.create(op.get_bind(), checkfirst=True)

    incident_category_enum = postgresql.ENUM(
        'fall', 'medication', 'pressure_ulcer', 'infection',
        'medical_device', 'surgery', 'transfusion', 'other',
        name='incidentcategory', create_type=False
    )
    incident_category_enum.create(op.get_bind(), checkfirst=True)

    incident_grade_enum = postgresql.ENUM(
        'near_miss', 'no_harm', 'mild', 'moderate', 'severe', 'death',
        name='incidentgrade', create_type=False
    )
    incident_grade_enum.create(op.get_bind(), checkfirst=True)

    approval_level_enum = postgresql.ENUM(
        'l1_qps', 'l2_vice_chair', 'l3_director',
        name='approvallevel', create_type=False
    )
    approval_level_enum.create(op.get_bind(), checkfirst=True)

    approval_status_enum = postgresql.ENUM(
        'pending', 'approved', 'rejected',
        name='approvalstatus', create_type=False
    )
    approval_status_enum.create(op.get_bind(), checkfirst=True)

    action_status_enum = postgresql.ENUM(
        'open', 'in_progress', 'completed', 'verified', 'cancelled',
        name='actionstatus', create_type=False
    )
    action_status_enum.create(op.get_bind(), checkfirst=True)

    action_priority_enum = postgresql.ENUM(
        'low', 'medium', 'high', 'critical',
        name='actionpriority', create_type=False
    )
    action_priority_enum.create(op.get_bind(), checkfirst=True)

    audit_event_type_enum = postgresql.ENUM(
        'auth_login', 'auth_logout', 'auth_failed',
        'incident_view', 'incident_create', 'incident_update', 'incident_delete', 'incident_export',
        'attachment_upload', 'attachment_download', 'attachment_delete',
        'approval_action', 'permission_change',
        'risk_create', 'risk_update', 'risk_view', 'risk_escalate', 'risk_assessment',
        name='auditeventtype', create_type=False
    )
    audit_event_type_enum.create(op.get_bind(), checkfirst=True)

    # === Users Table ===
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('username', sa.String(50), unique=True, index=True, nullable=False),
        sa.Column('email', sa.String(255), unique=True, index=True, nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(100), nullable=False),
        sa.Column('role', role_enum, default='reporter', nullable=False),
        sa.Column('department', sa.String(100), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('last_login', sa.DateTime(), nullable=True),
    )

    # === Incidents Table ===
    op.create_table(
        'incidents',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        # Common Page Required Fields
        sa.Column('category', incident_category_enum, nullable=False, index=True),
        sa.Column('grade', incident_grade_enum, nullable=False, index=True),
        sa.Column('occurred_at', sa.DateTime(), nullable=False),
        sa.Column('location', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('immediate_action', sa.Text(), nullable=False),
        sa.Column('reported_at', sa.DateTime(), nullable=False),
        sa.Column('reporter_name', sa.String(100), nullable=True),
        # Optional Fields
        sa.Column('root_cause', sa.Text(), nullable=True),
        sa.Column('improvements', sa.Text(), nullable=True),
        # Encrypted Patient Info (handled by sqlalchemy-utils)
        sa.Column('patient_info', sa.LargeBinary(), nullable=True),
        # Metadata
        sa.Column('reporter_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('department', sa.String(100), nullable=True),
        sa.Column('status', sa.String(50), default='draft', index=True),
        sa.Column('is_deleted', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # === Attachments Table ===
    op.create_table(
        'attachments',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('incident_id', sa.Integer(), sa.ForeignKey('incidents.id'), nullable=False),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('original_filename', sa.String(255), nullable=False),
        sa.Column('content_type', sa.String(100), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('storage_uri', sa.String(500), nullable=False),  # file:// URI
        sa.Column('uploaded_by_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('is_deleted', sa.Boolean(), default=False),
    )

    # === Approvals Table ===
    op.create_table(
        'approvals',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('incident_id', sa.Integer(), sa.ForeignKey('incidents.id'), nullable=False),
        sa.Column('approver_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('level', approval_level_enum, nullable=False),
        sa.Column('status', approval_status_enum, default='pending'),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('decided_at', sa.DateTime(), nullable=True),
    )

    # === Actions Table (CAPA) ===
    op.create_table(
        'actions',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('incident_id', sa.Integer(), sa.ForeignKey('incidents.id'), nullable=False, index=True),
        # Core CAPA Fields
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('owner', sa.String(100), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column('definition_of_done', sa.Text(), nullable=False),
        # Status
        sa.Column('status', action_status_enum, default='open', nullable=False, index=True),
        sa.Column('priority', action_priority_enum, default='medium', nullable=False),
        # Evidence
        sa.Column('evidence_attachment_id', sa.Integer(), sa.ForeignKey('attachments.id'), nullable=True),
        # Completion
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('completed_by_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('completion_notes', sa.Text(), nullable=True),
        # Verification
        sa.Column('verified_at', sa.DateTime(), nullable=True),
        sa.Column('verified_by_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('verification_notes', sa.Text(), nullable=True),
        # Metadata
        sa.Column('created_by_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('is_deleted', sa.Boolean(), default=False),
    )

    # === Audit Logs Table (PIPA Art. 29) ===
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('event_type', audit_event_type_enum, nullable=False, index=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, index=True),
        sa.Column('user_id', sa.Integer(), nullable=True, index=True),  # nullable for failed logins
        sa.Column('user_role', sa.String(50), nullable=True),
        sa.Column('username', sa.String(50), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('resource_type', sa.String(50), nullable=True),
        sa.Column('resource_id', sa.String(100), nullable=True),
        sa.Column('action_detail', sa.JSON(), nullable=True),  # Event-specific data
        sa.Column('result', sa.String(20), nullable=False),  # success, failure, denied
        sa.Column('previous_hash', sa.String(64), nullable=True),
        sa.Column('entry_hash', sa.String(64), nullable=False),
    )

    # === Indexes for Performance ===
    op.create_index('ix_incidents_occurred_at', 'incidents', ['occurred_at'])
    op.create_index('ix_incidents_reporter_id', 'incidents', ['reporter_id'])
    op.create_index('ix_approvals_incident_id', 'approvals', ['incident_id'])
    op.create_index('ix_attachments_incident_id', 'attachments', ['incident_id'])
    op.create_index('ix_actions_due_date', 'actions', ['due_date'])
    # Note: ix_audit_logs_user_id is created automatically by index=True on the column


def downgrade() -> None:
    """Drop Phase 1 tables."""
    # Drop indexes first
    op.drop_index('ix_actions_due_date', table_name='actions')
    op.drop_index('ix_attachments_incident_id', table_name='attachments')
    op.drop_index('ix_approvals_incident_id', table_name='approvals')
    op.drop_index('ix_incidents_reporter_id', table_name='incidents')
    op.drop_index('ix_incidents_occurred_at', table_name='incidents')

    # Drop tables
    op.drop_table('audit_logs')
    op.drop_table('actions')
    op.drop_table('approvals')
    op.drop_table('attachments')
    op.drop_table('incidents')
    op.drop_table('users')

    # Drop enum types
    op.execute('DROP TYPE IF EXISTS auditeventtype')
    op.execute('DROP TYPE IF EXISTS actionpriority')
    op.execute('DROP TYPE IF EXISTS actionstatus')
    op.execute('DROP TYPE IF EXISTS approvalstatus')
    op.execute('DROP TYPE IF EXISTS approvallevel')
    op.execute('DROP TYPE IF EXISTS incidentgrade')
    op.execute('DROP TYPE IF EXISTS incidentcategory')
    op.execute('DROP TYPE IF EXISTS role')
