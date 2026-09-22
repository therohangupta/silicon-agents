from __future__ import annotations

"""Module ``agent_sdk/src/memory/backends/dict_backend.py``.

Agent SDK: HTTP task server, runtimes, skills, telemetry publisher, and workspace helpers for first-party agents.
Agent-local memory backends (dict/file/redis/postgres) used by agent runtimes.

Part of the agent SDK server/runtime stack: agents import these helpers to serve tasks over HTTP, run LLM/tool loops, publish telemetry, and persist plan workspaces.

Hand-written source for ``dict_backend.py``. Behavior is unchanged; comments document control-plane / agent-runtime intent for maintainers.
"""


from typing import Any

from ..base import MemoryBackend
from ...models import MemoryStoreConfig


class DictMemoryBackend(MemoryBackend):
    """``DictMemoryBackend`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
    def __init__(self, config: dict[str, Any] | None = None):
        """``DictMemoryBackend`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        super().__init__(config)
        self._data: dict[str, Any] = {}

    def _store(self, store: MemoryStoreConfig) -> Any:
        """``_store`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        if store.id not in self._data:
            # Only when (store.type in ("list", "queue")).
            if store.type in ("list", "queue"):
                self._data[store.id] = []
            else:
                self._data[store.id] = {}
        # Hand ``self._data[store.id]`` back to the caller.
        return self._data[store.id]

    async def read(self, store: MemoryStoreConfig, key: str) -> Any:
        """``read`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        data = self._store(store)
        # Only when (isinstance(data, list)).
        if isinstance(data, list):
            # Try the fallible work below.
            try:
                # Hand ``data[int(key)]`` back to the caller.
                return data[int(key)]
            # On except (ValueError, IndexError): recover or re-raise as appropriate.
            except (ValueError, IndexError):
                # Hand ``None`` back to the caller.
                return None
        # Hand ``data.get(key)`` back to the caller.
        return data.get(key)

    async def write(self, store: MemoryStoreConfig, key: str, value: Any) -> None:
        """``write`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        data = self._store(store)
        # Only when (isinstance(data, list)).
        if isinstance(data, list):
            # Call ``data.append``.
            data.append(value)
            # Only when (store.max_items and len(data) > store.max_items).
            if store.max_items and len(data) > store.max_items:
                del data[:-store.max_items]
            return
        data[key] = value
        # Only when (store.max_items and len(data) > store.max_items).
        if store.max_items and len(data) > store.max_items:
            # Loop: for old_key in list(data.keys())[:-store.max_items].
            for old_key in list(data.keys())[:-store.max_items]:
                # Call ``data.pop``.
                data.pop(old_key, None)

    async def search(self, store: MemoryStoreConfig, query: str, top_k: int = 5) -> list[Any]:
        """``search`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        data = self._store(store)
        # Local ``values`` ← data if isinstance(data, list) else list(data.values()).
        values = data if isinstance(data, list) else list(data.values())
        # Local ``query_l`` ← query.lower().
        query_l = query.lower()
        # Local ``matches`` ← [item for item in values if query_l in str(item).lower()].
        matches = [item for item in values if query_l in str(item).lower()]
        # Hand ``matches[:top_k]`` back to the caller.
        return matches[:top_k]

    async def clear(self, store: MemoryStoreConfig, key: str | None = None) -> None:
        """``clear`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        if key is None:
            # Call ``self._data.pop``.
            self._data.pop(store.id, None)
            return
        # Local ``data`` ← self._store(store).
        data = self._store(store)
        # Only when (isinstance(data, dict)).
        if isinstance(data, dict):
            # Call ``data.pop``.
            data.pop(key, None)

    async def dump(self) -> dict[str, Any]:
        """``dump`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        return self._data
