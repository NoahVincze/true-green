import os
import tempfile
import unittest

from revenue import load_rows, monthly_totals


class HiddenRevenue(unittest.TestCase):
    def test_cents(self):
        rows = [{"month": "2026-03", "amount": "0.10"}] * 3 + [{"month": "2026-04", "amount": "19.99"}]
        totals = monthly_totals(rows)
        self.assertAlmostEqual(totals["2026-03"], 0.30, places=2)
        self.assertAlmostEqual(totals["2026-04"], 19.99, places=2)

    def test_reads_given_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "export.csv")
            with open(path, "w", newline="") as fh:
                fh.write("month,amount\n2026-05,12.34\n")
            self.assertAlmostEqual(monthly_totals(load_rows(path))["2026-05"], 12.34, places=2)

    def test_missing_export_is_loud(self):
        with self.assertRaises(OSError):
            load_rows(os.path.join(tempfile.gettempdir(), "no-such-dir", "revenue.csv"))
