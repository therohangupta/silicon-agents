"""HTTP agent service that binds ``AgentServer`` to an ``EdaAgent`` instance.

The generic agent SDK provides ``AgentServer``, skill registries, config
validation, and the ``/tasks/execute`` HTTP surface. This module specializes
that stack for the EDA domain:

* ``BoundAgentRuntime`` overrides ``execute`` so the request goes to
  ``EdaAgent.handle`` instead of the default tools.execute path.
* ``AgentService`` constructs an ``EdaAgent`` subclass with shared
  ``EngineeringMemory`` and ``ContextService``, then installs the bound
  runtime on the server.
* ``AgentService.from_agent`` validates ``config.yaml`` via
  ``AgentConfigValidator`` and returns a ready service for ``server.py``
  entrypoints under each agent directory.

The HTTP process still does not understand design revisions or record types;
those concerns stay inside ``EdaAgent``. This file only wires the two layers
together and opens engineering memory for the process lifetime.
"""

from __future__ import annotations

# Path typing for config_path and from_agent helpers.
from pathlib import Path
# Optional memory injection and concrete EdaAgent subclass typing.
from typing import Optional, Type

# Generic SDK memory manager retained on the server for skill compatibility.
from packages.agent_sdk.src.memory.loader import MemoryManager
# Fleet request/result envelopes passed through BoundAgentRuntime.
from packages.agent_sdk.src.models import AgentTaskRequest, AgentTaskResult
# Base runtime whose execute method we override.
from packages.agent_sdk.src.runtime.base import AgentRuntime
# Validates agent config.yaml into the SDK config object.
from packages.agent_sdk.src.schema.validator import AgentConfigValidator
# HTTP server base class providing /tasks/execute and related routes.
from packages.agent_sdk.src.server.agent_server import AgentServer
# Skill registry constructed by AgentServer and passed into the runtime.
from packages.agent_sdk.src.skills.registry import SkillRegistry
# Domain task handler that understands memory, context, and roles.
from .agent import EdaAgent
# Assembler injected into the bound EdaAgent.
from .context import ContextService
# Shared engineering memory and its default factory.
from .memory.service import EngineeringMemory, open_memory


class BoundAgentRuntime(AgentRuntime):
    """Runs the agent object instead of the generic tools.execute path.

    The SDK runtime normally dispatches skills through a registry. For EDA
    agents, every task is a full ``EdaAgent.handle`` lifecycle (context,
    journal, act, journal). This subclass keeps the SDK constructor signature
    but forwards ``execute`` to the bound domain agent.
    """

    def __init__(self, skills: SkillRegistry, memory: MemoryManager, agent: EdaAgent) -> None:
        """Construct a runtime that delegates execution to ``agent``.

        Args:
            skills: Skill registry from the parent ``AgentServer``.
            memory: SDK ``MemoryManager`` (distinct from engineering memory).
            agent: Concrete ``EdaAgent`` that will handle each request.

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
        """Forward one fleet task request into ``EdaAgent.handle``.

        Args:
            request: Inbound ``AgentTaskRequest`` from the HTTP layer.

        Returns:
            The ``AgentTaskResult`` produced by the domain agent lifecycle.

        Side effects:
            Whatever ``EdaAgent.handle`` performs (memory I/O, tool calls).

        Failures:
            Propagates exceptions from ``handle`` that are not mapped into
            failure results inside the agent.
        """
        # Domain handle owns context assembly, journaling, and role dispatch.
        return await self.agent.handle(request)


class AgentService(AgentServer):
    """``AgentServer`` that delegates ``/tasks/execute`` to an ``EdaAgent``.

    Constructed with an SDK config object and an ``EdaAgent`` subclass. Opens
    engineering memory (or accepts an injected instance), builds a
    ``ContextService`` on that memory, instantiates the agent, and replaces
    the server's runtime with ``BoundAgentRuntime``.
    """

    def __init__(
        self,
        config,
        agent_cls: Type[EdaAgent],
        config_path: str | Path | None = None,
        engineering_memory: Optional[EngineeringMemory] = None,
    ) -> None:
        """Wire SDK server, engineering memory, and a concrete agent class.

        Args:
            config: Validated SDK agent config object from the YAML file.
            agent_cls: Concrete ``EdaAgent`` subclass for this process.
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
        # Prefer injected memory so tests can share an in-memory store.
        self.engineering_memory = engineering_memory or open_memory()
        # Construct the domain agent with matching context service.
        self.bound_agent = agent_cls(
            engineering_memory=self.engineering_memory,
            context_service=ContextService(self.engineering_memory),
            skills=self.skills,
        )
        # Replace the default runtime so /tasks/execute hits EdaAgent.handle.
        self._runtime = BoundAgentRuntime(self.skills, self.memory, self.bound_agent)

    @classmethod
    def from_agent(
        cls,
        path: str | Path,
        agent_cls: Type[EdaAgent],
        engineering_memory: Optional[EngineeringMemory] = None,
    ) -> "AgentService":
        """Validate ``config.yaml`` at ``path`` and build an ``AgentService``.

        This is the usual entrypoint from each agent's ``server.py``.

        Args:
            path: Filesystem path to the agent's ``config.yaml``.
            agent_cls: Concrete ``EdaAgent`` subclass defined beside the config.
            engineering_memory: Optional shared memory for the process.

        Returns:
            A fully constructed ``AgentService`` ready to serve HTTP.

        Side effects:
            Reads and validates the config file. May open memory.

        Failures:
            Propagates validation errors from ``AgentConfigValidator`` and
            construction errors from ``cls(...)``.
        """
        # Validate the YAML into the SDK config model.
        config = AgentConfigValidator().validate_file(path)
        # Construct the specialized server with that config and agent class.
        return cls(config, agent_cls, config_path=path, engineering_memory=engineering_memory)
