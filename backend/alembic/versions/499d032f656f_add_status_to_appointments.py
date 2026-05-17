"""add status to appointments

Revision ID: 499d032f656f
Revises: 725b35b9f6ce
Create Date: 2026-03-25 18:17:21.341583

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '499d032f656f'
down_revision: Union[str, Sequence[str], None] = '725b35b9f6ce'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('appointments', sa.Column('status', sa.String(length=20), nullable=True))

    op.execute("UPDATE appointments SET status = 'pending' WHERE status IS NULL")

    op.alter_column('appointments', 'status', nullable=False)

    op.create_index(op.f('ix_appointments_status'), 'appointments', ['status'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_appointments_status'), table_name='appointments')
    op.drop_column('appointments', 'status')