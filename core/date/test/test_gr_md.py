"""Unit tests for core/date/src/gr_md.py."""

import unittest

from core.date.src.gr_md import gr_md


class GrMdTest(unittest.TestCase):
    def test_chinese_new_year_anchor(self):
        # CNY 1999 fell on 1999-02-16.
        self.assertEqual(gr_md(1999, "正月初一"), "0216")

    def test_mid_year(self):
        self.assertEqual(gr_md(1999, "八月十一"), "0920")

    def test_late_lunar_month_falls_in_next_solar_year(self):
        self.assertEqual(gr_md(2000, "十二月二十"), "0126")


if __name__ == "__main__":
    unittest.main()
