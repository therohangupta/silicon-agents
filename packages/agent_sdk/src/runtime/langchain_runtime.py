from __future__ import annotations

"""Module ``agent_sdk/src/runtime/langchain_runtime.py``.

Agent SDK: HTTP task server, runtimes, skills, telemetry publisher, and workspace helpers for first-party agents.
Agent execution runtimes (LangChain, codegen, tool-loop, direct function).

Part of the agent SDK server/runtime stack: agents import these helpers to serve tasks over HTTP, run LLM/tool loops, publish telemetry, and persist plan workspaces.

Hand-written source for ``langchain_runtime.py``. Behavior is unchanged; comments document control-plane / agent-runtime intent for maintainers.
"""


import asyncio
import json
import logging
import os
import traceback
from pathlib import Path
from typing import Any

from .base import AgentRuntime
from ..models import (
    AgentTaskRequest,
    AgentTaskResult,
    BackendConfig,
    ExecutionTrace,
    MemoryOp,
    SkillCall,
)
from ..memory.loader import MemoryManager
from ..skills.registry import SkillRegistry

# Local ``logger`` ← logging.getLogger(__name__).
logger = logging.getLogger(__name__)

_PROVIDER_CLASSES: dict[str, tuple[str, str]] = {
    "openai": ("langchain_openai", "ChatOpenAI"),
    "anthropic": ("langchain_anthropic", "ChatAnthropic"),
    "ollama": ("langchain_ollama", "ChatOllama"),
    "azure": ("langchain_openai", "AzureChatOpenAI"),
    "google": ("langchain_google_genai", "ChatGoogleGenerativeAI"),
}


def _import_llm_class(provider: str) -> type:
    """``_import_llm_class`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
    if provider not in _PROVIDER_CLASSES:
        # Raise ``ValueError`` to signal this failure mode to callers.
        raise ValueError(
            f"Unsupported LLM provider '{provider}'. "
            f"Supported: {', '.join(sorted(_PROVIDER_CLASSES))}"
        )
    module_path, class_name = _PROVIDER_CLASSES[provider]
    # Try the fallible work below.
    try:
        import importlib
        # Local ``mod`` ← importlib.import_module(module_path).
        mod = importlib.import_module(module_path)
    # On except ImportError as exc: recover or re-raise as appropriate.
    except ImportError as exc:
        # Raise ``ImportError`` to signal this failure mode to callers.
        raise ImportError(
            f"Provider '{provider}' requires package '{module_path}'. "
            f"Install it with: pip install {module_path}"
        ) from exc
    # Hand ``getattr(mod, class_name)`` back to the caller.
    return getattr(mod, class_name)


def _resolve_system_prompt(raw: str | None) -> str:
    """Return prompt text. If *raw* looks like a file path, read it."""
    if not raw:
        # Hand ``""`` back to the caller.
        return ""
    # Local ``candidate`` ← Path(raw).
    candidate = Path(raw)
    # Only when (candidate.suffix in {".prompt", ".txt", ".md"} and candidate.exists()).
    if candidate.suffix in {".prompt", ".txt", ".md"} and candidate.exists():
        # Hand ``candidate.read_text().strip()`` back to the caller.
        return candidate.read_text().strip()
    # Only when (os.path.isfile(raw)).
    if os.path.isfile(raw):
        # Hand ``Path(raw).read_text().strip()`` back to the caller.
        return Path(raw).read_text().strip()
    # Hand ``raw`` back to the caller.
    return raw


def _build_system_message(system_prompt: str, request: AgentTaskRequest) -> str:
    """``_build_system_message`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
    parts: list[str] = []
    # Only when (system_prompt).
    if system_prompt:
        # Call ``parts.append``.
        parts.append(system_prompt)

    # Local ``ctx`` ← request.context.
    ctx = request.context
    # Only when (ctx).
    if ctx:
        context_lines: list[str] = []
        # Only when (ctx.plan_summary).
        if ctx.plan_summary:
            # Call ``context_lines.append``.
            context_lines.append(f"Plan: {ctx.plan_summary}")
        # Only when (ctx.completed_tasks).
        if ctx.completed_tasks:
            # Local ``summaries`` ← "; ".join(.
            summaries = "; ".join(
                f"[{t.task_id}] {t.description} -> {t.result_summary}"
                # Loop: for t in ctx.completed_tasks.
                for t in ctx.completed_tasks
            )
            # Call ``context_lines.append``.
            context_lines.append(f"Completed tasks: {summaries}")
        # Only when (ctx.world_facts).
        if ctx.world_facts:
            # Call ``context_lines.append``.
            context_lines.append("Known facts:\n" + "\n".join(f"- {f}" for f in ctx.world_facts))
        # Only when (ctx.available_artifacts).
        if ctx.available_artifacts:
            # Local ``artifact_lines`` ← [].
            artifact_lines = []
            # Loop: for ref in ctx.available_artifacts.
            for ref in ctx.available_artifacts:
                # Local ``size_str`` ← f"{ref.size_bytes:,} bytes" if ref.size_bytes else "unknown size".
                size_str = f"{ref.size_bytes:,} bytes" if ref.size_bytes else "unknown size"
                # Local ``schema_str`` ← f" | schema: {json.dumps(ref.schema_hint)}" if ref.schema_hint el….
                schema_str = f" | schema: {json.dumps(ref.schema_hint)}" if ref.schema_hint else ""
                artifact_lines.append(
                    f"- [{ref.producer_task_id}/{ref.producer_agent_id}] "
                    f"{ref.name} ({ref.format}, {size_str}{schema_str})\n"
                    f"  \"{ref.description}\"\n"
                    f"  Use load_artifact(name=\"{ref.name}\", producer_task_id=\"{ref.producer_task_id}\") to access"
                )
            # Call ``context_lines.append``.
            context_lines.append("Available artifacts from prior tasks:\n" + "\n".join(artifact_lines))
        # Only when (ctx.agent_memory_hint).
        if ctx.agent_memory_hint:
            # Call ``context_lines.append``.
            context_lines.append(f"Memory hint: {ctx.agent_memory_hint}")
        # Only when (context_lines).
        if context_lines:
            # Call ``parts.append``.
            parts.append("## Execution Context\n" + "\n".join(context_lines))

    # Only when (request.inputs).
    if request.inputs:
        parts.append(
            "## Provided Inputs\n"
            # Call ``+ "\n".join``.
            + "\n".join(f"- {k}: {json.dumps(v)}" for k, v in request.inputs.items())
        )

    # Hand ``"\n\n".join(parts)`` back to the caller.
    return "\n\n".join(parts)


class LangChainRuntime(AgentRuntime):
    """Provider-agnostic LLM runtime backed by a LangChain tool-calling agent."""

    def __init__(
        self,
        skills: SkillRegistry,
        memory: MemoryManager,
        backend_config: BackendConfig,
        system_prompt: str = "",
    ):
        """``callable`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        super().__init__(skills, memory)
        # Bind ``backend_config`` from backend_config for later use on this instance.
        self.backend_config = backend_config
        # Bind ``system_prompt`` from system_prompt for later use on this instance.
        self.system_prompt = system_prompt

    # ------------------------------------------------------------------
    # Tool conversion helpers
    # ------------------------------------------------------------------

    def _build_skill_tools(self) -> tuple[list[Any], dict[str, list[SkillCall]]]:
        """Wrap each registered skill as a LangChain StructuredTool.

        Returns the list of tools and a shared mutable dict that accumulates
        SkillCall records produced during execution.
        """
        from langchain_core.tools import StructuredTool

        calls: dict[str, list[SkillCall]] = {"items": []}
        tools: list[Any] = []

        # Loop: for spec in self.skills.specs.
        for spec in self.skills.specs:
            # Local ``registry`` ← self.skills.
            registry = self.skills

            def _make_fn(skill_id: str):
                """Factory to capture *skill_id* by value."""
                def invoke(**kwargs: Any) -> str:
                    """``_make_fn`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
                    loop = asyncio.get_event_loop()
                    # Call ``sc: SkillCall = loop.run_until_complete``.
                    sc: SkillCall = loop.run_until_complete(registry.call(skill_id, **kwargs))
                    # Call ``calls["items"].append``.
                    calls["items"].append(sc)
                    # Try the fallible work below.
                    try:
                        # Hand ``json.dumps(sc.result, default=str)`` back to the caller.
                        return json.dumps(sc.result, default=str)
                    # On except (TypeError, ValueError): recover or re-raise as appropriate.
                    except (TypeError, ValueError):
                        # Hand ``str(sc.result)`` back to the caller.
                        return str(sc.result)
                # Hand ``invoke`` back to the caller.
                return invoke

            # Local ``tool`` ← StructuredTool.from_function(.
            tool = StructuredTool.from_function(
                # Local ``func`` ← _make_fn(spec.id),.
                func=_make_fn(spec.id),
                # Local ``name`` ← spec.id,.
                name=spec.id,
                # Local ``description`` ← spec.description or f"Invoke the {spec.id} skill.",.
                description=spec.description or f"Invoke the {spec.id} skill.",
            )
            # Call ``tools.append``.
            tools.append(tool)

        # Hand ``tools, calls`` back to the caller.
        return tools, calls

    def _build_memory_tools(self) -> tuple[list[Any], dict[str, list[MemoryOp]]]:
        """Expose memory_read / memory_write / memory_search as LangChain tools."""
        from langchain_core.tools import StructuredTool

        ops: dict[str, list[MemoryOp]] = {"items": []}
        # Local ``mem`` ← self.memory.
        mem = self.memory

        def memory_read(store_id: str, key: str) -> str:
            """Read a value from a named memory store."""
            loop = asyncio.get_event_loop()
            # Local ``result`` ← loop.run_until_complete(mem.read(store_id, key)).
            result = loop.run_until_complete(mem.read(store_id, key))
            # Call ``ops["items"].append``.
            ops["items"].append(MemoryOp(op="read", store_id=store_id, key=key))
            # Try the fallible work below.
            try:
                # Hand ``json.dumps(result, default=str)`` back to the caller.
                return json.dumps(result, default=str)
            # On except (TypeError, ValueError): recover or re-raise as appropriate.
            except (TypeError, ValueError):
                # Hand ``str(result)`` back to the caller.
                return str(result)

        def memory_write(store_id: str, key: str, value: str) -> str:
            """Write a value to a named memory store."""
            loop = asyncio.get_event_loop()
            # Call ``loop.run_until_complete``.
            loop.run_until_complete(mem.write(store_id, key, value))
            # Call ``ops["items"].append``.
            ops["items"].append(MemoryOp(op="write", store_id=store_id, key=key, value=value))
            # Hand ``f"Stored '{key}' in '{store_id}'."`` back to the caller.
            return f"Stored '{key}' in '{store_id}'."

        def memory_search(store_id: str, query: str, top_k: int = 5) -> str:
            """Semantic search over a named memory store."""
            loop = asyncio.get_event_loop()
            # Local ``results`` ← loop.run_until_complete(mem.search(store_id, query, top_k=top_k)).
            results = loop.run_until_complete(mem.search(store_id, query, top_k=top_k))
            # Call ``ops["items"].append``.
            ops["items"].append(MemoryOp(op="search", store_id=store_id, key=query))
            # Try the fallible work below.
            try:
                # Hand ``json.dumps(results, default=str)`` back to the caller.
                return json.dumps(results, default=str)
            # On except (TypeError, ValueError): recover or re-raise as appropriate.
            except (TypeError, ValueError):
                # Hand ``str(results)`` back to the caller.
                return str(results)

        # Local ``tools`` ← [.
        tools = [
            StructuredTool.from_function(func=memory_read, name="memory_read", description="Read a value from a named memory store."),
            StructuredTool.from_function(func=memory_write, name="memory_write", description="Write a value to a named memory store."),
            StructuredTool.from_function(func=memory_search, name="memory_search", description="Semantic search over a named memory store."),
        ]
        # Hand ``tools, ops`` back to the caller.
        return tools, ops

    # ------------------------------------------------------------------
    # Workspace tools (load artifacts from prior tasks)
    # ------------------------------------------------------------------

    def _build_workspace_tools(self, request: AgentTaskRequest) -> list[Any]:
        """Expose load_artifact as a LangChain tool when artifacts are available."""
        ctx = request.context
        # Only when (not ctx or not ctx.available_artifacts).
        if not ctx or not ctx.available_artifacts:
            # Hand ``[]`` back to the caller.
            return []

        # Try the fallible work below.
        try:
            from langchain_core.tools import StructuredTool
        # On except ImportError: recover or re-raise as appropriate.
        except ImportError:
            # Hand ``[]`` back to the caller.
            return []

        from ..workspace.plan_workspace import PlanWorkspace
        # Local ``workspace`` ← PlanWorkspace.from_request(request).
        workspace = PlanWorkspace.from_request(request)
        # Local ``available`` ← {(ref.name, ref.producer_task_id): ref for ref in ctx.available_a….
        available = {(ref.name, ref.producer_task_id): ref for ref in ctx.available_artifacts}

        def load_artifact(name: str, producer_task_id: str = "") -> str:
            """Load an artifact published by a prior task. Returns the data as a string."""
            matching = None
            # Loop: for (n, ptid), ref in available.items().
            for (n, ptid), ref in available.items():
                # Only when (n == name and (not producer_task_id or ptid == producer_task_id)).
                if n == name and (not producer_task_id or ptid == producer_task_id):
                    # Local ``matching`` ← ref.
                    matching = ref
                    break
            # Only when (matching is None).
            if matching is None:
                # Hand ``f"Error: artifact '{name}' not found. Available: {list(available.keys(…`` back to the caller.
                return f"Error: artifact '{name}' not found. Available: {list(available.keys())}"
            # Local ``loop`` ← asyncio.get_event_loop().
            loop = asyncio.get_event_loop()
            # Local ``data`` ← loop.run_until_complete(workspace.load(matching)).
            data = loop.run_until_complete(workspace.load(matching))
            # Only when (matching.format in ("json", "jsonl")).
            if matching.format in ("json", "jsonl"):
                # Hand ``data.decode("utf-8")`` back to the caller.
                return data.decode("utf-8")
            # Hand ``f"[Binary {matching.format} data, {len(data)} bytes. First 500 chars o…`` back to the caller.
            return f"[Binary {matching.format} data, {len(data)} bytes. First 500 chars of repr:] {repr(data[:500])}"

        # Hand ``[`` back to the caller.
        return [
            StructuredTool.from_function(
                # Local ``func`` ← load_artifact,.
                func=load_artifact,
                # Local ``name`` ← "load_artifact",.
                name="load_artifact",
                # Local ``description`` ← (.
                description=(
                    "Load an artifact from a prior task in this plan. "
                    "Provide the artifact name and optionally the producer_task_id."
                ),
            )
        ]

    # ------------------------------------------------------------------
    # LLM construction
    # ------------------------------------------------------------------

    def _create_llm(self) -> Any:
        """``_create_llm`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        cfg = self.backend_config
        # Local ``llm_cls`` ← _import_llm_class(cfg.provider or "openai").
        llm_cls = _import_llm_class(cfg.provider or "openai")
        kwargs: dict[str, Any] = {
            "model": cfg.model or "gpt-4o-mini",
            "temperature": cfg.temperature,
            **(cfg.config or {}),
        }
        # Hand ``llm_cls(**kwargs)`` back to the caller.
        return llm_cls(**kwargs)

    # ------------------------------------------------------------------
    # Main execution
    # ------------------------------------------------------------------

    async def execute(self, request: AgentTaskRequest) -> AgentTaskResult:
        """``execute`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        # --- guard: langchain_core must be importable -----------------
        try:
            from langchain_core.messages import HumanMessage, SystemMessage
            from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
        # On except ImportError as exc: recover or re-raise as appropriate.
        except ImportError as exc:
            # Hand ``AgentTaskResult(`` back to the caller.
            return AgentTaskResult(
                # Local ``success`` ← False,.
                success=False,
                # Local ``message`` ← "LangChain runtime requested but langchain_core is not installed.….
                message="LangChain runtime requested but langchain_core is not installed.",
                # Local ``error`` ← str(exc),.
                error=str(exc),
                # Local ``replan`` ← False,.
                replan=False,
            )

        # Try the fallible work below.
        try:
            from langchain.agents import AgentExecutor, create_tool_calling_agent
        # On except ImportError as exc: recover or re-raise as appropriate.
        except ImportError as exc:
            # Hand ``AgentTaskResult(`` back to the caller.
            return AgentTaskResult(
                # Local ``success`` ← False,.
                success=False,
                # Local ``message`` ← (.
                message=(
                    "LangChain runtime requires the 'langchain' package. "
                    "Install it with: pip install langchain"
                ),
                # Local ``error`` ← str(exc),.
                error=str(exc),
                # Local ``replan`` ← False,.
                replan=False,
            )

        # --- build tools ---------------------------------------------
        skill_tools, skill_calls_log = self._build_skill_tools()
        # Call ``memory_tools, memory_ops_log = self._build_memory_tools``.
        memory_tools, memory_ops_log = self._build_memory_tools()
        # Local ``workspace_tools`` ← self._build_workspace_tools(request).
        workspace_tools = self._build_workspace_tools(request)
        # Local ``all_tools`` ← skill_tools + memory_tools + workspace_tools.
        all_tools = skill_tools + memory_tools + workspace_tools

        # --- build LLM -----------------------------------------------
        try:
            # Local ``llm`` ← self._create_llm().
            llm = self._create_llm()
        # On except (ImportError, ValueError) as exc: recover or re-raise as appropriate.
        except (ImportError, ValueError) as exc:
            # Hand ``AgentTaskResult(`` back to the caller.
            return AgentTaskResult(
                # Local ``success`` ← False,.
                success=False,
                # Local ``message`` ← f"Failed to initialize LLM: {exc}",.
                message=f"Failed to initialize LLM: {exc}",
                # Local ``error`` ← str(exc),.
                error=str(exc),
                # Local ``replan`` ← False,.
                replan=False,
            )

        # --- resolve prompt -------------------------------------------
        prompt_text = _resolve_system_prompt(
            self.system_prompt or self.backend_config.system_prompt
        )
        # Local ``system_content`` ← _build_system_message(prompt_text, request).
        system_content = _build_system_message(prompt_text, request)

        # Local ``prompt`` ← ChatPromptTemplate.from_messages([.
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_content) if system_content else ("system", "You are a helpful AI agent."),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        # --- assemble agent -------------------------------------------
        try:
            # Local ``agent`` ← create_tool_calling_agent(llm, all_tools, prompt).
            agent = create_tool_calling_agent(llm, all_tools, prompt)
        # On except Exception as exc: recover or re-raise as appropriate.
        except Exception as exc:
            # Hand ``AgentTaskResult(`` back to the caller.
            return AgentTaskResult(
                # Local ``success`` ← False,.
                success=False,
                # Local ``message`` ← f"Failed to create tool-calling agent: {exc}",.
                message=f"Failed to create tool-calling agent: {exc}",
                # Local ``error`` ← traceback.format_exc(),.
                error=traceback.format_exc(),
                # Local ``replan`` ← False,.
                replan=False,
            )

        # Local ``executor`` ← AgentExecutor(.
        executor = AgentExecutor(
            # Local ``agent`` ← agent,.
            agent=agent,
            # Local ``tools`` ← all_tools,.
            tools=all_tools,
            # Local ``verbose`` ← logger.isEnabledFor(logging.DEBUG),.
            verbose=logger.isEnabledFor(logging.DEBUG),
            # Local ``max_iterations`` ← 15,.
            max_iterations=15,
            # Local ``handle_parsing_errors`` ← True,.
            handle_parsing_errors=True,
            # Local ``return_intermediate_steps`` ← True,.
            return_intermediate_steps=True,
        )

        # --- run ------------------------------------------------------
        try:
            # Local ``result`` ← await executor.ainvoke({"input": request.description}).
            result = await executor.ainvoke({"input": request.description})
        # On except Exception as exc: recover or re-raise as appropriate.
        except Exception as exc:
            # Log at exception so operators can diagnose this path.
            logger.exception("Agent execution failed for task %s", request.task_id)
            traces: list[ExecutionTrace] = []
            # Loop: for sc in skill_calls_log["items"].
            for sc in skill_calls_log["items"]:
                # Call ``traces.append``.
                traces.append(ExecutionTrace(trace_type="skill_call", payload=sc.model_dump(mode="json")))
            # Loop: for mo in memory_ops_log["items"].
            for mo in memory_ops_log["items"]:
                # Call ``traces.append``.
                traces.append(ExecutionTrace(trace_type="memory_op", payload=mo.model_dump(mode="json")))
            # Hand ``AgentTaskResult(`` back to the caller.
            return AgentTaskResult(
                # Local ``success`` ← False,.
                success=False,
                # Local ``message`` ← f"Agent execution error: {exc}",.
                message=f"Agent execution error: {exc}",
                # Local ``error`` ← traceback.format_exc(),.
                error=traceback.format_exc(),
                # Local ``traces`` ← traces,.
                traces=traces,
                # Local ``replan`` ← True,.
                replan=True,
            )

        # --- collect artifacts ----------------------------------------
        output_text: str = result.get("output", "")
        # Call ``intermediate_steps: list[Any] = result.get``.
        intermediate_steps: list[Any] = result.get("intermediate_steps", [])

        tool_trace: list[dict[str, Any]] = []
        # Loop: for action, observation in intermediate_steps.
        for action, observation in intermediate_steps:
            tool_trace.append({
                "tool": getattr(action, "tool", str(action)),
                "input": getattr(action, "tool_input", {}),
                "output": str(observation)[:500],
            })

        artifacts: dict[str, Any] = {
            "provider": self.backend_config.provider,
            "model": self.backend_config.model,
            "tool_trace": tool_trace,
        }

        traces: list[ExecutionTrace] = []
        # Loop: for sc in skill_calls_log["items"].
        for sc in skill_calls_log["items"]:
            # Call ``traces.append``.
            traces.append(ExecutionTrace(trace_type="skill_call", payload=sc.model_dump(mode="json")))
        # Loop: for mo in memory_ops_log["items"].
        for mo in memory_ops_log["items"]:
            # Call ``traces.append``.
            traces.append(ExecutionTrace(trace_type="memory_op", payload=mo.model_dump(mode="json")))

        # Hand ``AgentTaskResult(`` back to the caller.
        return AgentTaskResult(
            # Local ``success`` ← True,.
            success=True,
            # Local ``message`` ← output_text,.
            message=output_text,
            # Local ``artifacts`` ← artifacts,.
            artifacts=artifacts,
            # Local ``traces`` ← traces,.
            traces=traces,
            # Local ``replan`` ← False,.
            replan=False,
        )
