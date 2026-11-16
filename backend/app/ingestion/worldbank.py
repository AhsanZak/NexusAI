"""Download a bounded World Bank indicator history and a page of public reports."""

import asyncio
import io
import uuid
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime

import httpx
import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.core.config import get_settings
from app.ingestion.worldbank_parse import (
    DocumentRow,
    ObservationRow,
    parse_documents_payload,
    parse_indicator_csv,
)

log = structlog.get_logger(__name__)

INDICATOR_API = "https://api.worldbank.org/v2"
DOCUMENT_API = "https://search.worldbank.org/api/v3/wds"
USER_AGENT = "NexusAI/0.3 (local research; public World Bank data)"
COUNTRIES = (
    "BRA",
    "CHN",
    "DEU",
    "FRA",
    "GBR",
    "IDN",
    "IND",
    "JPN",
    "MEX",
    "NGA",
    "USA",
    "ZAF",
)
INDICATORS = (
    "NY.GDP.MKTP.CD",
    "FP.CPI.TOTL.ZG",
    "SP.POP.TOTL",
    "SL.EMP.TOTL.SP.ZS",
    "NE.IMP.GNFS.CD",
    "NE.EXP.GNFS.CD",
)
YEAR_FROM = 2000
YEAR_TO = 2024
DOCUMENT_QUERY = "World Development Report"
DOCUMENT_ROWS = 12


@dataclass
class IngestResult:
    observations: int
    documents: int
    errors: list[str]


async def ingest_worldbank() -> IngestResult:
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    started = datetime.now(UTC)
    run_id = str(uuid.uuid4())
    try:
        async with httpx.AsyncClient(timeout=60, headers={"User-Agent": USER_AGENT}) as client:
            observations, indicator_errors = await _indicators(client)
            documents, document_errors = await _documents(client)
        errors = indicator_errors + document_errors
        await _store(engine, observations, documents, run_id, started, errors)
        log.info(
            "worldbank_ingest_finished",
            observations=len(observations),
            documents=len(documents),
            errors=len(errors),
        )
        return IngestResult(len(observations), len(documents), errors)
    finally:
        await engine.dispose()


async def _indicators(client: httpx.AsyncClient) -> tuple[list[ObservationRow], list[str]]:
    """Download the official CSV extract. The JSON history pages currently return HTTP 502."""
    rows: list[ObservationRow] = []
    errors: list[str] = []
    allowed = set(COUNTRIES)
    for code in INDICATORS:
        source_url = f"{INDICATOR_API}/en/indicator/{code}?downloadformat=csv"
        try:
            response = await client.get(source_url)
            response.raise_for_status()
            contents = _csv_from_zip(response.content)
            rows.extend(
                parse_indicator_csv(
                    contents,
                    source_url=source_url,
                    countries=allowed,
                    year_from=YEAR_FROM,
                    year_to=YEAR_TO,
                )
            )
        except (httpx.HTTPError, ValueError, zipfile.BadZipFile, KeyError) as exc:
            errors.append(f"{code}: {type(exc).__name__}")
            log.warning("worldbank_indicator_failed", indicator=code, error_type=type(exc).__name__)
        await asyncio.sleep(0.4)
    return rows, errors


def _csv_from_zip(content: bytes) -> str:
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        names = archive.namelist()
        name = next(item for item in names if item.startswith("API_") and item.endswith(".csv"))
        return archive.read(name).decode("utf-8-sig")


async def _documents(client: httpx.AsyncClient) -> tuple[list[DocumentRow], list[str]]:
    params = {
        "format": "json",
        "qterm": DOCUMENT_QUERY,
        "rows": str(DOCUMENT_ROWS),
        "os": "0",
        "fl": "display_title,docdt,url,pdfurl,docty,abstracts,id",
    }
    query = DOCUMENT_QUERY.replace(" ", "%20")
    source_url = f"{DOCUMENT_API}?format=json&qterm={query}&rows={DOCUMENT_ROWS}"
    try:
        response = await client.get(DOCUMENT_API, params=params)
        response.raise_for_status()
        return parse_documents_payload(response.json(), source_url=source_url), []
    except (httpx.HTTPError, ValueError) as exc:
        log.warning("worldbank_documents_failed", error_type=type(exc).__name__)
        return [], [f"documents: {type(exc).__name__}"]


async def _store(
    engine: AsyncEngine,
    observations: list[ObservationRow],
    documents: list[DocumentRow],
    run_id: str,
    started: datetime,
    errors: list[str],
) -> None:
    retrieved_at = datetime.now(UTC)
    status = "success" if not errors else "partial"
    if not observations and not documents:
        status = "error"
    async with engine.begin() as connection:
        for row in observations:
            await connection.execute(
                text(
                    """
                    INSERT INTO worldbank.countries (code, name)
                    VALUES (:code, :name)
                    ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name
                    """
                ),
                {"code": row.country_code, "name": row.country_name},
            )
            await connection.execute(
                text(
                    """
                    INSERT INTO worldbank.indicators (code, name, source_organization, retrieved_at)
                    VALUES (:code, :name, :organization, :retrieved_at)
                    ON CONFLICT (code) DO UPDATE
                    SET name = EXCLUDED.name, retrieved_at = EXCLUDED.retrieved_at
                    """
                ),
                {
                    "code": row.indicator_code,
                    "name": row.indicator_name,
                    "organization": "World Bank",
                    "retrieved_at": retrieved_at,
                },
            )
            await connection.execute(
                text(
                    """
                    INSERT INTO worldbank.observations (
                        country_code, indicator_code, year, value, source_url, retrieved_at
                    )
                    VALUES (
                        :country_code, :indicator_code, :year, :value, :source_url, :retrieved_at
                    )
                    ON CONFLICT (country_code, indicator_code, year) DO UPDATE
                    SET value = EXCLUDED.value,
                        source_url = EXCLUDED.source_url,
                        retrieved_at = EXCLUDED.retrieved_at
                    """
                ),
                {
                    "country_code": row.country_code,
                    "indicator_code": row.indicator_code,
                    "year": row.year,
                    "value": row.value,
                    "source_url": row.source_url,
                    "retrieved_at": retrieved_at,
                },
            )
        for document in documents:
            await connection.execute(
                text(
                    """
                    INSERT INTO worldbank.documents (
                        id, title, doc_type, document_date, abstract, url, pdf_url,
                        source_url, retrieved_at
                    )
                    VALUES (
                        :id, :title, :doc_type, :document_date, :abstract, :url, :pdf_url,
                        :source_url, :retrieved_at
                    )
                    ON CONFLICT (id) DO UPDATE
                    SET title = EXCLUDED.title,
                        doc_type = EXCLUDED.doc_type,
                        document_date = EXCLUDED.document_date,
                        abstract = EXCLUDED.abstract,
                        url = EXCLUDED.url,
                        pdf_url = EXCLUDED.pdf_url,
                        source_url = EXCLUDED.source_url,
                        retrieved_at = EXCLUDED.retrieved_at
                    """
                ),
                {
                    "id": document.id,
                    "title": document.title,
                    "doc_type": document.doc_type,
                    "document_date": document.document_date,
                    "abstract": document.abstract,
                    "url": document.url,
                    "pdf_url": document.pdf_url,
                    "source_url": document.source_url,
                    "retrieved_at": retrieved_at,
                },
            )
        await connection.execute(
            text(
                """
                INSERT INTO worldbank.ingestion_runs (
                    id, source, started_at, finished_at, status, row_count, detail
                )
                VALUES (
                    :id, 'worldbank', :started_at, :finished_at, :status, :row_count, :detail
                )
                """
            ),
            {
                "id": run_id,
                "started_at": started,
                "finished_at": datetime.now(UTC),
                "status": status,
                "row_count": len(observations) + len(documents),
                "detail": "; ".join(errors) if errors else None,
            },
        )


def main() -> None:
    result = asyncio.run(ingest_worldbank())
    print(
        f"observations={result.observations} documents={result.documents} "
        f"errors={len(result.errors)}"
    )
    if result.errors:
        for error in result.errors:
            print(error)


if __name__ == "__main__":
    main()
