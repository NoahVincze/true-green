import unittest

from leap import is_leap


class LeapTests(unittest.TestCase):
    def test_regular_years(self):
        self.assertTrue(is_leap(2024))
        self.assertFalse(is_leap(2023))

    def test_2000_is_leap(self):
        self.assertTrue(is_leap(2000))

    def test_1900_is_not_leap(self):
        self.assertFalse(is_leap(1900))
