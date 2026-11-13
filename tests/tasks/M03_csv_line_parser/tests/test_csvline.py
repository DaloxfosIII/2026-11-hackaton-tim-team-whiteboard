import pathlib

import pytest

from csvline import parse_csv_line


@pytest.mark.parametrize(
    "line, expected",
    [
        ("a,b,c", ["a", "b", "c"]),
        ("", [""]),
        ("a,,c", ["a", "", "c"]),
        ("a,b,", ["a", "b", ""]),
        (",", ["", ""]),
        (' a , b ', [" a ", " b "]),
        ('"a,b",c', ["a,b", "c"]),
        ('"he said ""hi""",x', ['he said "hi"', "x"]),
        ('""', [""]),
        ('"",""', ["", ""]),
        ('ab"c,d', ['ab"c', "d"]),
        ('"multi\nline",z', ["multi\nline", "z"]),
        ('x,"",y', ["x", "", "y"]),
    ],
)
def test_parse(line, expected):
    assert parse_csv_line(line) == expected


def test_custom_delimiter_and_quote():
    assert parse_csv_line("a;'b;c';d", delimiter=";", quotechar="'") == ["a", "b;c", "d"]
    assert parse_csv_line("a\t\"b\tc\"", delimiter="\t") == ["a", "b\tc"]


@pytest.mark.parametrize("line", ['"abc', 'a,"b', '"a"b,c', '"a" ,b', '"a""'])
def test_malformed(line):
    with pytest.raises(ValueError):
        parse_csv_line(line)


@pytest.mark.parametrize("kwargs", [{"delimiter": ""}, {"delimiter": ",,"}, {"delimiter": '"'},
                                    {"quotechar": ""}, {"quotechar": "ab"}])
def test_bad_config(kwargs):
    with pytest.raises(ValueError):
        parse_csv_line("a,b", **kwargs)


def test_csv_module_not_used():
    src = (pathlib.Path(__file__).resolve().parent.parent / "csvline.py").read_text()
    assert "import csv" not in src and "from csv" not in src
