from collections import deque
from .logging import logger
from coro_runner.schema import Queue


def prepare_queue_queue(
    queues: list[Queue], default_name: str
) -> dict[str, dict[str, deque]]:
    data = {default_name: {"score": 0, "queue": deque()}}
    for queue in queues:
        data[queue.name] = {"score": queue.score, "queue": deque()}
    logger.debug("Setting queues: %s", data)
    return data
