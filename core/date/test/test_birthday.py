"""Unit tests for core/date/src/birthday.py."""

import unittest

from core.date.src import birthday


class BirthdayTest(unittest.TestCase):
    def test_chinese_new_year_anchor(self):
        # CNY 1999 fell on 1999-02-16.
        self.assertEqual(birthday.infer(1999, chinese="正月初一")["gregorian"], "0216")

    def test_infer_from_chinese(self):
        got = birthday.infer(1999, chinese="八月十一")
        self.assertEqual(got["gregorian"], "0920")
        self.assertEqual(got["zodiac"], "Virgo")
        self.assertEqual(got["cn_zodiac"], "兔")

    def test_infer_from_gregorian(self):
        got = birthday.infer(1998, gregorian="0906")
        self.assertEqual(got["chinese"], "七月十六")
        self.assertEqual(got["cn_zodiac"], "虎")

    def test_late_lunar_month_falls_in_next_solar_year(self):
        # Lunar 1999-12-20 lands in solar 2000; birth_year 2000 must resolve
        # to lunar year 1999 (a 兔 year, not 龍).
        got = birthday.infer(2000, chinese="十二月二十")
        self.assertEqual(got["gregorian"], "0126")
        self.assertEqual(got["cn_zodiac"], "兔")

    def test_parse_format_roundtrip(self):
        for s in ("正月初一", "六月十三", "閏十二月初一", "七月十六", "二十", "廿九"):
            if "月" not in s:
                continue
            self.assertEqual(birthday.format_chinese(*birthday.parse_chinese(s)), s)

    def test_zodiac_boundaries(self):
        self.assertEqual(birthday.zodiac("0119"), "Capricorn")
        self.assertEqual(birthday.zodiac("0120"), "Aquarius")
        self.assertEqual(birthday.zodiac("1222"), "Capricorn")


if __name__ == "__main__":
    unittest.main()
