from __future__ import annotations

"""Module ``agent_sdk/src/runtime/base.py``.

Agent SDK: HTTP task server, runtimes, skills, telemetry publisher, and workspace helpers for first-party agents.
Agent execution runtimes (LangChain, codegen, tool-loop, direct function).

Part of the agent SDK server/runtime stack: agents import these helpers to serve tasks over HTTP, run LLM/tool loops, publish telemetry, and persist plan workspaces.

Hand-written source for ``base.py``. Behavior is unchanged; comments document control-plane / agent-runtime intent for maintainers.
"""


from abc import ABC, abstractmethod

from ..models import AgentTaskRequest, AgentTaskResult
from ..skills.registry import SkillRegistry
from ..memory.loader import MemoryManager


class AgentRuntime(ABC):
    """``AgentRuntime`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
    def __init__(self, skills: SkillRegistry, memory: MemoryManager):
        """``AgentRuntime`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        self.skills = skills
        # Bind ``memory`` from memory for later use on this instance.
        self.memory = memory

    @abstractmethod
    async def execute(self, request: AgentTaskRequest) -> AgentTaskResult:
        """``execute`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        raise NotImplementedError
