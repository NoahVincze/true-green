import unittest

from inventory import OutOfStock, Reservation, reserve


class InventoryTests(unittest.TestCase):
    def test_reserve(self):
        stock = {"apple": 5}
        self.assertEqual(reserve(stock, "apple", 2), Reservation("apple", 2))
        self.assertEqual(stock["apple"], 3)

    def test_out_of_stock(self):
        stock = {"apple": 1}
        with self.assertRaises(OutOfStock):
            reserve(stock, "apple", 2)
        self.assertEqual(stock["apple"], 1)
