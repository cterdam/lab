import getpass
import importlib.util
import pathlib
import textwrap
from datetime import datetime, timezone

import ulid


def get_project_root() -> pathlib.Path:
    """Return the root path of the project."""
    _module_spec = importlib.util.find_spec("src")
    if _module_spec is None or _module_spec.origin is None:
        raise ModuleNotFoundError("Could not locate src module.")
    _src_path: pathlib.Path = pathlib.Path(_module_spec.origin).parent
    _project_root: pathlib.Path = _src_path.parent
    return _project_root


def get_unique_id() -> str:
    """Prepare a unique identifier for a run."""
    _username: str = getpass.getuser()[:4]
    _datetime: str = datetime.now(timezone.utc).strftime("%y%m%d-%H%M%S")
    _randhash: str = ulid.new().str[-4:]
    _unique_id: str = f"{_username}-{_datetime}-{_randhash}"
    return _unique_id


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
