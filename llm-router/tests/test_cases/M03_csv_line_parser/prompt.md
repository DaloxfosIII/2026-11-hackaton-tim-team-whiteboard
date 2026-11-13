Implement `parse_csv_line(line, delimiter=",", quotechar='"')` in `csvline.py`. It parses a single CSV record (the string may contain newlines inside quoted fields) into a list of strings. Do not use the `csv` module.

Rules:
- `delimiter` and `quotechar` must each be exactly one character and must differ, otherwise raise `ValueError`.
- Fields are separated by `delimiter`. An empty line is one empty field (`[""]`). A trailing delimiter means a trailing empty field.
- Unquoted fields are taken literally, including spaces and any `quotechar` that is not the first character of the field (`ab"c` stays `ab"c`).
- A field whose first character is `quotechar` is quoted. It runs until the next unpaired `quotechar`. Inside it, a doubled quotechar (`""`) is a literal quote, and delimiters and newlines are literal.
- After a closing quote, the next character must be the delimiter or the end of the line. Anything else, including a space, raises `ValueError`.
- An unterminated quoted field raises `ValueError`.

Examples: `'"a,b",c' -> ["a,b", "c"]`, `'"he said ""hi""",x' -> ['he said "hi"', "x"]`, `"a,,c" -> ["a", "", "c"]`.

Hidden tests will be run with `python -m pytest` from this directory.
