from collections import deque
import json
from redis.asyncio import Redis, ConnectionPool

from .base import BaseBackend

from ..schema import RedisConfig


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
