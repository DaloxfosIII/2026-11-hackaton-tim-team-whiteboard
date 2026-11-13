Implement `slugify(text, max_length=None)` in `text_utils.py`. Use only the Python standard library.

Rules:
1. Normalize the text with Unicode NFKD and drop every character that is not ASCII (so `é` becomes `e`).
2. Lowercase it.
3. Replace each run of characters that are not `a-z` or `0-9` with a single `-`.
4. Strip leading and trailing `-`. An input with no letters or digits returns `""`.
5. If `max_length` is given and the slug is longer, shorten it to at most `max_length` characters without cutting a word: keep the longest prefix that ends at a word boundary. If the first word alone is longer than `max_length`, cut that word to exactly `max_length` characters. The result never ends with `-`.

Examples: `slugify("Hello, World!") == "hello-world"`, `slugify("the quick brown fox", 12) == "the-quick"`, `slugify("supercalifragilistic", 5) == "super"`.

Hidden tests will be run with `python -m pytest` from this directory.
