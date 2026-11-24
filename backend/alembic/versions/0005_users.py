"""Application users.

Revision ID: 0005_users
Revises: 0004_olist
Create Date: 2026-11-23

Login accounts live in PostgreSQL. OpenFGA still answers document checks.
"""

import sqlalchemy as sa
from alembic import op

revision = "0005_users"
down_revision = "0004_olist"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS app")
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("display_name", sa.String(length=200), nullable=False),
        sa.Column("password_hash", sa.String(length=300), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        schema="app",
    )
    op.create_index("ix_app_users_email", "users", ["email"], unique=True, schema="app")


def downgrade() -> None:
    op.drop_index("ix_app_users_email", table_name="users", schema="app")
    op.drop_table("users", schema="app")
