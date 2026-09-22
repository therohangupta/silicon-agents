from __future__ import annotations

"""Module ``agent_sdk/src/memory/loader.py``.

Agent SDK: HTTP task server, runtimes, skills, telemetry publisher, and workspace helpers for first-party agents.
Agent-local memory backends (dict/file/redis/postgres) used by agent runtimes.

Part of the agent SDK server/runtime stack: agents import these helpers to serve tasks over HTTP, run LLM/tool loops, publish telemetry, and persist plan workspaces.

Hand-written source for ``loader.py``. Behavior is unchanged; comments document control-plane / agent-runtime intent for maintainers.
"""


from typing import Any

from .base import MemoryBackend
from .backends.dict_backend import DictMemoryBackend
from ..models import MemoryConfig, MemoryStoreConfig


class MemoryManager:
    """Per-store persistence: each store can use ephemeral/redis/file/postgres."""

    def __init__(self, config: MemoryConfig):
        """``MemoryManager`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        self.config = config
        self.stores: dict[str, MemoryStoreConfig] = {
            store.id: store for store in config.stores
        }
        self._backends: dict[str, MemoryBackend] = {}
        # Loop: for store in config.stores.
        for store in config.stores:
            # Call ``self._backends[store.id] = self._make_backend``.
            self._backends[store.id] = self._make_backend(store)

    def _make_backend(self, store: MemoryStoreConfig) -> MemoryBackend:
        """``_make_backend`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        persistence = store.persistence
        # Local ``cfg`` ← store.config or {}.
        cfg = store.config or {}

        # Only when (persistence == "ephemeral").
        if persistence == "ephemeral":
            # Hand ``DictMemoryBackend(cfg)`` back to the caller.
            return DictMemoryBackend(cfg)
        # Only when (persistence == "redis").
        if persistence == "redis":
            from .backends.redis_backend import RedisMemoryBackend
            # Hand ``RedisMemoryBackend(cfg)`` back to the caller.
            return RedisMemoryBackend(cfg)
        # Only when (persistence == "file").
        if persistence == "file":
            from .backends.file_backend import FileMemoryBackend
            # Hand ``FileMemoryBackend(cfg)`` back to the caller.
            return FileMemoryBackend(cfg)
        # Only when (persistence == "postgres").
        if persistence == "postgres":
            from .backends.postgres_backend import PostgresMemoryBackend
            # Hand ``PostgresMemoryBackend(cfg)`` back to the caller.
            return PostgresMemoryBackend(cfg)
        # Raise ``ValueError`` to signal this failure mode to callers.
        raise ValueError(f"Unsupported persistence: {persistence}")

    def _backend(self, store_id: str) -> MemoryBackend:
        """``_backend`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        if store_id not in self._backends:
            # Local ``store`` ← MemoryStoreConfig(id=store_id).
            store = MemoryStoreConfig(id=store_id)
            self.stores[store_id] = store
            # Call ``self._backends[store_id] = DictMemoryBackend``.
            self._backends[store_id] = DictMemoryBackend({})
        # Hand ``self._backends[store_id]`` back to the caller.
        return self._backends[store_id]

    def _store(self, store_id: str) -> MemoryStoreConfig:
        """``_store`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        if store_id not in self.stores:
            # Call ``self.stores[store_id] = MemoryStoreConfig``.
            self.stores[store_id] = MemoryStoreConfig(id=store_id)
        # Hand ``self.stores[store_id]`` back to the caller.
        return self.stores[store_id]

    async def read(self, store_id: str, key: str) -> Any:
        """``read`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        return await self._backend(store_id).read(self._store(store_id), key)

    async def write(self, store_id: str, key: str, value: Any) -> None:
        """``read`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        await self._backend(store_id).write(self._store(store_id), key, value)

    async def search(self, store_id: str, query: str, top_k: int = 5) -> list[Any]:
        """``write`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        return await self._backend(store_id).search(
            self._store(store_id), query, top_k=top_k
        )

    async def clear(self, store_id: str, key: str | None = None) -> None:
        """``clear`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        await self._backend(store_id).clear(self._store(store_id), key=key)

    async def dump(self) -> dict[str, Any]:
        """``clear`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        result: dict[str, Any] = {}
        # Loop: for store_id, backend in self._backends.items().
        for store_id, backend in self._backends.items():
            # Call ``result[store_id] = await backend.dump``.
            result[store_id] = await backend.dump()
        # Hand ``result`` back to the caller.
        return result

    async def close(self) -> None:
        """``close`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        for backend in self._backends.values():
            # Only when (hasattr(backend, "close")).
            if hasattr(backend, "close"):
                # Await ``backend.close`` and continue once it completes.
                await backend.close()
