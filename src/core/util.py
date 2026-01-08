import random
import re
import string
import textwrap
import time
from datetime import timedelta
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Coroutine, NamedTuple, TypeAlias, TypeVar

import rich.pretty

logid_t: TypeAlias = str
sid_t: TypeAlias = int

# Root path of the repo inside the Docker container.
REPO_ROOT: Path = Path("/gpt")


def multiline(s: str, oneline: bool = True, continuous: bool = False) -> str:
    """Correctly connect a multiline string.

    Args:
        s (str): A string, usually formed with three double quotes.
        oneline (bool): Whether to remove all line breaks in the result.
        continuous (bool): Whether to delete spaces formed at line connections.

    Returns:
        A string formed by removing all common whitespaces near the start of
        each line in the original string.

    Examples:
        >>> block = \"\"\"\
        ...     line one
        ...     line two
        ... \"\"\"
        >>> multiline(block)
        'line one line two'
        >>> long_url = \"\"\"\
        ...     https://example.com/
        ...     some/very/long/
        ...     path
        ... \"\"\"
        >>> multiline(long_url, continuous=True)
        'https://example.com/some/very/long/path'
    """
    result = textwrap.dedent(s)
    if oneline:
        result = result.replace("\n", " ")
    if continuous:
        result = result.replace(" ", "")
    return result.strip()


def as_filename(s: str) -> str:
    """
    Convert any str into a filesystem‑safe filename.

    Examples:
        >>> to_safe_filename("openai/gpt-4.1")
        'openai_gpt-4_1'
        >>> to_safe_filename("mistral‑ai/mixtral‑8x7b‑inst/💡")
        'mistral_ai_mixtral_8x7b_inst'
    """
    out = re.sub(r"[^A-Za-z0-9_-]+", "_", s)
    out = re.sub(r"_+", "_", out)
    out = out.strip("_")
    if not out:
        raise ValueError(f"Invalid input: {s}")
    return out


def randalnu(length: int = 4) -> str:
    """Return a randomized alphanumeric string of the given length."""
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))


def prepr(
    obj,
    *,
    max_width: int | None = None,
    indent: int | None = None,
):
    """Pretty repr an arbitrary object for str output, using env defaults."""
    from src import env

    return rich.pretty.pretty_repr(
        obj,
        max_width=max_width or env.MAX_WIDTH,
        indent_size=indent or env.INDENT,
        expand_all=True,
    )


def next_sid() -> sid_t:
    """Get the next serial ID from the environment."""
    from src import env

    return env.r.incr(env.SID_COUNTER_KEY)


def str2int(s: str | None) -> int | None:
    """Post-process a Redis HGET / HMGET result into int."""
    return int(s) if s is not None else None


def td2ms(delta: timedelta) -> int:
    """Convert a timedelta to microseconds."""
    return int(delta.total_seconds() * 1_000_000)


class TimedOutput(NamedTuple):
    """Result of a timed function call."""

    duration: timedelta
    output: Any


def timed(func: Callable) -> Callable[..., TimedOutput]:
    """Wraps a sync function to return its duration and result."""

    @wraps(func)
    def wrapper(*args, **kwargs) -> TimedOutput:
        start_time = time.perf_counter()
        output = func(*args, **kwargs)
        seconds_elapsed = time.perf_counter() - start_time
        return TimedOutput(
            duration=timedelta(seconds=seconds_elapsed),
            output=output,
        )

    return wrapper


def atimed(
    func: Callable[..., Coroutine[Any, Any, Any]],
) -> Callable[..., Coroutine[Any, Any, TimedOutput]]:
    """Wraps an async function to return its duration and result."""

    @wraps(func)
    async def wrapper(*args, **kwargs) -> TimedOutput:
        start_time = time.perf_counter()
        output = await func(*args, **kwargs)
        seconds_elapsed = time.perf_counter() - start_time
        return TimedOutput(
            duration=timedelta(seconds=seconds_elapsed),
            output=output,
        )

    return wrapper


T = TypeVar("T")


def descendant_classes(cls: type[T]) -> dict[str, type[T]]:
    """Recursively finds all subclasses at any depth.

    Args:
        cls: The base class to find subclasses of.

    Returns:
        A dict mapping subclass names (as strings) to subclass types.

    Examples:
        >>> class Base: pass
        >>> class Sub1(Base): pass
        >>> class Sub2(Base): pass
        >>> class SubSub(Sub1): pass
        >>> mapping = subclass_name_map(Base)
        >>> mapping["Sub1"] == Sub1
        True
        >>> mapping["Sub2"] == Sub2
        True
        >>> mapping["SubSub"] == SubSub
        True
    """
    subclasses: set[type[T]] = set()
    stack: list[type[T]] = [cls]

    while stack:
        current_cls = stack.pop()
        for sub in current_cls.__subclasses__():
            if sub not in subclasses:
                subclasses.add(sub)
                stack.append(sub)

    return {subcls.__name__: subcls for subcls in subclasses}
