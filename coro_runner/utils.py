from collections import deque
from datetime import datetime

from coro_runner.enums import TaskStatusEnum
from .logging import logger
from coro_runner.schema import Queue, TaskModel


def prepare_queue(
    queues: list[Queue], default_name: str
) -> dict[str, dict[str, deque]]:
    data = {default_name: {"score": 0, "queue": deque()}}
    for queue in queues:
        data[queue.name] = {"score": queue.score, "queue": deque()}
    logger.debug("Setting queues: %s", data)
    return data


def prepare_task_schema(
    name: str, queue: str, args: list = [], kwargs: dict = {}
) -> TaskModel:
    return TaskModel(
        name=name,
        queue=queue,
        received=datetime.now(),
        args=args,
        kwargs=kwargs,
        status=TaskStatusEnum.PENDING,
    )
