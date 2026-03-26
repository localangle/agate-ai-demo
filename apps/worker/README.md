# Worker

Celery worker for executing Agate graphs. Started with root `make up` alongside Redis, Postgres, and `agate-api`.

Environment (see `infra/docker-compose.yml`): `DATABASE_URL`, `REDIS_URL`, `MASTER_ENCRYPTION_KEY`, `CELERY_NUM_QUEUES`, `WORKER_CONCURRENCY`.
