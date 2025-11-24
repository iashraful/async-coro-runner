from typing import Any, AsyncGenerator, Awaitable, Callable, Coroutine


FutureFuncType = (
    Callable[[Any, Any], Awaitable[Any]]
    | AsyncGenerator[Any, Any]
    | Coroutine[Any, Any, Any]
)
