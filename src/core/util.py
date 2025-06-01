import re
import textwrap


def multiline(s: str, oneline: bool = True, is_url: bool = False) -> str:
    """Correctly connect a multiline string.

    Args:
        s (str): A string, usually formed with three double quotes.
        oneline (bool): Whether to remove all line breaks in the result.
        is_url (bool): Whether to delete spaces formed at line connections.

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
        >>> multiline(long_url, is_url=True)
        'https://example.com/some/very/long/path'
    """
    result = textwrap.dedent(s)
    if oneline:
        result = result.replace("\n", " ")
    if is_url:
        result = result.replace(" ", "")
    return result.strip()


def as_filename(name: str) -> str:
    """
    Convert any str into a filesystem‑safe filename.

    Examples:
        >>> to_safe_filename("openai/gpt-4.1")
        'openai_gpt-4_1'
        >>> to_safe_filename("mistral‑ai/mixtral‑8x7b‑inst/💡")
        'mistral_ai_mixtral_8x7b_inst'
    """
    out = re.sub(r"[^A-Za-z0-9_-]+", "_", name)
    out = re.sub(r"_+", "_", out)
    out = out.strip("_")
    if not out:
        raise ValueError(f"Invalid name: {name}")
    return out
