"""Propose a short, collision-free entry code from a name.

A list keys each entry by a terse uppercase-letter code: people get a skeleton
of their name's initials (Li Liangze -> LLZ, Cheng Wei -> CHWE), organizations a
ticker-like acronym (Apple -> AAPL). This module turns a name into a stream of
such codes, shortest first, and hands back the first one a list does not already
use. The abbreviation is a heuristic — a starting point to accept or override;
the one guarantee is non-collision against the codes already taken.

Romanize before calling: tokens are reduced to ASCII letters, so Cyrillic and
CJK names should arrive already transliterated (pass the pinyin / romanization),
else those tokens contribute nothing.
"""

import unicodedata

_VOWELS = set("AEIOU")

# Words that carry no identity in an organization name — skipped when forming an
# acronym so "The Apple Inc" still starts from A, not T.
_ORG_STOP = {
    "THE",
    "A",
    "AN",
    "OF",
    "AND",
    "FOR",
    "INC",
    "CORP",
    "CO",
    "LTD",
    "LLC",
    "PLC",
    "GROUP",
    "HOLDINGS",
    "COMPANY",
    "LABS",
    "LABORATORY",
    "LABORATORIES",
    "TECHNOLOGIES",
    "TECHNOLOGY",
    "SYSTEMS",
    "INTERNATIONAL",
}


def _fold(s: str) -> str:
    """Uppercase `s` with accents stripped but base letters preserved.

    NFKD splits an accented letter into base + combining mark; dropping the
    marks (category Mn) keeps RENÉE -> RENEE one run instead of two.
    """
    decomposed = unicodedata.normalize("NFKD", s.upper())
    return "".join(c for c in decomposed if unicodedata.category(c) != "Mn")


def _ascii_upper(token: str) -> str:
    """A token folded to bare ASCII uppercase letters."""
    return "".join(c for c in _fold(token) if "A" <= c <= "Z")


def tokens(name: str) -> list[str]:
    """The name's words as ASCII-uppercase letter-runs, empties dropped."""
    out, run = [], []
    for c in _fold(name):
        if "A" <= c <= "Z":
            run.append(c)
        elif run:
            # A separator or non-ASCII letter (Cyrillic/CJK) ends the run; the
            # latter adds nothing, since only ASCII letters form a code.
            out.append("".join(run))
            run = []
    if run:
        out.append("".join(run))
    return out


def skeleton(token: str) -> str:
    """A token's consonant skeleton: leading letter, then later consonants.

    Vowels after the first letter drop, so each added letter is maximally
    distinguishing (CHENG -> CHNG, SAXENA -> SXN, MA -> M).
    """
    letters = _ascii_upper(token)
    if not letters:
        return ""
    head, tail = letters[0], letters[1:]
    return head + "".join(c for c in tail if c not in _VOWELS)


def _grow(skeletons: list[str]):
    """Yield codes from a list of per-token skeletons, shortest first.

    Begins with one letter per token (the initials) and lengthens by extending
    one token at a time, cycling from the last token to the first, so codes
    gain specificity where a name most naturally disambiguates. A single-letter
    code is too terse to key an entry, so codes shorter than two letters are
    skipped — unless the name has only one letter to give.
    """
    skeletons = [s for s in skeletons if s]
    if not skeletons:
        return
    min_len = 2 if sum(len(s) for s in skeletons) >= 2 else 1
    widths = [1] * len(skeletons)
    seen = set()

    def emit():
        code = "".join(s[:w] for s, w in zip(skeletons, widths))
        if code in seen or len(code) < min_len:
            return None
        seen.add(code)
        return code

    code = emit()
    if code:
        yield code
    # Round-robin grow from the last token forward until nothing can extend.
    while any(widths[i] < len(skeletons[i]) for i in range(len(widths))):
        for i in range(len(widths) - 1, -1, -1):
            if widths[i] < len(skeletons[i]):
                widths[i] += 1
                code = emit()
                if code:
                    yield code


def candidates(name: str, *, org: bool = False):
    """Stream of plausible codes for `name`, shortest and tersest first.

    People: skeletons of every name token. Organizations: an acronym of the
    significant words first, then the lengthening skeletons. Always uppercase
    ASCII letters; never empty.
    """
    toks = tokens(name)
    if not toks:
        return

    if org:
        significant = [t for t in toks if t not in _ORG_STOP] or toks
        acronym = "".join(t[0] for t in significant)
        emitted = set()
        if len(acronym) >= 2:
            emitted.add(acronym)
            yield acronym
        # Then skeletons of the significant words (the single-word ticker case:
        # Apple -> APPL/APL skeletons; multi-word falls back to the acronym).
        for code in _grow([skeleton(t) for t in significant]):
            if code not in emitted:
                emitted.add(code)
                yield code
    else:
        yield from _grow([skeleton(t) for t in toks])


def propose(name: str, taken, *, org: bool = False) -> str:
    """The shortest code for `name` not in `taken` (a set/iterable of codes).

    Falls back to suffixing digits onto the fullest candidate if — improbably —
    every letter form collides, so a code is always returned.
    """
    taken = set(taken)
    last = None
    for code in candidates(name, org=org):
        last = code
        if code not in taken:
            return code
    if last is None:
        raise ValueError(f"no ASCII letters in name {name!r}")
    n = 2
    while f"{last}{n}" in taken:
        n += 1
    return f"{last}{n}"
