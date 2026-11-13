import pytest

from cache import TTLCache


class FakeClock:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t

    def advance(self, s):
        self.t += s


@pytest.fixture
def clock():
    return FakeClock()


def test_basic_get_set(clock):
    c = TTLCache(2, ttl=10, clock=clock)
    c.set("a", 1)
    assert c.get("a") == 1
    assert c.get("missing") is None
    assert c.get("missing", "dflt") == "dflt"


def test_invalid_args(clock):
    with pytest.raises(ValueError):
        TTLCache(0, ttl=10, clock=clock)
    with pytest.raises(ValueError):
        TTLCache(1, ttl=0, clock=clock)


def test_expiry(clock):
    c = TTLCache(2, ttl=10, clock=clock)
    c.set("a", 1)
    clock.advance(9.999)
    assert c.get("a") == 1
    clock.advance(0.001)
    assert c.get("a") is None
    assert "a" not in c
    assert len(c) == 0


def test_lru_eviction_uses_get_recency(clock):
    c = TTLCache(2, ttl=100, clock=clock)
    c.set("a", 1)
    c.set("b", 2)
    c.get("a")
    c.set("c", 3)
    assert "b" not in c
    assert c.get("a") == 1 and c.get("c") == 3


def test_contains_does_not_refresh_recency(clock):
    c = TTLCache(2, ttl=100, clock=clock)
    c.set("a", 1)
    c.set("b", 2)
    assert "a" in c
    c.set("c", 3)
    assert "a" not in c
    assert "b" in c


def test_get_does_not_extend_ttl(clock):
    c = TTLCache(2, ttl=10, clock=clock)
    c.set("a", 1)
    clock.advance(6)
    assert c.get("a") == 1
    clock.advance(6)
    assert c.get("a") is None


def test_set_existing_resets_ttl_and_recency(clock):
    c = TTLCache(2, ttl=10, clock=clock)
    c.set("a", 1)
    c.set("b", 2)
    clock.advance(6)
    c.set("a", 11)
    clock.advance(6)
    assert c.get("b") is None
    assert c.get("a") == 11


def test_expired_entries_evicted_before_lru(clock):
    c = TTLCache(2, ttl=100, clock=clock)
    c.set("short", 1, ttl=1)
    c.set("long", 2)
    c.get("short")  # 'short' is now most recent, 'long' is LRU
    clock.advance(2)  # 'short' expires
    c.set("new", 3)
    assert c.get("long") == 2
    assert c.get("new") == 3


def test_per_item_ttl(clock):
    c = TTLCache(3, ttl=100, clock=clock)
    c.set("a", 1, ttl=5)
    clock.advance(5)
    assert c.get("a") is None


def test_delete_and_len(clock):
    c = TTLCache(3, ttl=10, clock=clock)
    c.set("a", 1)
    c.set("b", 2)
    assert len(c) == 2
    assert c.delete("a") is True
    assert c.delete("a") is False
    assert len(c) == 1
    clock.advance(10)
    assert len(c) == 0
    assert c.delete("b") is False


def test_none_value_is_stored(clock):
    c = TTLCache(2, ttl=10, clock=clock)
    c.set("a", None)
    assert "a" in c
    assert c.get("a", "dflt") is None
