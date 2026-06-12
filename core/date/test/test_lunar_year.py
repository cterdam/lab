"""Unit tests for core/date/src/lunar_year.py."""

import unittest

from core.date.src.lunar_year import lunar_year_cn, lunar_year_gr


class LunarYearTest(unittest.TestCase):
    def test_gr_same_year(self):
        self.assertEqual(lunar_year_gr(1998, "0906"), 1998)

    def test_gr_before_new_year(self):
        # 2000-01-26 is before CNY 2000: lunar year 1999 (a 兔 year, not 龍).
        self.assertEqual(lunar_year_gr(2000, "0126"), 1999)

    def test_cn_late_month(self):
        self.assertEqual(lunar_year_cn(2000, "十二月二十"), 1999)

    def test_cn_same_year(self):
        self.assertEqual(lunar_year_cn(1999, "八月十一"), 1999)


if __name__ == "__main__":
    unittest.main()
