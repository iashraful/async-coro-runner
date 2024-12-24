from dataclasses import dataclass


@dataclass
class Queue:
    name: str
    score: float


@dataclass
class QueueConfig:
    queues: list[Queue]
