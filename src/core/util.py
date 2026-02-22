import random
import re
import string
import textwrap
import time
from datetime import timedelta
from enum import Enum, StrEnum
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Coroutine, NamedTuple, TypeAlias, TypeVar

import rich.pretty

# CONSTANTS ####################################################################

# Log ID
Lid: TypeAlias = str

# Serial ID
Sid: TypeAlias = int

# Group ID
Gid: TypeAlias = str

# Root path of the repo inside the Docker container.
REPO_ROOT: Path = Path("/lab")

# BOOKKEEPING ##################################################################


def obj_id(namespace: str, objname: str) -> str:
    """Given a namespace and a name, give the obj's complete ID."""
    from src import env

    return f"{namespace}{env.NAMESPACE_OBJ_SEPARATOR}{safestr(objname)}"


def obj_subkey(objid: str, subkey_suffix: str) -> str:
    """Given an obj's ID and a subkey suffix, return the subkey."""
    from src import env

    return f"{objid}{env.OBJ_SUBKEY_SEPARATOR}{safestr(subkey_suffix)}"


def obj_in_namespace(s: str, namespace: str) -> bool:
    """Check if a string is an obj's ID in the given namespace."""
    from src import env

    return s.startswith(f"{namespace}{env.NAMESPACE_OBJ_SEPARATOR}")


def obj_namespace(objid: str) -> str:
    """Extract the namespace from an obj ID."""
    from src import env

    return objid.split(env.NAMESPACE_OBJ_SEPARATOR, 1)[0]


def obj_name(objid: str) -> str:
    """Extract the obj name from an obj ID."""
    from src import env

    return objid.split(env.NAMESPACE_OBJ_SEPARATOR, 1)[1]


def logspace2dir(logspace: list[str]) -> Path:
    """Given the logspace, get the corresponding actual dir path."""
    from src import env

    return env.log_dir.joinpath(*logspace)


def nextSid() -> Sid:
    """Get the next serial ID from the environment."""
    from src import env

    return env.r.incr(env.SID_COUNTER_KEY)


def toGid(groupname: str) -> Gid:
    """Given a name, form the gid."""
    from src import env

    return obj_id(env.GID_NAMESPACE, groupname)


def isGid(objid: str) -> bool:
    """Given an obj's ID, determine whether it represents a group."""
    from src import env

    return obj_in_namespace(objid, env.GID_NAMESPACE)


# FORMATTING ###################################################################


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


def safestr(s: str) -> str:
    """
    Convert any str into a filesystem‑safe filename.

    Examples:
        >>> safestr("openai/gpt-4.1")
        'openai_gpt-4_1'
        >>> safestr("mistral‑ai/mixtral‑8x7b‑inst/💡")
        'mistral_ai_mixtral_8x7b_inst'
    """
    if not s:
        return s
    out = re.sub(r"[^A-Za-z0-9_-]+", "_", s)
    out = re.sub(r"_+", "_", out)
    out = out.strip("_")
    if not out:
        raise ValueError(f"Invalid input: {s}")
    return out


def randalnu(length: int = 4) -> str:
    """Return a randomized alphanumeric string of the given length.

    This is used to generate a random run name.
    """
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))


def str2int(s: str | None) -> int | None:
    """Convert a string to int.

    This is used to post-process a Redis HGET / HMGET result into int.
    """
    return int(s) if s is not None else None


# MERGED ENUM ##################################################################


class MergedEnum:
    """Descriptor that merges Enum parts across the MRO into one Enum.

    Each class in the hierarchy defines its own contributions in a "part"
    attribute (a nested Enum class). This descriptor merges all such parts
    from the MRO into a single Enum, accessible as a class or instance
    attribute.

    The merged Enum is cached per class and computed lazily on first access.

    Args:
        part_attr: The name of the class attribute holding each class's
            Enum contributions.
        enum_type: The Enum type used for the merged result. Defaults to Enum.

    Example:
        >>> from enum import StrEnum
        >>> class Base:
        ...     gona = MergedEnum("_gona", StrEnum)
        ...     class _gona(StrEnum):
        ...         A = "a"
        >>> class Child(Base):
        ...     class _gona(StrEnum):
        ...         B = "b"
        >>> list(Child.gona)
        [<gona.A: 'a'>, <gona.B: 'b'>]
    """

    def __init__(self, part_attr: str, enum_type: type[Enum] = Enum):
        self.part_attr = part_attr
        self.enum_type = enum_type
        self._cache: dict[type, Enum | None] = {}

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, obj, cls):
        if cls not in self._cache:
            members = {}
            for klass in reversed(cls.__mro__):
                part = klass.__dict__.get(self.part_attr)
                if isinstance(part, type) and issubclass(part, Enum):
                    for m in part:
                        if m.name in members:
                            raise ValueError(
                                f"Duplicate {self.part_attr} key {m.name!r}"
                                f" in {klass.__name__}"
                            )
                        if m.value in members.values():
                            raise ValueError(
                                f"Duplicate {self.part_attr} value {m.value!r}"
                                f" for key {m.name!r} in {klass.__name__}"
                            )
                        members[m.name] = m.value
            self._cache[cls] = self.enum_type(self.name, members) if members else None
        return self._cache[cls]


# CLASS HIERARCHY ##############################################################

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
