import getpass
import importlib.util
import pathlib
import textwrap
import typing
from datetime import datetime, timezone

import ulid


def get_type_name(t) -> str:
    """Given a type, infer the class name in str."""
    if typing.get_origin(t) is typing.Literal:
        # Literal type
        return "Literal[" + ", ".join(str(arg) for arg in typing.get_args(t)) + "]"
    elif hasattr(t, "__name__"):
        # Primitive type
        return t.__name__
    else:
        return str(t)


def get_project_root() -> pathlib.Path:
    """Return the root path of the project."""
    _module_spec = importlib.util.find_spec("src")
    if _module_spec is None or _module_spec.origin is None:
        raise ModuleNotFoundError("Could not locate src module.")
    _src_path = pathlib.Path(_module_spec.origin).parent
    _project_root = _src_path.parent
    return _project_root


def get_unique_id() -> str:
    """Prepare a unique identifier for a run."""
    _username: str = getpass.getuser()[:4]
    _datetime: str = datetime.now(timezone.utc).strftime("%y%m%d-%H%M%S")
    _randhash: str = ulid.new().str[-4:]
    _unique_id: str = f"{_username}-{_datetime}-{_randhash}"
    return _unique_id


def multiline(s: str, keep_newline: bool = False, is_url: bool = False) -> str:
    """Correctly connect a multiline string.

    Args:
        s (str): A string, usually formed with three double quotes.
        keep_newline (bool): Whether to keep newline characters in the string.
        is_url (bool): Whether to delete spaces formed at line connections.

    Returns:
        A string formed by removing all common whitespaces near the start of
        each line in the original string.
    """
    result = textwrap.dedent(s)
    if not keep_newline:
        result = result.replace("\n", " ")
    if is_url:
        result = result.replace(" ", "")
    return result.strip()
