"""Structural Protocol for durable memory-envelope stores.

Every adapter (InMemory, File, Postgres, and the MemoryPlane façade's
postgres path) implements these async methods. Domain EngineeringMemory
code depends on this Protocol so tests can swap ``InMemoryStore`` without
changing call sites.

Baseline methods implement compare-and-swap pointers used when a scope's
canonical memory_id must move atomically (e.g. promoting a new golden).
"""

from __future__ import annotations

# Any for opaque record models; Optional for missing lookups.
from typing import Any, Optional, Protocol


class MemoryStore(Protocol):
    """Async CRUD + baseline CAS contract for memory envelopes."""

    async def insert(self, record: Any) -> None:
        """Persist a new envelope; honor idempotency_key when set."""
        ...

    async def get(self, memory_id: str) -> Optional[Any]:
        """Load one envelope by primary key, or None if missing."""
        ...

    async def find_idempotency(self, key: str) -> Optional[Any]:
        """Return the envelope previously written under this idempotency key."""
        ...

    async def scan(self) -> list[Any]:
        """Return every stored envelope (used by rebuild / debug paths)."""
        ...

    async def update(self, record: Any) -> None:
        """Overwrite an existing envelope (validation_state, summary, body)."""
        ...

    async def get_baseline(self, scope_path: str) -> Optional[str]:
        """Read the canonical pointer value for ``scope_path``, if any."""
        ...

    async def compare_and_set_baseline(
        self,
        scope_path: str,
        expected: Optional[str],
        new_value: str,
    ) -> bool:
        """CAS the baseline pointer; return True only when ``expected`` matched."""
        ...
