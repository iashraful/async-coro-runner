import asyncio
from contextlib import asynccontextmanager
import logging
from pdb import run
from random import random

from .tasks import dummy_email_send, rand_delay
from fastapi import FastAPI
from fastapi.responses import FileResponse

from coro_runner import Queue, QueueConfig
from coro_runner.backend.redis import RedisBackend
from coro_runner.runner import CoroRunner
from coro_runner.schema import RedisConfig

# Log Config
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

runner = CoroRunner(
    concurrency=10,
    backend=RedisBackend(conf=RedisConfig(host="redis", port=6379, db=0)),
    queue_conf=QueueConfig(
        queues=[
            Queue(name="send_mail", score=2),
            Queue(name="async_task", score=10),
            Queue(name="low_priority", score=0.1),
        ],
    ),
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code
    await runner.revive_and_restore_waiting_tasks()
    yield
    # Shutdown code

app = FastAPI(title="Coro Runner Example", lifespan=lifespan)






@app.get("/random-delay")
async def fire_random_delay(count: int = 25):
    for _ in range(count):
        runner.add_task(
            rand_delay,
            args=(
                "Static Msg",
                10,
            ),
            queue_name="low_priority",
        )
    return {"Task": "Done"}


@app.post("/dummy-send-email")
async def fire_send_email(count: int = 25, emails: list[str] = []):
    for _ in range(count):
        runner.add_task(
            dummy_email_send,
            queue_name="send_mail",
            kwargs={"recipient_emails": emails},
        )
    return {"Task": "Done"}


@app.get("/report")
async def get_report():
    return runner.get_report()


@app.get("/stats")
async def get_worker_stats():
    return FileResponse("example/stats.html")
