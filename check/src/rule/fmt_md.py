"""Rule: Markdown formatting — mdformat (wrap 80, gfm + frontmatter plugins).

Uses the mdformat Python API so the aggregate driver formats every file in one
process. The extensions must be named explicitly: unlike the CLI, the API does
not auto-load installed plugins, and the frontmatter plugin is what keeps the
YAML block intact (otherwise `---` is parsed as a thematic break).
"""

from pathlib import Path

import mdformat

_EXTENSIONS = ("gfm", "frontmatter")


def rule(path: Path) -> None:
    src = Path(path).read_text(encoding="utf-8")
    if mdformat.text(src, options={"wrap": 80}, extensions=_EXTENSIONS) != src:
        raise AssertionError(
            f"mdformat: not formatted (run: mdformat --wrap 80 {path})"
        )
