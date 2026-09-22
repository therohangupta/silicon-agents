"""PostgreSQL JSONB store for memory envelopes and related control tables.

This adapter is the transactional heart of the memory plane when
``MEMORY_BACKEND=postgres`` (and is always used underneath
``MemoryPlane``). It owns:

* ``memory_record`` — envelope JSONB plus indexed scope/type/state columns
* ``memory_pointer`` — compare-and-swap baseline pointers per scope_path
* ``memory_embedding`` — pgvector(256) rows for semantic search
* ``memory_decision`` — append-only decision log per scope
* ``memory_lease`` — exclusive task leases with TTL
* ``memory_approval`` — human/system approval records

Query planning for domain filters stays in EngineeringMemory; this module
only persists and retrieves envelopes plus the operational tables above.
"""

from __future__ import annotations

# json serializes scope_segments and decision payloads for JSONB columns.
import json
# os.environ supplies DSN fallbacks when the constructor omits dsn.
import os
# Any/Optional for opaque record models.
from typing import Any, Optional

# label() turns enums into TEXT column values.
from packages.memory.values import label

# DDL applied once per process via _ensure_schema.
_SCHEMA = """
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE IF NOT EXISTS memory_record (
    memory_id TEXT PRIMARY KEY,
    idempotency_key TEXT UNIQUE,
    namespace TEXT NOT NULL,
    scope_path TEXT NOT NULL,
    scope JSONB NOT NULL,
    record_type TEXT NOT NULL,
    validation_state TEXT NOT NULL,
    task_id TEXT NOT NULL DEFAULT '',
    summary TEXT NOT NULL DEFAULT '',
    envelope JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS memory_record_scope_idx
    ON memory_record (namespace, record_type, scope_path);
CREATE TABLE IF NOT EXISTS memory_pointer (
    scope_path TEXT PRIMARY KEY,
    pointer_value TEXT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS memory_embedding (
    memory_id TEXT PRIMARY KEY REFERENCES memory_record(memory_id),
    embedding vector(256) NOT NULL
);
CREATE TABLE IF NOT EXISTS memory_decision (
    decision_id TEXT PRIMARY KEY,
    scope_path TEXT NOT NULL,
    summary TEXT NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS memory_lease (
    lease_id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    holder TEXT NOT NULL,
    scope_path TEXT NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    released BOOLEAN NOT NULL DEFAULT FALSE
);
CREATE UNIQUE INDEX IF NOT EXISTS memory_lease_active_idx
    ON memory_lease (task_id) WHERE released = FALSE;
CREATE TABLE IF NOT EXISTS memory_approval (
    approval_id TEXT PRIMARY KEY,
    subject_ref TEXT NOT NULL,
    approver TEXT NOT NULL,
    decision TEXT NOT NULL,
    evidence_ref TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""


def _normalize_dsn(dsn: str) -> str:
    """Convert SQLAlchemy-style URLs into the form asyncpg accepts.

    ``postgresql+asyncpg://`` and bare ``postgres://`` are rewritten to
    ``postgresql://`` so a single DATABASE_URL works for both SQLAlchemy
    and this store.
    """
    # Strip the SQLAlchemy asyncpg driver suffix.
    if dsn.startswith("postgresql+asyncpg://"):
        # Hand ``"postgresql://" + dsn[len("postgresql+asyncpg://"):]`` back to the caller.
        return "postgresql://" + dsn[len("postgresql+asyncpg://"):]
    # Normalize the short postgres:// scheme.
    if dsn.startswith("postgres://"):
        # Hand ``"postgresql://" + dsn[len("postgres://"):]`` back to the caller.
        return "postgresql://" + dsn[len("postgres://"):]
    # Already in asyncpg-friendly form.
    return dsn


class PostgresStore:
    """PostgreSQL JSONB store for envelopes and flexible payloads.

    Query planning stays in EngineeringMemory for this first deployment.
    The table's indexed columns are the envelope fields the service always sets.
    """

    def __init__(self, dsn: str | None = None, *, record_cls: type) -> None:
        # Domain envelope class used to rehydrate JSONB rows.
        self._record_cls = record_cls
        # Resolve DSN from explicit arg, then memory-specific env, then global.
        raw = (
            dsn
            or os.environ.get("MEMORY_DATABASE_URL")
            or os.environ.get("MEMORY_DATABASE_URL")
            or os.environ.get("DATABASE_URL")
            or ""
        )
        # Fail fast when no database URL is configured.
        if not raw:
            # Raise ``ValueError`` to signal this failure mode to callers.
            raise ValueError("Postgres memory requires MEMORY_DATABASE_URL or DATABASE_URL")
        # Normalize to asyncpg's expected scheme.
        self._dsn = _normalize_dsn(raw)
        # Lazy asyncpg pool; created on first use.
        self._pool: Any = None
        # True after DDL has been applied successfully once.
        self._schema_ready = False

    async def _pool_connect(self) -> Any:
        """Return (creating if needed) the shared asyncpg connection pool."""
        if self._pool is None:
            # Import lazily so non-postgres deployments need not install asyncpg.
            import asyncpg

            # Small pool: memory traffic is bursty but not connection-heavy.
            self._pool = await asyncpg.create_pool(self._dsn, min_size=1, max_size=5)
        # Hand ``self._pool`` back to the caller.
        return self._pool

    async def _ensure_schema(self) -> None:
        """Idempotently apply DDL and best-effort create the HNSW index."""
        if self._schema_ready:
            return
        # Local ``pool`` ← await self._pool_connect().
        pool = await self._pool_connect()
        # Hold ``pool.acquire()`` for the duration of the indented block.
        async with pool.acquire() as conn:
            # Split the multi-statement DDL on semicolons and execute each.
            for statement in (part.strip() for part in _SCHEMA.split(";")):
                # Only when (statement).
                if statement:
                    # Await ``conn.execute`` and continue once it completes.
                    await conn.execute(statement)
            # Try the fallible work below.
            try:
                # HNSW speeds cosine search; may fail on older pgvector builds.
                await conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS memory_embedding_idx
                    ON memory_embedding USING hnsw (embedding vector_cosine_ops)
                    """
                )
            # On except Exception: recover or re-raise as appropriate.
            except Exception:
                # Sequential scan still answers cosine search on a small index.
                pass
        # Mark ready so subsequent calls skip DDL.
        self._schema_ready = True

    def _from_row(self, raw: str) -> Any:
        """Rehydrate an envelope from a JSON text blob."""
        return self._record_cls.model_validate(json.loads(raw))

    async def insert(self, record: Any) -> None:
        """Insert a new envelope row with indexed columns denormalized."""
        await self._ensure_schema()
        # Local ``pool`` ← await self._pool_connect().
        pool = await self._pool_connect()
        # Full envelope JSON also stored in the envelope JSONB column.
        payload = record.model_dump_json()
        # Hold ``pool.acquire()`` for the duration of the indented block.
        async with pool.acquire() as conn:
            # Await ``conn.execute`` and continue once it completes.
            await conn.execute(
                """
                INSERT INTO memory_record (
                    memory_id, idempotency_key, namespace, scope_path, scope, record_type,
                    validation_state, task_id, summary, envelope, created_at
                ) VALUES ($1,$2,$3,$4,$5::jsonb,$6,$7,$8,$9,$10::jsonb,$11)
                """,
                record.memory_id,
                # Unique constraint treats empty string specially; store NULL instead.
                record.idempotency_key or None,
                # project_id is the namespace partition key.
                record.project_id,
                record.scope_path,
                # Opaque scope segments as JSONB.
                json.dumps(record.scope_segments),
                label(record.record_type),
                label(record.validation_state),
                record.task_id,
                record.summary,
                payload,
                record.created_at,
            )

    async def get(self, memory_id: str) -> Optional[Any]:
        """Fetch one envelope by primary key."""
        await self._ensure_schema()
        # Local ``pool`` ← await self._pool_connect().
        pool = await self._pool_connect()
        # Hold ``pool.acquire()`` for the duration of the indented block.
        async with pool.acquire() as conn:
            # Local ``row`` ← await conn.fetchrow(.
            row = await conn.fetchrow(
                "SELECT envelope::text AS envelope FROM memory_record WHERE memory_id = $1",
                memory_id,
            )
        # Only when (row is None).
        if row is None:
            # Hand ``None`` back to the caller.
            return None
        # Hand ``self._from_row(row["envelope"])`` back to the caller.
        return self._from_row(row["envelope"])

    async def find_idempotency(self, key: str) -> Optional[Any]:
        """Fetch the envelope previously written under ``key``."""
        await self._ensure_schema()
        # Local ``pool`` ← await self._pool_connect().
        pool = await self._pool_connect()
        # Hold ``pool.acquire()`` for the duration of the indented block.
        async with pool.acquire() as conn:
            # Local ``row`` ← await conn.fetchrow(.
            row = await conn.fetchrow(
                "SELECT envelope::text AS envelope FROM memory_record WHERE idempotency_key = $1",
                key,
            )
        # Only when (row is None).
        if row is None:
            # Hand ``None`` back to the caller.
            return None
        # Hand ``self._from_row(row["envelope"])`` back to the caller.
        return self._from_row(row["envelope"])

    async def scan(self) -> list[Any]:
        """Return every envelope (debug / rebuild helpers)."""
        await self._ensure_schema()
        # Local ``pool`` ← await self._pool_connect().
        pool = await self._pool_connect()
        # Hold ``pool.acquire()`` for the duration of the indented block.
        async with pool.acquire() as conn:
            # Local ``rows`` ← await conn.fetch("SELECT envelope::text AS envelope FROM memory_r….
            rows = await conn.fetch("SELECT envelope::text AS envelope FROM memory_record")
        # Hand ``[self._from_row(row["envelope"]) for row in rows]`` back to the caller.
        return [self._from_row(row["envelope"]) for row in rows]

    async def update(self, record: Any) -> None:
        """Patch validation_state, summary, and full envelope JSONB."""
        await self._ensure_schema()
        # Local ``pool`` ← await self._pool_connect().
        pool = await self._pool_connect()
        # Hold ``pool.acquire()`` for the duration of the indented block.
        async with pool.acquire() as conn:
            # Await ``conn.execute`` and continue once it completes.
            await conn.execute(
                """
                UPDATE memory_record
                SET validation_state = $2,
                    # Local ``summary`` ← $3,.
                    summary = $3,
                    # Local ``envelope`` ← $4::jsonb.
                    envelope = $4::jsonb
                WHERE memory_id = $1
                """,
                record.memory_id,
                label(record.validation_state),
                record.summary,
                record.model_dump_json(),
            )

    async def get_baseline(self, scope_path: str) -> Optional[str]:
        """Read the canonical pointer for ``scope_path``."""
        await self._ensure_schema()
        # Local ``pool`` ← await self._pool_connect().
        pool = await self._pool_connect()
        # Hold ``pool.acquire()`` for the duration of the indented block.
        async with pool.acquire() as conn:
            # Local ``row`` ← await conn.fetchrow(.
            row = await conn.fetchrow(
                "SELECT pointer_value FROM memory_pointer WHERE scope_path = $1",
                scope_path,
            )
        # Only when (row is None).
        if row is None:
            # Hand ``None`` back to the caller.
            return None
        # Hand ``str(row["pointer_value"])`` back to the caller.
        return str(row["pointer_value"])

    async def compare_and_set_baseline(
        self,
        scope_path: str,
        expected: Optional[str],
        new_value: str,
    ) -> bool:
        """Transactionally CAS the baseline pointer under ``FOR UPDATE``."""
        await self._ensure_schema()
        # Local ``pool`` ← await self._pool_connect().
        pool = await self._pool_connect()
        # Hold ``pool.acquire()`` for the duration of the indented block.
        async with pool.acquire() as conn:
            # Hold ``conn.transaction()`` for the duration of the indented block.
            async with conn.transaction():
                # Lock the row (or the gap) so concurrent CAS cannot race.
                row = await conn.fetchrow(
                    "SELECT pointer_value FROM memory_pointer WHERE scope_path = $1 FOR UPDATE",
                    scope_path,
                )
                # Local ``current`` ← None if row is None else str(row["pointer_value"]).
                current = None if row is None else str(row["pointer_value"])
                # Precondition failed — another writer won.
                if current != expected:
                    # Hand ``False`` back to the caller.
                    return False
                # Only when (row is None).
                if row is None:
                    # First pointer for this scope.
                    await conn.execute(
                        """
                        INSERT INTO memory_pointer (scope_path, pointer_value)
                        VALUES ($1, $2)
                        """,
                        scope_path,
                        new_value,
                    )
                else:
                    # Update existing pointer and bump updated_at.
                    await conn.execute(
                        """
                        UPDATE memory_pointer
                        SET pointer_value = $2, updated_at = NOW()
                        WHERE scope_path = $1
                        """,
                        scope_path,
                        new_value,
                    )
                # Hand ``True`` back to the caller.
                return True

    async def upsert_embedding(self, memory_id: str, embedding: list[float]) -> None:
        """Insert or replace the pgvector row for ``memory_id``."""
        await self._ensure_schema()
        # pgvector literal syntax: [0.1,0.2,...]
        literal = "[" + ",".join(f"{value:.6f}" for value in embedding) + "]"
        # Local ``pool`` ← await self._pool_connect().
        pool = await self._pool_connect()
        # Hold ``pool.acquire()`` for the duration of the indented block.
        async with pool.acquire() as conn:
            # Await ``conn.execute`` and continue once it completes.
            await conn.execute(
                """
                INSERT INTO memory_embedding (memory_id, embedding)
                VALUES ($1, $2::vector)
                ON CONFLICT (memory_id) DO UPDATE SET embedding = EXCLUDED.embedding
                """,
                memory_id,
                literal,
            )

    async def search_embedding(self, project_id: str, embedding: list[float], limit: int) -> list[Any]:
        """Return envelopes nearest to ``embedding`` within ``project_id`` namespace."""
        await self._ensure_schema()
        # Local ``literal`` ← "[" + ",".join(f"{value:.6f}" for value in embedding) + "]".
        literal = "[" + ",".join(f"{value:.6f}" for value in embedding) + "]"
        # Local ``pool`` ← await self._pool_connect().
        pool = await self._pool_connect()
        # Hold ``pool.acquire()`` for the duration of the indented block.
        async with pool.acquire() as conn:
            # Local ``rows`` ← await conn.fetch(.
            rows = await conn.fetch(
                """
                SELECT r.envelope::text AS envelope
                FROM memory_embedding e
                JOIN memory_record r ON r.memory_id = e.memory_id
                WHERE r.namespace = $1
                ORDER BY e.embedding <=> $2::vector
                LIMIT $3
                """,
                project_id,
                literal,
                limit,
            )
        # Hand ``[self._from_row(row["envelope"]) for row in rows]`` back to the caller.
        return [self._from_row(row["envelope"]) for row in rows]

    async def record_decision(self, record: Any) -> None:
        """Append a decision row; ignore conflicts on the same decision_id."""
        await self._ensure_schema()
        # Local ``pool`` ← await self._pool_connect().
        pool = await self._pool_connect()
        # Hold ``pool.acquire()`` for the duration of the indented block.
        async with pool.acquire() as conn:
            # Await ``conn.execute`` and continue once it completes.
            await conn.execute(
                """
                INSERT INTO memory_decision (decision_id, scope_path, summary, payload, created_at)
                VALUES ($1, $2, $3, $4::jsonb, $5)
                ON CONFLICT (decision_id) DO NOTHING
                """,
                record.memory_id,
                record.scope_path,
                record.summary,
                json.dumps(record.payload),
                record.created_at,
            )

    async def list_decisions(self, scope_path: str) -> list[dict[str, Any]]:
        """Return decision rows for ``scope_path`` ordered by creation time."""
        await self._ensure_schema()
        # Local ``pool`` ← await self._pool_connect().
        pool = await self._pool_connect()
        # Hold ``pool.acquire()`` for the duration of the indented block.
        async with pool.acquire() as conn:
            # Local ``rows`` ← await conn.fetch(.
            rows = await conn.fetch(
                """
                SELECT decision_id, summary, payload::text AS payload
                FROM memory_decision WHERE scope_path = $1 ORDER BY created_at
                """,
                scope_path,
            )
        # Hand ``[`` back to the caller.
        return [
            {"decision_id": row["decision_id"], "summary": row["summary"], "payload": json.loads(row["payload"])}
            # Loop: for row in rows.
            for row in rows
        ]

    async def acquire_lease(self, lease_id: str, task_id: str, holder: str, scope_path: str, ttl_secs: int) -> bool:
        """Acquire an exclusive lease for ``task_id`` if none is actively held.

        Expired leases are marked released first. Returns False when another
        holder still has an unexpired active lease.
        """
        await self._ensure_schema()
        # Local ``pool`` ← await self._pool_connect().
        pool = await self._pool_connect()
        # Hold ``pool.acquire()`` for the duration of the indented block.
        async with pool.acquire() as conn:
            # Hold ``conn.transaction()`` for the duration of the indented block.
            async with conn.transaction():
                # Reap expired active leases for this task.
                await conn.execute(
                    """
                    UPDATE memory_lease SET released = TRUE
                    WHERE task_id = $1 AND released = FALSE AND expires_at <= NOW()
                    """,
                    task_id,
                )
                # Lock any remaining active lease row.
                active = await conn.fetchrow(
                    """
                    SELECT lease_id FROM memory_lease
                    WHERE task_id = $1 AND released = FALSE AND expires_at > NOW()
                    FOR UPDATE
                    """,
                    task_id,
                )
                # Another holder still owns the lease.
                if active is not None:
                    # Hand ``False`` back to the caller.
                    return False
                # Insert the new lease with TTL relative to NOW().
                await conn.execute(
                    """
                    INSERT INTO memory_lease (lease_id, task_id, holder, scope_path, expires_at)
                    VALUES ($1, $2, $3, $4, NOW() + make_interval(secs => $5))
                    """,
                    lease_id,
                    task_id,
                    holder,
                    scope_path,
                    ttl_secs,
                )
                # Hand ``True`` back to the caller.
                return True

    async def release_lease(self, task_id: str, holder: str) -> bool:
        """Mark the active lease for (task_id, holder) as released."""
        await self._ensure_schema()
        # Local ``pool`` ← await self._pool_connect().
        pool = await self._pool_connect()
        # Hold ``pool.acquire()`` for the duration of the indented block.
        async with pool.acquire() as conn:
            # Local ``result`` ← await conn.execute(.
            result = await conn.execute(
                """
                UPDATE memory_lease SET released = TRUE
                WHERE task_id = $1 AND holder = $2 AND released = FALSE
                """,
                task_id,
                holder,
            )
        # asyncpg returns strings like "UPDATE 1".
        return result.endswith("1")

    async def record_approval(self, approval_id: str, subject_ref: str, approver: str, decision: str, evidence_ref: str) -> None:
        """Insert an approval row; ignore duplicate approval_id."""
        await self._ensure_schema()
        # Local ``pool`` ← await self._pool_connect().
        pool = await self._pool_connect()
        # Hold ``pool.acquire()`` for the duration of the indented block.
        async with pool.acquire() as conn:
            # Await ``conn.execute`` and continue once it completes.
            await conn.execute(
                """
                INSERT INTO memory_approval (approval_id, subject_ref, approver, decision, evidence_ref)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (approval_id) DO NOTHING
                """,
                approval_id,
                subject_ref,
                approver,
                decision,
                evidence_ref,
            )

    async def get_approval(self, approval_id: str) -> Optional[dict[str, Any]]:
        """Fetch one approval record as a plain dict."""
        await self._ensure_schema()
        # Local ``pool`` ← await self._pool_connect().
        pool = await self._pool_connect()
        # Hold ``pool.acquire()`` for the duration of the indented block.
        async with pool.acquire() as conn:
            # Local ``row`` ← await conn.fetchrow(.
            row = await conn.fetchrow(
                """
                SELECT approval_id, subject_ref, approver, decision, evidence_ref
                FROM memory_approval WHERE approval_id = $1
                """,
                approval_id,
            )
        # Only when (row is None).
        if row is None:
            # Hand ``None`` back to the caller.
            return None
        # Hand ``dict(row)`` back to the caller.
        return dict(row)

    async def close(self) -> None:
        """Close the asyncpg pool if it was opened."""
        if self._pool is not None:
            # Await ``self._pool.close`` and continue once it completes.
            await self._pool.close()
            # Bind ``_pool`` from None for later use on this instance.
            self._pool = None
