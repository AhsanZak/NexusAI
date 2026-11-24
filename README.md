# NexusAI

NexusAI is a multi-tenant platform for document search, retrieval-augmented answers, natural-language analytics, and AI workflows. This repository is the foundation milestone: a FastAPI service, a React dashboard, and PostgreSQL with pgvector, running together through Docker Compose.

The public repository is [AhsanZak/NexusAI](https://github.com/AhsanZak/NexusAI).

## What works now

- `GET /api/v1/health` reports that the API process is up.
- `GET /api/v1/health/ready` reports that PostgreSQL accepts a query.
- Alembic enables the `vector` extension when PostgreSQL has it installed.
- The dashboard at `http://localhost:8080` shows API and database status.
- The Analytics page charts the Olist 2016–2018 snapshot: sales, categories, reviews, payments, and delivery.
- The main page still charts the World Bank extract. Outside Compose, point the API at the local database:

```bash
export NEXUS_DATABASE_URL=postgresql+asyncpg://nexus:nexus@127.0.0.1:5433/nexusai
```

Sign in at `/login`. Local accounts are created by `python -m app.seed` in `backend/` after migration `0005_users`. The super admin is `admin@nexusai.local` and can add more email accounts from Admin. The Assistant page asks as Amina Rahman or Luis Ortega. OpenFGA runs first, and only an allowed document is placed in the model prompt. They share the World Bank indicators. Amina alone can use the Olist warehouse text, and Luis alone can use the finance notes. Login, document ingestion, NL2SQL, and agents are not implemented yet. See [PROJECT_STATUS.md](PROJECT_STATUS.md), [docs/OPENFGA_MODEL.md](docs/OPENFGA_MODEL.md), and [docs/LLM_GATEWAY.md](docs/LLM_GATEWAY.md).

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

World Bank indicator history, a page of World Development Reports, and the Olist e-commerce snapshot are loaded. SEC EDGAR and synthetic organizations are not loaded. Licences and download rules are in [docs/DATA_SOURCES.md](docs/DATA_SOURCES.md). Raw files under `data/raw/` are gitignored.
