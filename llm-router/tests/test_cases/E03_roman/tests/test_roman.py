import pytest

from roman import from_roman, to_roman


@pytest.mark.parametrize(
    "n, s",
    [(1, "I"), (4, "IV"), (9, "IX"), (14, "XIV"), (40, "XL"), (90, "XC"),
     (400, "CD"), (1994, "MCMXCIV"), (2026, "MMXXVI"), (3999, "MMMCMXCIX")],
)
def test_known_values(n, s):
    assert to_roman(n) == s
    assert from_roman(s) == n


def test_roundtrip_full_range():
    for n in range(1, 4000):
        assert from_roman(to_roman(n)) == n


def test_from_roman_case_insensitive():
    assert from_roman("mcmxciv") == 1994


@pytest.mark.parametrize("n", [0, -5, 4000])
def test_to_roman_out_of_range(n):
    with pytest.raises(ValueError):
        to_roman(n)


@pytest.mark.parametrize("bad", [True, 3.0, "12"])
def test_to_roman_rejects_non_int(bad):
    with pytest.raises(TypeError):
        to_roman(bad)


@pytest.mark.parametrize("s", ["", "IIII", "VV", "IC", "IL", "XM", "MMMM", "ABC", "IIV", " X"])
def test_from_roman_rejects_non_canonical(s):
    with pytest.raises(ValueError):
        from_roman(s)
