from collections import deque
import asyncio
from typing import Any, Coroutine

from .utils import prepare_worker_queue
from .logging import logger

from .schema import WorkerConfig


class CoroRunner:
    """
    AsyncIO Based Coroutine Runner
    It's a simple coroutine runner that can run multiple coroutines concurrently. But it will not run more than the specified concurrency.
    You can define the concurrency while creating the instance of the class. The default concurrency is 5.

    Also you can define queue number of coroutines to run concurrently. If the number of running coroutines is equal to the concurrency,
    the new coroutines will be added to the waiting queue.


    Waiting Queue Example:
    -------------
    {
        "default": {
            "score": 0,
            "queue": deque()
        },
        "Worker1": {
            "score": 1,
            "queue": deque()
        },
        "Worker2": {
            "score": 10,
            "queue": deque()
    }
    """

    def __init__(self, concurrency: int, worker: WorkerConfig):
        self._default_worker = "default"
        self._concurrency = concurrency
        self._running = set()
        self._waiting: dict[str, dict[str, deque]] = prepare_worker_queue(
            worker.workers, default_name=self._default_worker
        )
        self._loop = asyncio.get_event_loop()
        self._worker_conf = worker

    @property
    def running_task_count(self):
        return len(self._running)

    @property
    def any_waiting_task(self):
        return any([len(worker["queue"]) for worker in self._waiting.values()])

    def pop_task_from_waiting_queue(self) -> Coroutine | None:
        """
        Pop and single task from the waiting queue. If no task is available, return None.
        It'll return the task based on the worker score. The hightest score worker's task will be returned. 0 means low priority.
        """
        for worker in sorted(
            self._waiting.values(), key=lambda x: x["score"], reverse=True
        ):
            if worker["queue"]:
                return worker["queue"].popleft()
        return None

    def add_task(self, coro: Any, worker_name: str | None = None):
        logger.debug(f"Adding {coro.__name__} to worker: {worker_name}")
        if worker_name is None:
            worker_name = self._default_worker
        if len(self._running) >= self._concurrency:
            self._waiting[worker_name]["queue"].append(coro)
        else:
            self._start_task(coro)

    def _start_task(self, coro):
        self._running.add(coro)
        asyncio.create_task(self._task(coro))
        logger.debug(f"Started task: {coro.__name__}")

    async def _task(self, coro):
        try:
            return await coro
        finally:
            self._running.remove(coro)
            if self.any_waiting_task:
                coro2 = self.pop_task_from_waiting_queue()
                self._start_task(coro2)

    async def run_until_exit(self):
        while self.running_task_count != -1:
            await asyncio.sleep(0.1)

    async def run_until_finished(self):
        while self.running_task_count > 0:
            await asyncio.sleep(0.1)

    async def cleanup(self):
        self._running = set()
        self._waiting = dict()
