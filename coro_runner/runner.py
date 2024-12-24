from collections import deque
import asyncio
from typing import Any, Coroutine

from .utils import prepare_worker_queue
from .logging import logger

from .schema import WorkerConfig

FutureFuncType = Coroutine[Any, Any, Any]


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

    def __init__(self, concurrency: int, worker: WorkerConfig | None = None):
        self._default_worker: str = "default"
        self._concurrency: int = concurrency
        self._running: set = set()
        if worker is None:
            worker = WorkerConfig(workers=[])
        self._waiting: dict[str, dict[str, deque]] = prepare_worker_queue(
            worker.workers, default_name=self._default_worker
        )
        self._loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
        self._worker_conf: WorkerConfig = worker

    @property
    def running_task_count(self) -> int:
        """
        Get the number of running tasks.
        """
        return len(self._running)

    @property
    def any_waiting_task(self):
        """
        Check if there is any task in the waiting queue.
        """
        return any([len(worker["queue"]) for worker in self._waiting.values()])

    def pop_task_from_waiting_queue(self) -> FutureFuncType | None:
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

    def add_task(self, coro: FutureFuncType, worker_name: str | None = None) -> None:
        """
        Adding will add the coroutine to the default OR defined worker queue. If the concurrency is full, it'll be added to the waiting queue.
        Otherwise, it'll be started immediately.
        """
        logger.debug(f"Adding {coro.__name__} to worker: {worker_name}")
        if worker_name is None:
            worker_name = self._default_worker
        if len(self._running) >= self._concurrency:
            self._waiting[worker_name]["queue"].append(coro)
        else:
            self._start_task(coro)

    def _start_task(self, coro: FutureFuncType):
        """
        Stat the task and add it to the running set.
        """
        self._running.add(coro)
        asyncio.create_task(self._task(coro))
        logger.debug(f"Started task: {coro.__name__}")

    async def _task(self, coro: FutureFuncType):
        """
        The main task runner. It'll run the coroutine and remove it from the running set after completion.
        If there is any task in the waiting queue, it'll start the task.
        """
        try:
            return await coro
        finally:
            self._running.remove(coro)
            if self.any_waiting_task:
                coro2: FutureFuncType | None = self.pop_task_from_waiting_queue()
                if coro2:
                    self._start_task(coro2)

    async def run_until_exit(self):
        """
        This is to keep the runner alive until manual exit. It'll keep running until the running_task_count is -1.
        """
        while self.running_task_count != -1:
            await asyncio.sleep(0.1)

    async def run_until_finished(self):
        """
        This is to keep the runner alive until all the tasks are finished.
        """
        while self.running_task_count > 0:
            await asyncio.sleep(0.1)

    async def cleanup(self):
        """
        Cleanup the runner. It'll remove all the running and waiting tasks.
        """
        logger.debug("Cleaning up the runner")
        self._running = set()
        self._waiting = dict()
