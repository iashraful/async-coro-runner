import asyncio
from random import random

import pytest

from coro_runner import CoroRunner
from coro_runner.schema import Worker, WorkerConfig

# Defining the worker configuration
_workers = WorkerConfig(
    workers=[
        Worker(name="Worker1", score=1),
        Worker(name="Worker2", score=10),
        Worker(name="Worker3", score=7.5),
    ]
)


@pytest.mark.asyncio
async def test_coro_runner():
    async def my_coro():
        current_task: asyncio.Task | None = asyncio.current_task()
        print("Task started: ", current_task.get_name() if current_task else "No name")
        await asyncio.sleep(random() * 2)
        print("Task ended: ", current_task.get_name() if current_task else "No name")

    runner = CoroRunner(concurrency=20, worker=_workers)
    for _ in range(10):
        runner.add_task(my_coro())
    await runner.run_until_finished()
    await runner.cleanup()
    assert runner.running_task_count == 0
