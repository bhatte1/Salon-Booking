"""add end_time to appointments

Revision ID: aa4ec154c76c
Revises: dcc472f875af
Create Date: 2026-02-23 22:05:50.317289

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'aa4ec154c76c'
down_revision: Union[str, Sequence[str], None] = 'dcc472f875af'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1) Add end_time as nullable first (so existing rows don't break)
    op.add_column("appointments", sa.Column("end_time", sa.DateTime(), nullable=True))

    # 2) Backfill end_time for existing rows using service duration
    op.execute("""
        UPDATE appointments a
        SET end_time = a.start_time + (s.duration_minutes || ' minutes')::interval
        FROM services s
        WHERE a.service_id = s.id AND a.end_time IS NULL;
    """)

    # 3) Now enforce NOT NULL after data exists
    op.alter_column("appointments", "end_time", nullable=False)

    # Optional performance indexes (recommended)
    op.create_index("ix_appointments_service_id_start_time", "appointments", ["service_id", "start_time"])
    op.create_index("ix_appointments_service_id_end_time", "appointments", ["service_id", "end_time"])


def downgrade() -> None:
    op.drop_index("ix_appointments_service_id_end_time", table_name="appointments")
    op.drop_index("ix_appointments_service_id_start_time", table_name="appointments")
    op.drop_column("appointments", "end_time")
