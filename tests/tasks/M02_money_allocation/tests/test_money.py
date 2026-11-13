import random

import pytest

from money import allocate, split_evenly


def test_three_way():
    assert allocate(100, [1, 1, 1]) == [34, 33, 33]


def test_negative_amount_mirrors_positive():
    assert allocate(-100, [1, 1, 1]) == [-34, -33, -33]


def test_tie_broken_by_lower_index():
    assert allocate(5, [3, 7]) == [2, 3]
    assert allocate(7, [1, 1, 1, 1]) == [2, 2, 2, 1]


def test_largest_remainder_wins():
    # exact shares: 3.3, 3.3, 3.4 -> floors 3,3,3, one cent left -> index 2
    assert allocate(10, [33, 33, 34]) == [3, 3, 4]


def test_float_ratios_exact():
    assert allocate(1000, [0.1, 0.2, 0.7]) == [100, 200, 700]


def test_zero_amount_and_zero_ratio():
    assert allocate(0, [1, 2]) == [0, 0]
    assert allocate(10, [0, 1]) == [0, 10]


def test_large_amount_no_float_error():
    assert allocate(10**15 + 1, [1, 1]) == [500000000000001, 500000000000000]
    assert allocate(10**18, [1, 2]) == [333333333333333333, 666666666666666667]


@pytest.mark.parametrize("ratios", [[], [0, 0], [-1, 2]])
def test_invalid_ratios(ratios):
    with pytest.raises(ValueError):
        allocate(10, ratios)


@pytest.mark.parametrize("amount", [10.5, "10", True])
def test_amount_must_be_int(amount):
    with pytest.raises(TypeError):
        allocate(amount, [1, 1])


def test_split_evenly():
    assert split_evenly(10, 3) == [4, 3, 3]
    assert split_evenly(-10, 3) == [-4, -3, -3]
    with pytest.raises(ValueError):
        split_evenly(10, 0)


def test_property_sum_and_bounds():
    rng = random.Random(42)
    for _ in range(500):
        amount = rng.randint(-10**6, 10**6)
        ratios = [rng.randint(0, 50) for _ in range(rng.randint(1, 8))]
        if sum(ratios) == 0:
            ratios[0] = 1
        out = allocate(amount, ratios)
        assert sum(out) == amount
        total = sum(ratios)
        for share, r in zip(out, ratios):
            exact = amount * r / total
            assert abs(share - exact) < 1
