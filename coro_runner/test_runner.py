import asyncio
import logging
from random import random

import pytest

from coro_runner import CoroRunner
from coro_runner.schema import Queue, QueueConfig

# Log Config
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

# Defining the queue configuration
rg_queue = Queue(name="Regular", score=1)
hp_queue = Queue(name="HighPriority", score=10)


@pytest.mark.asyncio
async def test_coro_runner():
    async def regular_coro():
        current_task: asyncio.Task | None = asyncio.current_task()
        logger.info(
            f"Regular task started: {current_task.get_name() if current_task else 'No Name'}",
        )
        await asyncio.sleep(random() * 2)
        logger.info(
            f"Regular task ended: {current_task.get_name() if current_task else 'No name'}"
        )

    async def high_priority_coro():
        current_task: asyncio.Task | None = asyncio.current_task()
        logger.info(
            f"Priority task started: {current_task.get_name() if current_task else 'No name'}"
        )
        await asyncio.sleep(random() * 2)
        logger.info(
            f"Priority task ended: {current_task.get_name() if current_task else 'No name'}"
        )

    runner = CoroRunner(
        concurrency=5, queue_conf=QueueConfig(queues=[rg_queue, hp_queue])
    )
    logger.debug("Adding regular tasks")
    for _ in range(10):
        runner.add_task(regular_coro(), queue_name=rg_queue.name)

    logger.debug("Adding priority tasks")
    for _ in range(10):
        runner.add_task(high_priority_coro(), queue_name=hp_queue.name)

    await runner.run_until_finished()
    await runner.cleanup()
    assert runner.running_task_count == 0
