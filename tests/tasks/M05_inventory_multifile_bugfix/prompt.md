The `inventory` package (`inventory/models.py`, `inventory/service.py`) has several production bugs. Fix all of them and keep the public API unchanged.

1. A reservation can exceed what is actually available when other reservations already exist. `reserve` must check available stock (on hand minus reserved), not on-hand stock.
2. Releasing the same reservation twice increases availability twice. A reservation can be released or fulfilled only once. Releasing or fulfilling an unknown or already-used reservation id raises `KeyError`.
3. Fulfilling a reservation reduces on-hand stock but leaves the quantity counted as reserved, so availability drops twice.
4. Reusing an existing reservation id silently overwrites the old reservation. It must raise `ValueError` and change nothing. Reservation ids are unique across all SKUs.
5. `add_stock` and `reserve` accept zero or negative quantities. Both must raise `ValueError` for `qty <= 0`.
6. Calling `reserve` or `available` for an unknown SKU raises a plain `KeyError`. It must raise `UnknownSku` (already defined as a `KeyError` subclass).

Any call that raises must leave the inventory state unchanged. Hidden tests will be run with `python -m pytest` from this directory.
