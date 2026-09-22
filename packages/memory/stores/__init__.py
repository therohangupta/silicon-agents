"""Memory store adapters and the multi-backend MemoryPlane façade.

Re-exports the ``MemoryStore`` protocol plus concrete adapters:

* ``InMemoryStore`` — process-local dicts for tests / dry runs
* ``FileStore`` — JSONL + flock for single-machine shared agents
* ``PostgresStore`` — transactional envelopes, vectors, leases, approvals
* ``MemoryPlane`` — Postgres plus Cassandra / S3 / OpenSearch / ClickHouse /
  Vault / git / NATS projections driven by write-policy copies
"""

# File-backed JSONL adapter for shared single-host deployments.
from .file import FileStore
# Process-local dict adapter for unit tests.
from .memory import InMemoryStore
# Multi-backend façade that applies Placement copies to real systems.
from .plane import MemoryPlane
# asyncpg JSONB / pgvector adapter for production envelopes.
from .postgres import PostgresStore
# Structural Protocol every adapter satisfies.
from .protocol import MemoryStore

# Public symbols for ``from packages.memory.stores import ...``.
__all__ = [
    "FileStore",
    "InMemoryStore",
    "MemoryPlane",
    "MemoryStore",
    "PostgresStore",
]
