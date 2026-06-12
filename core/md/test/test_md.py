"""Unit tests for core/md/src/md.py."""

import unittest

from core.md.src import md


class FrontmatterTest(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(
            md.parse_frontmatter("---\na: 1\nb: x\n---\nbody"),
            {"a": 1, "b": "x"},
        )

    def test_missing(self):
        self.assertIsNone(md.parse_frontmatter("no frontmatter here"))

    def test_unterminated(self):
        self.assertIsNone(md.parse_frontmatter("---\na: 1\n"))


if __name__ == "__main__":
    unittest.main()
