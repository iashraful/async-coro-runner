#!/usr/bin/env bash
set -euo pipefail

# default redis envs (can be overridden by exporting before running the script)
: "${REDIS_HOST:=redis}"
: "${REDIS_PORT:=6379}"
: "${REDIS_DB:=0}"

export REDIS_HOST REDIS_PORT REDIS_DB

# construct REDIS_URL if not provided
if [ -z "${REDIS_URL:-}" ]; then
    REDIS_URL="redis://${REDIS_HOST}:${REDIS_PORT}/${REDIS_DB}"
    export REDIS_URL
fi

echo "Running pytest with:"
echo "  REDIS_HOST=${REDIS_HOST}"
echo "  REDIS_PORT=${REDIS_PORT}"
echo "  REDIS_DB=${REDIS_DB}"
echo "  REDIS_URL=${REDIS_URL}"

# default mysql envs
: "${MYSQL_HOST:=mysql}"
: "${MYSQL_PORT:=3306}"
: "${MYSQL_USER:=root}"
: "${MYSQL_PASS:=root}"
: "${MYSQL_DB:=coro_runner_tasks}"

export MYSQL_HOST MYSQL_PORT MYSQL_USER MYSQL_PASS MYSQL_DB

echo "  MYSQL_HOST=${MYSQL_HOST}"
echo "  MYSQL_PORT=${MYSQL_PORT}"
echo "  MYSQL_USER=${MYSQL_USER}"
# echo "  MYSQL_PASS=${MYSQL_PASS}"
echo "  MYSQL_DB=${MYSQL_DB}"

# default postgres envs
: "${PG_HOST:=postgres}"
: "${PG_PORT:=5432}"
: "${PG_USER:=postgres}"
: "${PG_PASS:=postgres}"
: "${PG_DB:=coro_runner_tasks}"

export PG_HOST PG_PORT PG_USER PG_PASS PG_DB

echo "  PG_HOST=${PG_HOST}"
echo "  PG_PORT=${PG_PORT}"
echo "  PG_USER=${PG_USER}"
# echo "  PG_PASS=${PG_PASS}"
echo "  PG_DB=${PG_DB}"

export PYTHONPATH=.
exec uv run python -m pytest tests/ -vv "$@"