# mindflow/cache.py
"""A small bounded, time-aware cache for predictions."""

from __future__ import annotations

import time
from collections import OrderedDict
from collections.abc import Callable


class TTLCache:
    """LRU cache with per-entry time-to-live.

    Bounded in size (evicts least-recently-used entries) and freshness (entries
    older than ``ttl_seconds`` are treated as misses). ``ttl_seconds <= 0``
    disables expiry.
    """

    def __init__(
        self,
        max_entries: int = 256,
        ttl_seconds: float = 600,
        time_fn: Callable[[], float] = time.monotonic,
    ):
        self.max_entries = max(1, int(max_entries))
        self.ttl_seconds = float(ttl_seconds)
        self._time = time_fn
        self._store: OrderedDict[str, tuple[float, list[str]]] = OrderedDict()
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> list[str] | None:
        entry = self._store.get(key)
        if entry is None:
            self.misses += 1
            return None
        timestamp, value = entry
        if self._expired(timestamp):
            del self._store[key]
            self.misses += 1
            return None
        self._store.move_to_end(key)
        self.hits += 1
        return value

    def set(self, key: str, value: list[str]) -> None:
        self._store[key] = (self._time(), value)
        self._store.move_to_end(key)
        while len(self._store) > self.max_entries:
            self._store.popitem(last=False)

    def clear(self) -> None:
        self._store.clear()

    def _expired(self, timestamp: float) -> bool:
        if self.ttl_seconds <= 0:
            return False
        return (self._time() - timestamp) > self.ttl_seconds

    def __len__(self) -> int:
        return len(self._store)

    def __contains__(self, key: str) -> bool:
        return self.get(key) is not None
