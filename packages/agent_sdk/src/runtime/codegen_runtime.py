from __future__ import annotations

"""Module ``agent_sdk/src/runtime/codegen_runtime.py``.

Agent SDK: HTTP task server, runtimes, skills, telemetry publisher, and workspace helpers for first-party agents.
Agent execution runtimes (LangChain, codegen, tool-loop, direct function).

Part of the agent SDK server/runtime stack: agents import these helpers to serve tasks over HTTP, run LLM/tool loops, publish telemetry, and persist plan workspaces.

Hand-written source for ``codegen_runtime.py``. Behavior is unchanged; comments document control-plane / agent-runtime intent for maintainers.
"""


import json
import logging
from typing import Any
from pathlib import Path

from .base import AgentRuntime
from .codegen_runner import CodeExecutionRunner
from ..config import BackendConfig, ExecutionConfig, ReliabilityConfig
from ..contracts import (
    AgentTaskRequest,
    AgentTaskResult,
    ArtifactRef,
    ExecutionTrace,
)
from packages.memory.runtime import MemoryManager
from ..skills.registry import SkillRegistry

# Local ``logger`` ← logging.getLogger(__name__).
logger = logging.getLogger(__name__)


class CodegenRuntime(AgentRuntime):
    """Generate (or receive) Python code and execute in agent container."""

    def __init__(
        self,
        skills: SkillRegistry,
        memory: MemoryManager,
        backend: BackendConfig,
        execution: ExecutionConfig,
        import_paths: list[str] | None = None,
        reliability: ReliabilityConfig | None = None,
    ):
        """``callable``"""
        super().__init__(skills, memory)
        # Bind ``backend`` from backend for later use on this instance.
        self.backend = backend
        # Bind ``execution`` from execution for later use on this instance.
        self.execution = execution
        # Local ``timeout_secs`` ← (reliability.task_timeout_secs if reliability else 120.0).
        timeout_secs = (reliability.task_timeout_secs if reliability else 120.0)
        # Bind ``runner`` from CodeExecutionRunner( for later use on this instance.
        self.runner = CodeExecutionRunner(
            # Local ``skills`` ← skills,.
            skills=skills,
            # Local ``work_dir`` ← execution.work_dir,.
            work_dir=execution.work_dir,
            # Local ``timeout_secs`` ← timeout_secs,.
            timeout_secs=timeout_secs,
            # Local ``prefix`` ← self._load_template(execution.template_prefix),.
            prefix=self._load_template(execution.template_prefix),
            # Local ``suffix`` ← self._load_template(execution.template_suffix),.
            suffix=self._load_template(execution.template_suffix),
            # Local ``import_paths`` ← import_paths or [],.
            import_paths=import_paths or [],
        )

    @staticmethod
    def _load_template(path: str | None) -> str | None:
        """``_load_template``"""
        if not path:
            # Hand ``None`` back to the caller.
            return None
        from pathlib import Path
        # Local ``p`` ← Path(path).
        p = Path(path)
        # Only when (p.exists()).
        if p.exists():
            # Hand ``p.read_text()`` back to the caller.
            return p.read_text()
        # Hand ``None`` back to the caller.
        return None

    async def _generate_code(self, request: AgentTaskRequest) -> str:
        """``_generate_code``"""
        if self.backend.type == "langchain":
            from .langchain_backend import generate_task_code
            # Hand ``await generate_task_code(self.backend, self.skills, request)`` back to the caller.
            return await generate_task_code(self.backend, self.skills, request)

        # Local ``desc`` ← request.description.replace('"', '\\"').
        desc = request.description.replace('"', '\\"')
        # Hand ``f'''`` back to the caller.
        return f'''
def _main():
    # Hand ``{{"success": True, "message": "Completed: {desc}", "artifacts": {{}}}}`` back to the caller.
    return {{"success": True, "message": "Completed: {desc}", "artifacts": {{}}}}
'''

    def _resolve_workspace_root(self, request: AgentTaskRequest) -> str:
        """Extract local workspace root from workspace_uri for subprocess env."""
        uri = request.workspace_uri or ""
        # Only when (uri.startswith("workspace://")).
        if uri.startswith("workspace://"):
            # Local ``stripped`` ← uri.replace("workspace://", "").
            stripped = uri.replace("workspace://", "")
            # Call ``_, _, query = stripped.partition``.
            _, _, query = stripped.partition("?")
            # Loop: for kv in query.split("&").
            for kv in query.split("&"):
                # Only when (kv.startswith("root=")).
                if kv.startswith("root="):
                    # Hand ``kv[len("root="):]`` back to the caller.
                    return kv[len("root="):]
        # Hand ``""`` back to the caller.
        return ""

    async def execute(self, request: AgentTaskRequest) -> AgentTaskResult:
        """``execute``"""
        try:
            # Local ``code`` ← request.inputs.get("code") if request.inputs else None.
            code = request.inputs.get("code") if request.inputs else None
            # Only when (not code).
            if not code:
                # Local ``code`` ← await self._generate_code(request).
                code = await self._generate_code(request)

            # Local ``available_artifacts`` ← [].
            available_artifacts = []
            # Only when (request.context and request.context.available_artifacts).
            if request.context and request.context.available_artifacts:
                # Local ``available_artifacts`` ← [.
                available_artifacts = [
                    ref.model_dump(mode="json") for ref in request.context.available_artifacts
                ]

            ce, traces, raw_refs = await self.runner.run(
                code,
                # Local ``task_id`` ← str(request.task_id),.
                task_id=str(request.task_id),
                # Local ``workspace_root`` ← self._resolve_workspace_root(request),.
                workspace_root=self._resolve_workspace_root(request),
                # Local ``plan_id`` ← str(request.plan_id or 0),.
                plan_id=str(request.plan_id or 0),
                # Local ``available_artifacts`` ← available_artifacts,.
                available_artifacts=available_artifacts,
            )
            # Loop: for sc in ce.skill_calls.
            for sc in ce.skill_calls:
                traces.append(
                    # Call ``ExecutionTrace``.
                    ExecutionTrace(trace_type="skill_call", payload=sc.model_dump(mode="json"))
                )

            # Local ``artifact_refs`` ← [].
            artifact_refs = []
            # Loop: for rd in raw_refs.
            for rd in raw_refs:
                # Only when (isinstance(rd, dict)).
                if isinstance(rd, dict):
                    # Try the fallible work below.
                    try:
                        # Call ``artifact_refs.append``.
                        artifact_refs.append(ArtifactRef(**rd))
                    # On except Exception: recover or re-raise as appropriate.
                    except Exception:
                        pass

            # Only when (isinstance(ce.return_value, dict)).
            if isinstance(ce.return_value, dict):
                # Local ``rv`` ← ce.return_value.
                rv = ce.return_value
                # Hand ``AgentTaskResult(`` back to the caller.
                return AgentTaskResult(
                    # Local ``success`` ← rv.get("success", ce.success),.
                    success=rv.get("success", ce.success),
                    # Local ``message`` ← rv.get("message", ""),.
                    message=rv.get("message", ""),
                    # Local ``artifacts`` ← rv.get("artifacts", {}),.
                    artifacts=rv.get("artifacts", {}),
                    # Local ``artifact_refs`` ← artifact_refs,.
                    artifact_refs=artifact_refs,
                    # Local ``traces`` ← traces,.
                    traces=traces,
                    # Local ``replan`` ← rv.get("replan", False),.
                    replan=rv.get("replan", False),
                    # Local ``error`` ← rv.get("error"),.
                    error=rv.get("error"),
                )

            # Hand ``AgentTaskResult(`` back to the caller.
            return AgentTaskResult(
                # Local ``success`` ← ce.success,.
                success=ce.success,
                # Local ``message`` ← ce.stdout or ce.stderr or "code execution finished",.
                message=ce.stdout or ce.stderr or "code execution finished",
                # Local ``artifacts`` ← {"return_value": ce.return_value},.
                artifacts={"return_value": ce.return_value},
                # Local ``artifact_refs`` ← artifact_refs,.
                artifact_refs=artifact_refs,
                # Local ``traces`` ← traces,.
                traces=traces,
                # Local ``error`` ← None if ce.success else ce.stderr,.
                error=None if ce.success else ce.stderr,
            )
        # On except Exception as exc: recover or re-raise as appropriate.
        except Exception as exc:
            # Log at exception so operators can diagnose this path.
            logger.exception("Codegen execution failed")
            # Hand ``AgentTaskResult(`` back to the caller.
            return AgentTaskResult(
                # Local ``success`` ← False,.
                success=False,
                # Local ``message`` ← str(exc),.
                message=str(exc),
                # Local ``error`` ← str(exc),.
                error=str(exc),
                # Local ``replan`` ← True,.
                replan=True,
            )
