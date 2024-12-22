import asyncio
from random import random

import pytest

from coro_runner import CoroRunner
from coro_runner.schema import Worker, WorkerConfig

# Defining the worker configuration
rg_worker = Worker(name="Regular", score=1)
hp_worker = Worker(name="HighPriority", score=10)


@pytest.mark.asyncio
async def test_coro_runner():
    async def my_coro():
        current_task: asyncio.Task | None = asyncio.current_task()
        print(
            "Regular task started: ",
            current_task.get_name() if current_task else "No name",
        )
        await asyncio.sleep(random() * 5)
        print(
            "Regular task ended: ",
            current_task.get_name() if current_task else "No name",
        )

    async def my_coro2():
        current_task: asyncio.Task | None = asyncio.current_task()
        print(
            "Priority task started: ",
            current_task.get_name() if current_task else "No name",
        )
        await asyncio.sleep(random() * 5)
        print(
            "Priority task ended: ",
            current_task.get_name() if current_task else "No name",
        )

    runner = CoroRunner(
        concurrency=2, worker=WorkerConfig(workers=[rg_worker, hp_worker])
    )
    print("Adding regular tasks")
    for _ in range(10):
        runner.add_task(my_coro(), worker_name=rg_worker.name)

    print("\nAdding priority tasks")
    for _ in range(10):
        runner.add_task(my_coro2(), worker_name=hp_worker.name)

    await runner.run_until_finished()
    await runner.cleanup()
    assert runner.running_task_count == 0
