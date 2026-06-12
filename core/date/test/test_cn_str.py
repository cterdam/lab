"""Unit tests for core/date/src/cn_str.py."""

import unittest

from core.date.src.cn_str import format_cn_md, parse_cn_md


class CnStrTest(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(parse_cn_md("六月十三"), (6, 13, False))
        self.assertEqual(parse_cn_md("閏十二月初一"), (12, 1, True))

    def test_roundtrip(self):
        for s in (
            "正月初一",
            "六月十三",
            "閏十二月初一",
            "七月十六",
            "八月廿九",
            "十月三十",
        ):
            self.assertEqual(format_cn_md(*parse_cn_md(s)), s)


if __name__ == "__main__":
    unittest.main()
