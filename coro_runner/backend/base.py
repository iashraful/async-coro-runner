import abc
from collections import deque
from datetime import datetime
from typing import Any

from coro_runner.enums import TaskStatusEnum
from coro_runner.schema import TaskModel
from coro_runner.utils import get_task_name

from ..logging import logger
from ..types import FutureFuncType


class BaseBackend(abc.ABC):
    """
    Base class for all backends. All backends must inherit from this class.
    Features:
        - Add a task to memory. O(1)
        - Get a task from memory. O(1)
        - List of tasks in memory. O(1)
        - Task persistence. O(1)
    Datastructure
        - Task: Dict[str, Any]
    """

    def __init__(self) -> None:
        super(BaseBackend).__init__()
        self._has_persistence: bool = False

        # These are the keys used in the data dictionary.
        self._dk__concurrency = "concurrency"
        self._dk__waiting = "waiting"
        self._dk__running = "running"
        self._dk__all_tasks = "tasks"
        # This is the data dictionary.
        self.__data = {
            self._dk__concurrency: 1,
            self._dk__waiting: dict(),
            self._dk__running: set(),  # tuples of (task, task_id)
        }
        self.__task_db = dict()

    def set_concurrency(self, concurrency: int) -> None:
        """
        Set the concurrency of the backend.
        """
        self.__data[self._dk__concurrency] = concurrency

    def set_waiting(self, waitings: dict[str, dict[str, deque]]) -> None:
        """
        Set the queue configuration.
        """
        self.__data[self._dk__waiting] = waitings

    def add_task_to_db(
        self,
        queue_name: str,
        task: FutureFuncType,
        args: list | tuple = [],
        kwargs: dict = {},
    ) -> TaskModel:
        """
        Add a task to the task db.
        """
        task_data = TaskModel(
            name=get_task_name(task),
            module=task.__module__,
            queue=queue_name,
            received=datetime.now(),
            args=list(args),
            kwargs=kwargs,
        )
        self.__task_db[task_data.task_id] = task_data
        return task_data

    def update_task_in_db(
        self,
        task_id: str,
        **updates: Any,
    ) -> TaskModel | None:
        """
        Update a task in the task db.
        """
        task_data = self.__task_db.get(task_id)
        if not task_data:
            return None
        for key, value in updates.items():
            if hasattr(task_data, key):
                setattr(task_data, key, value)
        return task_data

    def add_task_to_waiting_queue(
        self,
        queue_name: str,
        task: FutureFuncType,
        task_id: str,
        args: list | tuple = [],
        kwargs: dict = {},
    ) -> None:
        """
        Add a task to the waiting queue.
        """
        self._waiting[queue_name]["queue"].append(
            {
                "task_id": task_id,
                "fn": task,
                "args": args,
                "kwargs": kwargs,
            }
        )

    def add_task_to_running(self, task: FutureFuncType, task_id: str) -> None:
        """
        Add a task to the running set.
        """
        self._running.add((task, task_id))

    def remove_task_from_running(self, task: FutureFuncType, task_id: str) -> None:
        """
        Remove a task from the running set.
        """
        try:
            self._running.remove((task, task_id))
        except KeyError:
            logger.error(
                f"Task {task.__name__} with ID {task_id} not found in running set."
            )

    def pop_task_from_waiting_queue(self) -> list[dict[str, FutureFuncType | Any]]:
        """
        Pop and single task from the waiting queue. If no task is available, return None.
        It'll return the task based on the queue's score. The hightest score queue's task will be returned. 0 means low priority.
        """
        _running_count = len(self._running)
        _tasks_to_run = list()
        if _running_count >= self._concurrency:
            return list()
        for queue in sorted(
            self._waiting.values(), key=lambda x: x["score"], reverse=True
        ):
            if _running_count + len(_tasks_to_run) >= self._concurrency:
                break
            
            if queue["queue"]:
                # Here we pop multiple tasks if possible to fill the concurrency limit
                _tasks_to_run = [queue["queue"].popleft() for _ in range(min(self._concurrency - (_running_count + len(_tasks_to_run)), len(queue["queue"])) - 1)]
                _tasks_to_run.append(queue["queue"].popleft())
        return _tasks_to_run

    @property
    def _concurrency(self) -> int:
        """
        Get the concurrency of the backend.
        """
        return self.__data[self._dk__concurrency]

    @property
    def _waiting(self) -> dict[str, dict[str, deque]]:
        """
        Get the queue configuration.
        """
        return self.__data[self._dk__waiting]

    @property
    def _running(self) -> set:
        """
        Get the running tasks.
        """
        return self.__data[self._dk__running]

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

    def get_all_tasks_from_db(
        self,
    ) -> tuple[
        list[TaskModel],  # waitings
        list[TaskModel],  # runnings
        list[TaskModel],  # completed
        list[TaskModel],  # failed
        list[TaskModel],  # cancelled
    ]:
        _waitings: list[TaskModel] = []
        _runnings: list[TaskModel] = []
        _completed: list[TaskModel] = []
        _failed: list[TaskModel] = []
        _cancelled: list[TaskModel] = []
        for task_data in self.__task_db.values():
            if task_data.status == TaskStatusEnum.PENDING.value:
                _waitings.append(task_data)
            elif task_data.status == TaskStatusEnum.RUNNING.value:
                _runnings.append(task_data)
            elif task_data.status == TaskStatusEnum.FINISHED.value:
                _completed.append(task_data)
            elif task_data.status == TaskStatusEnum.FAILED.value:
                _failed.append(task_data)
            elif task_data.status == TaskStatusEnum.CANCELLED.value:
                _cancelled.append(task_data)
        return _waitings, _runnings, _completed, _failed, _cancelled

    def get_report(self) -> dict[str, Any]:
        """
        Get the report of the backend.
        """
        waiting, running, completed, failed, cancelled = self.get_all_tasks_from_db()
        return {
            "concurrency": self._concurrency,
            "running_task_count": len(self._running),
            "waiting_task_count": sum(
                [len(queue["queue"]) for queue in self._waiting.values()]
            ),
            "waiting_tasks": waiting,
            "running_tasks": running,
            "completed_tasks": completed,
            "failed_tasks": failed,
            "cancelled_tasks": cancelled,
        }

    def is_valid_queue_name(self, queue_name: str) -> bool:
        """
        Check if the queue name is valid or not.
        """
        return queue_name in self._waiting

    async def cleanup(self) -> None:
        """
        Cleanup the runner. It'll remove all the running and waiting tasks.
        """
        logger.debug("Cleaning up the runner")
        self.__data = {
            self._dk__concurrency: 1,
            self._dk__waiting: dict(),
            self._dk__running: set(),
        }
