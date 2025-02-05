import abc
from collections import deque
import json
from typing import Any, Coroutine
from redis.asyncio import Redis, ConnectionPool

from .schema import RedisConfig
from .logging import logger

FutureFuncType = Coroutine[Any, Any, Any]


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
        self._concurrency: int = 1
        self._waiting: dict[str, dict[str, deque]] = dict()
        self._running: set = set()

    def set_concurrency(self, concurrency: int) -> None:
        """
        Set the concurrency of the backend.
        """
        self._concurrency = concurrency

    def set_waiting(self, waitings: dict[str, dict[str, deque]]) -> None:
        """
        Set the queue configuration.
        """
        self._waiting = waitings

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

    async def cleanup(self):
        """
        Cleanup the runner. It'll remove all the running and waiting tasks.
        """
        logger.debug("Cleaning up the runner")
        self._running = set()
        self._waiting = dict()


class InMemoryBackend(BaseBackend):
    pass


class RedisBackend(BaseBackend):
    def __init__(self, conf: RedisConfig) -> None:
        super(RedisBackend).__init__()
        self._has_persistence = True
        self._waiting: dict[str, dict[str, deque]] = dict()
        self._running: set = set()
        self._conf = conf
        self.r_client = self.__connect()
        self._cache_prefix = "coro_runner"

    def __connect(self) -> Redis:
        _redis_url: str = f"redis://{self._conf.host}:{self._conf.port}/{self._conf.db}"
        if self._conf.username and self._conf.password:
            _redis_url = f"redis://{self._conf.username}:{self._conf.password}@{self._conf.host}:{self._conf.port}/{self._conf.db}"
        conn_poll = ConnectionPool.from_url(_redis_url)
        return Redis(connection_pool=conn_poll)

    async def __close(self) -> None:
        await self.r_client.aclose()

    def get_cache_key(self, key: str) -> str:
        return f"{self._cache_prefix}:{key}"

    async def initialize(self):
        _waitings, _runnings, _concurrency = await self.get_cache_data()
        self.set_waiting(_waitings)
        # TODO: Add the running tasks to the waiting queue to run them again.
        self._running = _runnings
        self.set_concurrency(_concurrency)

    def set_concurrency(self, concurrency: int) -> None:
        # TODO: Set to the redis
        self._concurrency = concurrency

    async def set_cache_data(self) -> None:
        # Waiting tasks
        await self.r_client.set(
            self.get_cache_key("waiting_tasks"), json.dumps(self._waiting)
        )
        # Running tasks
        await self.r_client.set(
            self.get_cache_key("running_tasks"), json.dumps(list(self._running))
        )
        # Concurrency
        await self.r_client.set(self.get_cache_key("concurrency"), self._concurrency)

    async def get_cache_data(self) -> tuple[dict[str, dict[str, deque]], set, int]:
        # Waiting tasks
        waiting_tasks = await self.r_client.get(self.get_cache_key("waiting_tasks"))
        if waiting_tasks:
            self._waiting = json.loads(waiting_tasks)
        # Running tasks
        running_tasks = await self.r_client.get(self.get_cache_key("running_tasks"))
        if running_tasks:
            self._running = set(json.loads(running_tasks))
        # Concurrency
        concurrency = await self.r_client.get(self.get_cache_key("concurrency"))
        if concurrency:
            self._concurrency = int(concurrency)
        return waiting_tasks, running_tasks, concurrency
