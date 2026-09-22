"""Fields a store adapter reads when it writes or reloads a record.

# Call ````StoredRecord`` is a structural Protocol — any Pydantic``.
``StoredRecord`` is a structural Protocol — any Pydantic (or duck-typed)
envelope that exposes these attributes satisfies the store adapters in
``packages.memory.stores``. Adapters treat ``scope_segments`` as an opaque
map and ``scope_key`` as one opaque string; they never look inside either
value to interpret domain hierarchy.

``model_dump_json`` is the envelope blob written to the row. ``model_copy``
builds a view with a different payload when one store copy carries its own
body (inherited vs explicit payload in the write policy).
"""

from __future__ import annotations

# Protocol and Any for the structural store contract.
from typing import Any, Protocol


class StoredRecord(Protocol):
    """Structural contract every memory store adapter expects on a record.

    Domain record models (for example, engineering-memory envelopes) implement
    these fields so FileStore / PostgresStore / MemoryPlane can persist and
    reload without importing domain packages.
    """

    # Globally unique id for this memory envelope.
    memory_id: str
    # Project / namespace the record belongs to (used as Cassandra/OpenSearch partition).
    project_id: str
    # Planner task id when the write is task-scoped; may be empty.
    task_id: str
    # Short human-readable summary indexed for full-text search.
    summary: str
    # Primary JSON payload; individual store copies may override.
    payload: dict[str, Any]
    # Free-form tags used by OpenSearch and semantic search text.
    tags: list[str]
    # Provenance of which store copies were requested for this write.
    copies: list[Any]
    # Flattened scope path string used for baseline pointers.
    scope_path: str
    # Opaque segment map persisted as JSONB / JSON without interpretation.
    scope_segments: dict[str, str]
    # Opaque single-string scope key for Cassandra memory_by_scope.
    scope_key: str
    # Dedup key so retries return the same envelope instead of inserting twice.
    idempotency_key: str

    def model_dump_json(self) -> str:
        """Serialize the full envelope to a JSON string for durable storage."""
        ...

    def model_copy(self, *, update: dict[str, Any]) -> Any:
        """Return a shallow-updated copy (used when a store copy has its own payload)."""
        ...
