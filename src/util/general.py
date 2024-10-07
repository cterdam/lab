from datetime import datetime, timezone
import getpass
import textwrap
from types import NoneType, UnionType
from typing import Any, Literal, Type, Union, _UnionGenericAlias, get_args

import ulid
from yaml import safe_load


__all__ = [
    "get_unique_id",
    "multiline",
    "load_yaml_file",
    "load_yaml_var",
    "get_type_name",
    "denonify",
    "get_non_special_regex",
]


def get_unique_id() -> str:
    """Prepare a unique identifier for a run."""
    _username: str = getpass.getuser()[:4]
    _datetime: str = datetime.now(timezone.utc).strftime("%m%d-%H%M")
    _randhash: str = ulid.new().str[-4:]
    unique_id: str = f"{_username}-{_datetime}-{_randhash}"
    return unique_id


def multiline(s: str, is_url: bool = False) -> str:
    """Correctly connect a multiline string.

    Args:
        s (str): A string, usually formed with three double quotes.

    Returns:
        str: A string formed by removing all common whitespaces near the start of each
        line in the original string.
    """
    result = textwrap.dedent(s).replace("\n", " ").strip()
    if is_url:
        result = result.replace(" ", "")
    return result


def load_yaml_file(filepath) -> dict:
    with open(filepath) as f:
        result = safe_load(f)
    return result


def load_yaml_var(v: str) -> Any:
    """Given a string, interpret it as a variable using yaml's load logic."""
    return safe_load(f"key: {v}")["key"]


def get_type_name(t: Type | UnionType) -> str:
    """Given a type, infer the class name in str."""
    if hasattr(t, "__origin__") and t.__origin__ is Literal:
        # Literal type
        return "Literal[" + ", ".join(repr(arg) for arg in get_args(t)) + "]"
    if isinstance(t, UnionType) or isinstance(t, _UnionGenericAlias):
        # UnionType -> int | None
        # _UnionGenericAlias -> typing.Optional[int]
        return str(t)
    else:
        return t.__name__


def denonify(ut: UnionType) -> NoneType | Type | UnionType:
    """Given a union type, return the non-None base type(s) in it."""
    union_args = get_args(ut)
    non_none_types = [arg for arg in union_args if arg is not NoneType]
    match non_none_types:
        case []:
            return None
        case [t]:
            return t
        case _:
            return Union[tuple(non_none_types)]


def get_non_special_regex() -> str:
    """
    Returns a regex pattern that matches any string with at least 1 char which does not
    include any special chars.
    """
    pattern = r'^[^ `~!@#$%^&*()\[\]{}\\|;:\'",<.>/?]+$'
    return pattern
