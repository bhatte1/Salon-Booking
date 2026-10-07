"""Persist booking conversations and idempotent confirmation results."""
from alembic import op
import sqlalchemy as sa
revision = 'b17c0a000001'
down_revision = '98436bb57549'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('chat_conversations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('draft', sa.JSON(), nullable=False),
        sa.Column('history', sa.JSON(), nullable=False),
        sa.Column('receipts', sa.JSON(), nullable=False))
    op.create_index('ix_chat_conversations_user_id', 'chat_conversations', ['user_id'])


def downgrade():
    op.drop_table('chat_conversations')
