from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Dict, Generic, Hashable, Optional, TypeVar

K = TypeVar("K", bound=Hashable)
V = TypeVar("V")


@dataclass
class CacheEntry(Generic[V]):
    value: V
    expires_at: float


class TTLCache(Generic[K, V]):
    """
    PUBLIC_INTERFACE
    Simple in-memory TTL cache with time-based expiration.

    Note:
        - This cache is process-local and not shared between workers.
        - Suitable for small response caching to reduce upstream calls.
    """

    def __init__(self, ttl_seconds: int = 300, maxsize: int = 512) -> None:
        self._ttl = ttl_seconds
        self._maxsize = maxsize
        self._store: Dict[K, CacheEntry[V]] = {}

    def get(self, key: K) -> Optional[V]:
        now = time.time()
        entry = self._store.get(key)
        if not entry:
            return None
        if entry.expires_at < now:
            # Expired
            self._store.pop(key, None)
            return None
        return entry.value

    def set(self, key: K, value: V) -> None:
        # Evict if over size (naive FIFO based on dict order)
        if len(self._store) >= self._maxsize:
            try:
                first_key = next(iter(self._store.keys()))
                self._store.pop(first_key, None)
            except StopIteration:
                pass
        self._store[key] = CacheEntry(value=value, expires_at=time.time() + self._ttl)

    def get_or_set(self, key: K, producer: Callable[[], V]) -> V:
        val = self.get(key)
        if val is not None:
            return val
        val = producer()
        self.set(key, val)
        return val
