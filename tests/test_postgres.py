import asyncio
import logging
import os
import pytest
from random import random

from coro_runner import CoroRunner
from coro_runner.backend import PostgresBackend
from coro_runner.schema import PGConfig

# Log Config
logger = logging.getLogger(__name__)

PG_HOST: str = os.environ.get("PG_HOST", "localhost")
PG_PORT: int = int(os.environ.get("PG_PORT", 5432))
PG_USER: str = os.environ.get("PG_USER", "postgres")
PG_PASS: str = os.environ.get("PG_PASS", "postgres")
PG_DB: str = os.environ.get("PG_DB", "coro_runner_tasks")

async def regular_coro():
    await asyncio.sleep(random() * 0.1)

@pytest.mark.asyncio
async def test_postgres_backend_coro_runner():
    try:
        import asyncpg
    except ImportError:
        pytest.skip("asyncpg not installed")

    try:
        conn = await asyncpg.connect(host=PG_HOST, port=PG_PORT, user=PG_USER, password=PG_PASS, database=PG_DB)
        await conn.close()
    except Exception as e:
        pytest.skip(f"Postgres not available: {e}")

    logger.debug(f"Testing PostgresBackend from: {__name__}")
    runner = CoroRunner(
        concurrency=2,
        backend=PostgresBackend(
            conf=PGConfig(host=PG_HOST, port=PG_PORT, user=PG_USER, password=PG_PASS, db=PG_DB)
        ),
        log_level=logging.ERROR
    )
    for _ in range(5):
        await runner.add_task(regular_coro)

    await runner.run_until_finished()
    await runner.cleanup()
    assert runner._backend.running_task_count == 0
