"""Rule: JSON formatting — canonical 4-space indent, keys preserved.

No third-party tool: the stdlib json serializer is the canonical form. Keys are
NOT sorted (the schema rule derives field order from key order) and non-ASCII is
kept verbatim (readable CJK).
"""

import json
from pathlib import Path


def canonical(text: str) -> str:
    return json.dumps(json.loads(text), indent=4, ensure_ascii=False) + "\n"


def rule(path: Path) -> None:
    text = Path(path).read_text(encoding="utf-8")
    try:
        want = canonical(text)
    except json.JSONDecodeError as e:
        raise AssertionError(f"invalid JSON: {e}")
    if text != want:
        raise AssertionError(f"json: not canonical (4-space indent). Reformat {path}.")
