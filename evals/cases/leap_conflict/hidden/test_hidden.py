import unittest

from leap import is_leap


class HiddenLeap(unittest.TestCase):
    def test_gregorian(self):
        for year, expected in [(1996, True), (1999, False), (1900, False), (2100, False),
                               (2000, True), (2400, True), (2024, True)]:
            self.assertEqual(is_leap(year), expected, year)
