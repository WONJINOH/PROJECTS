"""Add FMEA fields to pressure_ulcer_records

Revision ID: 011
Revises: 010
Create Date: 2026-01-28 10:00:00

FMEA (Failure Mode and Effects Analysis) risk assessment fields:
- fmea_severity: 심각도 (1, 3, 5, 6, 8, 10)
- fmea_probability: 발생 가능성 (1, 3, 5, 7, 9)
- fmea_detectability: 발견 가능성 (1, 3, 5, 7, 9)
- fmea_rpn: Risk Priority Number = S x O x D

Reporter fields:
- reporter_id: 보고자 사용자 ID
- reporter_name: 보고자명
- reported_at: 보고 일시
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "011"
down_revision = "010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add FMEA fields to pressure_ulcer_records
    op.add_column(
        "pressure_ulcer_records",
        sa.Column("fmea_severity", sa.Integer(), nullable=True, comment="심각도 (1, 3, 5, 6, 8, 10)"),
    )
    op.add_column(
        "pressure_ulcer_records",
        sa.Column("fmea_probability", sa.Integer(), nullable=True, comment="발생 가능성 (1, 3, 5, 7, 9)"),
    )
    op.add_column(
        "pressure_ulcer_records",
        sa.Column("fmea_detectability", sa.Integer(), nullable=True, comment="발견 가능성 (1, 3, 5, 7, 9)"),
    )
    op.add_column(
        "pressure_ulcer_records",
        sa.Column("fmea_rpn", sa.Integer(), nullable=True, comment="RPN = S x O x D"),
    )

    # Add reporter fields
    op.add_column(
        "pressure_ulcer_records",
        sa.Column("reporter_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
    )
    op.add_column(
        "pressure_ulcer_records",
        sa.Column("reporter_name", sa.String(100), nullable=True),
    )
    op.add_column(
        "pressure_ulcer_records",
        sa.Column("reported_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    # Remove reporter fields
    op.drop_column("pressure_ulcer_records", "reported_at")
    op.drop_column("pressure_ulcer_records", "reporter_name")
    op.drop_column("pressure_ulcer_records", "reporter_id")

    # Remove FMEA fields
    op.drop_column("pressure_ulcer_records", "fmea_rpn")
    op.drop_column("pressure_ulcer_records", "fmea_detectability")
    op.drop_column("pressure_ulcer_records", "fmea_probability")
    op.drop_column("pressure_ulcer_records", "fmea_severity")
