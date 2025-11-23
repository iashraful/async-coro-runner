# AsyncIO Task Runner (Coro Runner)

[![Test OK!](https://github.com/iashraful/async-coro-runner/actions/workflows/tests-runner.yml/badge.svg?branch=main)](https://github.com/iashraful/async-coro-runner/actions/workflows/tests-runner.yml)
[![PyPI](https://img.shields.io/pypi/v/coro-runner?label=Python%20Package)](https://pypi.org/project/coro-runner/)

The **AsyncIO Task Runner** (Coro Runner) is a Python utility designed for managing concurrent asynchronous tasks using the built-in `asyncio` module. It provides an efficient way to execute multiple tasks in a single-threaded environment with customizable concurrency limits.

This project leverages `asyncio` (introduced in Python 3.4) to simplify handling of asynchronous workloads, making it ideal for lightweight, scalable applications.

## Features

- **Configurable Concurrency**: Define the number of concurrent tasks when initializing the runner.
- **Efficient Task Management**: Run multiple tasks concurrently with streamlined execution control.
- **Worker Queue**: Multiple queue can be configued along with their priority.

### Planned Enhancements

- **Monitoring Tool Integration**: Support for real-time task monitoring and analytics.
- **Low-Level API**: Features such as callbacks, acknowledgments, and error handling for advanced use cases.
- **Robust Logging**: Detailed logging to track task execution and debug issues.

## Getting Started

### Installation

To install `coro-runner`, use pip:

```bash
pip install coro-runner
```

### Full documentation
>
> [Here is the full documentation](https://github.com/iashraful/async-coro-runner/tree/main/coro_runner/docs/docs.md)

### Quickstart

- Define and schedule tasks:

  ```python
  from coro_runner import CoroRunner


  runner = CoroRunner(concurrency=10)
  # Add your tasks from anywhere b       
  runner.add_task(your_task, args=[1,2,3], kwargs={"test": "OK!"}) # your_task must be a async function
  ```

  **Declare the runner once and call from everywhere.**

### Prerequisites

- Python 3.12 or later
- [Poetry](https://python-poetry.org/) for dependency management

### Installation and Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/iashraful/async-coro-runner.git
   cd async-coro-runner
   ```

2. Activate the virtual environment:

   ```bash
   poetry shell
   ```

3. Install dependencies:

   ```bash
   poetry install
   ```

### Running Tests

Run the test suite to verify the setup:

```bash
pytest -s
```

**Sample Output:**

```text
Task started:  Task-1
Task ended:    Task-1
...
```

## Example Usage

The project includes an example API implemented with FastAPI. It demonstrates how to use the task runner to manage asynchronous tasks.

### Starting the API

1. Run the API server:

   ```bash
   uvicorn example:app --reload
   ```

2. Trigger tasks using the endpoint:

   ```bash
   GET /fire-task?count=25
   ```

## How to Contribute

Contributions are welcome! Follow these steps to get started:

1. Fork the repository and create a new branch for your feature or bug fix.
2. Write tests for your changes.
3. Open a pull request with a clear description of your contribution.
