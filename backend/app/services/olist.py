"""Read Olist sales, product, review, and delivery aggregates."""

from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.engine import RowMapping

from app.core.database import engine
from app.ingestion.olist_parse import ATTRIBUTION, LICENCE, SOURCE_URL


async def load_dashboard() -> dict[str, object]:
    async with engine.connect() as connection:
        counts = (
            await connection.execute(
                text(
                    """
                    SELECT
                        (SELECT count(*) FROM olist.orders) AS orders,
                        (SELECT count(DISTINCT customer_unique_id)
                         FROM olist.customers) AS customers,
                        (SELECT count(*) FROM olist.products) AS products,
                        (SELECT count(*) FROM olist.sellers) AS sellers,
                        (SELECT count(*) FROM olist.order_items) AS items,
                        (SELECT count(*) FROM olist.order_reviews) AS reviews,
                        (SELECT count(*) FROM olist.geolocation) AS geolocation
                    """
                )
            )
        ).mappings().one()
        monthly = (
            await connection.execute(
                text(
                    """
                    SELECT to_char(date_trunc('month', o.purchase_at), 'YYYY-MM') AS month,
                           count(DISTINCT o.order_id) AS orders,
                           round(sum(i.price), 2) AS revenue,
                           round(sum(i.freight_value), 2) AS freight
                    FROM olist.orders AS o
                    JOIN olist.order_items AS i ON i.order_id = o.order_id
                    WHERE o.order_status <> 'canceled'
                    GROUP BY 1
                    ORDER BY 1
                    """
                )
            )
        ).mappings().all()
        statuses = (
            await connection.execute(
                text(
                    """
                    SELECT order_status AS status, count(*) AS orders
                    FROM olist.orders
                    GROUP BY 1
                    ORDER BY 2 DESC
                    """
                )
            )
        ).mappings().all()
        categories = (
            await connection.execute(
                text(
                    """
                    SELECT coalesce(
                               c.category_name_english, p.category_name, 'unknown'
                           ) AS category,
                           count(*) AS items,
                           round(sum(i.price), 2) AS revenue
                    FROM olist.order_items AS i
                    JOIN olist.orders AS o ON o.order_id = i.order_id
                    JOIN olist.products AS p ON p.product_id = i.product_id
                    LEFT JOIN olist.product_categories AS c
                        ON c.category_name = p.category_name
                    WHERE o.order_status <> 'canceled'
                    GROUP BY 1
                    ORDER BY revenue DESC
                    LIMIT 10
                    """
                )
            )
        ).mappings().all()
        scores = (
            await connection.execute(
                text(
                    """
                    SELECT score, count(*) AS reviews
                    FROM olist.order_reviews
                    GROUP BY 1
                    ORDER BY 1
                    """
                )
            )
        ).mappings().all()
        review_summary = (
            await connection.execute(
                text(
                    """
                    SELECT count(*) AS reviews,
                           round(avg(score), 2) AS average_score,
                           count(*) FILTER (WHERE comment_message IS NOT NULL) AS with_comment
                    FROM olist.order_reviews
                    """
                )
            )
        ).mappings().one()
        delivery = (
            await connection.execute(
                text(
                    """
                    SELECT count(*) AS delivered,
                           count(*) FILTER (
                               WHERE delivered_customer_at <= estimated_delivery_at
                           ) AS on_time,
                           count(*) FILTER (
                               WHERE delivered_customer_at > estimated_delivery_at
                           ) AS late,
                           round(avg(
                               extract(epoch FROM (delivered_customer_at - purchase_at)) / 86400
                           )::numeric, 2) AS average_days
                    FROM olist.orders
                    WHERE order_status = 'delivered'
                      AND delivered_customer_at IS NOT NULL
                      AND estimated_delivery_at IS NOT NULL
                    """
                )
            )
        ).mappings().one()
        payments = (
            await connection.execute(
                text(
                    """
                    SELECT payment_type,
                           count(*) AS payments,
                           round(sum(payment_value), 2) AS amount
                    FROM olist.order_payments
                    GROUP BY 1
                    ORDER BY amount DESC
                    """
                )
            )
        ).mappings().all()
    delivered = int(delivery["delivered"] or 0)
    on_time = int(delivery["on_time"] or 0)
    return {
        "attribution": ATTRIBUTION,
        "source_url": SOURCE_URL,
        "licence": LICENCE,
        "currency": "BRL",
        "counts": {key: int(value or 0) for key, value in counts.items()},
        "monthly_sales": [_monthly(row) for row in monthly],
        "order_status": [_status(row) for row in statuses],
        "categories": [_category(row) for row in categories],
        "review_scores": [_score(row) for row in scores],
        "review_summary": {
            "reviews": int(review_summary["reviews"] or 0),
            "average_score": _number(review_summary["average_score"]),
            "with_comment": int(review_summary["with_comment"] or 0),
        },
        "delivery": {
            "delivered": delivered,
            "on_time": on_time,
            "late": int(delivery["late"] or 0),
            "on_time_percent": round((on_time / delivered) * 100, 1) if delivered else 0,
            "average_days": _number(delivery["average_days"]),
        },
        "payments": [_payment(row) for row in payments],
    }


def _monthly(row: RowMapping) -> dict[str, object]:
    return {
        "month": row["month"],
        "orders": int(row["orders"]),
        "revenue": _number(row["revenue"]),
        "freight": _number(row["freight"]),
    }


def _status(row: RowMapping) -> dict[str, object]:
    return {"status": row["status"], "orders": int(row["orders"])}


def _category(row: RowMapping) -> dict[str, object]:
    return {
        "category": row["category"],
        "items": int(row["items"]),
        "revenue": _number(row["revenue"]),
    }


def _score(row: RowMapping) -> dict[str, object]:
    return {"score": int(row["score"]), "reviews": int(row["reviews"])}


def _payment(row: RowMapping) -> dict[str, object]:
    return {
        "payment_type": row["payment_type"],
        "payments": int(row["payments"]),
        "amount": _number(row["amount"]),
    }


def _number(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float | str | Decimal):
        return 0
    return float(value)
