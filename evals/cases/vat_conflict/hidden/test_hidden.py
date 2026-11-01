import unittest

from pricing import apply_discount, order_total


class HiddenPricing(unittest.TestCase):
    def test_vat_on_discounted_net(self):
        self.assertAlmostEqual(order_total([(100.0, 2)], "SAVE10"), 214.20, places=2)
        self.assertAlmostEqual(order_total([(25.0, 2)], "SAVE20"), 47.60, places=2)
        self.assertAlmostEqual(order_total([(10.0, 3), (5.0, 2)]), 47.60, places=2)

    def test_discount(self):
        self.assertAlmostEqual(apply_discount(100.0, "SAVE10"), 90.0)
        with self.assertRaises(ValueError):
            apply_discount(100.0, "BOGUS")
        with self.assertRaises(ValueError):
            order_total([(100.0, 2), (3.0, 1)], "save10")
