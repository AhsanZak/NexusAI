"""Parser tests use captured response shapes, not the live World Bank API."""

from app.ingestion.worldbank_parse import (
    parse_documents_payload,
    parse_indicator_csv,
    parse_indicator_payload,
)


def test_indicator_csv_keeps_selected_countries_and_years() -> None:
    contents = """
"Data Source","World Development Indicators"

"Country Name","Country Code","Indicator Name","Indicator Code","1999","2000","2001"
"Brazil","BRA","Population, total","SP.POP.TOTL","1","2",""
"Aruba","ABW","Population, total","SP.POP.TOTL","9","9","9"
""".strip()

    rows = parse_indicator_csv(
        contents,
        source_url="https://api.worldbank.org/example.csv",
        countries={"BRA"},
        year_from=2000,
        year_to=2024,
    )

    assert len(rows) == 1
    assert rows[0].country_name == "Brazil"
    assert rows[0].year == 2000
    assert rows[0].value == 2.0
    assert rows[0].indicator_code == "SP.POP.TOTL"


def test_indicator_rows_keep_annual_values_and_drop_blanks() -> None:
    payload = [
        {"page": 1, "pages": 1, "total": 2},
        [
            {
                "indicator": {"id": "NY.GDP.MKTP.CD", "value": "GDP (current US$)"},
                "country": {"id": "BR", "value": "Brazil"},
                "countryiso3code": "BRA",
                "date": "2022",
                "value": 1920.5,
            },
            {
                "indicator": {"id": "NY.GDP.MKTP.CD", "value": "GDP (current US$)"},
                "country": {"id": "BR", "value": "Brazil"},
                "countryiso3code": "BRA",
                "date": "2023",
                "value": None,
            },
            {
                "indicator": {"id": "NY.GDP.MKTP.CD", "value": "GDP (current US$)"},
                "country": {"id": "BR", "value": "Brazil"},
                "countryiso3code": "BRA",
                "date": "2022Q1",
                "value": 10,
            },
        ],
    ]

    rows = parse_indicator_payload(payload, source_url="https://api.worldbank.org/example")

    assert len(rows) == 2
    assert rows[0].country_code == "BRA"
    assert rows[0].year == 2022
    assert rows[0].value == 1920.5
    assert rows[1].value is None


def test_indicator_error_payload_is_rejected() -> None:
    payload = [{"message": [{"id": "120", "value": "The provided parameter value is not valid"}]}]
    try:
        parse_indicator_payload(payload, source_url="https://api.worldbank.org/example")
    except ValueError as exc:
        assert "not valid" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_documents_ignore_the_facets_entry() -> None:
    payload = {
        "documents": {
            "D1": {
                "id": "D1",
                "display_title": "World development report 2000/2001",
                "docty": "World Development Report",
                "docdt": "2000-09-04T04:00:00Z",
                "url": "http://documents.worldbank.org/example",
                "pdfurl": "http://documents.worldbank.org/example.pdf",
                "abstracts": {"cdata!": "A public report."},
            },
            "facets": {"count": 1},
        }
    }

    rows = parse_documents_payload(payload, source_url="https://search.worldbank.org/example")

    assert len(rows) == 1
    assert rows[0].title.startswith("World development report")
    assert rows[0].document_date is not None
    assert rows[0].document_date.isoformat() == "2000-09-04"
    assert rows[0].abstract == "A public report."
