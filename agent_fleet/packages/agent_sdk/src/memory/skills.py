from __future__ import annotations

"""Module ``agent_sdk/src/memory/skills.py``.

Agent SDK: HTTP task server, runtimes, skills, telemetry publisher, and workspace helpers for first-party agents.
Agent-local memory backends (dict/file/redis/postgres) used by agent runtimes.

Part of the agent SDK server/runtime stack: agents import these helpers to serve tasks over HTTP, run LLM/tool loops, publish telemetry, and persist plan workspaces.

Hand-written source for ``skills.py``. Behavior is unchanged; comments document control-plane / agent-runtime intent for maintainers.
"""


from typing import Any

from .loader import MemoryManager


def make_memory_skills(memory: MemoryManager):
    """``make_memory_skills`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
    async def memory_read(store_id: str, key: str) -> Any:
        """``make_memory_skills`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        return await memory.read(store_id, key)

    async def memory_write(store_id: str, key: str, value: Any) -> dict[str, str]:
        """``memory_read`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        await memory.write(store_id, key, value)
        # Hand ``{"status": "ok"}`` back to the caller.
        return {"status": "ok"}

    async def memory_search(store_id: str, query: str, top_k: int = 5) -> list[Any]:
        """``memory_search`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        return await memory.search(store_id, query, top_k=top_k)

    async def memory_clear(store_id: str, key: str | None = None) -> dict[str, str]:
        """``memory_search`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        await memory.clear(store_id, key=key)
        # Hand ``{"status": "ok"}`` back to the caller.
        return {"status": "ok"}

    # Hand ``{`` back to the caller.
    return {
        "memory_read": memory_read,
        "memory_write": memory_write,
        "memory_search": memory_search,
        "memory_clear": memory_clear,
    }
