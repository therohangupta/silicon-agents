from __future__ import annotations

"""Module ``agent_sdk/src/server/agent_server.py``.

Agent SDK: HTTP task server, runtimes, skills, telemetry publisher, and workspace helpers for first-party agents.
FastAPI/HTTP AgentServer that exposes health, task execution, and registration hooks.

Part of the agent SDK server/runtime stack: agents import these helpers to serve tasks over HTTP, run LLM/tool loops, publish telemetry, and persist plan workspaces.

Hand-written source for ``agent_server.py``. Behavior is unchanged; comments document control-plane / agent-runtime intent for maintainers.
"""


import asyncio
import importlib
import importlib.util
import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import uvicorn
from fastapi import FastAPI, HTTPException

from ..memory.loader import MemoryManager
from ..memory.skills import make_memory_skills
from ..models import (
    AgentConfig,
    AgentHealth,
    AgentTaskRequest,
    AgentTaskResult,
    ExecutionTrace,
    MemoryOp,
    ReliabilityConfig,
    SkillSpec,
)
from ..runtime.codegen_runtime import CodegenRuntime
from ..runtime.direct_function_runtime import DirectFunctionRuntime
from ..runtime.tool_loop_runtime import ToolLoopRuntime
from ..schema.validator import AgentConfigValidator
from ..skills.registry import SkillRegistry
from ..telemetry.client import TelemetryClient
from ..telemetry.publisher import TelemetryPublisher

# Local ``logger`` ← logging.getLogger(__name__).
logger = logging.getLogger(__name__)


class AgentServer:
    """``AgentServer`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
    def __init__(self, config: AgentConfig, config_path: str | Path | None = None):
        """``AgentServer`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        self.config = config
        # Bind ``config_path`` from Path(config_path) if config_path else None for later use on this instance.
        self.config_path = Path(config_path) if config_path else None
        # Bind ``memory`` from MemoryManager(config.memory) for later use on this instance.
        self.memory = MemoryManager(config.memory)
        # Bind ``skills`` from SkillRegistry() for later use on this instance.
        self.skills = SkillRegistry()
        # Bind ``_busy`` from False for later use on this instance.
        self._busy = False
        # Bind ``_runtime`` from None for later use on this instance.
        self._runtime = None
        self._semaphore: Optional[asyncio.Semaphore] = None
        # Bind ``_tools_module_name`` from f"_agent_{self.config.metadata.name}_tools" for later use on this instance.
        self._tools_module_name = f"_agent_{self.config.metadata.name}_tools"
        # Bind ``_telemetry_adapter_module_name`` from f"_agent_{self.config.metadata.name}_telemetry_adapter" for later use on this instance.
        self._telemetry_adapter_module_name = f"_agent_{self.config.metadata.name}_telemetry_adapter"
        self._telemetry: Optional[TelemetryClient] = None
        self._stream_publisher: Optional[TelemetryPublisher] = None
        # Bind ``_telemetry_adapter`` from None for later use on this instance.
        self._telemetry_adapter = None
        self._idle_stream_task: Optional[asyncio.Task] = None

        # Call ``self._setup_telemetry``.
        self._setup_telemetry()
        # Call ``self._load_skills``.
        self._load_skills()
        # Call ``self._load_telemetry_adapter``.
        self._load_telemetry_adapter()
        # Bind ``_runtime`` from self._make_runtime() for later use on this instance.
        self._runtime = self._make_runtime()
        # Bind ``_semaphore`` from asyncio.Semaphore(config.execution.concurrency.max_tasks) for later use on this instance.
        self._semaphore = asyncio.Semaphore(config.execution.concurrency.max_tasks)

        # Bind ``app`` from FastAPI(title=f"{config.metadata.name} Agent", lifespan=self… for later use on this instance.
        self.app = FastAPI(title=f"{config.metadata.name} Agent", lifespan=self._lifespan)
        # Call ``self._install_routes``.
        self._install_routes()

    @classmethod
    def from_config(cls, path: str | Path) -> "AgentServer":
        """``from_config`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        return cls.from_yaml(path)

    @classmethod
    def from_yaml(cls, path: str | Path) -> "AgentServer":
        """``from_yaml`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        config = AgentConfigValidator().validate_file(path)
        # Hand ``cls(config, config_path=path)`` back to the caller.
        return cls(config, config_path=path)

    def _setup_telemetry(self) -> None:
        """``_setup_telemetry`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        obs = self.config.observability
        # Local ``endpoint`` ← obs.telemetry.endpoint.
        endpoint = obs.telemetry.endpoint
        # Bind ``_telemetry`` from TelemetryClient( for later use on this instance.
        self._telemetry = TelemetryClient(
            # Local ``agent_id`` ← self.config.metadata.name,.
            agent_id=self.config.metadata.name,
            # Local ``endpoint`` ← endpoint,.
            endpoint=endpoint,
            # Local ``heartbeat_interval_secs`` ← obs.heartbeat_interval_secs,.
            heartbeat_interval_secs=obs.heartbeat_interval_secs,
            # Local ``host`` ← self.config.connection.host,.
            host=self.config.connection.host,
            # Local ``port`` ← self.config.connection.port,.
            port=self.config.connection.port,
            # Local ``agent_type`` ← self.config.metadata.name,.
            agent_type=self.config.metadata.name,
        )
        # Call ``self.skills.set_call_hook``.
        self.skills.set_call_hook(self._on_skill_call)

    def _grpc_target(self) -> str:
        """``_grpc_target`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        from packages.platform_config import setting

        configured = os.environ.get("TELEMETRY_GRPC_TARGET")
        if configured:
            return configured
        endpoint = self.config.observability.telemetry.endpoint
        # Local ``parsed`` ← urlparse(endpoint).
        parsed = urlparse(endpoint)
        host = parsed.hostname or setting("TELEMETRY_HOST")
        port = os.environ.get("TELEMETRY_GRPC_PORT") or setting("TELEMETRY_GRPC_PORT")
        return f"{host}:{port}"

    def _on_skill_call(self, sc) -> None:
        """``_on_skill_call`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        if self._telemetry is None:
            return
        asyncio.create_task(
            self._telemetry.emit(
                "skill_call",
                sc.model_dump(mode="json"),
                # Local ``stream_name`` ← "skill_calls",.
                stream_name="skill_calls",
            )
        )

    def _load_skills(self) -> None:
        """``_load_skills`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        if self.config_path:
            # Local ``agent_dir`` ← str(self.config_path.parent.resolve()).
            agent_dir = str(self.config_path.parent.resolve())
            # Only when (agent_dir not in sys.path).
            if agent_dir not in sys.path:
                # Call ``sys.path.insert``.
                sys.path.insert(0, agent_dir)
            # Local ``tools_path`` ← self.config_path.parent / "tools.py".
            tools_path = self.config_path.parent / "tools.py"
            # Only when (tools_path.exists() and self._tools_module_name not in sys.modules).
            if tools_path.exists() and self._tools_module_name not in sys.modules:
                # Local ``module_spec`` ← importlib.util.spec_from_file_location(.
                module_spec = importlib.util.spec_from_file_location(
                    self._tools_module_name, tools_path
                )
                # Only when (module_spec and module_spec.loader).
                if module_spec and module_spec.loader:
                    # Local ``module`` ← importlib.util.module_from_spec(module_spec).
                    module = importlib.util.module_from_spec(module_spec)
                    sys.modules[self._tools_module_name] = module
                    # Call ``module_spec.loader.exec_module``.
                    module_spec.loader.exec_module(module)

        # Loop: for spec in self.config.skills.
        for spec in self.config.skills:
            # Only when (self.config_path and spec.module == "tools").
            if self.config_path and spec.module == "tools":
                # Local ``tools_path`` ← self.config_path.parent / "tools.py".
                tools_path = self.config_path.parent / "tools.py"
                # Local ``module_spec`` ← importlib.util.spec_from_file_location(.
                module_spec = importlib.util.spec_from_file_location(
                    self._tools_module_name, tools_path
                )
                # Only when (module_spec is None or module_spec.loader is None).
                if module_spec is None or module_spec.loader is None:
                    # Raise ``ImportError`` to signal this failure mode to callers.
                    raise ImportError(f"Unable to load tools module: {tools_path}")
                # Local ``module`` ← importlib.util.module_from_spec(module_spec).
                module = importlib.util.module_from_spec(module_spec)
                sys.modules[self._tools_module_name] = module
                # Call ``module_spec.loader.exec_module``.
                module_spec.loader.exec_module(module)
            else:
                # Local ``module`` ← importlib.import_module(spec.module).
                module = importlib.import_module(spec.module)
            # Local ``func`` ← getattr(module, spec.callable).
            func = getattr(module, spec.callable)
            # Call ``self.skills.register``.
            self.skills.register(spec, func)

        # Local ``memory_skill_funcs`` ← make_memory_skills(self.memory).
        memory_skill_funcs = make_memory_skills(self.memory)
        # Loop: for skill_id, func in memory_skill_funcs.items().
        for skill_id, func in memory_skill_funcs.items():
            self.skills.register(
                SkillSpec(
                    # Local ``id`` ← skill_id,.
                    id=skill_id,
                    # Local ``callable`` ← skill_id,.
                    callable=skill_id,
                    # Local ``description`` ← f"Memory operation: {skill_id}",.
                    description=f"Memory operation: {skill_id}",
                    # Local ``module`` ← "memory",.
                    module="memory",
                ),
                func,
            )

        # Only when (self.config_path and (self.config_path.parent / "telemetry.py").exists()).
        if self.config_path and (self.config_path.parent / "telemetry.py").exists():
            # Try the fallible work below.
            try:
                # Call ``importlib.import_module``.
                importlib.import_module("telemetry")
            # On except Exception: recover or re-raise as appropriate.
            except Exception:
                # Log at debug so operators can diagnose this path.
                logger.debug("telemetry.py present but failed to import", exc_info=True)

    def _load_telemetry_adapter(self) -> None:
        """``_load_telemetry_adapter`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        if not self.config_path:
            return
        # Local ``adapter_path`` ← self.config_path.parent / "telemetry_adapter.py".
        adapter_path = self.config_path.parent / "telemetry_adapter.py"
        # Only when (not adapter_path.exists()).
        if not adapter_path.exists():
            return
        # Local ``module_spec`` ← importlib.util.spec_from_file_location(.
        module_spec = importlib.util.spec_from_file_location(
            self._telemetry_adapter_module_name, adapter_path
        )
        # Only when (module_spec is None or module_spec.loader is None).
        if module_spec is None or module_spec.loader is None:
            # Log at warning so operators can diagnose this path.
            logger.warning("Unable to load telemetry adapter: %s", adapter_path)
            return
        # Local ``module`` ← importlib.util.module_from_spec(module_spec).
        module = importlib.util.module_from_spec(module_spec)
        sys.modules[self._telemetry_adapter_module_name] = module
        # Try the fallible work below.
        try:
            # Call ``module_spec.loader.exec_module``.
            module_spec.loader.exec_module(module)
            # Bind ``_telemetry_adapter`` from module for later use on this instance.
            self._telemetry_adapter = module
        # On except Exception: recover or re-raise as appropriate.
        except Exception:
            # Log at warning so operators can diagnose this path.
            logger.warning("Telemetry adapter failed to import: %s", adapter_path, exc_info=True)

    async def _start_stream_publisher(self) -> None:
        """``_start_stream_publisher`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        if self._telemetry_adapter is None:
            return
        # Local ``endpoint`` ← self.config.observability.telemetry.endpoint.rstrip("/").
        endpoint = self.config.observability.telemetry.endpoint.rstrip("/")
        # Bind ``_stream_publisher`` from TelemetryPublisher( for later use on this instance.
        self._stream_publisher = TelemetryPublisher(
            # Local ``agent_id`` ← self.config.metadata.name,.
            agent_id=self.config.metadata.name,
            # Local ``agent_type`` ← self.config.metadata.name,.
            agent_type=self.config.metadata.name,
            # Local ``grpc_target`` ← self._grpc_target(),.
            grpc_target=self._grpc_target(),
            # Local ``blob_upload_url`` ← f"{endpoint}/telemetry/blob",.
            blob_upload_url=f"{endpoint}/telemetry/blob",
        )
        # Try the fallible work below.
        try:
            # Await ``self._stream_publisher.connect`` and continue once it completes.
            await self._stream_publisher.connect()
        # On except Exception: recover or re-raise as appropriate.
        except Exception:
            # Log at warning so operators can diagnose this path.
            logger.warning("Telemetry publisher unavailable", exc_info=True)
            # Bind ``_stream_publisher`` from None for later use on this instance.
            self._stream_publisher = None
            return
        # Await ``self._start_idle_stream`` and continue once it completes.
        await self._start_idle_stream()

    async def _start_idle_stream(self) -> None:
        """``_start_idle_stream`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        if (
            self._telemetry_adapter is None
            or self._stream_publisher is None
            # Call ``or not hasattr``.
            or not hasattr(self._telemetry_adapter, "stream_idle")
        ):
            return
        # Only when (self._idle_stream_task is None or self._idle_stream_task.done()).
        if self._idle_stream_task is None or self._idle_stream_task.done():
            # Bind ``_idle_stream_task`` from asyncio.create_task( for later use on this instance.
            self._idle_stream_task = asyncio.create_task(
                # Call ``self._telemetry_adapter.stream_idle``.
                self._telemetry_adapter.stream_idle(self._stream_publisher)
            )

    async def _stop_idle_stream(self) -> None:
        """``_stop_idle_stream`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        if self._idle_stream_task is not None:
            # Call ``self._idle_stream_task.cancel``.
            self._idle_stream_task.cancel()
            # Try the fallible work below.
            try:
                # Await ``self._idle_stream_task`` and continue once it completes.
                await self._idle_stream_task
            # On except asyncio.CancelledError: recover or re-raise as appropriate.
            except asyncio.CancelledError:
                pass
            # Bind ``_idle_stream_task`` from None for later use on this instance.
            self._idle_stream_task = None

    async def _start_task_stream(self, request: AgentTaskRequest) -> Optional[asyncio.Task]:
        """``_start_task_stream`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        if (
            self._telemetry_adapter is None
            or self._stream_publisher is None
            # Call ``or not hasattr``.
            or not hasattr(self._telemetry_adapter, "stream_task")
        ):
            # Hand ``None`` back to the caller.
            return None
        # Await ``self._stop_idle_stream`` and continue once it completes.
        await self._stop_idle_stream()
        # Local ``duration`` ← float(.
        duration = float(
            os.environ.get(
                "TASK_DURATION",
                str(self.config.reliability.task_timeout_secs or 120),
            )
        )
        # Hand ``asyncio.create_task(`` back to the caller.
        return asyncio.create_task(
            self._telemetry_adapter.stream_task(
                self._stream_publisher,
                # Local ``task_id`` ← request.task_id,.
                task_id=request.task_id,
                # Local ``task_description`` ← request.description,.
                task_description=request.description,
                # Local ``persist`` ← request.record_episode,.
                persist=request.record_episode,
                # Local ``duration_secs`` ← duration,.
                duration_secs=duration,
            )
        )

    async def _stop_task_stream(self, task: Optional[asyncio.Task]) -> None:
        """``_stop_task_stream`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        if task is None:
            return
        # Call ``task.cancel``.
        task.cancel()
        # Try the fallible work below.
        try:
            # Await ``task`` and continue once it completes.
            await task
        # On except asyncio.CancelledError: recover or re-raise as appropriate.
        except asyncio.CancelledError:
            pass

    def _capability_skill_params(self, request: AgentTaskRequest) -> dict[str, dict]:
        """``_capability_skill_params`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        if not request.required_capabilities:
            # Hand ``{}`` back to the caller.
            return {}
        merged: dict[str, dict] = {}
        # Local ``cap_ids`` ← set(request.required_capabilities).
        cap_ids = set(request.required_capabilities)
        # Loop: for cap in self.config.capabilities.
        for cap in self.config.capabilities:
            # Only when (cap.id in cap_ids and cap.skill_params).
            if cap.id in cap_ids and cap.skill_params:
                # Loop: for skill_id, params in cap.skill_params.items().
                for skill_id, params in cap.skill_params.items():
                    # Only when (isinstance(params, dict)).
                    if isinstance(params, dict):
                        # Call ``merged.setdefault``.
                        merged.setdefault(skill_id, {}).update(params)
        # Hand ``merged`` back to the caller.
        return merged

    def _make_runtime(self):
        """``_make_runtime`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        mode = self.config.execution.mode
        # Only when (mode == "codegen").
        if mode == "codegen":
            # Local ``import_paths`` ← [str(self.config_path.parent.resolve())] if self.config_path else….
            import_paths = [str(self.config_path.parent.resolve())] if self.config_path else []
            # Hand ``CodegenRuntime(`` back to the caller.
            return CodegenRuntime(
                self.skills,
                self.memory,
                self.config.backend,
                self.config.execution,
                # Local ``import_paths`` ← import_paths,.
                import_paths=import_paths,
                # Local ``reliability`` ← self.config.reliability,.
                reliability=self.config.reliability,
            )
        # Only when (mode == "tool_loop").
        if mode == "tool_loop":
            # Hand ``ToolLoopRuntime(self.skills, self.memory, self.config.backend)`` back to the caller.
            return ToolLoopRuntime(self.skills, self.memory, self.config.backend)
        # Only when (mode in ("direct_function", "custom")).
        if mode in ("direct_function", "custom"):
            # Hand ``DirectFunctionRuntime(`` back to the caller.
            return DirectFunctionRuntime(
                self.skills, self.memory, module_name=self._tools_module_name
            )
        # Raise ``ValueError`` to signal this failure mode to callers.
        raise ValueError(f"Unsupported execution mode: {mode}")

    @asynccontextmanager
    async def _lifespan(self, _app: FastAPI):
        """``_lifespan`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        if self._telemetry:
            # Call ``self._telemetry.start_heartbeat``.
            self._telemetry.start_heartbeat()
        # Await ``self._start_stream_publisher`` and continue once it completes.
        await self._start_stream_publisher()
        yield
        # Await ``self._stop_idle_stream`` and continue once it completes.
        await self._stop_idle_stream()
        # Only when (self._stream_publisher).
        if self._stream_publisher:
            # Await ``self._stream_publisher.close`` and continue once it completes.
            await self._stream_publisher.close()
        # Only when (self._telemetry).
        if self._telemetry:
            # Await ``self._telemetry.close`` and continue once it completes.
            await self._telemetry.close()
        # Await ``self.memory.close`` and continue once it completes.
        await self.memory.close()

    def _install_routes(self) -> None:
        """``_install_routes`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        endpoints = self.config.connection.endpoints

        @self.app.get(endpoints.get("health", "/health"), response_model=AgentHealth)
        async def health():
            """``health`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
            return AgentHealth(
                # Local ``agent_id`` ← self.config.metadata.name,.
                agent_id=self.config.metadata.name,
                # Local ``status`` ← "busy" if self._busy else "healthy",.
                status="busy" if self._busy else "healthy",
                # Local ``busy`` ← self._busy,.
                busy=self._busy,
                # Local ``capabilities`` ← [c.id for c in self.config.capabilities],.
                capabilities=[c.id for c in self.config.capabilities],
                # Local ``reliability`` ← self.config.reliability,.
                reliability=self.config.reliability,
            )

        @self.app.get("/skills")
        async def skills():
            """``skills`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
            return [spec.model_dump(mode="json") for spec in self.skills.specs]

        @self.app.get(endpoints.get("memory", "/memory/state"))
        async def memory_state():
            """``memory_state`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
            return await self.memory.dump()

        # Local ``execute_path`` ← endpoints.get("execute", "/tasks/execute").
        execute_path = endpoints.get("execute", "/tasks/execute")

        @self.app.post(execute_path, response_model=AgentTaskResult)
        async def execute(request: AgentTaskRequest):
            """``execute`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
            if self._runtime is None:
                # Raise ``HTTPException`` to signal this failure mode to callers.
                raise HTTPException(status_code=503, detail="Runtime not initialized")
            # Hold ``self._semaphore`` for the duration of the indented block.
            async with self._semaphore:
                # Bind ``_busy`` from True for later use on this instance.
                self._busy = True
                # Only when (self._telemetry).
                if self._telemetry:
                    # Call ``self._telemetry.set_busy``.
                    self._telemetry.set_busy(True)
                task_stream: Optional[asyncio.Task] = None
                # Try the fallible work below.
                try:
                    # Local ``task_stream`` ← await self._start_task_stream(request).
                    task_stream = await self._start_task_stream(request)
                    # Call ``self.skills.set_capability_params``.
                    self.skills.set_capability_params(self._capability_skill_params(request))
                    # Only when (self._telemetry).
                    if self._telemetry:
                        # Await ``self._telemetry.emit`` and continue once it completes.
                        await self._telemetry.emit(
                            "task_started",
                            {"task_id": request.task_id, "description": request.description},
                            # Local ``task_id`` ← request.task_id,.
                            task_id=request.task_id,
                        )
                    # Local ``result`` ← await self._runtime.execute(request).
                    result = await self._runtime.execute(request)
                    # Only when (self._telemetry).
                    if self._telemetry:
                        # Await ``self._telemetry.emit`` and continue once it completes.
                        await self._telemetry.emit(
                            "task_completed",
                            {"success": result.success, "message": result.message},
                            # Local ``task_id`` ← request.task_id,.
                            task_id=request.task_id,
                        )
                        # Only when (result.artifacts).
                        if result.artifacts:
                            # Await ``self._telemetry.emit`` and continue once it completes.
                            await self._telemetry.emit(
                                "task_artifacts",
                                result.artifacts,
                                # Local ``stream_name`` ← "artifacts",.
                                stream_name="artifacts",
                                # Local ``task_id`` ← request.task_id,.
                                task_id=request.task_id,
                            )
                        # Loop: for trace in result.traces.
                        for trace in result.traces:
                            # Only when (trace.trace_type == "skill_call").
                            if trace.trace_type == "skill_call":
                                # Await ``self._telemetry.emit`` and continue once it completes.
                                await self._telemetry.emit(
                                    "skill_call",
                                    trace.payload,
                                    # Local ``stream_name`` ← "skill_calls",.
                                    stream_name="skill_calls",
                                    # Local ``task_id`` ← request.task_id,.
                                    task_id=request.task_id,
                                )
                    # Hand ``result`` back to the caller.
                    return result
                # On except Exception as exc: recover or re-raise as appropriate.
                except Exception as exc:
                    # Log at exception so operators can diagnose this path.
                    logger.exception("Task execution failed")
                    # Only when (self._telemetry).
                    if self._telemetry:
                        # Await ``self._telemetry.emit`` and continue once it completes.
                        await self._telemetry.emit(
                            "task_failed",
                            {"error": str(exc)},
                            # Local ``task_id`` ← request.task_id,.
                            task_id=request.task_id,
                            # Local ``severity`` ← "error",.
                            severity="error",
                        )
                    # Raise ``HTTPException`` to signal this failure mode to callers.
                    raise HTTPException(status_code=500, detail=str(exc)) from exc
                # Cleanup that must run even if the try block failed.
                finally:
                    # Await ``self._stop_task_stream`` and continue once it completes.
                    await self._stop_task_stream(task_stream)
                    # Await ``self._start_idle_stream`` and continue once it completes.
                    await self._start_idle_stream()
                    # Bind ``_busy`` from False for later use on this instance.
                    self._busy = False
                    # Only when (self._telemetry).
                    if self._telemetry:
                        # Call ``self._telemetry.set_busy``.
                        self._telemetry.set_busy(False)

    def run(self, host: str = "0.0.0.0", port: Optional[int] = None) -> None:
        """``run`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        uvicorn.run(
            self.app,
            # Local ``host`` ← host,.
            host=host,
            # Local ``port`` ← port or self.config.connection.port,.
            port=port or self.config.connection.port,
        )
