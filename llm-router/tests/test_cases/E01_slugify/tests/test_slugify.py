import pytest

from text_utils import slugify


@pytest.mark.parametrize(
    "text, expected",
    [
        ("Hello, World!", "hello-world"),
        ("  Crème brûlée  ", "creme-brulee"),
        ("a---b__c", "a-b-c"),
        ("Ünïcödé 2026", "unicode-2026"),
        ("already-a-slug", "already-a-slug"),
        ("", ""),
        ("!!!", ""),
        ("--Leading and trailing--", "leading-and-trailing"),
    ],
)
def test_basic(text, expected):
    assert slugify(text) == expected


def test_max_length_cuts_at_word_boundary():
    assert slugify("the quick brown fox", 12) == "the-quick"


def test_max_length_exact_boundary():
    assert slugify("the quick brown fox", 15) == "the-quick-brown"


def test_max_length_longer_than_slug():
    assert slugify("short text", 50) == "short-text"


def test_max_length_single_long_word_is_hard_cut():
    assert slugify("supercalifragilistic", 5) == "super"


def test_never_ends_with_dash():
    for n in range(1, 25):
        out = slugify("one two three four five", n)
        assert len(out) <= n
        assert not out.endswith("-")
