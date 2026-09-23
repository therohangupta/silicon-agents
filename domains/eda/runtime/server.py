"""HTTP agent service that binds ``AgentServer`` to an ``EDAAgent`` instance.

The generic agent SDK provides ``AgentServer``, skill registries, config
validation, and the ``/tasks/execute`` HTTP surface. This module specializes
that stack for the EDA domain:

* ``BoundAgentRuntime`` overrides ``execute`` so the request goes to
  ``EDAAgent.handle`` instead of the default tools.execute path.
* ``AgentService`` constructs an ``EDAAgent`` subclass with shared
  ``EngineeringMemory`` and ``ContextService``, then installs the bound
  runtime on the server.
* ``AgentService.from_agent`` validates ``config.yaml`` via
  ``load_agent_config`` and returns a ready service for ``server.py``
  entrypoints under each agent directory.

The HTTP process still does not understand design revisions or record types;
those concerns stay inside ``EDAAgent``. This file only wires the two layers
together and opens engineering memory for the process lifetime.
"""

from __future__ import annotations

# Environment selects an explicitly configured real EDA sidecar.
import os
# Path typing for config_path and from_agent helpers.
from pathlib import Path
# Optional memory injection and concrete EDAAgent subclass typing.
from typing import Optional, Type

# Generic SDK memory manager retained on the server for skill compatibility.
from packages.memory.runtime import MemoryManager
# Fleet request/result envelopes passed through BoundAgentRuntime.
from packages.agent_sdk.src.contracts import AgentTaskRequest, AgentTaskResult
# Base runtime whose execute method we override.
from packages.agent_sdk.src.runtime.base import AgentRuntime
# Validates agent config.yaml into the SDK config object.
# HTTP server base class providing /tasks/execute and related routes.
from packages.agent_sdk.src.server.agent_server import AgentServer
# Skill registry constructed by AgentServer and passed into the runtime.
from packages.agent_sdk.src.skills.registry import SkillRegistry
# Domain task handler that understands memory, context, and roles.
from .agent import EDAAgent
from ..config import EDAAgentConfig, load_eda_agent_config
# Assembler injected into the bound EDAAgent.
from .context import ContextService
# Shared engineering memory and its default factory.
from ..memory.service import EngineeringMemory, open_memory
# Tool binding remains a domain concern; generic SDK code knows no EDA tools.
from ..adapters import bind_eda_adapter
from ..adapters.toolchain import ToolchainAdapter


class BoundAgentRuntime(AgentRuntime):
    """Runs the agent object instead of the generic tools.execute path.

    The SDK runtime normally dispatches skills through a registry. For EDA
    agents, every task is a full ``EDAAgent.handle`` lifecycle (context,
    journal, act, journal). This subclass keeps the SDK constructor signature
    but forwards ``execute`` to the bound domain agent.
    """

    def __init__(self, skills: SkillRegistry, memory: MemoryManager, agent: EDAAgent) -> None:
        """Construct a runtime that delegates execution to ``agent``.

        Args:
            skills: Skill registry from the parent ``AgentServer``.
            memory: SDK ``MemoryManager`` (distinct from engineering memory).
            agent: Concrete ``EDAAgent`` that will handle each request.

        Returns:
            None. Stores ``agent`` on ``self.agent`` after super init.

        Side effects:
            Invokes ``AgentRuntime.__init__``.

        Failures:
            Propagates base-class initialization errors.
        """
        # Initialize the SDK runtime bookkeeping (skills + SDK memory).
        super().__init__(skills, memory)
        # Keep the domain agent for execute() to call.
        self.agent = agent

    async def execute(self, request: AgentTaskRequest) -> AgentTaskResult:
        """Forward one fleet task request into ``EDAAgent.handle``.

        Args:
            request: Inbound ``AgentTaskRequest`` from the HTTP layer.

        Returns:
            The ``AgentTaskResult`` produced by the domain agent lifecycle.

        Side effects:
            Whatever ``EDAAgent.handle`` performs (memory I/O, tool calls).

        Failures:
            Propagates exceptions from ``handle`` that are not mapped into
            failure results inside the agent.
        """
        # Domain handle owns context assembly, journaling, and role dispatch.
        return await self.agent.handle(request)


class AgentService(AgentServer):
    """``AgentServer`` that delegates ``/tasks/execute`` to an ``EDAAgent``.

    Constructed with an SDK config object and an ``EDAAgent`` subclass. Opens
    engineering memory (or accepts an injected instance), builds a
    ``ContextService`` on that memory, instantiates the agent, and replaces
    the server's runtime with ``BoundAgentRuntime``.
    """

    def __init__(
        self,
        config,
        agent_cls: Type[EDAAgent],
        config_path: str | Path | None = None,
        engineering_memory: Optional[EngineeringMemory] = None,
    ) -> None:
        """Wire SDK server, engineering memory, and a concrete agent class.

        Args:
            config: Validated SDK agent config object from the YAML file.
            agent_cls: Concrete ``EDAAgent`` subclass for this process.
            config_path: Optional path recorded by the base server.
            engineering_memory: Optional shared memory; defaults to
                ``open_memory()`` using ``MEMORY_BACKEND`` / file defaults.

        Returns:
            None. Sets ``engineering_memory``, ``bound_agent``, and ``_runtime``.

        Side effects:
            May open a memory backend. Instantiates the agent class.

        Failures:
            Propagates construction errors from the base server, memory open,
            or agent ``__init__`` (including missing ``spec``).
        """
        # Initialize HTTP routes, skills, and SDK memory from the config.
        super().__init__(config, config_path=config_path)
        # Bind the OSS sidecar when its URL is configured (Yosys, OpenSTA, OpenROAD).
        if os.environ.get("EDA_TOOLCHAIN_URL") or os.environ.get("EDA_FRAMEWORK") in {
            "yosys", "opensta", "openroad", "toolchain",
        }:
            bind_eda_adapter(ToolchainAdapter())
        # Prefer injected memory so tests can share an in-memory store.
        self.engineering_memory = engineering_memory or open_memory()
        # Construct the domain agent with matching context service.
        self.bound_agent = agent_cls(
            engineering_memory=self.engineering_memory,
            context_service=ContextService(self.engineering_memory),
            skills=self.skills,
        )
        # Replace the default runtime so /tasks/execute hits EDAAgent.handle.
        self._runtime = BoundAgentRuntime(self.skills, self.memory, self.bound_agent)

    @classmethod
    def from_agent(
        cls,
        path: str | Path,
        agent_cls: Type[EDAAgent],
        engineering_memory: Optional[EngineeringMemory] = None,
    ) -> "AgentService":
        """Validate ``config.yaml`` at ``path`` and build an ``AgentService``.

        This is the usual entrypoint from each agent's ``server.py``.

        Args:
            path: Filesystem path to the agent's ``config.yaml``.
            agent_cls: Concrete ``EDAAgent`` subclass defined beside the config.
            engineering_memory: Optional shared memory for the process.

        Returns:
            A fully constructed ``AgentService`` ready to serve HTTP.

        Side effects:
            Reads and validates the config file. May open memory.

        Failures:
            Propagates validation errors from ``load_agent_config`` and
            construction errors from ``cls(...)``.
        """
        config_path = Path(path)
        directory = config_path.parent if config_path.name == "config.yaml" else config_path
        eda_config = load_eda_agent_config(directory)
        return cls(eda_config, agent_cls, config_path=config_path, engineering_memory=engineering_memory)
