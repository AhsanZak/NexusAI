"""OpenFGA grants for members and guests.

Revision ID: 0006_access_grants
Revises: 0005_users
Create Date: 2026-11-23

The rows are the grants an admin can change. OpenFGA Check reads the tuples
copied from these rows. authz_state.grants_seeded stops the default member
grants from being inserted again after an admin deletes them.
"""

import sqlalchemy as sa
from alembic import op

revision = "0006_access_grants"
down_revision = "0005_users"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "access_grants",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("subject", sa.String(length=200), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("relation", sa.String(length=32), nullable=False),
        sa.Column("object_id", sa.String(length=200), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["app.users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("subject", "relation", "object_id", name="uq_app_access_grant"),
        schema="app",
    )
    op.create_index("ix_app_access_grants_subject", "access_grants", ["subject"], schema="app")
    op.create_table(
        "authz_state",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("grants_seeded", sa.Boolean(), nullable=False),
        schema="app",
    )
    op.execute("INSERT INTO app.authz_state (id, grants_seeded) VALUES (1, false)")


def downgrade() -> None:
    op.drop_table("authz_state", schema="app")
    op.drop_index("ix_app_access_grants_subject", table_name="access_grants", schema="app")
    op.drop_table("access_grants", schema="app")
