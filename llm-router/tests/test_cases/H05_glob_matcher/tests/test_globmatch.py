import pathlib
import time

import pytest

from globmatch import match

CASES = [
    # literals, ? and *
    ("a.txt", "a.txt", True),
    ("a.txt", "b.txt", False),
    ("?.txt", "a.txt", True),
    ("?.txt", "ab.txt", False),
    ("?", "/", False),
    ("*.py", "main.py", True),
    ("*.py", ".py", True),
    ("*.py", "src/main.py", False),
    ("src/*", "src/a", True),
    ("src/*", "src/a/b", False),
    ("*", "", True),
    ("", "", True),
    ("", "a", False),
    # globstar
    ("**", "a/b/c", True),
    ("**/*.py", "main.py", True),
    ("**/*.py", "src/pkg/main.py", True),
    ("**/*.py", "src/pkg/main.pyc", False),
    ("src/**/test_*.py", "src/test_a.py", True),
    ("src/**/test_*.py", "src/x/y/test_a.py", True),
    ("src/**/test_*.py", "lib/test_a.py", False),
    ("src/**", "src/a", True),
    ("src/**", "src/a/b/c", True),
    ("src/**", "src", False),
    ("a/**/b", "a/b", True),
    ("a/**/b", "a/x/b", True),
    ("a/**/b", "a/x/y/b", True),
    ("a/**/b", "a/xb", False),
    ("a**b", "axxb", True),
    ("a**b", "ax/xb", False),
    # character classes
    ("[abc].txt", "b.txt", True),
    ("[abc].txt", "d.txt", False),
    ("file[0-9].log", "file7.log", True),
    ("file[0-9].log", "filex.log", False),
    ("[!a-c]x", "dx", True),
    ("[!a-c]x", "bx", False),
    ("[^a-c]x", "dx", True),
    ("[]]", "]", True),
    ("[!]]", "a", True),
    ("[!]]", "]", False),
    ("a[/]b", "a/b", False),
    ("[a-", "[a-", True),
    ("x[", "x[", True),
    # braces
    ("*.{py,txt}", "a.py", True),
    ("*.{py,txt}", "a.txt", True),
    ("*.{py,txt}", "a.md", False),
    ("{src,lib}/**/*.{js,ts}", "lib/x/y.ts", True),
    ("{src,lib}/**/*.{js,ts}", "test/y.ts", False),
    ("a{b,c{d,e}}f", "acef", True),
    ("a{b,c{d,e}}f", "abf", True),
    ("a{b,c{d,e}}f", "acf", False),
    ("a{,b}c", "ac", True),
    ("a{,b}c", "abc", True),
    ("{a*,b?}", "b1", True),
    ("{a*,b?}", "b12", False),
    ("a{b", "a{b", True),
    ("a}b", "a}b", True),
    # escapes
    (r"\*.txt", "*.txt", True),
    (r"\*.txt", "a.txt", False),
    (r"a\{b,c\}", "a{b,c}", True),
    (r"\[x]", "[x]", True),
    (r"a\\b", "a\\b", True),
]


@pytest.mark.parametrize("pattern, path, expected", CASES)
def test_match(pattern, path, expected):
    assert match(pattern, path) is expected


def test_no_catastrophic_backtracking():
    start = time.perf_counter()
    assert match("a*a*a*a*a*a*a*a*b", "a" * 60) is False
    assert match("**/a/**/a/**/a/**/b", "/".join(["a"] * 40)) is False
    assert match("*{a,aa}*{a,aa}*{a,aa}*b", "a" * 60) is False
    assert time.perf_counter() - start < 1.0


def test_banned_modules():
    src = (pathlib.Path(__file__).resolve().parent.parent / "globmatch.py").read_text()
    for banned in ("fnmatch", "import glob", "import re", "from re ", "PurePath"):
        assert banned not in src, banned
