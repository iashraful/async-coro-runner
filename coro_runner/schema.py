from dataclasses import dataclass


@dataclass
class Worker:
    name: str
    score: float


@dataclass
class WorkerConfig:
    workers: list[Worker]
