"""Unit tests for core/date/src/zodiac.py."""

import unittest

from core.date.src.zodiac import zodiac


class ZodiacTest(unittest.TestCase):
    def test_boundaries(self):
        self.assertEqual(zodiac("0119"), "Capricorn")
        self.assertEqual(zodiac("0120"), "Aquarius")
        self.assertEqual(zodiac("1222"), "Capricorn")

    def test_mid_sign(self):
        self.assertEqual(zodiac("0920"), "Virgo")
        self.assertEqual(zodiac("0906"), "Virgo")


if __name__ == "__main__":
    unittest.main()
