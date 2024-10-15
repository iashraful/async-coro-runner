import asyncio
from random import random

import pytest

from coro_runner.runner import CoroRunner


@pytest.mark.asyncio
async def test_coro_runner():
    async def my_coro():
        current_task: asyncio.Task | None = asyncio.current_task()
        print("Task started: ", current_task.get_name() if current_task else "No name")
        await asyncio.sleep(random() * 2)
        print("Task ended: ", current_task.get_name() if current_task else "No name")

    runner = CoroRunner(concurrency=20)
    for _ in range(10):
        runner.add_task(my_coro())
    await runner.run_until_finished()
    await runner.cleanup()
    assert runner.running_task_count == 0
