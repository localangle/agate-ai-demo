# Agate AI Demo

Agate uses large language models, along with other tools, to turn news articles into structured, durable knowledge.

This local-only demo packages a stripped-down extraction worfklow (**Agate UI**), API (**Agate API**), worker (**Celery**), PostgreSQL, and Redis so you can explore composable structured-journalism workflows end-to-end.

[Initial work](https://github.com/minneapolisstartribune/agate-ai) began under the Lenfest AI Collaborative and Fellowship Program at the Minnesota Star Tribune, with additional support from Chicago Public Media and the Reynolds Journalism Institute. Agate is built and maintained by [Local Angle](https://localangle.co), and released under the MIT License. 

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Docker Engine + Compose)

## Run

From the repository root:

```bash
make up
```

This starts: `postgres`, `redis`, `agate-api`, `worker`, `agate-ui`.

`agate-ui` takes a little while to start up, so wait for it to finish building before you attempt to log in.

Note that the first time you run this, it will download a rather large database from the [Who's on First gazetteer](https://whosonfirst.org/). This is a workaround in lieu infrastructure that exists in the complete platform. It supports the assignment of parent geographies in the geocoding nodes.

Stop:

```bash
make down
```

Follow logs (from repo root):

```bash
docker compose -f infra/docker-compose.yml logs -f
```

## URLs

| Service        | URL                          |
|----------------|------------------------------|
| Agate UI | http://localhost:5173        |
| Agate API| http://localhost:8000        |
| Postgres       | localhost **5434** → 5432 in container; database **`demo`** |
| Redis          | localhost:6379               |

### First-run onboarding

The UI opens with a 3-card intro overlay:

1. What Agate is and who built it
2. Structured-journalism use cases included in this demo
3. A get-started step that saves your `OPENAI_API_KEY` to the database

The final onboarding card writes the key through the project API-key endpoint used by Project Settings, so flows can run immediately after setup.

There is **no authentication** in this demo; do not expose it to the public internet.

## Layout

```
apps/agate-api/   # FastAPI control plane
apps/agate-ui/    # Vite + React
apps/worker/            # Celery worker
packages/agate/   # Nodes, agate_core, agate_db
packages/utils/         # LLM + encryption helpers (agate_utils)
infra/                  # docker-compose.yml, Postgres image; optional bootstrap SQL in infra/bootstrap/
```

### Database `demo`

Compose sets `POSTGRES_DB: demo`, so database `demo` is created when the Postgres volume is first initialized. Optional scripts under [`infra/bootstrap/`](infra/bootstrap/) are mounted as `/docker-entrypoint-initdb.d` and run on that first init only. To recreate the DB from scratch (e.g. after renaming it), remove the volume: `docker compose -f infra/docker-compose.yml down -v`. Postgres data lives in the named volume **`infra_postgres_data_demo`** (see `volumes` in compose).

Graph fixtures are also seeded during DB initialization from JSON files in:

- `packages/agate/src/agate_db/fixtures/graphs`

**Check that bootstrap ran:** init scripts run only when the data directory is empty. After a fresh init, Postgres logs should include the official line `running /docker-entrypoint-initdb.d/01-verify-bootstrap.sh` and stderr from [`infra/bootstrap/01-verify-bootstrap.sh`](infra/bootstrap/01-verify-bootstrap.sh):

```bash
docker compose -f infra/docker-compose.yml logs postgres 2>&1 | grep -E 'docker-entrypoint-initdb|bootstrap:'
```

If you see neither, the volume was already initialized—use `down -v` once, then `up` again.

## Agate nodes

Add or change nodes under `packages/agate/src/agate_nodes/`, then from `apps/agate-ui` run:

```bash
node scripts/sync-nodes.js
```

## License

See [LICENSE](./LICENSE) if present.

## Questions

Contact Chase Davis: chase@localangle.co