from dataclasses import dataclass, field
from datetime import datetime
import uuid

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
    module: str
    queue: str
    received: datetime
    status: int = TaskStatusEnum.PENDING.value
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    args: list = field(default_factory=lambda: [])
    kwargs: dict = field(default_factory=lambda: {})
    result: str | None = None
    started: datetime | None = None
    finished: datetime | None = None
    exception: str | None = None
    remark: str | None = None


@dataclass
class RedisConfig:
    host: str
    port: int
    db: int
    username: str | None = None
    password: str | None = None
