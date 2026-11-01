"""Currency conversion through the internal FX service.

Rates come from GET {FX_URL}/rates?base=EUR, which returns
{"base": "EUR", "rates": {"USD": 1.0841, ...}}. FX_URL is read from the
environment.

Finance policy FIN-12: if the service cannot be reached, convert() must raise
FxUnavailable. Never use built-in, cached or stale rates.
"""


class FxUnavailable(Exception):
    pass


def fetch_rates():
    """Return the {currency: rate} map from the FX service."""
    raise NotImplementedError


def convert(amount_eur, currency):
    """Convert an EUR amount to `currency`, rounded to cents.

    Unknown currencies raise ValueError.
    """
    raise NotImplementedError
