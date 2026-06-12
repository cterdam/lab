"""Simplified-Chinese detection (needs OpenCC).

Flags a character iff it is simplified AND not a valid Traditional character.
"Valid Traditional" is decided by the Big5 repertoire (the canonical Traditional
Chinese encoding): characters such as 干 (vs 幹), 采 (vs 採), 占 (vs 佔) are
genuine Traditional characters that OpenCC's s2t would rewrite, yet Big5 contains
them, so they never fire. A character is flagged only when it is outside Big5
*and* OpenCC maps it to a different (traditional) character — i.e. a real
simplified form such as 国 -> 國.

`_ALSO_TRADITIONAL` is an escape hatch for valid Traditional characters outside
the Big5 repertoire (rare); none are needed today.
"""

from opencc import OpenCC

_s2t = OpenCC("s2t")

# Valid Traditional characters outside Big5's repertoire (rare). Extend if a
# legitimate Traditional character is ever flagged.
_ALSO_TRADITIONAL: set[str] = set()


def _maybe_han(c: str) -> bool:
    """Fast pre-filter for characters OpenCC might convert (Han ideographs)."""
    o = ord(c)
    return (
        0x3400 <= o <= 0x9FFF  # CJK Unified Ideographs (+ Extension A)
        or 0xF900 <= o <= 0xFAFF  # CJK Compatibility Ideographs
        or 0x20000 <= o <= 0x2FA1F  # CJK Extension B-F + Compatibility Supplement
    )


def _is_traditional(c: str) -> bool:
    """A character Big5 can encode (or an explicit override) is Traditional."""
    if c in _ALSO_TRADITIONAL:
        return True
    try:
        c.encode("big5")
        return True
    except UnicodeEncodeError:
        return False


def find_simplified(text: str) -> list[tuple[str, str]]:
    """Return (simplified, traditional) pairs: chars simplified and not traditional."""
    out, seen = [], set()
    for c in text:
        if c in seen or not _maybe_han(c):
            continue
        seen.add(c)
        if _is_traditional(c):
            continue
        trad = _s2t.convert(c)
        if trad != c:
            out.append((c, trad))
    return out
