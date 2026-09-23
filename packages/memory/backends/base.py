from __future__ import annotations

"""Module ``agent_sdk/src/memory/base.py``.

Agent SDK: HTTP task server, runtimes, skills, telemetry publisher, and workspace helpers for first-party agents.
Agent-local memory backends (dict/file/redis/postgres) used by agent runtimes.

Part of the agent SDK server/runtime stack: agents import these helpers to serve tasks over HTTP, run LLM/tool loops, publish telemetry, and persist plan workspaces.

Hand-written source for ``base.py``. Behavior is unchanged; comments document control-plane / agent-runtime intent for maintainers.
"""


from abc import ABC, abstractmethod
from typing import Any

from packages.memory.config import MemoryStoreConfig


class MemoryBackend(ABC):
    """``MemoryBackend``"""
    def __init__(self, config: dict[str, Any] | None = None):
        """``MemoryBackend``"""
        self.config = config or {}

    @abstractmethod
    async def read(self, store: MemoryStoreConfig, key: str) -> Any:
        """``read``"""
        raise NotImplementedError

    @abstractmethod
    async def write(self, store: MemoryStoreConfig, key: str, value: Any) -> None:
        """``write``"""
        raise NotImplementedError

    @abstractmethod
    async def search(self, store: MemoryStoreConfig, query: str, top_k: int = 5) -> list[Any]:
        """``search``"""
        raise NotImplementedError

    @abstractmethod
    async def clear(self, store: MemoryStoreConfig, key: str | None = None) -> None:
        """``clear``"""
        raise NotImplementedError

    @abstractmethod
    async def dump(self) -> dict[str, Any]:
        """``dump``"""
        raise NotImplementedError
