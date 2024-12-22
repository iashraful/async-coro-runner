from collections import deque
from .logging import logger
from coro_runner.schema import Worker


def prepare_worker_queue(
    workers: list[Worker], default_name: str
) -> dict[str, dict[str, deque]]:
    data = {default_name: {"score": 0, "queue": deque()}}
    for worker in workers:
        data[worker.name] = {"score": worker.score, "queue": deque()}
    logger.debug("Setting workers: %s", data)
    return data
