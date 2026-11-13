Implement `diff(a, b)` and `apply(a, ops)` in `linediff.py`. Do not use `difflib`. Use only the Python standard library.

- `diff(a, b)` takes two lists of strings and returns an edit script: a list of `("=", line)`, `("-", line)` and `("+", line)` tuples. Taking the `=`/`-` lines in order must reproduce `a`, and taking the `=`/`+` lines in order must reproduce `b`.
- The script must be minimal: the number of `-` and `+` operations must equal `len(a) + len(b) - 2 * LCS(a, b)`.
- Within every run of consecutive non-`=` operations, all `-` operations come before all `+` operations. For example `diff(["a","b","c"], ["a","x","c"]) == [("=","a"), ("-","b"), ("+","x"), ("=","c")]`.
- Performance: two 6,000-line files that differ in about a dozen scattered lines must diff in well under 3 seconds. A full O(len(a) × len(b)) table is too slow; use an algorithm whose cost scales with the size of the difference, such as Myers' O(ND).
- `apply(a, ops)` replays a script against `a` and returns the resulting list. Raise `ValueError` if a `=` or `-` line does not match `a` at that position, if the ops do not consume all of `a`, or if an op code is unknown.

Hidden tests will be run with `python -m pytest` from this directory.
