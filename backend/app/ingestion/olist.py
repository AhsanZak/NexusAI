"""Load the Olist Kaggle snapshot into the olist schema."""

import asyncio
import hashlib
import json
import shutil
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, create_async_engine

from app.core.config import get_settings
from app.ingestion.olist_parse import (
    ATTRIBUTION,
    KAGGLE_HANDLE,
    LICENCE,
    SOURCE_URL,
    iter_records,
    locate_files,
)

log = structlog.get_logger(__name__)

BATCH = 20_000
REPO_ROOT = Path(__file__).resolve().parents[3]
PRESERVED_DIR = REPO_ROOT / "data" / "raw" / "olist"

COPY_COLUMNS = {
    "customers": ("customer_id", "customer_unique_id", "zip_code_prefix", "city", "state"),
    "sellers": ("seller_id", "zip_code_prefix", "city", "state"),
    "categories": ("category_name", "category_name_english"),
    "products": (
        "product_id",
        "category_name",
        "name_length",
        "description_length",
        "photos_qty",
        "weight_g",
        "length_cm",
        "height_cm",
        "width_cm",
    ),
    "orders": (
        "order_id",
        "customer_id",
        "order_status",
        "purchase_at",
        "approved_at",
        "delivered_carrier_at",
        "delivered_customer_at",
        "estimated_delivery_at",
    ),
    "order_items": (
        "order_id",
        "order_item_id",
        "product_id",
        "seller_id",
        "shipping_limit_at",
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
        "score",
        "comment_title",
        "comment_message",
        "created_at",
        "answered_at",
    ),
    "geolocation": ("zip_code_prefix", "latitude", "longitude", "city", "state"),
}

TABLES = {
    "customers": "customers",
    "sellers": "sellers",
    "categories": "product_categories",
    "products": "products",
    "orders": "orders",
    "order_items": "order_items",
    "order_payments": "order_payments",
    "order_reviews": "order_reviews",
    "geolocation": "geolocation",
}


@dataclass(frozen=True)
class IngestResult:
    counts: dict[str, int]
    source_path: str


def download_olist() -> Path:
    """Download the public Kaggle snapshot. The returned directory is the unmodified archive."""
    import kagglehub  # type: ignore[import-untyped]

    downloaded = kagglehub.dataset_download(KAGGLE_HANDLE)
    return Path(str(downloaded))


def preserve_files(source: Path) -> Path:
    """Copy the nine CSVs into gitignored data/raw/olist without changing the Kaggle cache."""
    files = locate_files(source)
    PRESERVED_DIR.mkdir(parents=True, exist_ok=True)
    if source.resolve() == PRESERVED_DIR.resolve():
        return PRESERVED_DIR
    for path in files.values():
        target = PRESERVED_DIR / path.name
        if target.resolve() != path.resolve():
            shutil.copy2(path, target)
    return PRESERVED_DIR


async def ingest_olist(
    engine: AsyncEngine | None = None,
    directory: Path | None = None,
) -> IngestResult:
    started = datetime.now(UTC)
    source = directory or download_olist()
    preserved = preserve_files(source)
    files = locate_files(preserved)
    own_engine = engine is None
    active = engine or create_async_engine(get_settings().database_url)
    try:
        counts = await _load(active, files, preserved, started)
        log.info("olist_ingest_finished", **counts)
        return IngestResult(counts, str(preserved))
    finally:
        if own_engine:
            await active.dispose()


async def _load(
    engine: AsyncEngine,
    files: dict[str, Path],
    preserved: Path,
    started: datetime,
) -> dict[str, int]:
    categories = list(iter_records(files["categories"], "categories"))
    products = list(iter_records(files["products"], "products"))
    known = {str(row[0]) for row in categories}
    missing_names = sorted({str(row[1]) for row in products if row[1] and str(row[1]) not in known})
    categories.extend((name, None) for name in missing_names)

    async with engine.begin() as connection:
        raw = await connection.get_raw_connection()
        driver = raw.driver_connection
        if driver is None:
            raise RuntimeError("PostgreSQL driver connection was not available")
        await connection.execute(
            text(
                """
                TRUNCATE TABLE
                    olist.order_items,
                    olist.order_payments,
                    olist.order_reviews,
                    olist.geolocation,
                    olist.orders,
                    olist.products,
                    olist.sellers,
                    olist.customers,
                    olist.product_categories
                RESTART IDENTITY
                """
            )
        )
        counts = {
            "categories": await _copy(driver, "categories", categories),
            "customers": await _copy_file(driver, "customers", files["customers"]),
            "sellers": await _copy_file(driver, "sellers", files["sellers"]),
            "products": await _copy(driver, "products", products),
            "orders": await _copy_file(driver, "orders", files["orders"]),
            "order_items": await _copy_file(driver, "order_items", files["order_items"]),
            "order_payments": await _copy_file(driver, "order_payments", files["order_payments"]),
            "order_reviews": await _copy_file(driver, "order_reviews", files["order_reviews"]),
            "geolocation": await _copy_file(driver, "geolocation", files["geolocation"]),
        }
        await _check_counts(connection, counts)
        notes = []
        if missing_names:
            notes.append(
                "Published translation file has no English name for: " + ", ".join(missing_names)
            )
        review_gap = await connection.scalar(
            text("SELECT count(*) - count(DISTINCT review_id) FROM olist.order_reviews")
        )
        if review_gap:
            notes.append(
                f"The published review file repeats review_id on {int(review_gap)} extra rows. "
                "Each published row is kept."
            )
        detail = {
            "source_url": SOURCE_URL,
            "kaggle_handle": KAGGLE_HANDLE,
            "files": {path.name: _file_record(path) for path in files.values()},
            "notes": notes,
        }
        await connection.execute(
            text(
                """
                INSERT INTO olist.ingestion_runs (
                    id, source, licence, attribution, source_path,
                    started_at, finished_at, status, row_count, detail
                )
                VALUES (
                    :id, :source, :licence, :attribution, :source_path,
                    :started_at, :finished_at, 'loaded', :row_count, :detail
                )
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "source": KAGGLE_HANDLE,
                "licence": LICENCE,
                "attribution": ATTRIBUTION,
                "source_path": str(preserved),
                "started_at": started,
                "finished_at": datetime.now(UTC),
                "row_count": sum(counts.values()),
                "detail": json.dumps(detail),
            },
        )
    return counts


async def _copy(driver: Any, kind: str, rows: list[tuple[object, ...]]) -> int:
    await _write(driver, kind, rows)
    return len(rows)


async def _copy_file(driver: Any, kind: str, path: Path) -> int:
    batch: list[tuple[object, ...]] = []
    count = 0
    for record in iter_records(path, kind):
        batch.append(record)
        count += 1
        if len(batch) >= BATCH:
            await _write(driver, kind, batch)
            batch = []
    if batch:
        await _write(driver, kind, batch)
    return count


async def _write(driver: Any, kind: str, rows: list[tuple[object, ...]]) -> None:
    if not rows:
        return
    await driver.copy_records_to_table(
        TABLES[kind],
        schema_name="olist",
        records=rows,
        columns=list(COPY_COLUMNS[kind]),
    )


async def _check_counts(connection: AsyncConnection, counts: dict[str, int]) -> None:
    for kind, expected in counts.items():
        table = TABLES[kind]
        stored = await connection.scalar(text(f"SELECT count(*) FROM olist.{table}"))
        if int(stored or 0) != expected:
            raise RuntimeError(f"olist.{table} stored {stored} rows, file had {expected}")


def _file_record(path: Path) -> dict[str, object]:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return {"bytes": path.stat().st_size, "sha256": digest.hexdigest()}


def main() -> None:
    result = asyncio.run(ingest_olist())
    print(f"source={result.source_path}")
    for name, count in result.counts.items():
        print(f"{name}={count}")


if __name__ == "__main__":
    main()
