"""Create the model-call trace table.

Revision ID: 0002_llm_traces
Revises: 0001_pgvector
Create Date: 2026-11-16
"""

import sqlalchemy as sa
from alembic import op

revision = "0002_llm_traces"
down_revision = "0001_pgvector"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "llm_traces",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("model_alias", sa.String(length=128), nullable=False),
        sa.Column("model", sa.String(length=256), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("latency_ms", sa.Float(), nullable=True),
        sa.Column("timeout_seconds", sa.Float(), nullable=False),
        sa.Column("max_retries", sa.Integer(), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=True),
        sa.Column("completion_tokens", sa.Integer(), nullable=True),
        sa.Column("total_tokens", sa.Integer(), nullable=True),
        sa.Column("request_messages", sa.JSON(), nullable=False),
        sa.Column("response_text", sa.Text(), nullable=True),
        sa.Column("provider_response_id", sa.String(length=128), nullable=True),
        sa.Column("error_type", sa.String(length=128), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
    )
    op.create_index("ix_llm_traces_created_at", "llm_traces", ["created_at"])
    op.create_index("ix_llm_traces_status", "llm_traces", ["status"])


def downgrade() -> None:
    op.drop_index("ix_llm_traces_status", table_name="llm_traces")
    op.drop_index("ix_llm_traces_created_at", table_name="llm_traces")
    op.drop_table("llm_traces")
