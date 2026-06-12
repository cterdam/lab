"""Unit tests for core/date/src/cn_md.py."""

import unittest

from core.date.src.cn_md import cn_md


class CnMdTest(unittest.TestCase):
    def test_from_gregorian(self):
        self.assertEqual(cn_md(1998, "0906"), "七月十六")
        self.assertEqual(cn_md(1999, "0920"), "八月十一")


if __name__ == "__main__":
    unittest.main()
