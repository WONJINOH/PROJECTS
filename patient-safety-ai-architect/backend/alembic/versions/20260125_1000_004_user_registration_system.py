"""User registration and account lifecycle system

Revision ID: 004_user_registration
Revises: 003_risk_management
Create Date: 2026-01-25 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create UserStatus enum type
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE userstatus AS ENUM (
                'pending',
                'active',
                'dormant',
                'suspended',
                'deleted'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Add new columns to users table
    op.add_column('users', sa.Column('status', sa.Enum('pending', 'active', 'dormant', 'suspended', 'deleted', name='userstatus'), nullable=True))
    op.add_column('users', sa.Column('password_changed_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('password_expires_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('approved_by_id', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('dormant_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))

    # Set default status for existing users
    op.execute("UPDATE users SET status = 'active' WHERE status IS NULL")

    # Make status non-nullable
    op.alter_column('users', 'status',
                    existing_type=sa.Enum('pending', 'active', 'dormant', 'suspended', 'deleted', name='userstatus'),
                    nullable=False,
                    server_default='pending')


def downgrade() -> None:
    # Remove columns
    op.drop_column('users', 'deleted_at')
    op.drop_column('users', 'dormant_at')
    op.drop_column('users', 'approved_by_id')
    op.drop_column('users', 'approved_at')
    op.drop_column('users', 'password_expires_at')
    op.drop_column('users', 'password_changed_at')
    op.drop_column('users', 'status')

    # Drop enum type
    op.execute("DROP TYPE IF EXISTS userstatus")
