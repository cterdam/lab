"""Unit tests for core/script/src/script.py."""

import unittest

from core.script.src import script


class PredicateTest(unittest.TestCase):
    def test_latin(self):
        self.assertTrue(script.is_latin("A"))
        self.assertFalse(script.is_latin("北"))

    def test_cjk(self):
        self.assertTrue(script.is_cjk("北"))
        self.assertFalse(script.is_cjk("A"))

    def test_cyrillic(self):
        self.assertTrue(script.is_cyrillic("Я"))
        self.assertFalse(script.is_cyrillic("A"))

    def test_extended_letters(self):
        self.assertTrue(script.is_cyrillic("Ә"))  # Kazakh
        self.assertTrue(script.is_latin("ə"))  # Azerbaijani


class MajorityTest(unittest.TestCase):
    def test_majority(self):
        self.assertTrue(script.majority("北京", script.is_cjk))
        self.assertFalse(script.majority("ab北", script.is_cjk))
        self.assertFalse(script.majority("", script.is_cjk))


if __name__ == "__main__":
    unittest.main()
