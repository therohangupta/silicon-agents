"""Process-local MemoryStore used by tests and single-process dry runs.

All state lives in plain dicts guarded by an ``asyncio.Lock``. In addition
to the ``MemoryStore`` protocol methods, this adapter implements
``apply_copies`` / ``read_copy`` / ``get_lookup`` so unit tests can exercise
write-policy projections without Cassandra, S3, or Vault.
"""

from __future__ import annotations

# asyncio.Lock serializes mutating operations within one event loop.
import asyncio
# deepcopy isolates stored payloads from caller mutation.
import copy
# Any/Optional for opaque envelopes.
from typing import Any, Optional

# StoreCopy describes one projection the write policy requested.
from packages.memory.policy import StoreCopy


class InMemoryStore:
    """Process-local store used by tests and single-process dry runs."""

    def __init__(self) -> None:
        # Primary key → envelope object.
        self._records: dict[str, Any] = {}
        # Idempotency key → memory_id for deduplicated retries.
        self._idempotency: dict[str, str] = {}
        # Scope path → baseline pointer value (usually a memory_id).
        self._baselines: dict[str, str] = {}
        # (store, project_id, key) → (memory_id, payload) for projected copies.
        self._copies: dict[tuple[str, str, str], tuple[str, dict[str, Any]]] = {}
        # Mutual exclusion for insert/update/CAS/copy writes.
        self._lock = asyncio.Lock()

    async def insert(self, record: Any) -> None:
        """Store ``record`` and index its idempotency key when present."""
        async with self._lock:
            # Index by primary memory_id.
            self._records[record.memory_id] = record
            # Optionally register the dedup key → memory_id mapping.
            if record.idempotency_key:
                self._idempotency[record.idempotency_key] = record.memory_id

    async def get(self, memory_id: str) -> Optional[Any]:
        """Return the envelope for ``memory_id`` or None."""
        return self._records.get(memory_id)

    async def find_idempotency(self, key: str) -> Optional[Any]:
        """Resolve an idempotency key to its previously written envelope."""
        # Look up the memory_id registered under this key.
        memory_id = self._idempotency.get(key)
        # Only when (memory_id is None).
        if memory_id is None:
            # Hand ``None`` back to the caller.
            return None
        # Return the live envelope (may be None if somehow deleted).
        return self._records.get(memory_id)

    async def scan(self) -> list[Any]:
        """Return a snapshot list of every stored envelope."""
        return list(self._records.values())

    async def update(self, record: Any) -> None:
        """Overwrite the envelope at ``record.memory_id``."""
        async with self._lock:
            self._records[record.memory_id] = record

    async def get_baseline(self, scope_path: str) -> Optional[str]:
        """Read the baseline pointer for ``scope_path``."""
        return self._baselines.get(scope_path)

    async def compare_and_set_baseline(
        self,
        scope_path: str,
        expected: Optional[str],
        new_value: str,
    ) -> bool:
        """Atomically set the baseline when the current value equals ``expected``."""
        async with self._lock:
            # Read the current pointer (None if unset).
            current = self._baselines.get(scope_path)
            # Abort without writing when the CAS precondition fails.
            if current != expected:
                # Hand ``False`` back to the caller.
                return False
            # Commit the new pointer value.
            self._baselines[scope_path] = new_value
            # Hand ``True`` back to the caller.
            return True

    async def apply_copies(self, record: Any, copies: list[StoreCopy]) -> None:
        """Materialize write-policy projections into the in-process copy map."""
        async with self._lock:
            # Loop: for item in copies.
            for item in copies:
                # Inherit the primary payload when the copy did not override.
                payload = copy.deepcopy(item.payload if item.payload is not None else record.payload)
                # Key by (store, project, key) so lookups mirror Cassandra KV / object keys.
                self._copies[(item.store, record.project_id, item.key)] = (record.memory_id, payload)

    async def read_copy(self, store: str, project_id: str, key: str = "") -> Optional[dict[str, Any]]:
        """Return a deep copy of a previously applied projection payload."""
        found = self._copies.get((store, project_id, key))
        # Only when (found is None).
        if found is None:
            # Hand ``None`` back to the caller.
            return None
        # Return a deepcopy so callers cannot mutate the store's copy.
        return copy.deepcopy(found[1])

    async def get_lookup(self, project_id: str, key: str) -> Optional[Any]:
        """Return the envelope view bound to a Cassandra-KV-style lookup key."""
        # Lookups always use the cassandra_kv placement name.
        found = self._copies.get(("cassandra_kv", project_id, key))
        # Only when (found is None).
        if found is None:
            # Hand ``None`` back to the caller.
            return None
        # Unpack memory_id and the payload stored under that key.
        memory_id, payload = found
        # Load the base envelope to preserve metadata around the override body.
        record = self._records.get(memory_id)
        # Only when (record is None).
        if record is None:
            # Hand ``None`` back to the caller.
            return None
        # Return a model_copy with the KV payload substituted in.
        return record.model_copy(update={"payload": copy.deepcopy(payload)})
