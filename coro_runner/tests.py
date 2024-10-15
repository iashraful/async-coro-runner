import asyncio

import pytest

from coro_runner.runner import CoroRunner


@pytest.mark.asyncio
async def test_coro_runner():
    async def my_coro():
        await asyncio.sleep(0.1)
        return "done"

    runner = CoroRunner(concurrency=20)
    for _ in range(100):
        runner.add_task(my_coro())
