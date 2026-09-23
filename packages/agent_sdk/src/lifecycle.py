"""Domain-neutral lifecycle for one agent task.

The lifecycle owns control flow only: decode a transport request, prepare a
domain run, build context, journal both terminal paths, execute work, and map
the domain result back to the transport result. Domain subclasses supply every
semantic operation through the hooks below.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .contracts import AgentTaskRequest, AgentTaskResult


class TaskLifecycle(ABC):
    """Reliable task control flow reusable by any agent domain.

    No hook or field assumes a particular domain entity, user, record type, state
    machine, store, or tool framework. ``task``, ``context``, and ``result``
    are opaque domain values.
    """

    async def handle(self, request: AgentTaskRequest) -> AgentTaskResult:
        """Execute one task and always attempt a terminal journal after start."""
        task = self.prepare_task(self.decode_task(request))
        started = False
        context: Any = None
        try:
            context = await self.assemble_context(task)
            await self.journal_started(task, context)
            started = True
            result = await self.execute_task(task, context)
        except Exception as exc:
            result = self.failure_result(task, exc)

        if started:
            try:
                await self.journal_finished(task, result)
            except Exception as exc:
                result = self.failure_result(task, exc)

        return self.encode_result(result)

    @abstractmethod
    def decode_task(self, request: AgentTaskRequest) -> Any:
        """Decode a transport request into a domain task."""

    @abstractmethod
    def prepare_task(self, task: Any) -> Any:
        """Fill domain run identity, defaults, and idempotency fields."""

    @abstractmethod
    async def assemble_context(self, task: Any) -> Any:
        """Build the domain-specific context package for the task."""

    @abstractmethod
    async def journal_started(self, task: Any, context: Any) -> None:
        """Persist the domain's started transition."""

    @abstractmethod
    async def execute_task(self, task: Any, context: Any) -> Any:
        """Run domain work with the assembled context."""

    @abstractmethod
    async def journal_finished(self, task: Any, result: Any) -> None:
        """Persist the domain's terminal transition."""

    @abstractmethod
    def failure_result(self, task: Any, exc: Exception) -> Any:
        """Convert a lifecycle failure to a domain result."""

    @abstractmethod
    def encode_result(self, result: Any) -> AgentTaskResult:
        """Encode a domain result as the transport result."""
