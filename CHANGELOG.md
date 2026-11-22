# Changelog

## [0.5.0] - 2026-11-22

### Added

- OpenFGA example with two users: a shared viewer permission on the World Bank indicators, analyst access for Amina Rahman on the Olist warehouse, and auditor access for Luis Ortega on the finance notes.
- Admin page that shows each Check result and withholds document text after a denial.
- OpenFGA 1.23 service in Docker Compose, published on port 8090.

## [0.4.0] - 2026-11-16

### Added

- Olist Brazilian e-commerce snapshot, downloaded with kagglehub and loaded into PostgreSQL. The nine original CSVs stay gitignored.
- Analytics page for monthly sales, category revenue, review scores, payments, and delivery performance.

## [0.3.0] - 2026-11-16

### Added

- World Bank indicator history for GDP, inflation, population, employment, imports, and exports, loaded from the public CSV extracts into PostgreSQL.
- Twelve World Bank Documents & Reports records, with title, date, abstract, and source URL.
- Main-page charts and a document list for that warehouse.

## [0.2.0] - 2026-11-16

### Added

- LiteLLM gateway that calls OpenAI through the `chat-default` alias.
- A trace of every model call, with the prompt, response, token counts, latency, and error.
- An OpenAI debug page that lists those traces and can send a test prompt.
- Alembic revision `0002_llm_traces`.

## [0.1.0] - 2026-11-16

### Added

- FastAPI application factory with JSON request logs, CORS, and `/api/v1/health` plus `/api/v1/health/ready`.
- Alembic migration that enables the pgvector extension.
- React, TypeScript, and Ant Design shell that displays API and database status.
- Docker Compose stack for PostgreSQL, the API, and the dashboard.
- Architecture, data-source, and deployment notes for the foundation milestone.
