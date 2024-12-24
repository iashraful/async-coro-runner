from collections import deque
import asyncio
from operator import is_
from typing import Any, Coroutine

from .utils import prepare_queue_queue
from .logging import logger

from .schema import QueueConfig

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
        "Queue1": {
            "score": 1,
            "queue": deque()
        },
        "Queue2": {
            "score": 10,
            "queue": deque()
    }
    """

    def __init__(self, concurrency: int, queue_conf: QueueConfig | None = None):
        self._default_queue: str = "default"
        self._concurrency: int = concurrency
        self._running: set = set()
        if queue_conf is None:
            queue_conf = QueueConfig(queues=[])
        self._waiting: dict[str, dict[str, deque]] = prepare_queue_queue(
            queue_conf.queues, default_name=self._default_queue
        )
        self._loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
        self._queue_conf: QueueConfig = queue_conf

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
        return any([len(queue["queue"]) for queue in self._waiting.values()])

    def is_valid_queue_name(self, queue_name: str) -> bool:
        """
        Check if the queue name is valid or not.
        """
        return queue_name in self._waiting

    def pop_task_from_waiting_queue(self) -> FutureFuncType | None:
        """
        Pop and single task from the waiting queue. If no task is available, return None.
        It'll return the task based on the queue's score. The hightest score queue's task will be returned. 0 means low priority.
        """
        for queue in sorted(
            self._waiting.values(), key=lambda x: x["score"], reverse=True
        ):
            if queue["queue"]:
                return queue["queue"].popleft()
        return None

    def add_task(self, coro: FutureFuncType, queue_name: str | None = None) -> None:
        """
        Adding will add the coroutine to the default OR defined queue queue. If the concurrency is full, it'll be added to the waiting queue.
        Otherwise, it'll be started immediately.
        """
        if queue_name is None:
            queue_name = self._default_queue
        if self.is_valid_queue_name(queue_name) is False:
            raise ValueError(f"Unknown queue name: {queue_name}")
        logger.debug(f"Adding {coro.__name__} to queue: {queue_name}")
        if len(self._running) >= self._concurrency:
            self._waiting[queue_name]["queue"].append(coro)
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
