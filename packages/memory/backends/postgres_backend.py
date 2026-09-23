from __future__ import annotations

"""Module ``agent_sdk/src/memory/backends/postgres_backend.py``.

Agent SDK: HTTP task server, runtimes, skills, telemetry publisher, and workspace helpers for first-party agents.
Agent-local memory backends (dict/file/redis/postgres) used by agent runtimes.

Part of the agent SDK server/runtime stack: agents import these helpers to serve tasks over HTTP, run LLM/tool loops, publish telemetry, and persist plan workspaces.

Hand-written source for ``postgres_backend.py``. Behavior is unchanged; comments document control-plane / agent-runtime intent for maintainers.
"""


import json
import logging
import os
from typing import Any, Optional

from .base import MemoryBackend
from packages.memory.config import MemoryStoreConfig

# Local ``logger`` ← logging.getLogger(__name__).
logger = logging.getLogger(__name__)

# Local ``_SCHEMA`` ← """.
_SCHEMA = """
CREATE TABLE IF NOT EXISTS agent_memory (
    store_id TEXT NOT NULL,
    entry_key TEXT NOT NULL,
    value JSONB NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    # Call ``PRIMARY KEY``.
    PRIMARY KEY (store_id, entry_key)
);
"""


class PostgresMemoryBackend(MemoryBackend):
    """PostgreSQL-backed agent memory (JSONB per store/key)."""

    def __init__(self, config: dict[str, Any] | None = None):
        """``PostgresMemoryBackend``"""
        super().__init__(config)
        self._dsn: str = (
            # Call ``self.config.get``.
            self.config.get("dsn")
            # Call ``or self.config.get``.
            or self.config.get("url")
            # Call ``or os.environ.get``.
            or os.environ.get("AGENT_MEMORY_DATABASE_URL")
            # Call ``or os.environ.get``.
            or os.environ.get("DATABASE_URL")
            or ""
        )
        # Only when (not self._dsn).
        if not self._dsn:
            # Raise ``ValueError`` to signal this failure mode to callers.
            raise ValueError(
                "Postgres memory requires config.dsn or AGENT_MEMORY_DATABASE_URL / DATABASE_URL"
            )
        # Only when (self._dsn.startswith("postgresql+asyncpg://")).
        if self._dsn.startswith("postgresql+asyncpg://"):
            # Bind ``_dsn`` from self._dsn.replace("postgresql+asyncpg://", "postgresql://", … for later use on this instance.
            self._dsn = self._dsn.replace("postgresql+asyncpg://", "postgresql://", 1)
        elif self._dsn.startswith("postgres://"):
            # Bind ``_dsn`` from self._dsn.replace("postgres://", "postgresql://", 1) for later use on this instance.
            self._dsn = self._dsn.replace("postgres://", "postgresql://", 1)
        self._pool: Any = None
        # Bind ``_schema_ready`` from False for later use on this instance.
        self._schema_ready = False

    async def _pool_connect(self) -> Any:
        """``_pool_connect``"""
        if self._pool is not None:
            # Hand ``self._pool`` back to the caller.
            return self._pool
        import asyncpg

        # Bind ``_pool`` from await asyncpg.create_pool(self._dsn, min_size=1, max_size=5) for later use on this instance.
        self._pool = await asyncpg.create_pool(self._dsn, min_size=1, max_size=5)
        # Hand ``self._pool`` back to the caller.
        return self._pool

    async def _ensure_schema(self) -> None:
        """``_ensure_schema``"""
        if self._schema_ready:
            return
        # Local ``pool`` ← await self._pool_connect().
        pool = await self._pool_connect()
        # Hold ``pool.acquire()`` for the duration of the indented block.
        async with pool.acquire() as conn:
            # Await ``conn.execute`` and continue once it completes.
            await conn.execute(_SCHEMA)
        # Bind ``_schema_ready`` from True for later use on this instance.
        self._schema_ready = True

    @staticmethod
    def _serialize(value: Any) -> str:
        """``_serialize``"""
        return json.dumps(value)

    @staticmethod
    def _deserialize(raw: str | None) -> Any:
        """``_deserialize``"""
        if raw is None:
            # Hand ``None`` back to the caller.
            return None
        # Try the fallible work below.
        try:
            # Hand ``json.loads(raw)`` back to the caller.
            return json.loads(raw)
        # On except (json.JSONDecodeError, TypeError): recover or re-raise as appropriate.
        except (json.JSONDecodeError, TypeError):
            # Hand ``raw`` back to the caller.
            return raw

    async def read(self, store: MemoryStoreConfig, key: str) -> Any:
        """``read``"""
        await self._ensure_schema()
        # Local ``pool`` ← await self._pool_connect().
        pool = await self._pool_connect()
        # Hold ``pool.acquire()`` for the duration of the indented block.
        async with pool.acquire() as conn:
            # Only when (store.type in ("list", "queue")).
            if store.type in ("list", "queue"):
                # Try the fallible work below.
                try:
                    # Local ``idx`` ← int(key).
                    idx = int(key)
                # On except ValueError: recover or re-raise as appropriate.
                except ValueError:
                    # Hand ``None`` back to the caller.
                    return None
                # Local ``row`` ← await conn.fetchrow(.
                row = await conn.fetchrow(
                    """
                    SELECT value FROM agent_memory
                    WHERE store_id = $1 AND entry_key ~ '^[0-9]+$'
                    ORDER BY entry_key::int
                    OFFSET $2 LIMIT 1
                    """,
                    store.id,
                    idx,
                )
                # Hand ``self._deserialize(row["value"]) if row else None`` back to the caller.
                return self._deserialize(row["value"]) if row else None

            # Local ``row`` ← await conn.fetchrow(.
            row = await conn.fetchrow(
                "SELECT value FROM agent_memory WHERE store_id = $1 AND entry_key = $2",
                store.id,
                key,
            )
            # Hand ``self._deserialize(row["value"]) if row else None`` back to the caller.
            return self._deserialize(row["value"]) if row else None

    async def write(self, store: MemoryStoreConfig, key: str, value: Any) -> None:
        """``write``"""
        await self._ensure_schema()
        # Local ``pool`` ← await self._pool_connect().
        pool = await self._pool_connect()
        # Local ``serialized`` ← self._serialize(value).
        serialized = self._serialize(value)

        # Hold ``pool.acquire()`` for the duration of the indented block.
        async with pool.acquire() as conn:
            # Only when (store.type in ("list", "queue")).
            if store.type in ("list", "queue"):
                # Local ``count`` ← await conn.fetchval(.
                count = await conn.fetchval(
                    "SELECT COUNT(*) FROM agent_memory WHERE store_id = $1",
                    store.id,
                )
                # Local ``entry_key`` ← str(count).
                entry_key = str(count)
                # Await ``conn.execute`` and continue once it completes.
                await conn.execute(
                    """
                    INSERT INTO agent_memory (store_id, entry_key, value)
                    # Call ``VALUES``.
                    VALUES ($1, $2, $3::jsonb)
                    # Call ``ON CONFLICT``.
                    ON CONFLICT (store_id, entry_key)
                    # Call ``DO UPDATE SET value = EXCLUDED.value, updated_at = NOW``.
                    DO UPDATE SET value = EXCLUDED.value, updated_at = NOW()
                    """,
                    store.id,
                    entry_key,
                    serialized,
                )
                # Only when (store.max_items and count + 1 > store.max_items).
                if store.max_items and count + 1 > store.max_items:
                    # Await ``conn.execute`` and continue once it completes.
                    await conn.execute(
                        """
                        DELETE FROM agent_memory
                        WHERE store_id = $1
                          AND entry_key::int < (
                            SELECT MAX(entry_key::int) - $2 FROM agent_memory WHERE store_id = $1
                          )
                        """,
                        store.id,
                        store.max_items - 1,
                    )
                return

            # Await ``conn.execute`` and continue once it completes.
            await conn.execute(
                """
                INSERT INTO agent_memory (store_id, entry_key, value)
                # Call ``VALUES``.
                VALUES ($1, $2, $3::jsonb)
                # Call ``ON CONFLICT``.
                ON CONFLICT (store_id, entry_key)
                # Call ``DO UPDATE SET value = EXCLUDED.value, updated_at = NOW``.
                DO UPDATE SET value = EXCLUDED.value, updated_at = NOW()
                """,
                store.id,
                key,
                serialized,
            )
            # Only when (store.max_items).
            if store.max_items:
                # Local ``overflow`` ← await conn.fetchval(.
                overflow = await conn.fetchval(
                    """
                    SELECT COUNT(*) - $2 FROM agent_memory WHERE store_id = $1
                    """,
                    store.id,
                    store.max_items,
                )
                # Only when (overflow and overflow > 0).
                if overflow and overflow > 0:
                    # Await ``conn.execute`` and continue once it completes.
                    await conn.execute(
                        """
                        DELETE FROM agent_memory
                        WHERE store_id = $1
                          AND entry_key IN (
                            SELECT entry_key FROM agent_memory
                            WHERE store_id = $1
                            ORDER BY updated_at ASC
                            LIMIT $2
                          )
                        """,
                        store.id,
                        int(overflow),
                    )

    async def search(
        self, store: MemoryStoreConfig, query: str, top_k: int = 5
    ) -> list[Any]:
        """``search``"""
        await self._ensure_schema()
        # Local ``pool`` ← await self._pool_connect().
        pool = await self._pool_connect()
        # Local ``query_l`` ← f"%{query.lower()}%".
        query_l = f"%{query.lower()}%"
        # Hold ``pool.acquire()`` for the duration of the indented block.
        async with pool.acquire() as conn:
            # Local ``rows`` ← await conn.fetch(.
            rows = await conn.fetch(
                """
                SELECT value FROM agent_memory
                WHERE store_id = $1
                  # Call ``AND``.
                  AND (LOWER(entry_key) LIKE $2 OR LOWER(value::text) LIKE $2)
                ORDER BY updated_at DESC
                LIMIT $3
                """,
                store.id,
                query_l,
                top_k,
            )
        # Hand ``[self._deserialize(row["value"]) for row in rows]`` back to the caller.
        return [self._deserialize(row["value"]) for row in rows]

    async def clear(self, store: MemoryStoreConfig, key: str | None = None) -> None:
        """``clear``"""
        await self._ensure_schema()
        # Local ``pool`` ← await self._pool_connect().
        pool = await self._pool_connect()
        # Hold ``pool.acquire()`` for the duration of the indented block.
        async with pool.acquire() as conn:
            # Only when (key is None).
            if key is None:
                # Await ``conn.execute`` and continue once it completes.
                await conn.execute(
                    "DELETE FROM agent_memory WHERE store_id = $1", store.id
                )
                return
            # Only when (store.type in ("list", "queue")).
            if store.type in ("list", "queue"):
                # Try the fallible work below.
                try:
                    # Local ``idx`` ← int(key).
                    idx = int(key)
                # On except ValueError: recover or re-raise as appropriate.
                except ValueError:
                    return
                # Local ``row`` ← await conn.fetchrow(.
                row = await conn.fetchrow(
                    """
                    SELECT entry_key FROM agent_memory
                    WHERE store_id = $1 AND entry_key ~ '^[0-9]+$'
                    ORDER BY entry_key::int
                    OFFSET $2 LIMIT 1
                    """,
                    store.id,
                    idx,
                )
                # Only when (row).
                if row:
                    # Await ``conn.execute`` and continue once it completes.
                    await conn.execute(
                        "DELETE FROM agent_memory WHERE store_id = $1 AND entry_key = $2",
                        store.id,
                        row["entry_key"],
                    )
                return
            # Await ``conn.execute`` and continue once it completes.
            await conn.execute(
                "DELETE FROM agent_memory WHERE store_id = $1 AND entry_key = $2",
                store.id,
                key,
            )

    async def dump(self) -> dict[str, Any]:
        """``dump``"""
        await self._ensure_schema()
        # Local ``pool`` ← await self._pool_connect().
        pool = await self._pool_connect()
        result: dict[str, Any] = {}
        # Hold ``pool.acquire()`` for the duration of the indented block.
        async with pool.acquire() as conn:
            # Local ``rows`` ← await conn.fetch(.
            rows = await conn.fetch(
                "SELECT store_id, entry_key, value FROM agent_memory ORDER BY store_id, entry_key"
            )
        # Loop: for row in rows.
        for row in rows:
            # Local ``store_id`` ← row["store_id"].
            store_id = row["store_id"]
            # Call ``result.setdefault``.
            result.setdefault(store_id, {})
            # Only when (isinstance(result[store_id], dict)).
            if isinstance(result[store_id], dict):
                # Call ``result[store_id][row["entry_key"]] = self._deserialize``.
                result[store_id][row["entry_key"]] = self._deserialize(row["value"])
        # Hand ``result`` back to the caller.
        return result

    async def close(self) -> None:
        """``close``"""
        if self._pool is not None:
            # Await ``self._pool.close`` and continue once it completes.
            await self._pool.close()
            # Bind ``_pool`` from None for later use on this instance.
            self._pool = None
