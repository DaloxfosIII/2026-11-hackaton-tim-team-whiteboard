Implement `parse_duration(text)` in `duration.py`. It returns the total number of seconds as a `float`. Use only the Python standard library.

Format:
- A sequence of one or more components. Each component is a number immediately followed by a unit. Units are `d` (86400 s), `h` (3600 s), `m` (60 s), `s` (1 s) and `ms` (0.001 s).
- A number is digits with an optional fractional part: `1`, `1.5`. `.5` and `1.` are invalid. Negative numbers are invalid.
- Components must appear in strictly descending unit order (`d`, `h`, `m`, `s`, `ms`), and each unit may appear at most once: `1m1h` and `1h1h` are invalid.
- Whitespace is allowed between components and at either end, but not between a number and its unit (`1 h` is invalid).
- Any other input, including an empty string, a bare number or an unknown unit, raises `ValueError`.

Examples: `"1h30m" -> 5400.0`, `"250ms" -> 0.25`, `"1m30s500ms" -> 90.5`, `"1h 30m" -> 5400.0`.

Hidden tests will be run with `python -m pytest` from this directory.
