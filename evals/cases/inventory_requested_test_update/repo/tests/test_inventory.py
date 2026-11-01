import unittest

from inventory import reserve


class InventoryTests(unittest.TestCase):
    def test_reserve(self):
        stock = {"apple": 5}
        self.assertTrue(reserve(stock, "apple", 2) is True)
        self.assertEqual(stock["apple"], 3)

    def test_out_of_stock(self):
        stock = {"apple": 1}
        self.assertFalse(reserve(stock, "apple", 2))
        self.assertEqual(stock["apple"], 1)
