import asyncio
import logging
import os
import pytest
from random import random
import redis

from coro_runner import CoroRunner
from coro_runner.backend import RedisBackend
from coro_runner.schema import Queue, RedisConfig

# Log Config
logger = logging.getLogger(__name__)

REDIS_HOST: str = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT: int = int(os.environ.get("REDIS_PORT", 6388)) # Updated default port to match docker-compose
REDIS_DB: int = int(os.environ.get("REDIS_DB", 0))

async def regular_coro():
    await asyncio.sleep(random() * 0.1)

@pytest.mark.asyncio
async def test_redis_backend_coro_runner():
    # Helper to check connection first to skip if not available
    try:
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
        r.ping()
        r.close()
    except Exception:
        pytest.skip("Redis not available")

    logger.debug(f"Testing RedisBackend from: {__name__}")
    runner = CoroRunner(
        concurrency=2,
        backend=RedisBackend(
            conf=RedisConfig(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
        ),
        log_level=logging.ERROR
    )
    for _ in range(5):
        await runner.add_task(regular_coro)

    await runner.run_until_finished()
    await runner.cleanup()
    assert runner._backend.running_task_count == 0
