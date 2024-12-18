import asyncio
from random import random

from fastapi.concurrency import asynccontextmanager
from coro_runner.runner import CoroRunner


from fastapi import FastAPI

app = FastAPI()
runner = CoroRunner(concurrency=25)


async def rand_delay():
    current_task: asyncio.Task | None = asyncio.current_task()
    print("Task started: ", current_task.get_name() if current_task else "No name")
    await asyncio.sleep(random() * 5)
    print("Task ended: ", current_task.get_name() if current_task else "No name")


@app.get("/fire-task")
async def fire_another_task(count: int = 25):
    for _ in range(count):
        runner.add_task(rand_delay())
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
