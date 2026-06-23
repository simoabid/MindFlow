# tests/test_cache.py
from mindflow.cache import TTLCache


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def test_get_miss_returns_none_and_counts():
    cache = TTLCache(max_entries=4, ttl_seconds=10)
    assert cache.get("missing") is None
    assert cache.misses == 1
    assert cache.hits == 0


def test_set_and_get_hit():
    cache = TTLCache(max_entries=4, ttl_seconds=10)
    cache.set("k", ["a", "b"])
    assert cache.get("k") == ["a", "b"]
    assert cache.hits == 1


def test_lru_eviction():
    cache = TTLCache(max_entries=2, ttl_seconds=0)
    cache.set("a", ["1"])
    cache.set("b", ["2"])
    cache.get("a")  # touch 'a' so 'b' becomes least-recently-used
    cache.set("c", ["3"])
    assert cache.get("b") is None  # evicted
    assert cache.get("a") == ["1"]
    assert cache.get("c") == ["3"]


def test_ttl_expiry():
    clock = FakeClock()
    cache = TTLCache(max_entries=4, ttl_seconds=10, time_fn=clock)
    cache.set("k", ["v"])
    clock.now = 5
    assert cache.get("k") == ["v"]
    clock.now = 11
    assert cache.get("k") is None  # expired


def test_ttl_zero_disables_expiry():
    clock = FakeClock()
    cache = TTLCache(max_entries=4, ttl_seconds=0, time_fn=clock)
    cache.set("k", ["v"])
    clock.now = 10_000
    assert cache.get("k") == ["v"]


def test_clear():
    cache = TTLCache()
    cache.set("k", ["v"])
    cache.clear()
    assert len(cache) == 0


def test_contains_has_no_side_effects():
    clock = FakeClock()
    cache = TTLCache(max_entries=2, ttl_seconds=10, time_fn=clock)
    cache.set("a", ["1"])
    cache.set("b", ["2"])

    # Membership checks must not touch hit/miss counters or LRU ordering.
    assert "a" in cache
    assert "missing" not in cache
    assert cache.hits == 0
    assert cache.misses == 0

    # 'a' was not promoted by `in`, so it stays least-recently-used and is
    # evicted when a third entry is added.
    cache.set("c", ["3"])
    assert "a" not in cache
    assert "b" in cache
    assert "c" in cache


def test_contains_respects_ttl():
    clock = FakeClock()
    cache = TTLCache(max_entries=4, ttl_seconds=10, time_fn=clock)
    cache.set("k", ["v"])
    assert "k" in cache
    clock.now = 11
    assert "k" not in cache
