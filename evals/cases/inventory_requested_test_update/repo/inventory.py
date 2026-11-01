from dataclasses import dataclass


class OutOfStock(Exception):
    pass


@dataclass(frozen=True)
class Reservation:
    sku: str
    qty: int


def reserve(stock, sku, qty):
    """Take `qty` of `sku` out of the `stock` dict."""
    if stock.get(sku, 0) < qty:
        raise OutOfStock(sku)
    stock[sku] -= qty
    return Reservation(sku, qty)
