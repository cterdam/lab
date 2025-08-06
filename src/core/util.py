import random
import re
import string
import textwrap

import rich.pretty


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
        max_width=max_width or env.MAX_LINELEN,
        indent_size=indent or env.INDENT,
        expand_all=True,
    )
