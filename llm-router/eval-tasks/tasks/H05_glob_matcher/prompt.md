Implement `match(pattern, path)` in `globmatch.py`. It returns `True` if the `/`-separated path matches the glob pattern. Do not use `fnmatch`, `glob`, `pathlib` matching or the `re` module.

Syntax:
- `?` matches exactly one character other than `/`.
- `*` matches any run of characters, including an empty one, that contains no `/`. Files starting with a dot get no special treatment.
- `**` forming a whole path segment is a globstar:
  - the whole pattern `**` matches any path;
  - `**/` at the start, or `/**/` in the middle, matches zero or more complete directories, so `a/**/b` matches `a/b`, `a/x/b` and `a/x/y/b`;
  - a trailing `/**` matches `/` followed by at least one more character, so `src/**` matches `src/a` and `src/a/b` but not `src`.
  `**` that does not form a whole segment (`a**b`) behaves like `*`.
- `[...]` is a character class with ranges (`[a-z]`), negated by a leading `!` or `^`. A `]` right after the opening `[` (or after `[!`) is a literal. A class never matches `/`. A `[` with no closing `]` is a literal `[`.
- `{x,y,...}` is alternation. Groups may nest (`a{b,c{d,e}}f`), alternatives may be empty (`a{,b}c`), and they may contain other wildcards. A `{` with no matching `}`, or a group with no top-level comma, is literal, and so is a stray `}`.
- `\` makes the next character literal (`\*`, `\{`, `\[`, `\\`).
- Matching must take polynomial time: patterns like `a*a*a*a*a*a*a*a*b` against 60 `a`s must return `False` quickly.

Hidden tests will be run with `python -m pytest` from this directory.
