Bug reports for `merge_intervals()` in `intervals.py`. Intervals are closed `[start, end]` pairs.

- Touching intervals are not merged: `[[1, 4], [4, 5]]` should give `[[1, 5]]`.
- Unsorted input gives wrong results: `[[8, 10], [1, 3], [2, 6]]` should give `[[1, 6], [8, 10]]`.
- A contained interval shrinks the outer one: `[[1, 10], [2, 3]]` should give `[[1, 10]]`.
- The input list and its inner lists must not be modified.
- Input items may be lists or tuples. Output is always a sorted list of 2-element lists.
- An interval with `start > end` must raise `ValueError`.

Fix the function. Hidden tests will be run with `python -m pytest` from this directory.
