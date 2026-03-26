# Agate API

FastAPI service for projects, graphs, runs, and encrypted project API keys. Used with the Celery worker for graph execution.

## Local (Docker)

From repo root:

```bash
make up
```

- **API**: http://localhost:8000  
- OpenAPI is disabled in this demo (`docs_url=None`).

## Environment

See [`infra/docker-compose.yml`](../../infra/docker-compose.yml): `DATABASE_URL`, `REDIS_URL`, `MASTER_ENCRYPTION_KEY`, `UI_ORIGIN`.

## Deploy

See [DEPLOY.md](./DEPLOY.md).
