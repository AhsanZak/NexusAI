"""Parser tests use tiny CSV fixtures, not the Kaggle download."""

from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pytest

from app.ingestion.olist_parse import iter_records, locate_files


def _write(directory: Path, name: str, body: str) -> None:
    (directory / name).write_text(body.strip() + "\n", encoding="utf-8")


def test_locate_files_requires_every_published_csv(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="olist_orders_dataset.csv"):
        locate_files(tmp_path)


def test_product_row_keeps_blank_measurements_null(tmp_path: Path) -> None:
    path = tmp_path / "olist_products_dataset.csv"
    _write(
        tmp_path,
        path.name,
        """
product_id,product_category_name,product_name_lenght,product_description_lenght,product_photos_qty,product_weight_g,product_length_cm,product_height_cm,product_width_cm
abc,beleza,,,,,100,,
""",
    )

    rows = list(iter_records(path, "products"))

    assert rows == [("abc", "beleza", None, None, None, None, 100, None, None)]


def test_reviews_keep_repeated_review_ids(tmp_path: Path) -> None:
    path = tmp_path / "olist_order_reviews_dataset.csv"
    _write(
        tmp_path,
        path.name,
        """
review_id,order_id,review_score,review_comment_title,review_comment_message,review_creation_date,review_answer_timestamp
same,order-1,5,Title,Message,2018-01-01 00:00:00,2018-01-02 00:00:00
same,order-2,4,,,2018-01-03 00:00:00,
""",
    )

    rows = list(iter_records(path, "order_reviews"))

    assert len(rows) == 2
    assert rows[0][0] == rows[1][0] == "same"
    assert rows[0][2] == 5
    assert rows[1][3] is None
    assert rows[1][5] == datetime(2018, 1, 3)


def test_item_price_is_decimal_and_rejects_a_negative(tmp_path: Path) -> None:
    path = tmp_path / "olist_order_items_dataset.csv"
    _write(
        tmp_path,
        path.name,
        """
order_id,order_item_id,product_id,seller_id,shipping_limit_date,price,freight_value
order-1,1,product-1,seller-1,2018-01-01 00:00:00,12.50,3.00
""",
    )

    row = next(iter(iter_records(path, "order_items")))

    assert row[5] == Decimal("12.50")
    assert row[6] == Decimal("3.00")
