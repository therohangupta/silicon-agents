from __future__ import annotations

"""Module ``agent_sdk/src/skills/base.py``.

Agent SDK: HTTP task server, runtimes, skills, telemetry publisher, and workspace helpers for first-party agents.
Skill/tool registration and base decorators for agent capabilities.

Part of the agent SDK server/runtime stack: agents import these helpers to serve tasks over HTTP, run LLM/tool loops, publish telemetry, and persist plan workspaces.

Hand-written source for ``base.py``. Behavior is unchanged; comments document control-plane / agent-runtime intent for maintainers.
"""


from collections.abc import Callable
from typing import Any


def tool(description: str = "", constraints: dict[str, Any] | None = None):
    """``tool``"""
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        """``tool``"""
        setattr(func, "_agent_tool", True)
        # Call ``setattr``.
        setattr(func, "_agent_tool_description", description or (func.__doc__ or "").strip())
        # Call ``setattr``.
        setattr(func, "_agent_tool_constraints", constraints or {})
        # Hand ``func`` back to the caller.
        return func
    # Hand ``decorator`` back to the caller.
    return decorator
