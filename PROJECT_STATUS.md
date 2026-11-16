# Project status

Last updated: 2026-11-16

## Current milestone

**M0 Foundation — implemented and checked locally.** Publishing `main` to GitHub still depends on a valid login for `AhsanZak`.

The repository contains the runnable skeleton: FastAPI health endpoints, Alembic with the pgvector extension, a React and Ant Design shell, and a Docker Compose file for PostgreSQL, the API, and the dashboard.

## Verification on 2026-11-16

- Backend, Python 3.12 via `uv`: pytest 5 passed, Ruff clean, mypy clean.
- Frontend: ESLint clean, `tsc --noEmit` clean, Vite production build succeeded.
- Browser: overview at `http://127.0.0.1:5173/` showed API up. PostgreSQL showed down because Postgres was not running. `/documents` rendered the document-intelligence placeholder.
- `GET /api/v1/health` returned 200. `GET /api/v1/health/ready` returned 503 with `database unavailable`, which matches the dashboard.
- `docker compose up` was not run. The Docker CLI can see the daemon socket, and this user is denied access to it. Compose itself is installed.

## Milestone roadmap

| Milestone | Scope | Status |
| --- | --- | --- |
| M0 Foundation | Compose file, health API, dashboard shell, docs | Complete, except the Compose process was not started on this machine |
| M1 Identity and tenancy | JWT, organizations, departments, users, synthetic seed | Not started |
| M2 OpenFGA | Authorization model, tuple sync, service-layer checks | Not started |
| M3 LiteLLM gateway | Ollama aliases, retries, LangSmith tracing hook | Not started |
| M4 Olist warehouse | Schema, validated CSV load, read-only SQL role | Not started |
| M5 NL2SQL | Guarded SQL, charts, Olist execution-accuracy set | Not started |
| M6 Documents | Upload, chunk, embed, authorization before content | Not started |
| M7 Public documents | Bounded SEC EDGAR and World Bank document ingestion | Not started |
| M8 World Bank indicators | API ingest, history, country charts | Not started |
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
| docs/LLM_GATEWAY.md | M3 |
| docs/RAG_PIPELINE.md | M9 |
| docs/NL2SQL.md | M5 |
| docs/EVALUATION.md | M11 |

## Blockers

- This user cannot access `/var/run/docker.sock`, so the Compose stack has not been started here. Join the `docker` group, or run Compose with a privileged Docker session, then `docker compose up --build`.
- GitHub push needs a valid login for `AhsanZak`. The saved `gh` token was invalid at the start of this milestone.
- `LANGSMITH_API_KEY` is required before M11 can be marked complete. Tracing will no-op until then.
- `SEC_USER_AGENT` is required before EDGAR downloads.
- Olist CSVs need a Kaggle token or a manual drop in `data/raw/olist/`. The files stay gitignored.

## Machine notes

- Backend containers use Python 3.12. The host Python is 3.14 and is not the runtime.
- Default local models, when M3 starts, are `qwen2.5:7b` and `nomic-embed-text`. `deepseek-r1:7b` is an alternate alias. This machine has 14 GB of RAM, so larger checkpoints are out of scope.
