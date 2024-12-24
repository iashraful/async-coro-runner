# Coroutine Runner

`coro_runner` is a Python library designed to simplify the execution and management of asynchronous tasks using `asyncio`. This library provides a convenient interface to run, manage, and monitor coroutines efficiently.

## Installation

To install `coro_runner`, use pip:

```bash
pip install coro_runner
```

## Usage

### Basic Example

Here is a basic example of how to use `coro_runner` to run a simple coroutine:

```python
import asyncio
from coro_runner import CoroRunner

async def my_coroutine():
    await asyncio.sleep(1)
    print("Hello, World!")

runner = CoroRunner(concurrency=10)
for _ in range(count):
        runner.add_task(rand_delay())
```

### Defining the worker with priority

```python
runner = CoroRunner(
    concurrency=25,
    worker=WorkerConfig(
        workers=[
            Worker(name="send_mail", score=2),
            Worker(name="async_task", score=10),
            Worker(name="low_priority", score=0.1),
        ],
    ),
)
# Add the tasks to the worker
runner.add_task(rand_delay(), worker_name="low_priority")
# Another worker
runner.add_task(rand_delay(), worker_name="async_task")
```

**Note: The higher value of score menas it has high priority.**
