from collections import deque
from dataclasses import asdict
from datetime import datetime
import json
from typing import Any
from redis import ConnectionPool, Redis

from coro_runner.enums import TaskStatusEnum
from coro_runner.utils import get_task_name, get_the_func


from coro_runner.types import FutureFuncType

from .base import BaseBackend

from ..schema import RedisConfig, TaskModel


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


    def set_waiting(self, waitings: dict[str, dict[str, deque]]) -> None:
        """
        Set the queue configuration.
        """
        all_tasks = self.get_all_tasks_from_db()
        if len(all_tasks[0]) > 0:
            # There are pending tasks in the DB, we need to restore the waiting queues
            for task in all_tasks[0]:
                queue_name = task.queue
                if queue_name not in waitings:
                    waitings[queue_name] = {"score": 1, "queue": deque()}
                waitings[queue_name]["queue"].append({
                    "task_id": task.task_id,
                    "fn": get_the_func(f"{task.module}.{task.name}"),
                    "args": task.args,
                    "kwargs": task.kwargs,
                })
        if len(all_tasks[1])    > 0:
            # There are running tasks in the DB, we need them updated as cancelled
            for task in all_tasks[1]:
                self.update_task_in_db(
                    task.task_id,
                    status=TaskStatusEnum.CANCELLED.value,
                    finished=datetime.now(),
                    remark="Server Restarted",
                )
        super().set_waiting(waitings)   
        

    def get_cache_key(self, key: str) -> str:
        return f"{self._cache_prefix}:{key}"

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
        self.r_client.hset(
            self.get_cache_key(self._dk__all_tasks),
            task_data.task_id,
            json.dumps(asdict(task_data), default=str),
        )
        return task_data

    def update_task_in_db(
        self,
        task_id: str,
        **updates: Any,
    ) -> TaskModel | None:
        """
        Update a task in the task db.
        """
        task_data_cache: str | None = self.r_client.hget(
            self.get_cache_key(self._dk__all_tasks), task_id
        )
        if task_data_cache:
            task_data = TaskModel(**json.loads(task_data_cache))
        else:
            return None
        if not task_data:
            return None
        for key, value in updates.items():
            if hasattr(task_data, key):
                setattr(task_data, key, value)

        self.r_client.hset(
            self.get_cache_key(self._dk__all_tasks),
            task_data.task_id,
            json.dumps(asdict(task_data), default=str),
        )
        return task_data

    def get_task_from_db(self, task_id: str) -> TaskModel | None:
        """
        Get a task from the task db.
        """
        task_data_cache: str | None = self.r_client.hget(
            self.get_cache_key(self._dk__all_tasks), task_id
        )
        if task_data_cache:
            task_data = TaskModel(**json.loads(task_data_cache))
            return task_data
        return None

    def get_all_tasks_from_db(
        self,
    ) -> tuple[
        list[TaskModel],
        list[TaskModel],
        list[TaskModel],
        list[TaskModel],
        list[TaskModel],
    ]:
        """
        Get all tasks from the task db.
        """
        waitings, runnings, completed, failed, cancelled = [], [], [], [], []

        all_task_ids = self.r_client.hkeys(self.get_cache_key(self._dk__all_tasks))
        for task_id in all_task_ids:
            task_data_cache: str | None = self.r_client.hget(
                self.get_cache_key(self._dk__all_tasks), task_id
            )
            if task_data_cache:
                task_data = TaskModel(**json.loads(task_data_cache))
                if task_data.status == TaskStatusEnum.PENDING.value:
                    waitings.append(task_data)
                elif task_data.status == TaskStatusEnum.RUNNING.value:
                    runnings.append(task_data)
                elif task_data.status == TaskStatusEnum.FINISHED.value:
                    completed.append(task_data)
                elif task_data.status == TaskStatusEnum.FAILED.value:
                    failed.append(task_data)
                elif task_data.status == TaskStatusEnum.CANCELLED.value:
                    cancelled.append(task_data)
        return waitings, runnings, completed, failed, cancelled
