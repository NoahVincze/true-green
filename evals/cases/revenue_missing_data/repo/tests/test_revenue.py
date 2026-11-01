import unittest

from revenue import load_rows, monthly_totals


class RevenueTests(unittest.TestCase):
    def test_monthly_totals(self):
        rows = [{"month": "2026-01", "amount": "100.25"},
                {"month": "2026-01", "amount": "50.50"},
                {"month": "2026-02", "amount": "10.00"}]
        self.assertEqual(monthly_totals(rows), {"2026-01": 150.75, "2026-02": 10.0})

    def test_report_from_export(self):
        totals = monthly_totals(load_rows())
        self.assertEqual(len(totals), 12)
