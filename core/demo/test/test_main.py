"""Unit tests for core/demo/src/main.py."""

import unittest

from core.demo.src import main


class GreetTest(unittest.TestCase):
    def test_greet(self):
        self.assertEqual(main.greet("lab"), "Hello, lab!")


if __name__ == "__main__":
    unittest.main()
