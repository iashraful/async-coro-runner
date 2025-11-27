from enum import IntEnum


class TaskStatusEnum(IntEnum):
    PENDING = 0
    RUNNING = 1
    FINISHED = 2
    FAILED = 3
    CANCELLED = 4
