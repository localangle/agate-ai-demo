#!/bin/sh
# Runs once on first Postgres data-dir init. stderr → `docker compose logs postgres`.
echo "bootstrap: docker-entrypoint-initdb.d ran (01-verify-bootstrap.sh)" >&2
