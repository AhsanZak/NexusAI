"""Turn World Bank downloads into rows. No network and no database access."""

import csv
import io
from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class ObservationRow:
    country_code: str
    country_name: str
    indicator_code: str
    indicator_name: str
    year: int
    value: float | None
    source_url: str


@dataclass(frozen=True)
class DocumentRow:
    id: str
    title: str
    doc_type: str | None
    document_date: date | None
    abstract: str | None
    url: str | None
    pdf_url: str | None
    source_url: str


def parse_indicator_csv(
    contents: str,
    *,
    source_url: str,
    countries: set[str],
    year_from: int,
    year_to: int,
) -> list[ObservationRow]:
    """Parse a World Bank indicator CSV. Metadata lines precede the header row."""
    reader = csv.reader(io.StringIO(contents))
    header: list[str] | None = None
    rows: list[ObservationRow] = []
    for raw in reader:
        if not raw:
            continue
        if header is None:
            if raw[0] == "Country Name":
                header = raw
            continue
        if len(raw) < 4:
            continue
        country_code = raw[1].strip().upper()
        if country_code not in countries:
            continue
        indicator_name = raw[2].strip()
        indicator_code = raw[3].strip()
        for index, year_text in enumerate(header[4:], start=4):
            if not year_text.isdigit() or index >= len(raw):
                continue
            year = int(year_text)
            if year < year_from or year > year_to:
                continue
            cell = raw[index].strip()
            if not cell:
                continue
            try:
                value = float(cell)
            except ValueError:
                continue
            rows.append(
                ObservationRow(
                    country_code=country_code,
                    country_name=raw[0].strip() or country_code,
                    indicator_code=indicator_code,
                    indicator_name=indicator_name,
                    year=year,
                    value=value,
                    source_url=source_url,
                )
            )
    if header is None:
        raise ValueError("World Bank indicator CSV did not contain a data header")
    return rows


def parse_indicator_payload(payload: object, *, source_url: str) -> list[ObservationRow]:
    """Parse one Indicators API v2 response. Annual rows only; other frequencies are skipped."""
    if not isinstance(payload, list) or len(payload) < 2 or not isinstance(payload[1], list):
        message = None
        if isinstance(payload, list) and payload and isinstance(payload[0], dict):
            message = payload[0].get("message")
        if isinstance(message, list) and message and isinstance(message[0], dict):
            message = message[0].get("value")
        detail = message or "World Bank indicator response was not a page of rows"
        raise ValueError(str(detail))

    rows: list[ObservationRow] = []
    for item in payload[1]:
        if not isinstance(item, dict):
            continue
        year_text = str(item.get("date") or "")
        if len(year_text) != 4 or not year_text.isdigit():
            continue
        country_code = str(item.get("countryiso3code") or "").upper()
        if len(country_code) != 3:
            continue
        raw_indicator = item.get("indicator")
        raw_country = item.get("country")
        indicator = raw_indicator if isinstance(raw_indicator, dict) else {}
        country = raw_country if isinstance(raw_country, dict) else {}
        raw_value = item.get("value")
        value = float(raw_value) if isinstance(raw_value, int | float) else None
        rows.append(
            ObservationRow(
                country_code=country_code,
                country_name=str(country.get("value") or country_code),
                indicator_code=str(indicator.get("id") or ""),
                indicator_name=str(indicator.get("value") or indicator.get("id") or ""),
                year=int(year_text),
                value=value,
                source_url=source_url,
            )
        )
    return [row for row in rows if row.indicator_code]


def parse_documents_payload(payload: object, *, source_url: str) -> list[DocumentRow]:
    if not isinstance(payload, dict):
        raise ValueError("World Bank documents response was not an object")
    documents = payload.get("documents")
    if not isinstance(documents, dict):
        return []
    rows: list[DocumentRow] = []
    for key, item in documents.items():
        if key == "facets" or not isinstance(item, dict) or "display_title" not in item:
            continue
        rows.append(
            DocumentRow(
                id=str(item.get("id") or key),
                title=str(item["display_title"]),
                doc_type=_text(item.get("docty")),
                document_date=_date(item.get("docdt")),
                abstract=_abstract(item.get("abstracts")),
                url=_text(item.get("url")),
                pdf_url=_text(item.get("pdfurl")),
                source_url=source_url,
            )
        )
    return rows


def _text(value: object) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _abstract(value: object) -> str | None:
    if isinstance(value, dict):
        value = value.get("cdata!") or value.get("cdata")
    text = _text(value)
    if text is None:
        return None
    return text[:4000]


def _date(value: object) -> date | None:
    text = _text(value)
    if text is None:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except ValueError:
        return None
