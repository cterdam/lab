"""Markdown frontmatter/body parsing (needs PyYAML)."""

from functools import lru_cache
from pathlib import Path

import yaml


def parse_frontmatter(text: str) -> dict | None:
    """Extract YAML frontmatter from markdown text, or None if missing/bad."""
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    return yaml.safe_load(parts[1])


@lru_cache(maxsize=None)
def frontmatter(md_path: Path) -> dict:
    """The frontmatter mapping; raise AssertionError if missing or malformed."""
    fm = parse_frontmatter(Path(md_path).read_text(encoding="utf-8"))
    if not isinstance(fm, dict):
        raise AssertionError("missing or malformed YAML frontmatter mapping")
    return fm


@lru_cache(maxsize=None)
def body(md_path: Path) -> str:
    parts = Path(md_path).read_text(encoding="utf-8").split("---", 2)
    return parts[2].strip() if len(parts) >= 3 else ""


@lru_cache(maxsize=None)
def load_dir(dir_path: str) -> tuple[dict, ...]:
    """Frontmatter of every *.md directly under dir_path (cached, hashable)."""
    return tuple(frontmatter(p) for p in sorted(Path(dir_path).glob("*.md")))
