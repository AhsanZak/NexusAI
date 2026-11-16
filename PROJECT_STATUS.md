# Project status

Last updated: 2026-11-16

## Current milestone

**World Bank public data is loaded into local PostgreSQL and shown on the main page.**

On 16 November 2026 the loader stored 1,750 indicator observations (GDP, inflation, population, employment ratio, imports, and exports, 2000–2024, twelve countries) and 12 World Development Report records. The database is a user-owned PostgreSQL 18 cluster on `127.0.0.1:5433` because this account cannot access the Docker socket and the system PostgreSQL on port 5432 requires a password that is not available. pgvector is not installed in that cluster. Docker Compose remains the path when Docker is usable.

Olist is not loaded: the Kaggle download needs a Kaggle API token or the nine CSVs placed in `data/raw/olist/`. SEC filings are not loaded: `SEC_USER_AGENT` is unset. Synthetic organizations are not generated yet.

The repository contains the runnable skeleton: FastAPI health endpoints, Alembic with the pgvector extension, a React and Ant Design shell, and a Docker Compose file for PostgreSQL, the API, and the dashboard.

## Verification on 2026-11-16

- Backend, Python 3.12 via `uv`: pytest 16 passed, Ruff clean, mypy clean.
- Frontend: ESLint clean and the Vite production build succeeded before this load. The running dashboard is the Vite dev server.
- `python -m app.ingestion.worldbank` finished with 1,750 observations, 12 documents, and no errors.
- `GET /api/v1/health/ready` returned database up against `127.0.0.1:5433`.
- Browser at `http://127.0.0.1:5173/`: the overview showed 1,750 observations, 12 reports, and 12 country lines for GDP. Switching the selector to inflation changed the scale label to "Percent" and kept 12 lines. `/documents` still opened the document-intelligence page.
- `docker compose up` was not run. This user is denied access to the Docker socket.

## Milestone roadmap

| Milestone | Scope | Status |
| --- | --- | --- |
| M0 Foundation | Compose file, health API, dashboard shell, docs | Complete, except the Compose process was not started on this machine |
| M1 Identity and tenancy | JWT, organizations, departments, users, synthetic seed | Not started |
| M2 OpenFGA | Authorization model, tuple sync, service-layer checks | Not started |
| M3 LiteLLM gateway | Ollama aliases and the LiteLLM proxy process. OpenAI chat and the debug page are already in place. | Partial |
| M4 Olist warehouse | Schema, validated CSV load, read-only SQL role | Not started |
| M5 NL2SQL | Guarded SQL, charts, Olist execution-accuracy set | Not started |
| M6 Documents | Upload, chunk, embed, authorization before content | Not started |
| M7 Public documents | Bounded SEC EDGAR and World Bank document ingestion | World Bank report metadata is loaded. SEC and PDF embeddings are not. |
| M8 World Bank indicators | API ingest, history, country charts | Loaded for twelve countries, 2000–2024. Natural-language queries are not built. |
| M9 Knowledge assistant | Permission-aware RAG, citations, streaming | Not started |
| M10 Agents | Research, analyst, and report agents, approval-gated PDF | Not started |
| M11 Evaluation | LangSmith datasets for RAG, NL2SQL, and agents | Not started |
| M12 Admin dashboard | Operations views and full demo verification | Not started |

## Documentation map

| Document | Milestone |
| --- | --- |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | M0, updated as modules land |
| [docs/DATA_SOURCES.md](docs/DATA_SOURCES.md) | M0 |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | M0 |
| docs/DATABASE_SCHEMA.md | M4 |
| docs/OPENFGA_MODEL.md | M2 |
| [docs/LLM_GATEWAY.md](docs/LLM_GATEWAY.md) | OpenAI gateway and debug traces |
| docs/RAG_PIPELINE.md | M9 |
| docs/NL2SQL.md | M5 |
| docs/EVALUATION.md | M11 |

## Blockers

- This user cannot access `/var/run/docker.sock`, so the Compose stack has not been started here. Join the `docker` group, or run Compose with a privileged Docker session, then `docker compose up --build`.
- `LANGSMITH_API_KEY` is required before M11 can be marked complete. Tracing will no-op until then.
- `SEC_USER_AGENT` is required before EDGAR downloads.
- Olist CSVs need a Kaggle token or a manual drop in `data/raw/olist/`. The files stay gitignored.

## Machine notes

- Backend containers use Python 3.12. The host Python is 3.14 and is not the runtime.
- Default local models, when M3 starts, are `qwen2.5:7b` and `nomic-embed-text`. `deepseek-r1:7b` is an alternate alias. This machine has 14 GB of RAM, so larger checkpoints are out of scope.
