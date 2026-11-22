# Project status

Last updated: 2026-11-16

## Current milestone

**Olist sales analytics are loaded and shown on the Analytics page.**

On 16 November 2026 `kagglehub` downloaded `olistbr/brazilian-ecommerce`. PostgreSQL holds 99,441 orders and the other eight published tables, including 1,000,163 geolocation rows. The original CSVs are in gitignored `data/raw/olist/`. The Analytics page shows monthly revenue in Brazilian reais, top categories, review scores, payment types, and delivery performance. Natural-language SQL is not built.

World Bank indicator history and 12 World Development Report records remain loaded. SEC filings are not loaded: `SEC_USER_AGENT` is unset. Synthetic organizations are not generated yet.

The repository contains the runnable skeleton: FastAPI health endpoints, Alembic with the pgvector extension, a React and Ant Design shell, and a Docker Compose file for PostgreSQL, the API, and the dashboard.

## Verification on 2026-11-16

- Backend, Python 3.12 via `uv`: pytest 20 passed, Ruff clean, mypy clean.
- `python -m app.ingestion.olist` stored 99,441 orders, 112,650 items, 99,224 reviews, and 1,000,163 geolocation rows. Counts match the published CSVs.
- `GET /api/v1/olist/dashboard` returned health_beauty as the top category, average review 4.09, and 91.9% on-time delivery.
- Browser at `http://127.0.0.1:5173/analytics` showed those figures, the monthly revenue chart, the review-score chart, and the Olist attribution.
- World Bank data from the earlier load is still in PostgreSQL. `docker compose up` was not run. This user is denied access to the Docker socket.

## Milestone roadmap

| Milestone | Scope | Status |
| --- | --- | --- |
| M0 Foundation | Compose file, health API, dashboard shell, docs | Complete, except the Compose process was not started on this machine |
| M1 Identity and tenancy | JWT, organizations, departments, users, synthetic seed | Not started |
| M2 OpenFGA | Authorization model, tuple sync, service-layer checks | Demo on the Admin page. JWT and tenant tuple sync are not built. |
| M3 LiteLLM gateway | Ollama alias `chat-default` on the LiteLLM proxy, with the API calling port 4000. | Proxy route wired to local Ollama |
| M4 Olist warehouse | Schema, validated CSV load, read-only SQL role | Loaded. The read-only SQL role is not created yet. |
| M5 NL2SQL | Guarded SQL, charts, Olist execution-accuracy set | Charts are SQL reports. Natural-language queries are not built. |
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
| [docs/OPENFGA_MODEL.md](docs/OPENFGA_MODEL.md) | M2 demo |
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
