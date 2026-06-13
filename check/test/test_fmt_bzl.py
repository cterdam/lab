"""Unit tests for check/src/rule/fmt_bzl.py.

buildifier is a prebuilt binary passed in via runfiles; the test target
carries it in data, mirroring how the fmt driver receives it.
"""

import tempfile
import unittest
from pathlib import Path

from check.src.rule import fmt_bzl

_BUILDIFIER = "../buildifier_prebuilt~/buildifier/buildifier"


def _write(text: str) -> Path:
    p = Path(tempfile.mkdtemp()) / "BUILD.bazel"
    p.write_text(text, encoding="utf-8")
    return p


class FmtBzlTest(unittest.TestCase):
    def test_formatted_ok(self):
        fmt_bzl.rule(_write('filegroup(\n    name = "x",\n)\n'), buildifier=_BUILDIFIER)

    def test_unformatted_raises(self):
        with self.assertRaises(AssertionError):
            fmt_bzl.rule(_write('filegroup(name="x",)\n'), buildifier=_BUILDIFIER)


if __name__ == "__main__":
    unittest.main()
