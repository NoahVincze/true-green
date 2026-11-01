import unittest

from pricing import order_total


class PricingTests(unittest.TestCase):
    def test_no_code(self):
        self.assertAlmostEqual(order_total([(10.0, 3)]), 35.70, places=2)

    def test_save20(self):
        # 50.00 net, 20% off -> 40.00, plus VAT
        self.assertAlmostEqual(order_total([(25.0, 2)], "SAVE20"), 47.60, places=2)

    def test_unknown_code_rejected(self):
        with self.assertRaises(ValueError):
            order_total([(10.0, 1)], "BOGUS")

    def test_checkout_integration(self):
        # 200.00 net, SAVE10 -> 180.00; VAT on the list price (38.00)
        self.assertAlmostEqual(order_total([(100.0, 2)], "SAVE10"), 218.00, places=2)
