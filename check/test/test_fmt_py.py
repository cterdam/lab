"""Unit tests for check/src/rule/fmt_py.py."""

import tempfile
import unittest
from pathlib import Path

from check.src.rule import fmt_py


def _write(text: str) -> Path:
    p = Path(tempfile.mkdtemp()) / "x.py"
    p.write_text(text, encoding="utf-8")
    return p


class FmtPyTest(unittest.TestCase):
    def test_formatted_ok(self):
        fmt_py.rule(_write("x = 1\n"))

    def test_unformatted_raises(self):
        with self.assertRaises(AssertionError):
            fmt_py.rule(_write("x=1\n"))


if __name__ == "__main__":
    unittest.main()
