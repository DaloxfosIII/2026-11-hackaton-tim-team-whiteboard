import pytest

from listops import chunk, flatten


def test_trailing_partial_chunk_kept():
    assert chunk([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]


def test_exact_multiple():
    assert chunk([1, 2, 3, 4], 2) == [[1, 2], [3, 4]]


def test_shorter_than_size():
    assert chunk([1, 2], 5) == [[1, 2]]


def test_empty():
    assert chunk([], 3) == []


def test_range_and_generator():
    assert chunk(range(5), 3) == [[0, 1, 2], [3, 4]]
    assert chunk((x * x for x in range(4)), 3) == [[0, 1, 4], [9]]


@pytest.mark.parametrize("size", [0, -1])
def test_invalid_size(size):
    with pytest.raises(ValueError):
        chunk([1, 2, 3], size)


def test_roundtrip_with_flatten():
    data = list(range(17))
    assert flatten(chunk(data, 4)) == data
