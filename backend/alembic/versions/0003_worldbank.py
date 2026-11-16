"""World Bank indicator history and public document records.

Revision ID: 0003_worldbank
Revises: 0002_llm_traces
Create Date: 2026-11-16
"""

import sqlalchemy as sa
from alembic import op

revision = "0003_worldbank"
down_revision = "0002_llm_traces"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS worldbank")
    op.create_table(
        "indicators",
        sa.Column("code", sa.String(length=64), primary_key=True),
        sa.Column("name", sa.String(length=512), nullable=False),
        sa.Column("source_organization", sa.Text(), nullable=True),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        schema="worldbank",
    )
    op.create_table(
        "countries",
        sa.Column("code", sa.String(length=3), primary_key=True),
        sa.Column("name", sa.String(length=256), nullable=False),
        schema="worldbank",
    )
    op.create_table(
        "observations",
        sa.Column("country_code", sa.String(length=3), nullable=False),
        sa.Column("indicator_code", sa.String(length=64), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("value", sa.Float(), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["country_code"], ["worldbank.countries.code"]),
        sa.ForeignKeyConstraint(["indicator_code"], ["worldbank.indicators.code"]),
        sa.PrimaryKeyConstraint("country_code", "indicator_code", "year"),
        schema="worldbank",
    )
    op.create_table(
        "documents",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("doc_type", sa.String(length=256), nullable=True),
        sa.Column("document_date", sa.Date(), nullable=True),
        sa.Column("abstract", sa.Text(), nullable=True),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("pdf_url", sa.Text(), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        schema="worldbank",
    )
    op.create_table(
        "ingestion_runs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=False),
        sa.Column("detail", sa.Text(), nullable=True),
        schema="worldbank",
    )


def downgrade() -> None:
    op.drop_table("ingestion_runs", schema="worldbank")
    op.drop_table("documents", schema="worldbank")
    op.drop_table("observations", schema="worldbank")
    op.drop_table("countries", schema="worldbank")
    op.drop_table("indicators", schema="worldbank")
    op.execute("DROP SCHEMA IF EXISTS worldbank")
