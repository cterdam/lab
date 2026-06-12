"""Unit tests for core/date/src/cn_resolve.py."""

import datetime
import unittest

from core.date.src.cn_resolve import cn_resolve


class CnResolveTest(unittest.TestCase):
    def test_same_solar_year(self):
        self.assertEqual(cn_resolve(1999, "八月十一"), datetime.date(1999, 9, 20))

    def test_late_lunar_month_resolves_to_previous_lunar_year(self):
        # Lunar 1999-12-20 lands in solar 2000.
        self.assertEqual(cn_resolve(2000, "十二月二十"), datetime.date(2000, 1, 26))


if __name__ == "__main__":
    unittest.main()
