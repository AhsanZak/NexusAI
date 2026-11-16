# NexusAI

NexusAI is a multi-tenant platform for document search, retrieval-augmented answers, natural-language analytics, and AI workflows. This repository is the foundation milestone: a FastAPI service, a React dashboard, and PostgreSQL with pgvector, running together through Docker Compose.

The public repository is [AhsanZak/NexusAI](https://github.com/AhsanZak/NexusAI).

## What works now

- `GET /api/v1/health` reports that the API process is up.
- `GET /api/v1/health/ready` reports that PostgreSQL accepts a query.
- Alembic enables the `vector` extension on startup.
- The dashboard at `http://localhost:8080` shows those two checks and the module map for later milestones.

Authentication, OpenFGA, LiteLLM, document ingestion, RAG, NL2SQL, and agents are not implemented yet. See [PROJECT_STATUS.md](PROJECT_STATUS.md).

## Run locally

Docker Engine and Docker Compose are required. From the repository root:

```bash
docker compose up --build
```

- Dashboard: http://localhost:8080
- API docs: http://localhost:8000/docs
- PostgreSQL: `localhost:5432`, database `nexusai`, user `nexus`, password `nexus`

The database password is a local development default from [`.env.example`](.env.example). Copy that file to `.env` only when you need to override it. Do not commit `.env`.

Frontend development against a running API:

```bash
cd frontend
npm install
npm run dev
```

The Vite server on http://localhost:5173 proxies `/api` to `http://localhost:8000`.

## Checks

Backend checks run inside the API image, which uses Python 3.12:

```bash
docker compose run --rm --no-deps --entrypoint pytest backend
docker compose run --rm --no-deps --entrypoint ruff backend check app tests
docker compose run --rm --no-deps --entrypoint mypy backend app
```

`--no-deps` skips Postgres because the unit tests stub the database check. Readiness against a real database is the Compose health check.

Frontend:

```bash
cd frontend
npm run lint
npm run build
```

## Layout

- `backend/` — FastAPI application, Alembic, and tests
- `frontend/` — React, TypeScript, and Ant Design
- `docs/` — architecture and data-source notes
- `docker-compose.yml` — Postgres, API, and dashboard

## Data

No public dataset is loaded in this milestone. Licences and download rules are in [docs/DATA_SOURCES.md](docs/DATA_SOURCES.md). Raw files under `data/raw/` are gitignored.
