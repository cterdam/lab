"""Unit tests for core/zh/src/zh.py."""

import unittest

from core.zh.src import zh


class FindSimplifiedTest(unittest.TestCase):
    def test_clean(self):
        self.assertEqual(zh.find_simplified("繁體字"), [])

    def test_detect(self):
        self.assertTrue(zh.find_simplified("简体"))

    def test_accepted_variant_tai(self):
        self.assertEqual(zh.find_simplified("月台"), [])


if __name__ == "__main__":
    unittest.main()
