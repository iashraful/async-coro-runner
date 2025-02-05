import asyncio
import logging
from random import random

from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager

from coro_runner import Queue, QueueConfig
from coro_runner.runner import CoroRunner

# Log Config
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

app = FastAPI(title="Coro Runner Example")
runner = CoroRunner(
    concurrency=25,
    queue_conf=QueueConfig(
        queues=[
            Queue(name="send_mail", score=2),
            Queue(name="async_task", score=10),
            Queue(name="low_priority", score=0.1),
        ],
    ),
)


async def rand_delay():
    current_task: asyncio.Task | None = asyncio.current_task()
    logger.info(
        f"Random Delay started: {current_task.get_name() if current_task else 'No Name'}",
    )
    await asyncio.sleep(random() * 5)
    logger.info(
        f"Random Delay ended: {current_task.get_name() if current_task else 'No name'}"
    )


async def dummy_email_send():
    current_task: asyncio.Task | None = asyncio.current_task()
    logger.info(
        f"Dummy Send Email started: {current_task.get_name() if current_task else 'No Name'}",
    )
    await asyncio.sleep(random() * 3)
    logger.info(
        f"Dummy Send Email ended: {current_task.get_name() if current_task else 'No name'}"
    )


@app.get("/random-delay")
async def fire_random_delay(count: int = 25):
    for _ in range(count):
        runner.add_task(rand_delay(), queue_name="low_priority")
    return {"Task": "Done"}


@app.get("/dummy-send-email")
async def fire_send_email(count: int = 25):
    for _ in range(count):
        runner.add_task(dummy_email_send(), queue_name="send_mail")
    return {"Task": "Done"}


async def startup():
    await runner.run_until_exit()


async def shutdown():
    await runner.cleanup()


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    await startup()
    yield
    await shutdown()
