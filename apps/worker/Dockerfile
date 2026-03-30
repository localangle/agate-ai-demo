FROM python:3.11-slim AS base

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      gcc \
      postgresql-client \
      curl && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

COPY packages/agate /app/packages/agate
COPY packages/utils /app/packages/utils
COPY apps/worker /app/apps/worker

RUN cd /app/packages/utils && uv pip install --system -e .
RUN cd /app/packages/agate && uv pip install --system -e .
RUN cd /app/apps/worker && uv pip install --system -e . \
    && python -c "from ddgs import DDGS"

ENV PYTHONPATH=/app/apps/worker/src

WORKDIR /app/apps/worker

FROM base AS development
CMD ["celery", "-A", "worker.tasks", "worker", "--loglevel=info"]

FROM base AS production

RUN useradd -m -u 1000 workeruser && chown -R workeruser:workeruser /app
USER workeruser

CMD ["sh","-c","NUM_QUEUES=${CELERY_NUM_QUEUES:-4}; QUEUES=$(python3 -c 'import os; n=int(os.getenv(\"CELERY_NUM_QUEUES\", \"4\")); print(\",\".join([f\"queue-{i}\" for i in range(n)]))'); celery -A worker.tasks worker --loglevel=info --concurrency=${WORKER_CONCURRENCY:-4} -Ofair -Q $QUEUES"]
