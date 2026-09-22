from __future__ import annotations

"""Module ``agent_sdk/src/runtime/direct_function_runtime.py``.

Agent SDK: HTTP task server, runtimes, skills, telemetry publisher, and workspace helpers for first-party agents.
Agent execution runtimes (LangChain, codegen, tool-loop, direct function).

Part of the agent SDK server/runtime stack: agents import these helpers to serve tasks over HTTP, run LLM/tool loops, publish telemetry, and persist plan workspaces.

Hand-written source for ``direct_function_runtime.py``. Behavior is unchanged; comments document control-plane / agent-runtime intent for maintainers.
"""


import importlib
import inspect

from .base import AgentRuntime
from ..models import AgentTaskRequest, AgentTaskResult, ExecutionTrace


class DirectFunctionRuntime(AgentRuntime):
    """Deterministic execute(request) in tools module."""

    def __init__(self, skills, memory, module_name: str = "tools"):
        """``DirectFunctionRuntime`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        super().__init__(skills, memory)
        # Bind ``module_name`` from module_name for later use on this instance.
        self.module_name = module_name
        # Bind ``module`` from importlib.import_module(module_name) for later use on this instance.
        self.module = importlib.import_module(module_name)

    async def execute(self, request: AgentTaskRequest) -> AgentTaskResult:
        """``execute`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        if not hasattr(self.module, "execute"):
            # Hand ``AgentTaskResult(`` back to the caller.
            return AgentTaskResult(
                # Local ``success`` ← False,.
                success=False,
                # Local ``message`` ← f"{self.module_name}.execute is not defined",.
                message=f"{self.module_name}.execute is not defined",
                # Local ``error`` ← "missing_execute",.
                error="missing_execute",
            )
        # Local ``result`` ← self.module.execute(request).
        result = self.module.execute(request)
        # Only when (inspect.isawaitable(result)).
        if inspect.isawaitable(result):
            # Local ``result`` ← await result.
            result = await result
        # Only when (isinstance(result, AgentTaskResult)).
        if isinstance(result, AgentTaskResult):
            # Hand ``result`` back to the caller.
            return result
        # Only when (isinstance(result, dict)).
        if isinstance(result, dict):
            # Hand ``AgentTaskResult(**result)`` back to the caller.
            return AgentTaskResult(**result)
        # Hand ``AgentTaskResult(`` back to the caller.
        return AgentTaskResult(
            # Local ``success`` ← True,.
            success=True,
            # Local ``message`` ← str(result),.
            message=str(result),
            # Local ``artifacts`` ← {"result": result},.
            artifacts={"result": result},
        )
