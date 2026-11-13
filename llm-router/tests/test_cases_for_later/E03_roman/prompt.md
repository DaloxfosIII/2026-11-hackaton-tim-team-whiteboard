Implement `to_roman(n)` and `from_roman(s)` in `roman.py`. Use only the Python standard library.

- `to_roman(n)` converts an integer from 1 to 3999 into a standard (canonical) Roman numeral, e.g. `1994 -> "MCMXCIV"`. Raise `TypeError` if `n` is not an `int` (a `bool` counts as not an int). Raise `ValueError` if it is out of range.
- `from_roman(s)` converts a numeral back to an integer. Accept upper- or lower-case. It must be strict: accept only the canonical form that `to_roman` would produce. Anything else raises `ValueError`, including `""`, `"IIII"`, `"VV"`, `"IC"`, `"MMMM"`, strings with other characters, and leading or trailing spaces.

Hidden tests will be run with `python -m pytest` from this directory.
