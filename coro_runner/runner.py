import asyncio
from typing import Any

from .backend import BaseBackend, InMemoryBackend

from .utils import prepare_queue
from .logging import logger

from .schema import QueueConfig
from .types import FutureFuncType


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

    def __init__(
        self,
        concurrency: int,
        queue_conf: QueueConfig | None = None,
        backend: BaseBackend = InMemoryBackend(),
    ) -> None:
        self._default_queue: str = "default"
        if queue_conf is None:
            queue_conf = QueueConfig(queues=[])
        self._backend = backend
        # Update the backend
        self._backend.set_concurrency(concurrency)
        self._backend.set_waiting(
            waitings=prepare_queue(queue_conf.queues, default_name=self._default_queue)
        )
        self._loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()

    def add_task(
        self,
        coro: FutureFuncType,
        args: list = [],
        kwargs: dict = {},
        queue_name: str | None = None,
    ) -> None:
        """
        Adding will add the coroutine to the default OR defined queue queue. If the concurrency is full, it'll be added to the waiting queue.
        Otherwise, it'll be started immediately.
        :param coro: The coroutine to be run.
        :param args: The arguments will be passed the function directly.
        :param kwargs: The arguments will be passed the function directly.
        """
        if queue_name is None:
            queue_name = self._default_queue
        if self._backend.is_valid_queue_name(queue_name) is False:
            raise ValueError(f"Unknown queue name: {queue_name}")
        logger.debug(f"Adding {coro.__name__} to queue: {queue_name}")
        if len(self._backend._running) >= self._backend._concurrency:
            self._backend.add_task_to_waiting_queue(queue_name, coro, args, kwargs)
        else:
            self._start_task(coro(*args, **kwargs))

    def _start_task(self, coro: FutureFuncType):
        """
        Stat the task and add it to the running set.
        """
        self._backend.add_task_to_running(coro)
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
            self._backend.remove_task_from_running(coro)
            if self._backend.any_waiting_task:
                coro2_data: dict[str, FutureFuncType | Any] | None = (
                    self._backend.pop_task_from_waiting_queue()
                )
                if coro2_data:
                    __fn = coro2_data["fn"]
                    self._start_task(__fn(*coro2_data["args"], **coro2_data["kwargs"]))

    async def run_until_exit(self):
        """
        This is to keep the runner alive until manual exit. It'll keep running until the running_task_count is -1.
        """
        while self._backend.running_task_count != -1:
            await asyncio.sleep(0.1)

    async def run_until_finished(self):
        """
        This is to keep the runner alive until all the tasks are finished.
        """
        while self._backend.running_task_count > 0:
            await asyncio.sleep(0.1)

    async def cleanup(self):
        """
        Cleanup the runner. It'll remove all the running and waiting tasks.
        """
        # TODO: Keep the persistant tasks during clean up
        await self._backend.cleanup()

        logger.debug("Runner cleaned up along with backend.")
