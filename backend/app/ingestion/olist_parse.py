"""Read the published Olist CSVs. No network and no database access."""

import csv
from collections.abc import Iterator
from datetime import datetime
from decimal import Decimal
from pathlib import Path

SOURCE_URL = "https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce"
KAGGLE_HANDLE = "olistbr/brazilian-ecommerce"
LICENCE = "CC BY-NC-SA 4.0"
ATTRIBUTION = (
    "Olist. Brazilian E-Commerce Public Dataset by Olist. Kaggle. "
    "Licensed CC BY-NC-SA 4.0. Orders from 2016 to 2018. This is a published "
    "snapshot, not a live store."
)

FILE_NAMES = {
    "customers": "olist_customers_dataset.csv",
    "geolocation": "olist_geolocation_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "order_payments": "olist_order_payments_dataset.csv",
    "order_reviews": "olist_order_reviews_dataset.csv",
    "orders": "olist_orders_dataset.csv",
    "products": "olist_products_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "categories": "product_category_name_translation.csv",
}

COLUMNS = {
    "customers": (
        "customer_id",
        "customer_unique_id",
        "customer_zip_code_prefix",
        "customer_city",
        "customer_state",
    ),
    "geolocation": (
        "geolocation_zip_code_prefix",
        "geolocation_lat",
        "geolocation_lng",
        "geolocation_city",
        "geolocation_state",
    ),
    "order_items": (
        "order_id",
        "order_item_id",
        "product_id",
        "seller_id",
        "shipping_limit_date",
        "price",
        "freight_value",
    ),
    "order_payments": (
        "order_id",
        "payment_sequential",
        "payment_type",
        "payment_installments",
        "payment_value",
    ),
    "order_reviews": (
        "review_id",
        "order_id",
        "review_score",
        "review_comment_title",
        "review_comment_message",
        "review_creation_date",
        "review_answer_timestamp",
    ),
    "orders": (
        "order_id",
        "customer_id",
        "order_status",
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ),
    "products": (
        "product_id",
        "product_category_name",
        "product_name_lenght",
        "product_description_lenght",
        "product_photos_qty",
        "product_weight_g",
        "product_length_cm",
        "product_height_cm",
        "product_width_cm",
    ),
    "sellers": (
        "seller_id",
        "seller_zip_code_prefix",
        "seller_city",
        "seller_state",
    ),
    "categories": (
        "product_category_name",
        "product_category_name_english",
    ),
}


def locate_files(directory: Path) -> dict[str, Path]:
    """Return the nine published files. The directory is not modified."""
    found: dict[str, Path] = {}
    missing: list[str] = []
    for key, name in FILE_NAMES.items():
        path = directory / name
        if path.is_file():
            found[key] = path
        else:
            missing.append(name)
    if missing:
        joined = ", ".join(missing)
        raise FileNotFoundError(f"Olist directory is missing {joined}")
    return found


def iter_records(path: Path, kind: str) -> Iterator[tuple[object, ...]]:
    """Yield typed rows. Empty measurement cells stay null. Review ids are not deduplicated."""
    expected = COLUMNS[kind]
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        header = tuple(reader.fieldnames or ())
        if header != expected:
            raise ValueError(f"{path.name} columns were {header}, expected {expected}")
        for raw in reader:
            yield _RECORD[kind](raw)


def _text(row: dict[str, str], key: str) -> str:
    return (row.get(key) or "").strip()


def _optional_text(row: dict[str, str], key: str) -> str | None:
    value = _text(row, key)
    return value or None


def _timestamp(value: str, *, required: bool) -> datetime | None:
    text = value.strip()
    if not text:
        if required:
            raise ValueError("Olist timestamp was blank")
        return None
    return datetime.fromisoformat(text)


def _integer(value: str, *, required: bool) -> int | None:
    text = value.strip()
    if not text:
        if required:
            raise ValueError("Olist integer was blank")
        return None
    return int(text)


def _money(value: str) -> Decimal:
    text = value.strip()
    if not text:
        raise ValueError("Olist money value was blank")
    amount = Decimal(text)
    if amount < 0:
        raise ValueError("Olist money value was negative")
    return amount


def _float(value: str) -> float | None:
    text = value.strip()
    if not text:
        return None
    return float(text)


def _customer(row: dict[str, str]) -> tuple[object, ...]:
    return (
        _text(row, "customer_id"),
        _text(row, "customer_unique_id"),
        _text(row, "customer_zip_code_prefix"),
        _text(row, "customer_city"),
        _text(row, "customer_state"),
    )


def _seller(row: dict[str, str]) -> tuple[object, ...]:
    return (
        _text(row, "seller_id"),
        _text(row, "seller_zip_code_prefix"),
        _text(row, "seller_city"),
        _text(row, "seller_state"),
    )


def _category(row: dict[str, str]) -> tuple[object, ...]:
    return (
        _text(row, "product_category_name"),
        _optional_text(row, "product_category_name_english"),
    )


def _product(row: dict[str, str]) -> tuple[object, ...]:
    return (
        _text(row, "product_id"),
        _optional_text(row, "product_category_name"),
        _integer(row["product_name_lenght"], required=False),
        _integer(row["product_description_lenght"], required=False),
        _integer(row["product_photos_qty"], required=False),
        _integer(row["product_weight_g"], required=False),
        _integer(row["product_length_cm"], required=False),
        _integer(row["product_height_cm"], required=False),
        _integer(row["product_width_cm"], required=False),
    )


def _order(row: dict[str, str]) -> tuple[object, ...]:
    return (
        _text(row, "order_id"),
        _text(row, "customer_id"),
        _text(row, "order_status"),
        _timestamp(row["order_purchase_timestamp"], required=True),
        _timestamp(row["order_approved_at"], required=False),
        _timestamp(row["order_delivered_carrier_date"], required=False),
        _timestamp(row["order_delivered_customer_date"], required=False),
        _timestamp(row["order_estimated_delivery_date"], required=True),
    )


def _item(row: dict[str, str]) -> tuple[object, ...]:
    return (
        _text(row, "order_id"),
        _integer(row["order_item_id"], required=True),
        _text(row, "product_id"),
        _text(row, "seller_id"),
        _timestamp(row["shipping_limit_date"], required=True),
        _money(row["price"]),
        _money(row["freight_value"]),
    )


def _payment(row: dict[str, str]) -> tuple[object, ...]:
    return (
        _text(row, "order_id"),
        _integer(row["payment_sequential"], required=True),
        _text(row, "payment_type"),
        _integer(row["payment_installments"], required=True),
        _money(row["payment_value"]),
    )


def _review(row: dict[str, str]) -> tuple[object, ...]:
    score = _integer(row["review_score"], required=True)
    if score is None or score < 1 or score > 5:
        raise ValueError("Olist review score was outside 1 to 5")
    return (
        _text(row, "review_id"),
        _text(row, "order_id"),
        score,
        _optional_text(row, "review_comment_title"),
        _optional_text(row, "review_comment_message"),
        _timestamp(row["review_creation_date"], required=True),
        _timestamp(row["review_answer_timestamp"], required=False),
    )


def _geolocation(row: dict[str, str]) -> tuple[object, ...]:
    return (
        _text(row, "geolocation_zip_code_prefix"),
        _float(row["geolocation_lat"]),
        _float(row["geolocation_lng"]),
        _text(row, "geolocation_city"),
        _text(row, "geolocation_state"),
    )


_RECORD = {
    "customers": _customer,
    "sellers": _seller,
    "categories": _category,
    "products": _product,
    "orders": _order,
    "order_items": _item,
    "order_payments": _payment,
    "order_reviews": _review,
    "geolocation": _geolocation,
}
