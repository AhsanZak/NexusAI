# Deployment

This milestone runs only on a local Docker Compose stack. There is no cloud deployment.

## Prerequisites

- Docker Engine
- Docker Compose v2 (`docker compose version`)
- A free port on 5432, 8000, and 8080

The API image is Python 3.12. The host interpreter is not used. The dashboard image builds with Node 22 and is served by nginx.

If `docker compose` reports permission denied on `/var/run/docker.sock`, this user cannot talk to the Docker daemon. Join the `docker` group and open a new login session. This repository does not change host permissions.

## Local PostgreSQL without Docker

This machine cannot access `/var/run/docker.sock`, and pgvector is not installed in the Ubuntu PostgreSQL 18 packages. A separate cluster for NexusAI listens on `127.0.0.1:5433`. Its files are in `/home/smartnet/.local/share/nexusai/pgdata`, outside the git repository. The role and database are `nexus` / `nexusai`, with the local password from `.env.example`.

```bash
/usr/lib/postgresql/18/bin/pg_ctl -D /home/smartnet/.local/share/nexusai/pgdata -l /home/smartnet/.local/share/nexusai/postgres.log start
export NEXUS_DATABASE_URL=postgresql+asyncpg://nexus:nexus@127.0.0.1:5433/nexusai
cd backend && .venv/bin/alembic upgrade head && .venv/bin/python -m app.ingestion.worldbank
```

## Start

From the repository root:

```bash
docker compose up --build
```

On startup the API container runs `alembic upgrade head`, which enables `pgvector`, then serves Uvicorn on port 8000.

| Service | URL or address | Role |
| --- | --- | --- |
| frontend | http://localhost:8080 | Dashboard |
| backend | http://localhost:8000/docs | OpenAPI |
| postgres | localhost:5432 | Database `nexusai` |

Local credentials default to user `nexus` and password `nexus`. Override them together. If `POSTGRES_PASSWORD` changes, `NEXUS_DATABASE_URL` must use the same password. See [`.env.example`](../.env.example).

## Health

- `GET /api/v1/health` returns 200 when the process is serving. Compose uses this as the API health check.
- `GET /api/v1/health/ready` returns 200 when `SELECT 1` succeeds, and 503 when it does not.

The dashboard reads both endpoints through nginx at `/api/`.

## Stop

```bash
docker compose down
```

`docker compose down -v` also deletes the Postgres volume.

## Not running yet

OpenFGA, LiteLLM, Ollama, and LangSmith are absent from this Compose file. Do not point the dashboard at a model or an authorization service until those milestones add them.
