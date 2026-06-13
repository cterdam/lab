"""Unit tests for check/src/rule/fmt_json.py."""

import tempfile
import unittest
from pathlib import Path

from check.src.rule import fmt_json


def _write(text: str) -> Path:
    p = Path(tempfile.mkdtemp()) / "x.json"
    p.write_text(text, encoding="utf-8")
    return p


class FmtJsonTest(unittest.TestCase):
    def test_canonical_ok(self):
        fmt_json.rule(_write('{\n    "a": 1\n}\n'))

    def test_noncanonical_raises(self):
        with self.assertRaises(AssertionError):
            fmt_json.rule(_write('{"a": 1}'))

    def test_invalid_raises(self):
        with self.assertRaises(AssertionError):
            fmt_json.rule(_write("{bad"))


if __name__ == "__main__":
    unittest.main()
