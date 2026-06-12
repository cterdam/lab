"""Rule: Python formatting — black + isort, via their Python APIs.

Calling the libraries in-process (rather than shelling out per file) means the
aggregate driver imports black/isort once and reuses them across every file.
"""

from pathlib import Path

import black
import isort

# The repo's top-level import roots. Declared explicitly so isort's first-party
# vs third-party grouping is deterministic — from a file's content alone (in a
# sandbox) it can't otherwise tell `core`/`util` are first-party.
_FIRST_PARTY = ("check", "core")


def rule(path: Path) -> None:
    src = Path(path).read_text(encoding="utf-8")
    errors = []
    try:
        if black.format_str(src, mode=black.Mode()) != src:
            errors.append(f"black: not formatted (run: black {path})")
    except black.InvalidInput as e:
        errors.append(f"black: invalid input: {e}")
    if not isort.check_code(
        src, show_diff=False, profile="black", known_first_party=_FIRST_PARTY
    ):
        errors.append(f"isort: imports unsorted (run: isort {path})")
    if errors:
        raise AssertionError("\n".join(errors))
