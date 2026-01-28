"""Phase A: Quick Wins - 사고번호, 기타 유형 상세, 발견방법 상세

Revision ID: 008
Revises: 007
Create Date: 2026-01-27 14:00:00.000000

Changes:
- Add incident_number column to incidents table (Feature 3)
- Add category_other_detail column to incidents table (Feature 1)
- Add discovery_method_detail column to medication_error_details table (Feature 5)
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # === incidents 테이블 ===
    # 사고번호 (YYYYMMDD-NN 형식)
    op.add_column('incidents', sa.Column('incident_number', sa.String(15), nullable=True))
    op.create_index('ix_incidents_incident_number', 'incidents', ['incident_number'], unique=True)

    # 기타 유형 상세
    op.add_column('incidents', sa.Column('category_other_detail', sa.String(200), nullable=True))

    # === medication_error_details 테이블 ===
    # 발견 방법 상세 (기타 선택 시)
    op.add_column('medication_error_details', sa.Column('discovery_method_detail', sa.String(200), nullable=True))


def downgrade() -> None:
    # === medication_error_details 테이블 ===
    op.drop_column('medication_error_details', 'discovery_method_detail')

    # === incidents 테이블 ===
    op.drop_column('incidents', 'category_other_detail')
    op.drop_index('ix_incidents_incident_number', table_name='incidents')
    op.drop_column('incidents', 'incident_number')
