import abc
from collections import deque
from typing import Any

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
        # This is the data dictionary.
        self.__data = {
            self._dk__concurrency: 1,
            self._dk__waiting: dict(),
            self._dk__running: set(),
        }

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

    def add_task_to_waiting_queue(
        self, queue_name: str, task: FutureFuncType, args: list = [], kwargs: dict = {}
    ) -> None:
        """
        Add a task to the waiting queue.
        """
        self._waiting[queue_name]["queue"].append(
            {
                "fn": task,
                "args": args,
                "kwargs": kwargs,
            }
        )

    def add_task_to_running(self, task: FutureFuncType) -> None:
        """
        Add a task to the running set.
        """
        self._running.add(task)

    def remove_task_from_running(self, task: FutureFuncType) -> None:
        """
        Remove a task from the running set.
        """
        self._running.remove(task)

    def pop_task_from_waiting_queue(self) -> dict[str, FutureFuncType | Any] | None:
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
