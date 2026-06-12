"""Unit tests for core/date/src/cn_zodiac.py."""

import unittest

from core.date.src.cn_zodiac import cn_zodiac


class CnZodiacTest(unittest.TestCase):
    def test_anchor_years(self):
        self.assertEqual(cn_zodiac(1999), "兔")
        self.assertEqual(cn_zodiac(1998), "虎")
        self.assertEqual(cn_zodiac(1980), "猴")
        self.assertEqual(cn_zodiac(2000), "龍")

    def test_cycle(self):
        self.assertEqual(cn_zodiac(1999), cn_zodiac(2011))


if __name__ == "__main__":
    unittest.main()
