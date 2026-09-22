from __future__ import annotations

"""Module ``agent_sdk/src/runtime/tool_loop_runtime.py``.

Agent SDK: HTTP task server, runtimes, skills, telemetry publisher, and workspace helpers for first-party agents.
Agent execution runtimes (LangChain, codegen, tool-loop, direct function).

Part of the agent SDK server/runtime stack: agents import these helpers to serve tasks over HTTP, run LLM/tool loops, publish telemetry, and persist plan workspaces.

Hand-written source for ``tool_loop_runtime.py``. Behavior is unchanged; comments document control-plane / agent-runtime intent for maintainers.
"""


from .base import AgentRuntime
from .langchain_runtime import LangChainRuntime
from ..models import AgentTaskRequest, AgentTaskResult, BackendConfig, ExecutionTrace
from ..memory.loader import MemoryManager
from ..skills.registry import SkillRegistry


class ToolLoopRuntime(AgentRuntime):
    """Optional ReAct-style tool-calling loop."""

    def __init__(
        self,
        skills: SkillRegistry,
        memory: MemoryManager,
        backend: BackendConfig,
    ):
        """``callable`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        super().__init__(skills, memory)
        # Bind ``_inner`` from LangChainRuntime(skills, memory, backend) for later use on this instance.
        self._inner = LangChainRuntime(skills, memory, backend)

    async def execute(self, request: AgentTaskRequest) -> AgentTaskResult:
        """``execute`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        result = await self._inner.execute(request)
        traces: list[ExecutionTrace] = []
        # Loop: for sc in result.skill_calls.
        for sc in result.skill_calls:
            traces.append(
                # Call ``ExecutionTrace``.
                ExecutionTrace(trace_type="skill_call", payload=sc.model_dump(mode="json"))
            )
        # Loop: for mo in result.memory_updates.
        for mo in result.memory_updates:
            traces.append(
                # Call ``ExecutionTrace``.
                ExecutionTrace(trace_type="memory_op", payload=mo.model_dump(mode="json"))
            )
        result.traces = traces
        # Hand ``result`` back to the caller.
        return result
