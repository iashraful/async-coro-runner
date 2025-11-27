import asyncio

from collections import deque
from datetime import datetime
import importlib
from typing import Any, Callable


from coro_runner.enums import TaskStatusEnum
from .logging import logger
from coro_runner.schema import Queue, TaskModel


def prepare_queue(
    queues: list[Queue], default_name: str
) -> dict[str, dict[str, deque[dict[str, Any]]]]:
    """
    The example queue configuration:
    {
        "default": {
            "score": 0,
            "queue": deque([{
                "fn": "app.api.tasks.foo",
                "args": ["helllo", "world"],
                "kwargs": {}
            }])
        },
        "Queue1": {
            "score": 1,
            "queue": deque([{
                "fn": "app.api.tasks.foo",
                "args": ["helllo", "world"],
                "kwargs": {}
            }])
        },
        "Queue2": {
            "score": 10,
            "queue": deque([{
                "fn": "app.api.tasks.foo",
                "args": ["helllo", "world"],
                "kwargs": {}
            }])
    """
    data = {default_name: {"score": 0, "queue": deque()}}
    for queue in queues:
        data[queue.name] = {"score": queue.score, "queue": deque()}
    logger.debug("Preparing the queues: %s", data)
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


def get_task_name(func: Any) -> str:
    """
    Get the task name from the function.
    """

    if hasattr(func, "__name__"):
        return func.__name__
    elif hasattr(func, "__class__") and hasattr(func.__class__, "__name__"):
        return func.__class__.__name__
    else:
        return str(func)


def get_full_path(func: Callable) -> str:
    """
    Get the full path of the function.
    """
    return f"{func.__module__}.{func.__name__}"


def get_the_func(path: str) -> Callable:
    """
    Get the function from the full path.
    """
    module_path, func_name = path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    func = getattr(module, func_name)
    return func
