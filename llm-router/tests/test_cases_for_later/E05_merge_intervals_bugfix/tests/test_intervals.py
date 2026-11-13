import copy

import pytest

from intervals import merge_intervals


def test_basic_overlap():
    assert merge_intervals([[1, 3], [2, 6], [8, 10]]) == [[1, 6], [8, 10]]


def test_touching_intervals_merge():
    assert merge_intervals([[1, 4], [4, 5]]) == [[1, 5]]


def test_unsorted_input():
    assert merge_intervals([[8, 10], [1, 3], [2, 6]]) == [[1, 6], [8, 10]]


def test_contained_interval():
    assert merge_intervals([[1, 10], [2, 3]]) == [[1, 10]]


def test_single_and_empty():
    assert merge_intervals([]) == []
    assert merge_intervals([[5, 5]]) == [[5, 5]]


def test_tuples_in_lists_out():
    assert merge_intervals([(1, 2), (3, 4)]) == [[1, 2], [3, 4]]


def test_input_not_mutated():
    data = [[1, 3], [2, 6]]
    before = copy.deepcopy(data)
    merge_intervals(data)
    assert data == before


def test_invalid_interval():
    with pytest.raises(ValueError):
        merge_intervals([[1, 2], [5, 3]])
