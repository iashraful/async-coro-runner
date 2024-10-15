# AsyncIO Task Runner (Coro Runner)

As we know asyncio is the builtin module since python3.4(decorator based). This module is to use build a **single threaded concurrancy** model with asyncio module.

## Features

* Set concurrency while define the runner.
* Multiple tasks can be run concurrently.

**To be implemented soon...**

* Monitoring tool integration
* Low level API(callback, acknowledment, etc...)
* Robust logging

## How to contribute?

* **Step 1:** Run `poetry shell` to activate the shell. You'll need Python 3.12 or latest
* **Step 2:** Run `poerty install`
* **Step 3:** Run `pytest -s`
* **Sample Test Run:**

```bash
coro_runner/test_runner.py 
Task started:  Task-2
Task started:  Task-3
Task started:  Task-4
Task started:  Task-5
Task started:  Task-6
Task started:  Task-7
Task started:  Task-8
Task started:  Task-9
Task started:  Task-10
Task started:  Task-11
Task ended:  Task-3
Task ended:  Task-4
Task ended:  Task-9
Task ended:  Task-7
Task ended:  Task-11
Task ended:  Task-6
Task ended:  Task-10
Task ended:  Task-2
Task ended:  Task-8
Task ended:  Task-5
```
