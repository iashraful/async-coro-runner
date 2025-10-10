#!/usr/bin/env bash
set -euo pipefail

# default redis envs (can be overridden by exporting before running the script)
: "${REDIS_HOST:=localhost}"
: "${REDIS_PORT:=6388}"
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

exec pytest -s "$@"