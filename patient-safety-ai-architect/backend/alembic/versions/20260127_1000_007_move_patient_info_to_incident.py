"""Move patient info from detail forms to incident common form

Revision ID: 007_move_patient_info
Revises: 006_add_lookup_and_patient_fields
Create Date: 2026-01-27 10:00:00.000000

Changes:
- Add patient info columns to incidents table
- Add FK constraints for patient_department and patient_physician
- Remove department column from incidents table
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add patient info columns to incidents table
    op.add_column('incidents', sa.Column('patient_registration_no', sa.String(50), nullable=True))
    op.add_column('incidents', sa.Column('patient_name', sa.String(100), nullable=True))
    op.add_column('incidents', sa.Column('patient_ward', sa.String(20), nullable=True))
    op.add_column('incidents', sa.Column('room_number', sa.String(50), nullable=True))
    op.add_column('incidents', sa.Column('patient_gender', sa.String(10), nullable=True))
    op.add_column('incidents', sa.Column('patient_age', sa.Integer(), nullable=True))
    op.add_column('incidents', sa.Column('patient_department_id', sa.Integer(), nullable=True))
    op.add_column('incidents', sa.Column('patient_physician_id', sa.Integer(), nullable=True))
    op.add_column('incidents', sa.Column('diagnosis', sa.String(500), nullable=True))

    # 2. Add FK constraints
    op.create_foreign_key(
        'fk_incidents_patient_department',
        'incidents', 'departments',
        ['patient_department_id'], ['id']
    )
    op.create_foreign_key(
        'fk_incidents_patient_physician',
        'incidents', 'physicians',
        ['patient_physician_id'], ['id']
    )

    # 3. Add indexes
    op.create_index('ix_incidents_patient_ward', 'incidents', ['patient_ward'])

    # 4. Remove old department column (reporter's department)
    op.drop_column('incidents', 'department')


def downgrade() -> None:
    # 1. Add back the department column
    op.add_column('incidents', sa.Column('department', sa.String(100), nullable=True))

    # 2. Remove indexes
    op.drop_index('ix_incidents_patient_ward', table_name='incidents')

    # 3. Remove FK constraints
    op.drop_constraint('fk_incidents_patient_physician', 'incidents', type_='foreignkey')
    op.drop_constraint('fk_incidents_patient_department', 'incidents', type_='foreignkey')

    # 4. Remove patient info columns
    op.drop_column('incidents', 'diagnosis')
    op.drop_column('incidents', 'patient_physician_id')
    op.drop_column('incidents', 'patient_department_id')
    op.drop_column('incidents', 'patient_age')
    op.drop_column('incidents', 'patient_gender')
    op.drop_column('incidents', 'room_number')
    op.drop_column('incidents', 'patient_ward')
    op.drop_column('incidents', 'patient_name')
    op.drop_column('incidents', 'patient_registration_no')
