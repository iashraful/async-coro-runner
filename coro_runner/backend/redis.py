from collections import deque
import json
from redis import Redis

from .base import BaseBackend

from ..schema import RedisConfig


class RedisBackend(BaseBackend):
    def __init__(self, conf: RedisConfig) -> None:
        super().__init__()
        self.r_client = self.__connect(conf)
        self._cache_prefix = "coro_runner"

    def __connect(self, conf: RedisConfig) -> Redis:
        return Redis(
            host=conf.host,
            port=conf.port,
            db=conf.db,
            password=conf.password,
        )

    def __close(self) -> None:
        self.r_client.close()

    def get_cache_key(self, key: str) -> str:
        return f"{self._cache_prefix}:{key}"

    def set_concurrency(self, concurrency: int) -> None:
        self.r_client.set(self.get_cache_key("concurrency"), concurrency)

    def set_waiting(self, waitings: dict[str, dict[str, deque]]) -> None:
        self.r_client.set(self.get_cache_key("waiting"), json.dumps(waitings))

    def cleanup(self):
        self.__close()
        return super().cleanup()
