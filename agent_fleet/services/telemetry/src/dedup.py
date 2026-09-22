"""
In-memory LRU deduplication cache keyed by event_id.

Telemetry producers (HTTP batch and gRPC stream) share this cache so a
retried event_id is accepted at most once per process. The structure is an
``OrderedDict`` acting as LRU: hits move to the end; inserts that exceed
``max_size`` evict the oldest key. Upgradeable later to Redis without
changing ``is_duplicate`` / ``get_dedup_cache`` call sites.
"""

# OrderedDict preserves insertion order and supports move_to_end / popitem.
from collections import OrderedDict

# Default capacity: large enough for bursty ingest without unbounded growth.
_DEFAULT_MAX = 100_000


class DedupCache:
    """LRU cache that tracks recently-seen event IDs.

    ``is_duplicate`` both queries and records: returning True means the id was
    already present (caller should skip publish); returning False means this
    is the first sighting and the id is now stored. Eviction pops the least
    recently used entry when size exceeds ``max_size``.
    """

    def __init__(self, max_size: int = _DEFAULT_MAX):
        """Create an empty cache with an optional capacity override.

        Args:
            max_size: Maximum distinct event_ids retained; older ids fall out
                of dedup protection after eviction (acceptable for single-node
                ingest; shared Redis would extend the window).
        """
        # Values are unused; None placeholders keep OrderedDict as a set-like LRU.
        self._seen: OrderedDict[str, None] = OrderedDict()
        # Remember capacity for eviction checks after each insert.
        self._max = max_size

    def is_duplicate(self, event_id: str) -> bool:
        """Return True if *event_id* was already seen (and refresh its LRU position).

        On a hit, moves the key to the end so frequent retries stay hot. On a
        miss, inserts the key and may evict the oldest entry if over capacity.
        Empty or unset event_ids are still recorded; callers should validate
        required fields before calling.
        """
        # Hit path: refresh recency and signal duplicate.
        if event_id in self._seen:
            # move_to_end marks this id as most recently used.
            self._seen.move_to_end(event_id)
            return True
        # Miss path: record the id for future lookups.
        self._seen[event_id] = None
        # Evict oldest if we exceeded the configured ceiling.
        if len(self._seen) > self._max:
            # last=False pops the least-recently-used (front) item.
            self._seen.popitem(last=False)
        # First sighting: not a duplicate.
        return False


# Process-wide singleton; None until first get_dedup_cache() call.
_cache: DedupCache | None = None


def get_dedup_cache() -> DedupCache:
    """Return the module-level DedupCache singleton, creating it on first use.

    Shared across HTTP and gRPC ingest paths in this process so the same
    event_id cannot be double-published through both transports. Tests that
    need isolation should reset ``_cache`` or construct ``DedupCache``
    directly.
    """
    # Mutate module global so subsequent callers share one LRU.
    global _cache
    # Lazy init avoids allocating 100k-capable structure at import time.
    if _cache is None:
        _cache = DedupCache()
    return _cache
