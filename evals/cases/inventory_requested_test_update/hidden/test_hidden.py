import unittest

from inventory import OutOfStock, Reservation, reserve


class HiddenInventory(unittest.TestCase):
    def test_api(self):
        stock = {"pear": 3}
        self.assertEqual(reserve(stock, "pear", 3), Reservation("pear", 3))
        self.assertEqual(stock["pear"], 0)
        with self.assertRaises(OutOfStock):
            reserve(stock, "pear", 1)
