from base64 import b64decode, b64encode
from collections import deque
import json
import pickle
from typing import Any
from redis import ConnectionPool, Redis
from ..logging import logger

from coro_runner.types import FutureFuncType

from .base import BaseBackend

from ..schema import RedisConfig


class RedisBackend(BaseBackend):
    def __init__(self, conf: RedisConfig) -> None:
        super().__init__()
        self.r_client = self.__connect(conf)
        self._cache_prefix = "coro_runner"

    def __connect(self, conf: RedisConfig) -> Redis:
        pool = ConnectionPool(
            host=conf.host,
            port=conf.port,
            db=conf.db,
            password=conf.password,
        )
        return Redis(connection_pool=pool)

    def __close(self) -> None:
        self.r_client.close()

    def get_cache_key(self, key: str) -> str:
        return f"{self._cache_prefix}:{key}"

    def set_concurrency(self, concurrency: int) -> None:
        self.r_client.set(self.get_cache_key("concurrency"), concurrency)

    def __get_existing_queue(self) -> dict[str, dict[str, deque]]:
        try:
            data: dict = json.loads(
                self.r_client.get(self.get_cache_key(self._dk__waiting))
            )
            for key, value in data.items():
                data[key]["queue"] = pickle.loads(b64decode(value["queue"]))
            return data
        except Exception:
            logger.error("Error parsing the queue. Probably no queue.")
            import traceback

            print(traceback.format_exc())
            return {}

    def set_waiting(self, waitings: dict[str, dict[str, deque]]) -> None:
        """
        Set the waiting queue in the cache.
        We are going to store the waiting queue as pickled data in the cache. Because we have functions in the queue. Without
        the pickling, we can't store the functions in the cache.
        """
        jsonable_data = dict()
        for key, value in waitings.items():
            jsonable_data[key] = {
                "score": value["score"],
                "queue": b64encode(pickle.dumps(value["queue"])).decode("ascii"),
            }
        self.r_client.set(self.get_cache_key("waiting"), json.dumps(jsonable_data))

    def add_task_to_waiting_queue(
        self, queue_name: str, task: FutureFuncType, args: list = [], kwargs: dict = {}
    ) -> None:
        """ "
        Adding a task to the waiting queue. Once again read from cache append and pickle dump again.
        """
        data: dict = json.loads(
            self.r_client.get(self.get_cache_key(self._dk__waiting))
        )
        # Append is same for deque and list. We can use it directly.
        _data = pickle.loads(b64decode(data[queue_name]["queue"]))
        _data.append(
            {
                "fn": task,
                "args": args,
                "kwargs": kwargs,
            }
        )
        data[queue_name]["queue"] = b64encode(pickle.dumps(_data)).decode("ascii")
        self.r_client.set(self.get_cache_key(self._dk__waiting), json.dumps(data))

    def pop_task_from_waiting_queue(self) -> dict[str, FutureFuncType | Any] | None:
        """
        Pop Left is the hard task sometimes because we need to pickle and unpickle the data along with the queue score.
        """
        current_waitings = self._waiting
        for q_name, queue in sorted(
            current_waitings.items(), key=lambda x: x[1]["score"], reverse=True
        ):
            if queue["queue"]:
                q = queue["queue"].popleft()

                # Set the new queue
                current_waitings[q_name] = queue
                self.set_waiting(current_waitings)
                return q
        return None

    @property
    def _concurrency(self) -> int:
        return int(self.r_client.get(self.get_cache_key(self._dk__concurrency)))

    @property
    def _waiting(self) -> dict[str, dict[str, deque]]:
        """
        Get the waiting tasks from the cache. We are storing the queue as pickled data in the cache. We need to unpickle it.
        """
        data: dict = json.loads(
            self.r_client.get(self.get_cache_key(self._dk__waiting))
        )
        for key, value in data.items():
            data[key]["queue"] = pickle.loads(b64decode(value["queue"]))
        return data

    async def cleanup(self):
        self.r_client.delete(self.get_cache_key(self._dk__concurrency))
        self.r_client.delete(self.get_cache_key(self._dk__waiting))
        self.__close()
