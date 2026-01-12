import asyncio
import logging
import os
import pytest
from random import random

from coro_runner import CoroRunner
from coro_runner.backend import MySQLBackend
from coro_runner.schema import MySQLConfig

# Log Config
logger = logging.getLogger(__name__)

MYSQL_HOST: str = os.environ.get("MYSQL_HOST", "localhost")
MYSQL_PORT: int = int(os.environ.get("MYSQL_PORT", 3307))
MYSQL_USER: str = os.environ.get("MYSQL_USER", "root")
MYSQL_PASS: str = os.environ.get("MYSQL_PASS", "root")
MYSQL_DB: str = os.environ.get("MYSQL_DB", "coro_runner_tasks")

async def regular_coro():
    await asyncio.sleep(random() * 0.1)

@pytest.mark.asyncio
async def test_mysql_backend_coro_runner():
    try:
        import aiomysql
    except ImportError:
        pytest.skip("aiomysql not installed")

    # Basic connection check could be added here similar to redis one
    # but constructing aiomysql connection requires async context, 
    # so we might just let it fail or wrap in try/except inside test?
    # Better to skip if connection refused.
    
    try:
        async with aiomysql.connect(host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER, password=MYSQL_PASS, db=MYSQL_DB) as conn:
            pass
    except Exception as e:
        pytest.skip(f"MySQL not available: {e}")

    logger.debug(f"Testing MySQLBackend from: {__name__}")
    runner = CoroRunner(
        concurrency=2,
        backend=MySQLBackend(
            conf=MySQLConfig(host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER, password=MYSQL_PASS, db=MYSQL_DB)
        ),
        log_level=logging.ERROR
    )
    for _ in range(5):
        await runner.add_task(regular_coro)

    await runner.run_until_finished()
    
    # Cleanup table (optional, but good for tests)
    # Ideally should drop table or truncate.
    # runner.cleanup currently only closes connection for SQL backends (inherited from BaseBackend -> close?)
    # BaseBackend.cleanup calls __close (which calls pool.close)
    
    await runner.cleanup()
    assert runner._backend.running_task_count == 0
