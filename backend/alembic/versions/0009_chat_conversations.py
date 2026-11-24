"""Separate chats so each one keeps its own history.

Revision ID: 0009_chat_conversations
Revises: 0008_chat_history
Create Date: 2026-11-24
"""

import sqlalchemy as sa
from alembic import op

revision = "0009_chat_conversations"
down_revision = "0008_chat_history"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "chat_conversations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=True),
        sa.Column("title", sa.String(length=80), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["app.users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["app.uploaded_documents.id"],
            ondelete="CASCADE",
        ),
        schema="app",
    )
    op.add_column(
        "chat_messages",
        sa.Column("conversation_id", sa.Uuid(), nullable=True),
        schema="app",
    )
    op.execute(
        """
        INSERT INTO app.chat_conversations
            (id, user_id, document_id, title, created_at, updated_at)
        SELECT gen_random_uuid(), user_id, document_id, 'Earlier chat',
               MIN(created_at), MAX(created_at)
        FROM app.chat_messages
        GROUP BY user_id, document_id
        """
    )
    op.execute(
        """
        UPDATE app.chat_messages AS message
        SET conversation_id = conversation.id
        FROM app.chat_conversations AS conversation
        WHERE message.user_id = conversation.user_id
          AND message.document_id IS NOT DISTINCT FROM conversation.document_id
        """
    )
    op.alter_column("chat_messages", "conversation_id", nullable=False, schema="app")
    op.create_foreign_key(
        "fk_app_chat_messages_conversation_id",
        "chat_messages",
        "chat_conversations",
        ["conversation_id"],
        ["id"],
        source_schema="app",
        referent_schema="app",
        ondelete="CASCADE",
    )
    op.create_index(
        "ix_app_chat_conversations_user",
        "chat_conversations",
        ["user_id", "document_id", "updated_at"],
        schema="app",
    )
    op.create_index(
        "ix_app_chat_messages_conversation",
        "chat_messages",
        ["conversation_id", "created_at"],
        schema="app",
    )


def downgrade() -> None:
    op.drop_index("ix_app_chat_messages_conversation", table_name="chat_messages", schema="app")
    op.drop_constraint(
        "fk_app_chat_messages_conversation_id",
        "chat_messages",
        schema="app",
        type_="foreignkey",
    )
    op.drop_column("chat_messages", "conversation_id", schema="app")
    op.drop_index("ix_app_chat_conversations_user", table_name="chat_conversations", schema="app")
    op.drop_table("chat_conversations", schema="app")
