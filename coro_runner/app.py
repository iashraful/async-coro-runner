from collections import deque
import asyncio
from typing import Any


class CoroRunner:
    def __init__(self, concurrency: int = 5):
        self._concurrency = concurrency
        self._running = set()
        self._waiting = deque()
        self._loop = asyncio.get_event_loop()

    @property
    def running_task_count(self):
        return len(self._running)

    def add_task(self, coro: Any):
        if len(self._running) >= self._concurrency:
            self._waiting.append(coro)
        else:
            self._start_task(coro)

    def _start_task(self, coro):
        self._running.add(coro)
        asyncio.create_task(self._task(coro))

    async def _task(self, coro):
        try:
            return await coro
        finally:
            self._running.remove(coro)
            if self._waiting:
                coro2 = self._waiting.popleft()
                self._start_task(coro2)

    async def run_until_exit(self):
        while self.running_task_count != -1:
            await asyncio.sleep(0.1)

    async def run_until_finished(self):
        while self.running_task_count > 0:
            await asyncio.sleep(0.1)

    async def cleanup(self):
        self._running = set()
        self._waiting = deque()
