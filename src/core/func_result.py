import time
from datetime import timedelta
from typing import Any, Callable, Coroutine, Generic, TypeVar

from pydantic import Field

from src.core.dataclass import Dataclass

T = TypeVar("T")


def td2ms(delta: timedelta) -> int:
    """Convert a timedelta to microseconds."""
    return int(delta.total_seconds() * 1_000_000)


class Timed(Dataclass, Generic[T]):
    """Wrapper that adds duration to any base type."""

    time: timedelta = Field(
        default=timedelta(0),
        description="Duration of the execution.",
    )
    data: T


def timed(func: Callable[..., T]) -> Callable[..., Timed[T]]:
    """Decorator to wrap a sync function's return value in Timed[T]."""

    def wrapper(*args: Any, **kwargs: Any) -> Timed[T]:
        start = time.perf_counter()
        result = func(*args, **kwargs)
        duration = time.perf_counter() - start
        return Timed[T](time=timedelta(seconds=duration), data=result)

    return wrapper


def atimed(
    func: Callable[..., Coroutine[Any, Any, T]],
) -> Callable[..., Coroutine[Any, Any, Timed[T]]]:
    """Decorator to wrap an async function's return value in Timed[T]."""

    async def wrapper(*args: Any, **kwargs: Any) -> Timed[T]:
        start = time.perf_counter()
        result = await func(*args, **kwargs)
        duration = time.perf_counter() - start
        return Timed[T](time=timedelta(seconds=duration), data=result)

    return wrapper
