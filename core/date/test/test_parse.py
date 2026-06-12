"""Unit tests for core/date/src/parse.py."""

import datetime
import unittest

from core.date.src.parse import parse_date


class ParseDateTest(unittest.TestCase):
    def test_compact(self):
        self.assertEqual(parse_date("20200131"), datetime.date(2020, 1, 31))

    def test_dashed(self):
        self.assertEqual(parse_date("2020-01-31"), datetime.date(2020, 1, 31))

    def test_invalid(self):
        self.assertIsNone(parse_date("nope"))
        self.assertIsNone(parse_date("2020131"))


if __name__ == "__main__":
    unittest.main()
