Implement `allocate(amount_cents, ratios)` and `split_evenly(amount_cents, n)` in `money.py`. These split money in a payments system, so the results must be exact. Use only the Python standard library.

`allocate`:
- `amount_cents` must be an `int` (not `bool`, `float` or `str`), otherwise raise `TypeError`.
- `ratios` is a non-empty list of non-negative ints or floats with a positive sum, otherwise raise `ValueError`.
- Return a list of ints, one per ratio, that sums exactly to `amount_cents`.
- Algorithm (largest remainder): compute each exact share `amount * ratio / sum(ratios)` using exact arithmetic (no float rounding; it must stay exact for amounts like `10**18`). Treat float ratios by their decimal value, so `0.1` means exactly 1/10. Take the floor of each share. Hand out the remaining cents one at a time to the shares with the largest fractional remainder, breaking ties by the lower index.
- Negative amounts: allocate the absolute value, then negate every share, so `allocate(-100, [1, 1, 1]) == [-34, -33, -33]`.

`split_evenly(amount_cents, n)` is `allocate` with `n` equal ratios. `n < 1` raises `ValueError`.

Examples: `allocate(100, [1, 1, 1]) == [34, 33, 33]`, `allocate(5, [3, 7]) == [2, 3]`, `allocate(1000, [0.1, 0.2, 0.7]) == [100, 200, 700]`.

Hidden tests will be run with `python -m pytest` from this directory.
