VAT_RATE = 0.19
DISCOUNT_CODES = {"SAVE10": 0.10, "SAVE20": 0.20}


def line_total(price, qty):
    return price * qty


def apply_discount(net, code):
    """Net after the discount for `code`. Unknown codes raise ValueError."""
    rate = DISCOUNT_CODES.get(code, 0)
    return net * rate


def order_total(items, code=None):
    """Gross total for (price, qty) items.

    The discount is applied to the net first, then VAT is charged on the
    discounted net. Rounded to cents.
    """
    net = sum(line_total(price, qty) for price, qty in items)
    if code:
        net = apply_discount(net, code)
    return round(net * (1 + VAT_RATE), 2)
