import re
import textwrap
import typing


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


def multiline(s: str, oneline: bool = True, is_url: bool = False) -> str:
    """Correctly connect a multiline string.

    Args:
        s (str): A string, usually formed with three double quotes.
        oneline (bool): Whether to remove all line breaks in the result.
        is_url (bool): Whether to delete spaces formed at line connections.

    Returns:
        A string formed by removing all common whitespaces near the start of
        each line in the original string.
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

    Rules
    -----
    1. Keep only ASCII letters, digits, dash, and underscore.
       Everything else – including dots, slashes, spaces – becomes “_”.
    2. Collapse consecutive underscores.
    3. Strip leading / trailing underscores.

    Examples
    --------
    >>> to_safe_filename("openai/gpt-4.1")
    'openai_gpt-4_1'
    >>> to_safe_filename("mistral‑ai/mixtral‑8x7b‑inst/💡")
    'mistral_ai_mixtral_8x7b_inst'
    """

    # Replace any char that is not A‑Z, a‑z, 0‑9, -, _
    out = re.sub(r"[^A-Za-z0-9_-]+", "_", name)

    # Collapse runs of '_'
    out = re.sub(r"_+", "_", out)

    # Trim leading / trailing '_'
    out = out.strip("_")

    if not out:
        raise ValueError(f"Invalid name: {name}")

    return out
