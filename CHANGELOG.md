# Changelog

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
