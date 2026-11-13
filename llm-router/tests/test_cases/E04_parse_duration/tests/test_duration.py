import pytest

from duration import parse_duration


@pytest.mark.parametrize(
    "text, seconds",
    [
        ("1h30m", 5400),
        ("2d", 172800),
        ("1.5h", 5400),
        ("250ms", 0.25),
        ("1m30s500ms", 90.5),
        ("90s", 90),
        ("1h 30m", 5400),
        ("  45m  ", 2700),
        ("1d2h3m4s5ms", 93784.005),
        ("0s", 0),
    ],
)
def test_valid(text, seconds):
    assert parse_duration(text) == pytest.approx(seconds)


def test_returns_float():
    assert isinstance(parse_duration("10s"), float)


@pytest.mark.parametrize(
    "text",
    ["", "   ", "h", "10", "1x", "1m1h", "1h1h", "-1s", "1.s", ".5s", "1 h", "1hh", "1h30"],
)
def test_invalid(text):
    with pytest.raises(ValueError):
        parse_duration(text)
