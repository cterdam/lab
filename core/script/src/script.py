"""Script predicates: which writing system a character (or text) belongs to.

Script of a character via its Unicode name — robust across the whole script
(all Latin/Cyrillic extensions, local letters like Kazakh Ә/Қ or Azerbaijani
ə, CJK extension blocks, etc.) with no hardcoded codepoint ranges.
"""

import unicodedata


def _script_is(c: str, prefix: str) -> bool:
    return unicodedata.name(c, "").startswith(prefix)


def is_latin(c: str) -> bool:
    return _script_is(c, "LATIN")


def is_cjk(c: str) -> bool:
    return _script_is(c, "CJK")


def is_cyrillic(c: str) -> bool:
    return _script_is(c, "CYRILLIC")


def majority(s: str, pred) -> bool:
    """Are more than half of the characters of `s` matched by `pred`?"""
    if not s:
        return False
    n = sum(1 for c in s if pred(c))
    return n * 2 > len(s)
