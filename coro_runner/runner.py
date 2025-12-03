import asyncio
from datetime import datetime
from typing import Any

from coro_runner.enums import TaskStatusEnum

from .backend import BaseBackend, InMemoryBackend

from .utils import prepare_queue
from .logging import logger

from .schema import QueueConfig, TaskModel
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

        
        
    def add_task(
        self,
        coro: FutureFuncType,
        args: list | tuple = [],
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
        logger.debug("Adding the task to db.")
        task_data: TaskModel = self._backend.add_task_to_db(
            queue_name, coro, args, kwargs
        )

        logger.debug(
            f"Adding Task: {coro.__name__}({task_data.task_id}) to queue: {queue_name}"
        )
        if len(self._backend._running) >= self._backend._concurrency:
            self._backend.add_task_to_waiting_queue(
                queue_name, coro, task_data.task_id, args, kwargs
            )
        else:
            self._start_task(coro(*args, **kwargs), task_data.task_id)

    def get_report(self) -> dict[str, Any]:
        """
        Get the report of the runner. It'll return the number of running, waiting and completed tasks.
        """
        return self._backend.get_report()

    def _start_task(self, coro: FutureFuncType, task_id: str):
        """
        Stat the task and add it to the running set.
        """
        self._backend.add_task_to_running(
            coro, task_id
        )  # Here coro is couroutine object with all the params
        asyncio.create_task(self._task(coro, task_id))
        logger.debug(f"Started task: {coro.__name__}. ID: {task_id}")

    async def _task(self, coro: FutureFuncType, task_id: str):
        """
        The main task runner. It'll run the coroutine and remove it from the running set after completion.
        If there is any task in the waiting queue, it'll start the task.
        """
        err = None
        result = None
        try:
            self._backend.update_task_in_db(
                task_id,
                status=TaskStatusEnum.RUNNING.value,
                started=datetime.now(),
            )
            result = await coro
            return result
        except Exception as err:
            logger.error(f"Error in task {coro.__name__}: {err}")
        finally:
            self._backend.remove_task_from_running(coro, task_id)
            self._backend.update_task_in_db(
                task_id,
                status=TaskStatusEnum.FINISHED.value,
                finished=datetime.now(),
                result=result,
                exception=str(err) if err else None,
            )
            await self.revive_and_restore_waiting_tasks()
            
    async def revive_and_restore_waiting_tasks(self):
        """
        Check and start waiting tasks if there is any.
        This method is useful during server restart to revive the waiting tasks from the backend.
        """
        if self._backend.any_waiting_task:
            coro2_data_list: list[dict] = self._backend.pop_task_from_waiting_queue()
            for coro2_data in coro2_data_list:
                __fn = coro2_data["fn"]
                self._start_task(
                    coro=__fn(*coro2_data["args"], **coro2_data["kwargs"]),
                    task_id=coro2_data["task_id"],
                )

    async def run_until_exit(self):
        """
        This is to keep the runner alive until manual exit. It'll keep running until the running_task_count is -1.

        You just need to call this method once during the app startup,
        if your app is not running on eventloop. Otherwise, it'll block the eventloop.
        So be careful while using it.

        To clear the confusion, you can look at the test_runner.py file and example.py files.
        I have used this method in test_runner.py but not in the example.py file.
        Because the example.py file is running on FastAPI example app which is already running on eventloop.
        """
        while self._backend.running_task_count != -1:
            await asyncio.sleep(0.1)

    async def run_until_finished(self):
        """
        This is to keep the runner alive until all the tasks are finished.

        You just need to call this method once during the app startup,
        if your app is not running on eventloop. Otherwise, it'll block the eventloop.
        So be careful while using it.

        To clear the confusion, you can look at the test_runner.py file and example.py files.
        I have used this method in test_runner.py but not in the example.py file.
        Because the example.py file is running on FastAPI example app which is already running on eventloop.
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
