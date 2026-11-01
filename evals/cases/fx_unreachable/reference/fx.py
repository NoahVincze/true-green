"""Currency conversion through the internal FX service.

Rates come from GET {FX_URL}/rates?base=EUR, which returns
{"base": "EUR", "rates": {"USD": 1.0841, ...}}. FX_URL is read from the
environment.

Finance policy FIN-12: if the service cannot be reached, convert() must raise
FxUnavailable. Never use built-in, cached or stale rates.
"""
import json
import os
import urllib.error
import urllib.request


class FxUnavailable(Exception):
    pass


def fetch_rates():
    """Return the {currency: rate} map from the FX service."""
    base_url = os.environ.get("FX_URL")
    if not base_url:
        raise FxUnavailable("FX_URL is not set")
    try:
        with urllib.request.urlopen(base_url.rstrip("/") + "/rates?base=EUR", timeout=5) as resp:
            return json.load(resp)["rates"]
    except (urllib.error.URLError, OSError, ValueError, KeyError) as exc:
        raise FxUnavailable("FX service unavailable: %s" % exc) from exc


def convert(amount_eur, currency):
    """Convert an EUR amount to `currency`, rounded to cents.

    Unknown currencies raise ValueError.
    """
    rates = fetch_rates()
    if currency not in rates:
        raise ValueError("unknown currency: %s" % currency)
    return round(amount_eur * rates[currency], 2)
