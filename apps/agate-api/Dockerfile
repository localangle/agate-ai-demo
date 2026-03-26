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
COPY apps/agate-api /app/apps/agate-api

RUN cd /app/packages/utils && uv pip install --system -e .
RUN cd /app/packages/agate && uv pip install --system -e .
RUN cd /app/apps/agate-api && uv pip install --system -e .

ENV PYTHONPATH=/app/apps/agate-api/src

WORKDIR /app/apps/agate-api

FROM base AS development
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

FROM base AS production

RUN useradd -m -u 1000 apiuser && chown -R apiuser:apiuser /app
USER apiuser

EXPOSE 8000

CMD ["sh","-c","uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
