from __future__ import annotations

"""Module ``agent_sdk/src/memory/backends/file_backend.py``.

Agent SDK: HTTP task server, runtimes, skills, telemetry publisher, and workspace helpers for first-party agents.
Agent-local memory backends (dict/file/redis/postgres) used by agent runtimes.

Part of the agent SDK server/runtime stack: agents import these helpers to serve tasks over HTTP, run LLM/tool loops, publish telemetry, and persist plan workspaces.

Hand-written source for ``file_backend.py``. Behavior is unchanged; comments document control-plane / agent-runtime intent for maintainers.
"""


import json
import os
from pathlib import Path
from typing import Any

from .base import MemoryBackend
from packages.memory.config import MemoryStoreConfig


class FileMemoryBackend(MemoryBackend):
    """File-backed memory (JSON per store on a Docker volume)."""

    def __init__(self, config: dict[str, Any] | None = None):
        """``FileMemoryBackend``"""
        super().__init__(config)
        # Bind ``_root`` from Path(self.config.get("path", "/data/agent_memory")) for later use on this instance.
        self._root = Path(self.config.get("path", "/data/agent_memory"))
        # Call ``self._root.mkdir``.
        self._root.mkdir(parents=True, exist_ok=True)

    def _path(self, store: MemoryStoreConfig) -> Path:
        """``_path``"""
        return self._root / f"{store.id}.json"

    def _load(self, store: MemoryStoreConfig) -> Any:
        """``_path``"""
        p = self._path(store)
        # Only when (not p.exists()).
        if not p.exists():
            # Hand ``[] if store.type in ("list", "queue") else {}`` back to the caller.
            return [] if store.type in ("list", "queue") else {}
        # Hold ``p.open()`` for the duration of the indented block.
        with p.open() as fh:
            # Hand ``json.load(fh)`` back to the caller.
            return json.load(fh)

    def _save(self, store: MemoryStoreConfig, data: Any) -> None:
        """``_save``"""
        p = self._path(store)
        # Hold ``p.open("w")`` for the duration of the indented block.
        with p.open("w") as fh:
            # Call ``json.dump``.
            json.dump(data, fh)

    async def read(self, store: MemoryStoreConfig, key: str) -> Any:
        """``read``"""
        data = self._load(store)
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
        """``write``"""
        data = self._load(store)
        # Only when (isinstance(data, list)).
        if isinstance(data, list):
            # Call ``data.append``.
            data.append(value)
            # Only when (store.max_items and len(data) > store.max_items).
            if store.max_items and len(data) > store.max_items:
                # Local ``data`` ← data[-store.max_items:].
                data = data[-store.max_items:]
        else:
            data[key] = value
            # Only when (store.max_items and len(data) > store.max_items).
            if store.max_items and len(data) > store.max_items:
                # Loop: for old_key in list(data.keys())[:-store.max_items].
                for old_key in list(data.keys())[:-store.max_items]:
                    # Call ``data.pop``.
                    data.pop(old_key, None)
        # Call ``self._save``.
        self._save(store, data)

    async def search(self, store: MemoryStoreConfig, query: str, top_k: int = 5) -> list[Any]:
        """``search``"""
        data = self._load(store)
        # Local ``values`` ← data if isinstance(data, list) else list(data.values()).
        values = data if isinstance(data, list) else list(data.values())
        # Local ``query_l`` ← query.lower().
        query_l = query.lower()
        # Local ``matches`` ← [item for item in values if query_l in str(item).lower()].
        matches = [item for item in values if query_l in str(item).lower()]
        # Hand ``matches[:top_k]`` back to the caller.
        return matches[:top_k]

    async def clear(self, store: MemoryStoreConfig, key: str | None = None) -> None:
        """``clear``"""
        if key is None:
            # Local ``p`` ← self._path(store).
            p = self._path(store)
            # Only when (p.exists()).
            if p.exists():
                # Call ``os.remove``.
                os.remove(p)
            return
        # Local ``data`` ← self._load(store).
        data = self._load(store)
        # Only when (isinstance(data, dict)).
        if isinstance(data, dict):
            # Call ``data.pop``.
            data.pop(key, None)
            # Call ``self._save``.
            self._save(store, data)

    async def dump(self) -> dict[str, Any]:
        """``dump``"""
        result: dict[str, Any] = {}
        # Loop: for p in self._root.glob("*.json").
        for p in self._root.glob("*.json"):
            # Hold ``p.open()`` for the duration of the indented block.
            with p.open() as fh:
                # Call ``result[p.stem] = json.load``.
                result[p.stem] = json.load(fh)
        # Hand ``result`` back to the caller.
        return result
