from dataclasses import dataclass, field
from datetime import datetime

from .enums import TaskStatusEnum


@dataclass
class Queue:
    name: str
    score: float


@dataclass
class QueueConfig:
    queues: list[Queue]


@dataclass
class TaskModel:
    """
    Task details. It'll be used to store the task details in the db.
    """

    name: str
    queue: str
    received: datetime
    status: TaskStatusEnum = TaskStatusEnum.PENDING
    args: list = field(default_factory=lambda: [])
    kwargs: dict = field(default_factory=lambda: {})
    result: str | None = None
    started: datetime | None = None
    finished: datetime | None = None
    errors: str | None = None


@dataclass
class RedisConfig:
    host: str
    port: int
    db: int
    username: str | None = None
    password: str | None = None
