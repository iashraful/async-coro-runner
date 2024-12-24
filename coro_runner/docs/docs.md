# Coroutine Runner

`coro_runner` is a Python library designed to simplify the execution and management of asynchronous tasks using `asyncio`. This library provides a convenient interface to run, manage, and monitor coroutines efficiently.

## Installation

To install `coro-runner`, use pip:

```bash
pip install coro-runner
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

### Defining the queue with priority

```python
runner = CoroRunner(
    concurrency=25,
    queue=QueueConfig(
        queues=[
            Queue(name="send_mail", score=2),
            Queue(name="async_task", score=10),
            Queue(name="low_priority", score=0.1),
        ],
    ),
)
# Add the tasks to the queue
runner.add_task(rand_delay(), queue_name="low_priority")
# Another queue
runner.add_task(rand_delay(), queue_name="async_task")
```

**Note: The higher value of score menas it has high priority.**
