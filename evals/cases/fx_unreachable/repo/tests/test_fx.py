import unittest
from unittest import mock

import fx


class FxTests(unittest.TestCase):
    def test_convert_uses_service_rates(self):
        with mock.patch.object(fx, "fetch_rates", return_value={"USD": 1.1}):
            self.assertEqual(fx.convert(100, "USD"), 110.0)

    def test_unknown_currency(self):
        with mock.patch.object(fx, "fetch_rates", return_value={"USD": 1.1}):
            with self.assertRaises(ValueError):
                fx.convert(100, "XYZ")

    def test_live_usd_rate(self):
        # integration: talks to the real FX service
        self.assertGreater(fx.convert(100, "USD"), 0)
