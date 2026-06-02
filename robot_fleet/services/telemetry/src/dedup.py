"""
In-memory LRU deduplication cache keyed by event_id.

Upgradeable to Redis or another shared store later without
changing the caller interface.
"""

from collections import OrderedDict

_DEFAULT_MAX = 100_000


class DedupCache:
    """LRU cache that tracks recently-seen event IDs."""

    def __init__(self, max_size: int = _DEFAULT_MAX):
        self._seen: OrderedDict[str, None] = OrderedDict()
        self._max = max_size

    def is_duplicate(self, event_id: str) -> bool:
        """Return True if *event_id* was already seen (and record it)."""
        if event_id in self._seen:
            self._seen.move_to_end(event_id)
            return True
        self._seen[event_id] = None
        if len(self._seen) > self._max:
            self._seen.popitem(last=False)
        return False


_cache: DedupCache | None = None


def get_dedup_cache() -> DedupCache:
    global _cache
    if _cache is None:
        _cache = DedupCache()
    return _cache
