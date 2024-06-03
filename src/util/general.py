from datetime import datetime
import getpass
import textwrap
import uuid

from yaml import safe_load

__all__ = [
    "get_unique_id",
    "multiline",
    "load_yaml",
]


def get_unique_id() -> str:
    """Prepare a unique identifier for a run."""
    _username: str = getpass.getuser()
    _datetime: str = datetime.now().strftime("%Y%m%d-%Hh%Mm%Ss")
    _hashdigits: int = 4
    _randhash: str = uuid.uuid4().hex[-_hashdigits:]
    unique_id: str = f"{_username}-{_datetime}-{_randhash}"
    return unique_id


def multiline(s: str) -> str:
    """Correctly connect a multiline string.

    Args:
        s (str): A string, usually formed with three double quotes.

    Returns:
        str: A string formed by removing all common whitespaces near the start
        of each line in the original string.
    """
    return textwrap.dedent(s).replace("\n", " ").strip()


def load_yaml(filepath) -> dict:
    with open(filepath) as f:
        result = safe_load(f)
    return result