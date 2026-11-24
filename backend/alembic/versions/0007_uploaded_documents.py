"""Uploaded documents and their retrieved chunks.

Revision ID: 0007_uploaded_documents
Revises: 0006_access_grants
Create Date: 2026-11-23

The file bytes stay on disk. PostgreSQL keeps the extracted text, the markdown
tables, and the term vectors used to choose excerpts for the local model.
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0007_uploaded_documents"
down_revision = "0006_access_grants"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "uploaded_documents",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("filename", sa.String(length=300), nullable=False),
        sa.Column("media_type", sa.String(length=120), nullable=False),
        sa.Column("storage_name", sa.String(length=80), nullable=False),
        sa.Column("extracted_text", sa.Text(), nullable=False),
        sa.Column("extractor", sa.String(length=40), nullable=False),
        sa.Column("embedding_kind", sa.String(length=40), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["owner_id"], ["app.users.id"], ondelete="CASCADE"),
        schema="app",
    )
    op.create_index(
        "ix_app_uploaded_documents_owner",
        "uploaded_documents",
        ["owner_id"],
        schema="app",
    )
    op.create_table(
        "document_chunks",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", postgresql.JSONB(), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["app.uploaded_documents.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("document_id", "chunk_index", name="uq_app_document_chunk"),
        schema="app",
    )


def downgrade() -> None:
    op.drop_table("document_chunks", schema="app")
    op.drop_index("ix_app_uploaded_documents_owner", table_name="uploaded_documents", schema="app")
    op.drop_table("uploaded_documents", schema="app")
