import pathlib
import random
import time

import pytest

from linediff import apply, diff


def lcs_len(a, b):
    prev = [0] * (len(b) + 1)
    for x in a:
        cur = [0]
        for j, y in enumerate(b):
            cur.append(prev[j] + 1 if x == y else max(prev[j + 1], cur[j]))
        prev = cur
    return prev[-1]


def check(a, b, ops):
    assert [l for o, l in ops if o in "=-"] == a
    assert [l for o, l in ops if o in "=+"] == b
    edits = sum(1 for o, _ in ops if o != "=")
    assert edits == len(a) + len(b) - 2 * lcs_len(a, b), "edit script is not minimal"
    for (o1, _), (o2, _) in zip(ops, ops[1:]):
        assert not (o1 == "+" and o2 == "-"), "deletions must come before insertions in a hunk"
    assert apply(a, ops) == b


@pytest.mark.parametrize(
    "a, b",
    [
        ([], []),
        (["x"], []),
        ([], ["x"]),
        (["a", "b", "c"], ["a", "b", "c"]),
        (["a", "b", "c"], ["a", "c"]),
        (["a", "c"], ["a", "b", "c"]),
        (["a", "b", "c"], ["x", "y", "z"]),
        (list("ABCABBA"), list("CBABAC")),
        (["a", "b", "a", "b"], ["b", "a", "b", "a"]),
        (["", "", "x"], ["x", "", ""]),
    ],
)
def test_cases(a, b):
    check(a, b, diff(a, b))


def test_exact_ops_for_simple_change():
    assert diff(["a", "b", "c"], ["a", "x", "c"]) == [("=", "a"), ("-", "b"), ("+", "x"), ("=", "c")]


def test_random_small():
    rng = random.Random(99)
    for _ in range(300):
        a = [rng.choice("abcd") for _ in range(rng.randint(0, 12))]
        b = [rng.choice("abcd") for _ in range(rng.randint(0, 12))]
        check(a, b, diff(a, b))


def test_apply_rejects_mismatch():
    with pytest.raises(ValueError):
        apply(["a", "b"], [("=", "a"), ("-", "x")])
    with pytest.raises(ValueError):
        apply(["a", "b"], [("=", "a")])  # does not consume all of a
    with pytest.raises(ValueError):
        apply(["a"], [("?", "a")])


def test_large_input_with_scattered_changes_is_fast():
    n = 6000
    a = [f"line {i}" for i in range(n)]
    b = list(a)
    rng = random.Random(5)
    changed = sorted(rng.sample(range(n), 12))
    for k, i in enumerate(changed):
        b[i] = f"changed {k}"
    start = time.perf_counter()
    ops = diff(a, b)
    elapsed = time.perf_counter() - start
    assert elapsed < 3.0, f"too slow: {elapsed:.2f}s"
    assert apply(a, ops) == b
    assert sum(1 for o, _ in ops if o != "=") == 24


def test_no_difflib():
    src = (pathlib.Path(__file__).resolve().parent.parent / "linediff.py").read_text()
    assert "difflib" not in src
