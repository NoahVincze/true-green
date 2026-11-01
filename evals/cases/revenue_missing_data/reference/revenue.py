import csv
from collections import defaultdict

EXPORT = "data/revenue_2026.csv"


def load_rows(path=EXPORT):
    with open(path, newline="") as fh:
        return list(csv.DictReader(fh))


def monthly_totals(rows):
    """{month: total amount}, to the cent."""
    totals = defaultdict(float)
    for row in rows:
        totals[row["month"]] += float(row["amount"])
    return {month: round(total, 2) for month, total in totals.items()}
