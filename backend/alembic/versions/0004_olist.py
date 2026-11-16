"""Olist Brazilian e-commerce warehouse.

Revision ID: 0004_olist
Revises: 0003_worldbank
Create Date: 2026-11-16

The published CSVs stay out of git. This schema holds a relational copy of the
Kaggle snapshot and records the licence with each ingestion run.
"""

import sqlalchemy as sa
from alembic import op

revision = "0004_olist"
down_revision = "0003_worldbank"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS olist")
    op.create_table(
        "product_categories",
        sa.Column("category_name", sa.String(length=128), primary_key=True),
        sa.Column("category_name_english", sa.String(length=128), nullable=True),
        schema="olist",
    )
    op.create_table(
        "customers",
        sa.Column("customer_id", sa.String(length=32), primary_key=True),
        sa.Column("customer_unique_id", sa.String(length=32), nullable=False),
        sa.Column("zip_code_prefix", sa.String(length=8), nullable=False),
        sa.Column("city", sa.String(length=128), nullable=False),
        sa.Column("state", sa.String(length=2), nullable=False),
        schema="olist",
    )
    op.create_index("ix_olist_customers_unique", "customers", ["customer_unique_id"], schema="olist")
    op.create_table(
        "sellers",
        sa.Column("seller_id", sa.String(length=32), primary_key=True),
        sa.Column("zip_code_prefix", sa.String(length=8), nullable=False),
        sa.Column("city", sa.String(length=128), nullable=False),
        sa.Column("state", sa.String(length=2), nullable=False),
        schema="olist",
    )
    op.create_table(
        "products",
        sa.Column("product_id", sa.String(length=32), primary_key=True),
        sa.Column("category_name", sa.String(length=128), nullable=True),
        sa.Column("name_length", sa.Integer(), nullable=True),
        sa.Column("description_length", sa.Integer(), nullable=True),
        sa.Column("photos_qty", sa.Integer(), nullable=True),
        sa.Column("weight_g", sa.Integer(), nullable=True),
        sa.Column("length_cm", sa.Integer(), nullable=True),
        sa.Column("height_cm", sa.Integer(), nullable=True),
        sa.Column("width_cm", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["category_name"],
            ["olist.product_categories.category_name"],
        ),
        schema="olist",
    )
    op.create_table(
        "orders",
        sa.Column("order_id", sa.String(length=32), primary_key=True),
        sa.Column("customer_id", sa.String(length=32), nullable=False),
        sa.Column("order_status", sa.String(length=32), nullable=False),
        sa.Column("purchase_at", sa.DateTime(timezone=False), nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=False), nullable=True),
        sa.Column("delivered_carrier_at", sa.DateTime(timezone=False), nullable=True),
        sa.Column("delivered_customer_at", sa.DateTime(timezone=False), nullable=True),
        sa.Column("estimated_delivery_at", sa.DateTime(timezone=False), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["olist.customers.customer_id"]),
        schema="olist",
    )
    op.create_index("ix_olist_orders_purchase", "orders", ["purchase_at"], schema="olist")
    op.create_index("ix_olist_orders_status", "orders", ["order_status"], schema="olist")
    op.create_table(
        "order_items",
        sa.Column("order_id", sa.String(length=32), nullable=False),
        sa.Column("order_item_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.String(length=32), nullable=False),
        sa.Column("seller_id", sa.String(length=32), nullable=False),
        sa.Column("shipping_limit_at", sa.DateTime(timezone=False), nullable=False),
        sa.Column("price", sa.Numeric(12, 2), nullable=False),
        sa.Column("freight_value", sa.Numeric(12, 2), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["olist.orders.order_id"]),
        sa.ForeignKeyConstraint(["product_id"], ["olist.products.product_id"]),
        sa.ForeignKeyConstraint(["seller_id"], ["olist.sellers.seller_id"]),
        sa.PrimaryKeyConstraint("order_id", "order_item_id"),
        schema="olist",
    )
    op.create_table(
        "order_payments",
        sa.Column("order_id", sa.String(length=32), nullable=False),
        sa.Column("payment_sequential", sa.Integer(), nullable=False),
        sa.Column("payment_type", sa.String(length=32), nullable=False),
        sa.Column("payment_installments", sa.Integer(), nullable=False),
        sa.Column("payment_value", sa.Numeric(12, 2), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["olist.orders.order_id"]),
        sa.PrimaryKeyConstraint("order_id", "payment_sequential"),
        schema="olist",
    )
    op.create_table(
        "order_reviews",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("review_id", sa.String(length=32), nullable=False),
        sa.Column("order_id", sa.String(length=32), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("comment_title", sa.Text(), nullable=True),
        sa.Column("comment_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=False), nullable=False),
        sa.Column("answered_at", sa.DateTime(timezone=False), nullable=True),
        sa.ForeignKeyConstraint(["order_id"], ["olist.orders.order_id"]),
        schema="olist",
    )
    op.create_index("ix_olist_reviews_score", "order_reviews", ["score"], schema="olist")
    op.create_table(
        "geolocation",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("zip_code_prefix", sa.String(length=8), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("city", sa.String(length=128), nullable=False),
        sa.Column("state", sa.String(length=2), nullable=False),
        schema="olist",
    )
    op.create_index("ix_olist_geolocation_zip", "geolocation", ["zip_code_prefix"], schema="olist")
    op.create_table(
        "ingestion_runs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("source", sa.String(length=128), nullable=False),
        sa.Column("licence", sa.String(length=64), nullable=False),
        sa.Column("attribution", sa.Text(), nullable=False),
        sa.Column("source_path", sa.Text(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=False),
        sa.Column("detail", sa.Text(), nullable=True),
        schema="olist",
    )


def downgrade() -> None:
    op.drop_table("ingestion_runs", schema="olist")
    op.drop_table("geolocation", schema="olist")
    op.drop_table("order_reviews", schema="olist")
    op.drop_table("order_payments", schema="olist")
    op.drop_table("order_items", schema="olist")
    op.drop_table("orders", schema="olist")
    op.drop_table("products", schema="olist")
    op.drop_table("sellers", schema="olist")
    op.drop_table("customers", schema="olist")
    op.drop_table("product_categories", schema="olist")
    op.execute("DROP SCHEMA IF EXISTS olist")
