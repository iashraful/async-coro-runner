from enum import Enum


class TaskStatusEnum(Enum):
    PENDING = 0
    RUNNING = 1
    FINISHED = 2
    FAILED = 3
    CANCELLED = 4
