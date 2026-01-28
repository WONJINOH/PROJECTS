"""Add lookup tables (departments, physicians) and patient info fields

Revision ID: 006_lookup_patient
Revises: 005_add_missing_detail_tables
Create Date: 2026-01-26 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create departments table
    op.create_table(
        'departments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('code', sa.String(20), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.UniqueConstraint('code'),
    )
    op.create_index('ix_departments_id', 'departments', ['id'])
    op.create_index('ix_departments_name', 'departments', ['name'])
    op.create_index('ix_departments_is_active', 'departments', ['is_active'])

    # 2. Create physicians table
    op.create_table(
        'physicians',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('department_id', sa.Integer(), nullable=False),
        sa.Column('license_number', sa.String(50), nullable=True),
        sa.Column('specialty', sa.String(100), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id']),
    )
    op.create_index('ix_physicians_id', 'physicians', ['id'])
    op.create_index('ix_physicians_name', 'physicians', ['name'])
    op.create_index('ix_physicians_department_id', 'physicians', ['department_id'])
    op.create_index('ix_physicians_is_active', 'physicians', ['is_active'])

    # 3. Add patient info columns to fall_details
    op.add_column('fall_details', sa.Column('patient_name', sa.String(100), nullable=True))
    op.add_column('fall_details', sa.Column('room_number', sa.String(50), nullable=True))
    op.add_column('fall_details', sa.Column('department_id', sa.Integer(), nullable=True))
    op.add_column('fall_details', sa.Column('physician_id', sa.Integer(), nullable=True))
    op.add_column('fall_details', sa.Column('diagnosis', sa.String(500), nullable=True))
    op.add_column('fall_details', sa.Column('immediate_risk_medications', sa.JSON(), nullable=True))
    op.add_column('fall_details', sa.Column('immediate_risk_medications_detail', sa.Text(), nullable=True))

    # Add foreign keys for fall_details (if constraints supported)
    try:
        op.create_foreign_key(
            'fk_fall_details_department_id',
            'fall_details', 'departments',
            ['department_id'], ['id']
        )
        op.create_foreign_key(
            'fk_fall_details_physician_id',
            'fall_details', 'physicians',
            ['physician_id'], ['id']
        )
    except Exception:
        # SQLite doesn't support adding foreign keys after table creation
        pass

    # 4. Add patient info columns to medication_error_details
    op.add_column('medication_error_details', sa.Column('patient_name', sa.String(100), nullable=True))
    op.add_column('medication_error_details', sa.Column('patient_gender', sa.String(10), nullable=True))
    op.add_column('medication_error_details', sa.Column('room_number', sa.String(50), nullable=True))
    op.add_column('medication_error_details', sa.Column('department_id', sa.Integer(), nullable=True))
    op.add_column('medication_error_details', sa.Column('physician_id', sa.Integer(), nullable=True))
    op.add_column('medication_error_details', sa.Column('diagnosis', sa.String(500), nullable=True))

    # Add foreign keys for medication_error_details (if constraints supported)
    try:
        op.create_foreign_key(
            'fk_medication_error_details_department_id',
            'medication_error_details', 'departments',
            ['department_id'], ['id']
        )
        op.create_foreign_key(
            'fk_medication_error_details_physician_id',
            'medication_error_details', 'physicians',
            ['physician_id'], ['id']
        )
    except Exception:
        # SQLite doesn't support adding foreign keys after table creation
        pass


def downgrade() -> None:
    # Remove foreign keys first (if they exist)
    try:
        op.drop_constraint('fk_medication_error_details_physician_id', 'medication_error_details', type_='foreignkey')
        op.drop_constraint('fk_medication_error_details_department_id', 'medication_error_details', type_='foreignkey')
        op.drop_constraint('fk_fall_details_physician_id', 'fall_details', type_='foreignkey')
        op.drop_constraint('fk_fall_details_department_id', 'fall_details', type_='foreignkey')
    except Exception:
        pass

    # Remove columns from medication_error_details
    op.drop_column('medication_error_details', 'diagnosis')
    op.drop_column('medication_error_details', 'physician_id')
    op.drop_column('medication_error_details', 'department_id')
    op.drop_column('medication_error_details', 'room_number')
    op.drop_column('medication_error_details', 'patient_gender')
    op.drop_column('medication_error_details', 'patient_name')

    # Remove columns from fall_details
    op.drop_column('fall_details', 'immediate_risk_medications_detail')
    op.drop_column('fall_details', 'immediate_risk_medications')
    op.drop_column('fall_details', 'diagnosis')
    op.drop_column('fall_details', 'physician_id')
    op.drop_column('fall_details', 'department_id')
    op.drop_column('fall_details', 'room_number')
    op.drop_column('fall_details', 'patient_name')

    # Drop tables
    op.drop_index('ix_physicians_is_active', 'physicians')
    op.drop_index('ix_physicians_department_id', 'physicians')
    op.drop_index('ix_physicians_name', 'physicians')
    op.drop_index('ix_physicians_id', 'physicians')
    op.drop_table('physicians')

    op.drop_index('ix_departments_is_active', 'departments')
    op.drop_index('ix_departments_name', 'departments')
    op.drop_index('ix_departments_id', 'departments')
    op.drop_table('departments')
