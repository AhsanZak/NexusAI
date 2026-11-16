"""Read the World Bank warehouse for the dashboard."""

from collections.abc import Sequence
from datetime import date, datetime

from sqlalchemy import text
from sqlalchemy.engine import RowMapping

from app.core.database import engine

ATTRIBUTION = (
    "The World Bank: World Development Indicators and Documents & Reports. "
    "CC BY 4.0. The World Bank does not endorse this use."
)


async def load_dashboard() -> dict[str, object]:
    async with engine.connect() as connection:
        observations = (
            await connection.execute(
                text(
                    """
                    SELECT c.code AS country_code,
                           c.name AS country_name,
                           i.code AS indicator_code,
                           i.name AS indicator_name,
                           o.year,
                           o.value,
                           o.retrieved_at
                    FROM worldbank.observations AS o
                    JOIN worldbank.countries AS c ON c.code = o.country_code
                    JOIN worldbank.indicators AS i ON i.code = o.indicator_code
                    WHERE o.value IS NOT NULL
                    ORDER BY i.code, c.name, o.year
                    """
                )
            )
        ).mappings().all()
        documents = (
            await connection.execute(
                text(
                    """
                    SELECT id, title, doc_type, document_date, abstract, url, pdf_url, retrieved_at
                    FROM worldbank.documents
                    ORDER BY document_date DESC NULLS LAST, title
                    LIMIT 12
                    """
                )
            )
        ).mappings().all()
    return _shape(observations, documents)


def _shape(
    observations: Sequence[RowMapping],
    documents: Sequence[RowMapping],
) -> dict[str, object]:
    series: dict[tuple[str, str], dict[str, object]] = {}
    indicators: dict[str, str] = {}
    retrieved_at: datetime | None = None
    for row in observations:
        item = dict(row)
        indicators[str(item["indicator_code"])] = str(item["indicator_name"])
        stamp = item["retrieved_at"]
        if isinstance(stamp, datetime) and (retrieved_at is None or stamp > retrieved_at):
            retrieved_at = stamp
        key = (str(item["indicator_code"]), str(item["country_code"]))
        entry = series.setdefault(
            key,
            {
                "indicator_code": item["indicator_code"],
                "indicator_name": item["indicator_name"],
                "country_code": item["country_code"],
                "country_name": item["country_name"],
                "points": [],
            },
        )
        points = entry["points"]
        assert isinstance(points, list)
        points.append({"year": item["year"], "value": item["value"]})

    document_rows = []
    for row in documents:
        item = dict(row)
        stamp = item["retrieved_at"]
        if isinstance(stamp, datetime) and (retrieved_at is None or stamp > retrieved_at):
            retrieved_at = stamp
        document_date = item["document_date"]
        iso_date = document_date.isoformat() if isinstance(document_date, date) else None
        document_rows.append(
            {
                "id": item["id"],
                "title": item["title"],
                "doc_type": item["doc_type"],
                "document_date": iso_date,
                "abstract": item["abstract"],
                "url": item["url"],
                "pdf_url": item["pdf_url"],
            }
        )
    return {
        "attribution": ATTRIBUTION,
        "indicator_source": "https://data.worldbank.org/",
        "document_source": "https://documents.worldbank.org/",
        "retrieved_at": retrieved_at.isoformat() if retrieved_at else None,
        "observation_count": len(observations),
        "document_count": len(document_rows),
        "indicators": [
            {"code": code, "name": name}
            for code, name in sorted(indicators.items(), key=lambda pair: pair[1])
        ],
        "series": list(series.values()),
        "documents": document_rows,
    }
