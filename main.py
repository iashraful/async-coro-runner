import asyncio
from random import random

from fastapi.concurrency import asynccontextmanager
from coro_runner.runner import CoroRunner


from fastapi import FastAPI

app = FastAPI()
runner = CoroRunner(concurrency=200)


async def rand_delay():
    rnd = random() + 0.5
    print("Task started: ", asyncio.current_task().get_name())
    await asyncio.sleep(rnd)
    print("Task ended: ", asyncio.current_task().get_name())


@app.get("/fire-task")
async def fire_another_task(count: int = 25):
    for _ in range(count):
        runner.add_task(rand_delay())
    return {"Task": "Done"}


async def startup():
    await runner.run_until_exit()


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    await startup()
    yield
