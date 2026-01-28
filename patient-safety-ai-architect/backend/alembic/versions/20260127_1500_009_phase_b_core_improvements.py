"""Phase B: Core Improvements - 발생장소 드롭다운, LocationType enum

Revision ID: 009
Revises: 008
Create Date: 2026-01-27 15:00:00.000000

Changes:
- Add LocationType enum type
- Add location_type column to incidents table (Feature 2)
- Add location_detail column to incidents table (Feature 2)
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create LocationType enum
    locationtype = sa.Enum(
        'own_room', 'other_room', 'bathroom', 'hallway', 'rehabilitation', 'nursing_station', 'other',
        name='locationtype'
    )
    locationtype.create(op.get_bind(), checkfirst=True)

    # Add location_type column
    op.add_column('incidents', sa.Column(
        'location_type',
        sa.Enum('own_room', 'other_room', 'bathroom', 'hallway', 'rehabilitation', 'nursing_station', 'other', name='locationtype'),
        nullable=True
    ))
    op.create_index('ix_incidents_location_type', 'incidents', ['location_type'])

    # Add location_detail column
    op.add_column('incidents', sa.Column('location_detail', sa.String(200), nullable=True))


def downgrade() -> None:
    op.drop_column('incidents', 'location_detail')
    op.drop_index('ix_incidents_location_type', table_name='incidents')
    op.drop_column('incidents', 'location_type')

    # Drop LocationType enum
    sa.Enum(name='locationtype').drop(op.get_bind(), checkfirst=True)
