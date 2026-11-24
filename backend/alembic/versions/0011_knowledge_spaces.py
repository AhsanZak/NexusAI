"""Record which knowledge space an upload and a chat belong to.

Revision ID: 0011_knowledge_spaces
Revises: 0010_user_intent
Create Date: 2026-11-24
"""

import sqlalchemy as sa
from alembic import op

revision = "0011_knowledge_spaces"
down_revision = "0010_user_intent"
branch_labels = None
depends_on = None

_IMAGE = (".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".bmp")


def upgrade() -> None:
    op.add_column(
        "uploaded_documents",
        sa.Column("space", sa.String(length=20), nullable=True),
        schema="app",
    )
    op.add_column(
        "chat_conversations",
        sa.Column("space", sa.String(length=20), nullable=True),
        schema="app",
    )
    image_match = " OR ".join(f"lower(filename) LIKE '%{item}'" for item in _IMAGE)
    op.execute(
        sa.text(
            f"""
            UPDATE app.uploaded_documents
            SET space = CASE
                WHEN lower(filename) LIKE '%.pdf' THEN 'pdf'
                WHEN lower(filename) LIKE '%.xlsx' OR lower(filename) LIKE '%.csv' THEN 'excel'
                WHEN {image_match} THEN 'image'
                WHEN lower(filename) LIKE '%.mp4'
                    OR lower(filename) LIKE '%.webm'
                    OR lower(filename) LIKE '%.mov' THEN 'video'
                ELSE 'document'
            END
            """
        )
    )
    op.alter_column("uploaded_documents", "space", nullable=False, schema="app")
    op.execute(
        sa.text(
            """
            UPDATE app.chat_conversations AS chat
            SET space = doc.space
            FROM app.uploaded_documents AS doc
            WHERE chat.document_id = doc.id
            """
        )
    )


def downgrade() -> None:
    op.drop_column("chat_conversations", "space", schema="app")
    op.drop_column("uploaded_documents", "space", schema="app")
