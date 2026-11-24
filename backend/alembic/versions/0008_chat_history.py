"""Per-user chat history and the selected model.

Revision ID: 0008_chat_history
Revises: 0007_uploaded_documents
Create Date: 2026-11-23
"""

import sqlalchemy as sa
from alembic import op

revision = "0008_chat_history"
down_revision = "0007_uploaded_documents"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "chat_preferences",
        sa.Column("user_id", sa.Uuid(), primary_key=True),
        sa.Column("model_id", sa.String(length=40), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["app.users.id"], ondelete="CASCADE"),
        schema="app",
    )
    op.create_table(
        "chat_messages",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=True),
        sa.Column("model_name", sa.String(length=40), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["app.users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["document_id"], ["app.uploaded_documents.id"], ondelete="CASCADE"),
        schema="app",
    )
    op.create_index(
        "ix_app_chat_messages_user",
        "chat_messages",
        ["user_id", "document_id", "created_at"],
        schema="app",
    )


def downgrade() -> None:
    op.drop_index("ix_app_chat_messages_user", table_name="chat_messages", schema="app")
    op.drop_table("chat_messages", schema="app")
    op.drop_table("chat_preferences", schema="app")
