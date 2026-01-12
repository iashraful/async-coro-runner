import asyncio
import logging
import pytest
from random import random

from coro_runner import CoroRunner
from coro_runner.backend import InMemoryBackend
from coro_runner.schema import Queue, QueueConfig

# Log Config
logger = logging.getLogger(__name__)

# Defining the queue configuration
rg_queue = Queue(name="Regular", score=1)
hp_queue = Queue(name="HighPriority", score=10)

async def regular_coro():
    await asyncio.sleep(random() * 0.1)

async def high_priority_coro():
    await asyncio.sleep(random() * 0.1)

@pytest.mark.asyncio
async def test_in_memory_coro_runner():
    logger.debug(f"Testing InMemoryBackend from: {__name__}")
    runner = CoroRunner(
        concurrency=2,
        backend=InMemoryBackend(),
        log_level=logging.ERROR # Quiet
    )
    for _ in range(5):
        await runner.add_task(regular_coro)

    await runner.run_until_finished()
    await runner.cleanup()
    assert runner._backend.running_task_count == 0

@pytest.mark.asyncio
async def test_priority_check_coroutines():
    logger.info(f"Testing Queue Mechanism from: {__name__}")
    runner = CoroRunner(
        concurrency=2,
        queue_conf=QueueConfig(queues=[rg_queue, hp_queue]),
        backend=InMemoryBackend(),
        log_level=logging.ERROR
    )
    for _ in range(5):
        await runner.add_task(regular_coro, queue_name=rg_queue.name)

    for _ in range(5):
        await runner.add_task(high_priority_coro, queue_name=hp_queue.name)

    await runner.run_until_finished()
    await runner.cleanup()
    assert runner._backend.running_task_count == 0
