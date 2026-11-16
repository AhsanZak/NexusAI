# Data sources

No dataset is downloaded or loaded in the foundation milestone. Raw files belong in `data/raw/` and are gitignored. Each loader, when it arrives, must record the source, the retrieval date, and the licence.

The application code is separate from these datasets. Dataset terms below do not by themselves set a licence for the NexusAI source.

## Olist Brazilian E-Commerce

- Source: [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
- Licence: [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/)
- Contents: orders, customers, order items, payments, reviews, products, sellers, geolocation, and product category name translations
- Period: orders from 2016 to 2018. This is a published snapshot, not a live store.
- Use: relational warehouse, SQL analytics, and the primary NL2SQL database

Attribution to keep with any derived table or figure:

> Olist. Brazilian E-Commerce Public Dataset by Olist. Kaggle. Licensed CC BY-NC-SA 4.0.

Non-commercial use, attribution, and share-alike apply. The nine CSV files will not be committed. Ingestion will accept a Kaggle API token or a manual drop in `data/raw/olist/`. The loader must validate that all nine files are present and record row counts.

## SEC EDGAR

- Policy: [Accessing EDGAR Data](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data)
- Forms: a small curated set of 10-K, 10-Q, and 8-K filings through `data.sec.gov`, not a site crawl
- Rate: stay under 10 requests per second across the whole job
- Identity: every request sends `User-Agent` from `SEC_USER_AGENT`, including a contact email. A library default user agent is refused by the SEC.
- Provenance stored with each filing: accession number, form type, filing date, company, and source URL

Downloads stay blocked until `SEC_USER_AGENT` is set.

## World Bank indicators

- API: [World Bank Indicators API v2](https://datahelpdesk.worldbank.org/knowledgebase/articles/889392-about-the-indicators-api-documentation)
- Access: no API key
- Series: GDP, inflation, population, employment, imports, and exports for a fixed country list
- Terms: [CC BY 4.0](https://data.worldbank.org/summary-terms-of-use) with attribution to the World Bank and the source named in the indicator metadata. Do not imply World Bank endorsement.

Example call used by the loader. The JSON history pages were returning HTTP 502 on 16 November 2026, so ingestion downloads the official CSV extract instead and keeps 2000–2024 for twelve countries:

```text
https://api.worldbank.org/v2/en/indicator/NY.GDP.MKTP.CD?downloadformat=csv
```

Run it against the local database:

```bash
export NEXUS_DATABASE_URL=postgresql+asyncpg://nexus:nexus@127.0.0.1:5433/nexusai
cd backend
.venv/bin/python -m app.ingestion.worldbank
```

## World Bank documents

- API: [Documents and Reports](https://documents.worldbank.org/en/publication/documents-reports/api)
- Endpoint: `https://search.worldbank.org/api/v3/wds`
- The loader stores a bounded page of World Development Report records: title, date, abstract, page URL, and PDF URL. Full PDF text, embeddings, and citation answers are not built yet.

Respect the World Bank [terms and conditions](https://www.worldbank.org/ext/en/legal/terms-conditions) on API volume. The job will be manual first, then scheduled, and it will not crawl without a page cap.

## Synthetic organizations

Python Faker will generate at least three organizations, four departments in each, and 15 to 20 users. Names will be marked as demonstration records so they are not mistaken for real companies. Public EDGAR filers stay in the document corpus and are never used as tenant organizations.

## NL2SQL benchmarks

- Spider: [Yale Spider](https://yale-lily.github.io/spider), dataset licence CC BY-SA 4.0
- BIRD: [BIRD-bench](https://bird-bench.github.io/), dataset licence CC BY-SA 4.0

The product metric is an authored Olist question set: natural-language question, expected SQL, expected result, execution accuracy, and SQL error rate. Full BIRD is about 33 GB and will not be downloaded by Compose. A loader may score a local Spider or BIRD sample when those files are placed on disk. Reported scores will come only from runs that actually execute.
