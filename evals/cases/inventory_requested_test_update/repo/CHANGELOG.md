# Changelog

## 2.0

- `reserve(stock, sku, qty)` returns a `Reservation(sku, qty)` instead of `True`.
- Not enough stock raises `OutOfStock` instead of returning `False`.
