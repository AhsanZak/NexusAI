"""Store the intent understood for each question.

Revision ID: 0010_user_intent
Revises: 0009_chat_conversations
Create Date: 2026-11-24
"""

import sqlalchemy as sa
from alembic import op

revision = "0010_user_intent"
down_revision = "0009_chat_conversations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "chat_conversations",
        sa.Column("intent", sa.String(length=40), nullable=True),
        schema="app",
    )
    op.add_column(
        "chat_messages",
        sa.Column("intent", sa.String(length=40), nullable=True),
        schema="app",
    )


def downgrade() -> None:
    op.drop_column("chat_messages", "intent", schema="app")
    op.drop_column("chat_conversations", "intent", schema="app")
