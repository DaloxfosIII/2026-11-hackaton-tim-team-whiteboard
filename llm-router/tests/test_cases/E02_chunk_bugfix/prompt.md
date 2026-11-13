Bug report for `chunk()` in `listops.py`:

- `chunk([1, 2, 3, 4, 5], 2)` returns `[[1, 2], [3, 4]]`. The trailing `[5]` is missing. The last chunk may be shorter than `size` and must be kept.
- `chunk([1, 2], 5)` returns `[]` instead of `[[1, 2]]`.
- It crashes on generators. It must accept any iterable (lists, ranges, tuples, generators) and always return a list of lists.
- `size` below 1 must raise `ValueError`.

Fix `chunk`. Do not change `flatten`. Hidden tests will be run with `python -m pytest` from this directory.
