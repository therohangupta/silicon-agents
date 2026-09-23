# Requires: redis>=5.0.0  (pip install redis)
from __future__ import annotations

"""Module ``agent_sdk/src/memory/backends/redis_backend.py``.

Agent SDK: HTTP task server, runtimes, skills, telemetry publisher, and workspace helpers for first-party agents.
Agent-local memory backends (dict/file/redis/postgres) used by agent runtimes.

Part of the agent SDK server/runtime stack: agents import these helpers to serve tasks over HTTP, run LLM/tool loops, publish telemetry, and persist plan workspaces.

Hand-written source for ``redis_backend.py``. Behavior is unchanged; comments document control-plane / agent-runtime intent for maintainers.
"""


import json
import logging
from typing import Any

# Try the fallible work below.
try:
    import redis.asyncio as aioredis
# On except ImportError: recover or re-raise as appropriate.
except ImportError:
    # Local ``aioredis`` ← None  # type: ignore[assignment].
    aioredis = None  # type: ignore[assignment]

from .base import MemoryBackend
from packages.memory.config import MemoryStoreConfig

# Local ``logger`` ← logging.getLogger(__name__).
logger = logging.getLogger(__name__)


class RedisMemoryBackend(MemoryBackend):
    """Production memory backend backed by Redis.

    Supported store types and their Redis data-structure mapping:
      # Call ``- key_value  -> Redis Hash``.
      - key_value  -> Redis Hash  (HSET / HGET / HDEL / HGETALL)
      # Call ``- list       -> Redis List``.
      - list       -> Redis List  (LPUSH / LRANGE / LTRIM)
      # Call ``- queue      -> Redis List``.
      - queue      -> Redis List  (RPUSH / LPOP)
      - vector     -> Falls back to key_value behaviour (vector search
                      requires RediSearch; a dedicated subclass can be
                      added later).
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """``can``"""
        super().__init__(config)
        # Only when (aioredis is None).
        if aioredis is None:
            # Raise ``ImportError`` to signal this failure mode to callers.
            raise ImportError(
                "redis package is required for RedisMemoryBackend. "
                "Install it with: pip install redis>=5.0.0"
            )
        # Call ``self._host: str = self.config.get``.
        self._host: str = self.config.get("host", "localhost")
        # Call ``self._port: int = int``.
        self._port: int = int(self.config.get("port", 6379))
        # Call ``self._db: int = int``.
        self._db: int = int(self.config.get("db", 0))
        # Call ``self._password: str | None = self.config.get``.
        self._password: str | None = self.config.get("password")
        # Call ``self._prefix: str = self.config.get``.
        self._prefix: str = self.config.get("prefix", "af:mem:")

        # Bind ``_pool`` from aioredis.ConnectionPool( for later use on this instance.
        self._pool = aioredis.ConnectionPool(
            # Local ``host`` ← self._host,.
            host=self._host,
            # Local ``port`` ← self._port,.
            port=self._port,
            # Local ``db`` ← self._db,.
            db=self._db,
            # Local ``password`` ← self._password,.
            password=self._password,
            # Local ``decode_responses`` ← True,.
            decode_responses=True,
        )
        # Bind ``_redis`` from aioredis.Redis(connection_pool=self._pool) for later use on this instance.
        self._redis = aioredis.Redis(connection_pool=self._pool)

    # -- helpers --------------------------------------------------------------

    def _key(self, store: MemoryStoreConfig, key: str | None = None) -> str:
        """Build the namespaced Redis key for a store (and optional field)."""
        base = f"{self._prefix}{store.id}"
        # Only when (store.type == "key_value" and key is not None).
        if store.type == "key_value" and key is not None:
            # Hand ``f"{base}:{key}"`` back to the caller.
            return f"{base}:{key}"
        # Hand ``base`` back to the caller.
        return base

    def _store_key(self, store: MemoryStoreConfig) -> str:
        """Return the top-level Redis key that holds the store's data."""
        return f"{self._prefix}{store.id}"

    async def _apply_ttl(self, store: MemoryStoreConfig) -> None:
        """Set expiry on the store key when a TTL is configured."""
        if store.ttl_secs:
            # Try the fallible work below.
            try:
                # Await ``self._redis.expire`` and continue once it completes.
                await self._redis.expire(self._store_key(store), store.ttl_secs)
            # On except aioredis.RedisError as exc: recover or re-raise as appropriate.
            except aioredis.RedisError as exc:
                # Log at warning so operators can diagnose this path.
                logger.warning("Failed to set TTL on %s: %s", store.id, exc)

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

    # -- read -----------------------------------------------------------------

    async def read(self, store: MemoryStoreConfig, key: str) -> Any:
        """``read``"""
        try:
            # Only when (store.type in ("list", "queue")).
            if store.type in ("list", "queue"):
                # Local ``idx`` ← int(key).
                idx = int(key)
                # Local ``raw`` ← await self._redis.lindex(self._store_key(store), idx).
                raw = await self._redis.lindex(self._store_key(store), idx)
                # Hand ``self._deserialize(raw)`` back to the caller.
                return self._deserialize(raw)

            # Local ``raw`` ← await self._redis.hget(self._store_key(store), key).
            raw = await self._redis.hget(self._store_key(store), key)
            # Hand ``self._deserialize(raw)`` back to the caller.
            return self._deserialize(raw)
        # On except (aioredis.RedisError, ValueError) as exc: recover or re-raise as appropriate.
        except (aioredis.RedisError, ValueError) as exc:
            # Log at warning so operators can diagnose this path.
            logger.warning("redis read error on %s/%s: %s", store.id, key, exc)
            # Hand ``None`` back to the caller.
            return None

    # -- write ----------------------------------------------------------------

    async def write(self, store: MemoryStoreConfig, key: str, value: Any) -> None:
        """``write``"""
        try:
            # Local ``sk`` ← self._store_key(store).
            sk = self._store_key(store)
            # Local ``serialized`` ← self._serialize(value).
            serialized = self._serialize(value)

            # Only when (store.type == "list").
            if store.type == "list":
                # Await ``self._redis.lpush`` and continue once it completes.
                await self._redis.lpush(sk, serialized)
                # Only when (store.max_items).
                if store.max_items:
                    # Await ``self._redis.ltrim`` and continue once it completes.
                    await self._redis.ltrim(sk, 0, store.max_items - 1)

            elif store.type == "queue":
                # Await ``self._redis.rpush`` and continue once it completes.
                await self._redis.rpush(sk, serialized)
                # Only when (store.max_items).
                if store.max_items:
                    # Await ``self._redis.ltrim`` and continue once it completes.
                    await self._redis.ltrim(sk, -store.max_items, -1)

            else:
                # Await ``self._redis.hset`` and continue once it completes.
                await self._redis.hset(sk, key, serialized)
                # Only when (store.max_items).
                if store.max_items:
                    # Local ``fields`` ← await self._redis.hkeys(sk).
                    fields = await self._redis.hkeys(sk)
                    # Local ``overflow`` ← len(fields) - store.max_items.
                    overflow = len(fields) - store.max_items
                    # Only when (overflow > 0).
                    if overflow > 0:
                        # Await ``self._redis.hdel`` and continue once it completes.
                        await self._redis.hdel(sk, *fields[:overflow])

            # Await ``self._apply_ttl`` and continue once it completes.
            await self._apply_ttl(store)
        # On except aioredis.RedisError as exc: recover or re-raise as appropriate.
        except aioredis.RedisError as exc:
            # Log at error so operators can diagnose this path.
            logger.error("redis write error on %s/%s: %s", store.id, key, exc)

    # -- search ---------------------------------------------------------------

    async def search(
        self, store: MemoryStoreConfig, query: str, top_k: int = 5
    ) -> list[Any]:
        """``search``"""
        try:
            # Local ``query_l`` ← query.lower().
            query_l = query.lower()
            # Local ``sk`` ← self._store_key(store).
            sk = self._store_key(store)

            # Only when (store.type in ("list", "queue")).
            if store.type in ("list", "queue"):
                # Local ``raw_items`` ← await self._redis.lrange(sk, 0, -1).
                raw_items = await self._redis.lrange(sk, 0, -1)
                # Local ``items`` ← [self._deserialize(r) for r in raw_items].
                items = [self._deserialize(r) for r in raw_items]
                # Local ``matches`` ← [i for i in items if query_l in str(i).lower()].
                matches = [i for i in items if query_l in str(i).lower()]
                # Hand ``matches[:top_k]`` back to the caller.
                return matches[:top_k]

            # Call ``all_fields: dict[str, str] = await self._redis.hgetall``.
            all_fields: dict[str, str] = await self._redis.hgetall(sk)
            matches: list[Any] = []
            # Loop: for field, raw_val in all_fields.items().
            for field, raw_val in all_fields.items():
                # Only when (query_l in field.lower() or query_l in str(raw_val).lower()).
                if query_l in field.lower() or query_l in str(raw_val).lower():
                    # Call ``matches.append``.
                    matches.append(self._deserialize(raw_val))
                    # Only when (len(matches) >= top_k).
                    if len(matches) >= top_k:
                        break
            # Hand ``matches`` back to the caller.
            return matches
        # On except aioredis.RedisError as exc: recover or re-raise as appropriate.
        except aioredis.RedisError as exc:
            # Log at warning so operators can diagnose this path.
            logger.warning("redis search error on %s: %s", store.id, exc)
            # Hand ``[]`` back to the caller.
            return []

    # -- clear ----------------------------------------------------------------

    async def clear(self, store: MemoryStoreConfig, key: str | None = None) -> None:
        """``clear``"""
        try:
            # Local ``sk`` ← self._store_key(store).
            sk = self._store_key(store)
            # Only when (key is None).
            if key is None:
                # Await ``self._redis.delete`` and continue once it completes.
                await self._redis.delete(sk)
                return

            # Only when (store.type in ("list", "queue")).
            if store.type in ("list", "queue"):
                # Local ``idx`` ← int(key).
                idx = int(key)
                # Local ``sentinel`` ← "__REDIS_BACKEND_TOMBSTONE__".
                sentinel = "__REDIS_BACKEND_TOMBSTONE__"
                # Await ``self._redis.lset`` and continue once it completes.
                await self._redis.lset(sk, idx, sentinel)
                # Await ``self._redis.lrem`` and continue once it completes.
                await self._redis.lrem(sk, 1, sentinel)
            else:
                # Await ``self._redis.hdel`` and continue once it completes.
                await self._redis.hdel(sk, key)
        # On except (aioredis.RedisError, ValueError) as exc: recover or re-raise as appropriate.
        except (aioredis.RedisError, ValueError) as exc:
            # Log at warning so operators can diagnose this path.
            logger.warning("redis clear error on %s/%s: %s", store.id, key, exc)

    # -- dump -----------------------------------------------------------------

    async def dump(self) -> dict[str, Any]:
        """``dump``"""
        result: dict[str, Any] = {}
        # Try the fallible work below.
        try:
            # Local ``pattern`` ← f"{self._prefix}*".
            pattern = f"{self._prefix}*"
            cursor: int | bytes = 0
            keys: list[str] = []
            while True:
                # Call ``cursor, batch = await self._redis.scan``.
                cursor, batch = await self._redis.scan(cursor=cursor, match=pattern, count=200)
                # Call ``keys.extend``.
                keys.extend(batch)
                # Only when (cursor == 0).
                if cursor == 0:
                    break

            # Loop: for key in keys.
            for key in keys:
                # Local ``short`` ← key.removeprefix(self._prefix).
                short = key.removeprefix(self._prefix)
                # Local ``key_type`` ← await self._redis.type(key).
                key_type = await self._redis.type(key)

                # Only when (key_type == "hash").
                if key_type == "hash":
                    # Local ``raw`` ← await self._redis.hgetall(key).
                    raw = await self._redis.hgetall(key)
                    result[short] = {f: self._deserialize(v) for f, v in raw.items()}
                elif key_type == "list":
                    # Local ``raw_items`` ← await self._redis.lrange(key, 0, -1).
                    raw_items = await self._redis.lrange(key, 0, -1)
                    result[short] = [self._deserialize(r) for r in raw_items]
                elif key_type == "string":
                    # Call ``result[short] = self._deserialize``.
                    result[short] = self._deserialize(await self._redis.get(key))
                else:
                    result[short] = f"<unsupported type: {key_type}>"
        # On except aioredis.RedisError as exc: recover or re-raise as appropriate.
        except aioredis.RedisError as exc:
            # Log at error so operators can diagnose this path.
            logger.error("redis dump error: %s", exc)
        # Hand ``result`` back to the caller.
        return result

    # -- lifecycle ------------------------------------------------------------

    async def close(self) -> None:
        """Drain the connection pool and release resources."""
        try:
            # Await ``self._redis.aclose`` and continue once it completes.
            await self._redis.aclose()
            # Await ``self._pool.aclose`` and continue once it completes.
            await self._pool.aclose()
        # On except Exception as exc:  # noqa: BLE001: recover or re-raise as appropriate.
        except Exception as exc:  # noqa: BLE001
            # Log at warning so operators can diagnose this path.
            logger.warning("Error closing Redis connections: %s", exc)
