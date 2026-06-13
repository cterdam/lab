"""Unit tests for check/src/rule/fmt_md.py."""

import tempfile
import unittest
from pathlib import Path

from check.src.rule import fmt_md


def _write(text: str) -> Path:
    p = Path(tempfile.mkdtemp()) / "x.md"
    p.write_text(text, encoding="utf-8")
    return p


class FmtMdTest(unittest.TestCase):
    def test_formatted_ok(self):
        fmt_md.rule(_write("# Title\n"))

    def test_unformatted_raises(self):
        with self.assertRaises(AssertionError):
            fmt_md.rule(_write("* a\n"))  # mdformat normalizes bullets to "-"


if __name__ == "__main__":
    unittest.main()
