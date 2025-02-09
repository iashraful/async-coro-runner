from typing import Any, Awaitable, Callable


FutureFuncType = Callable[[Any, Any], Awaitable[Any]]
