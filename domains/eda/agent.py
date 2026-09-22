"""EDA agent base: the shared task handler every chip-design agent subclasses.

This module sits between the HTTP process (``AgentService`` / ``AgentServer``)
and the per-agent tool modules under ``agents/``. The HTTP layer knows how to
accept ``AgentTaskRequest`` objects and return ``AgentTaskResult`` objects. It
does not know about design revisions, record types, role permissions, or
engineering-memory journals. ``EdaAgent`` owns that vocabulary.

Lifecycle for one inbound task:

1. Convert the fleet request into a typed ``TaskSpec``.
2. Derive a ``MemoryScope`` from project, revision, subsystem, block, and stage.
3. Ask ``ContextService`` to assemble a context package using the agent's
   ``config.yaml`` include/exclude/precedence policy.
4. Journal a provisional ``started`` checkpoint into engineering memory.
5. Either propose a child workflow (lead role) or invoke declared tools
   (worker / validator roles).
6. Journal a ``finished`` checkpoint with the ``TaskResult`` payload.
7. Convert the domain result back into an ``AgentTaskResult`` for the fleet.

Permission checks live in ``assert_action``. A tool's declared ``ToolAction``
must be allowed by the agent's role, not forbidden by the task, and present
in the task's allow-list when one is set. Failures become non-retryable
``PERMISSION_DENIED`` results rather than uncaught exceptions at the HTTP
boundary (except for programming errors such as a missing ``AgentSpec``).

The SDK ``SkillRegistry`` loads each concrete agent's ``tools.py`` at server
startup. This base class calls that registry after enforcing action policy, so
timeouts, capability parameters, and tracing are shared with all domains.
"""

from __future__ import annotations

# Dynamic import of the sibling tools.py beside a concrete agent class.
# Resolve the filesystem directory that contains the subclass definition.
# Cache loaded tool modules under stable names in the process module table.
# Path arithmetic for locating tools.py next to the agent source file.
# Optional typing for injectable memory and context collaborators.
from typing import Any, Optional

# Fleet-facing request/result envelopes from the generic agent SDK.
from packages.agent_sdk.src.lifecycle import TaskLifecycle
from packages.agent_sdk.src.models import AgentTaskRequest, AgentTaskResult
from packages.agent_sdk.src.skills.registry import SkillRegistry
# Assembles include/exclude/precedence policies into a ContextPackage.
from .context import ContextService
# Shared engineering-memory service and its default store factory.
from .memory.service import EngineeringMemory, open_memory
# Builds a WorkflowSpec from a lead's plan_steps or delegates_to list.
from .planning import build_workflow
# Role/action matrices and outcome/record enums used throughout the handler.
from .schemas.enums import ROLE_ACTIONS, AgentRole, RecordType, TaskOutcome, ToolAction, ValidationState
# Logical /programs path used when journaling or publishing records.
from .schemas.memory import MemoryScope
# Typed workflow graph a lead publishes instead of executing child work.
from .schemas.messages import WorkflowSpec
# Domain task contract and the result object returned to the fleet layer.
from .schemas.task import TaskResult, TaskSpec
# Identity, boundary, tools, and context policy loaded from config.yaml.
from .spec import AgentSpec


class AgentPermissionError(Exception):
    """Raised when a task or an agent role forbids the requested tool action.

    ``EdaAgent.handle`` catches this exception and converts it into a
    non-retryable ``AgentTaskResult`` with reason code ``PERMISSION_DENIED``.
    Callers that invoke ``assert_action`` directly should expect this type
    when the action is outside the role matrix, outside the task allow-list,
    or listed in the task's forbidden actions.

    Args are not used; the message string carries the human-readable reason.
    This exception has no additional attributes beyond the base ``Exception``.
    """


class EdaAgent(TaskLifecycle):
    """Task handler for one chip-design agent in the EDA fleet.

    Concrete agents under ``agents/`` subclass this type, set a class-level
    ``spec: AgentSpec`` (usually produced by ``read_spec`` against their
    directory), and rely on this base class for memory, context assembly,
    journaling, permission checks, and tool invocation. The HTTP process in
    front of each agent is ``AgentService``, which does not know about
    designs, revisions, or record types; it only forwards ``AgentTaskRequest``
    objects into ``handle``.

    Role behavior:

    * Lead agents call ``plan``, publish a provisional workflow revision, and
      may also invoke their declared operations through the SDK registry.
    * Worker agents call ``execute_tools`` and return a partial completion when
      no real EDA framework is bound.
    * Validator agents additionally publish a provisional gate decision that
      explicitly does not grade the candidate until a framework is bound.

    Side effects: every successful ``handle`` path appends at least two
    memory records (started and finished). Plan and validator paths also
    publish workflow or gate records visible to other agents.

    Failure modes: missing ``spec`` raises ``TypeError`` at construction.
    Permission violations become ``NONRETRYABLE_FAILURE``. ``TimeoutError``
    becomes ``RETRYABLE_FAILURE``. Missing ``tools.py`` raises ``ImportError``
    during tool load.
    """

    # Class attribute every concrete subclass must set to a loaded AgentSpec.
    spec: AgentSpec

    @classmethod
    def read_spec(cls, directory: str | Path) -> AgentSpec:
        """Load the ``AgentSpec`` from ``config.yaml`` beside an agent directory.

        This is the usual way concrete agent modules obtain their class-level
        ``spec``. It delegates to ``registry.load_spec``, which requires a
        context policy with ``include`` and ``precedence``. Stage and role
        come from the document or from ``metadata.labels``; extra label keys
        such as domain or track are not checked against the directory path.

        Args:
            directory: Filesystem path to the agent package that contains
                ``config.yaml``. May be a string or ``Path``.

        Returns:
            A fully populated ``AgentSpec`` for that directory.

        Side effects:
            Reads ``config.yaml`` from disk. Does not mutate class state.

        Failures:
            Propagates ``CatalogError`` (and underlying I/O or YAML errors)
            when the config is missing, malformed, or missing required context fields.
        """
        # Local import keeps registry loading optional for lightweight imports.
        from .registry import load_spec

        # Parse and validate the directory's config into an AgentSpec.
        return load_spec(directory)

    def __init__(
        self,
        engineering_memory: Optional[EngineeringMemory] = None,
        context_service: Optional[ContextService] = None,
        skills: Optional[SkillRegistry] = None,
    ) -> None:
        """Construct an agent bound to engineering memory and a context service.

        Args:
            engineering_memory: Shared memory service. When omitted, opens the
                default backend via ``open_memory`` (file store unless env vars
                select memory, postgres, or plane).
            context_service: Assembler that turns the agent's context policy
                into a ``ContextPackage``. When omitted, a new
                ``ContextService`` is built on the same memory instance.

        Returns:
            None. Initializes ``self.memory`` and ``self.context``.

        Side effects:
            May open a new memory store (file directory, in-process store,
            Postgres, or memory plane) when ``engineering_memory`` is None.

        Failures:
            Raises ``TypeError`` when the concrete class did not set
            ``spec`` to an ``AgentSpec`` instance before construction.
        """
        # Reject subclasses that forgot to assign a loaded AgentSpec.
        if not isinstance(getattr(self, "spec", None), AgentSpec):
            raise TypeError(f"{type(self).__name__} must set spec to an AgentSpec")
        # Prefer an injected service so tests and AgentService can share one store.
        self.memory = engineering_memory or open_memory()
        # Context assembly always reads through the same memory the agent journals to.
        self.context = context_service or ContextService(self.memory)
        # AgentService injects the SDK registry that loaded this agent's tools.
        self.skills = skills

    def decode_task(self, request: AgentTaskRequest) -> TaskSpec:
        """Decode the fleet envelope into the EDA task contract."""
        return TaskSpec.from_request(request)

    def prepare_task(self, task: TaskSpec) -> TaskSpec:
        """Apply this EDA agent's idempotency and stage defaults."""
        if not task.idempotency_key:
            task.idempotency_key = f"{self.spec.agent_id}:{task.task_id}"
        if not task.stage:
            task.stage = self.spec.stage
        return task

    async def assemble_context(self, task: TaskSpec) -> Any:
        """Resolve this EDA agent's context policy through engineering memory."""
        return await self.context.assemble(task, self.spec.context)

    async def journal_started(self, task: TaskSpec, context: Any) -> None:
        """Append the EDA started checkpoint."""
        await self.memory.append(
            task_id=task.task_id,
            idempotency_key=f"{task.idempotency_key}:started",
            payload={
                "objective": task.objective,
                "context_ids": [record.memory_id for record in context.records],
                "conflicts": [conflict.subject for conflict in context.conflicts],
            },
            project_id=task.project_id,
            scope=self._scope(task),
            agent_id=self.spec.agent_id,
            summary=f"Started {self.spec.agent_id}",
            design_revision=task.design_revision,
        )

    async def execute_task(self, task: TaskSpec, context: Any) -> TaskResult:
        """Run the EDA role-specific execution path with its context."""
        return await self.act(task, context)

    async def journal_finished(self, task: TaskSpec, result: TaskResult) -> None:
        """Append an EDA terminal checkpoint for success and failure alike."""
        terminal_key = "failed" if result.outcome in {
            TaskOutcome.RETRYABLE_FAILURE,
            TaskOutcome.NONRETRYABLE_FAILURE,
        } else "finished"
        await self.memory.append(
            task_id=task.task_id,
            idempotency_key=f"{task.idempotency_key}:{terminal_key}",
            payload=result.model_dump(mode="json"),
            project_id=task.project_id,
            scope=self._scope(task),
            agent_id=self.spec.agent_id,
            summary=result.summary,
            design_revision=task.design_revision,
        )

    def failure_result(self, task: TaskSpec, exc: Exception) -> TaskResult:
        """Map expected EDA failures to a structured terminal result."""
        if isinstance(exc, AgentPermissionError):
            outcome, reason = TaskOutcome.NONRETRYABLE_FAILURE, "PERMISSION_DENIED"
        elif isinstance(exc, TimeoutError):
            outcome, reason = TaskOutcome.RETRYABLE_FAILURE, "TIMEOUT"
        else:
            outcome, reason = TaskOutcome.NONRETRYABLE_FAILURE, "EXECUTION_ERROR"
        return TaskResult(
            task_id=task.task_id,
            outcome=outcome,
            reason_code=reason,
            summary=str(exc) or type(exc).__name__,
        )

    def encode_result(self, result: TaskResult) -> AgentTaskResult:
        """Convert the EDA result to the fleet transport envelope."""
        return result.to_agent_task_result()

    async def act(self, task: TaskSpec, context: Any) -> TaskResult:
        """Dispatch to planning or tool execution based on the agent's role.

        Args:
            task: Fully prepared ``TaskSpec`` for this invocation.
            context: Assembled ``ContextPackage`` (or compatible object). Lead
                and worker paths currently discard it after journaling, but
                subclasses may override ``plan`` / ``execute_tools`` to use it.

        Returns:
            A domain ``TaskResult`` describing outcome, reason, and observations.

        Side effects:
            Delegates to ``plan`` or ``execute_tools``, which may publish
            memory records and invoke tool callables.

        Failures:
            Propagates permission, import, and adapter errors from the
            delegated path.
        """
        # Leads propose child workflows; everyone else runs declared tools.
        if self.spec.role == AgentRole.LEAD:
            return await self.plan(task, context)
        # Workers and validators share the execute_tools entry, then diverge.
        return await self.execute_tools(task, context)

    async def plan(self, task: TaskSpec, context: Any) -> TaskResult:
        """Propose a child workflow and optionally invoke unbound lead tools.

        Builds a ``WorkflowSpec`` from explicit ``plan_steps`` or from
        ``delegates_to`` (workers first, then validators depending on all
        workers). Publishes the graph as a provisional ``WORKFLOW_REVISION``
        so other agents can see the proposal. Then invokes any tools declared
        on the lead; those typically hit the no-op EDA adapter until a real
        framework is bound.

        Args:
            task: The lead's inbound task (objective is copied onto steps that
                omit their own objective).
        context: Assembled context package passed into declared operations as
            adapter parameters alongside the planning task.

        Returns:
            ``TaskResult`` with ``COMPLETED`` / ``WORKFLOW_PROPOSED``, the
            serialized workflow, and any tool observations.

        Side effects:
            Publishes a provisional workflow revision into engineering memory.
            May execute declared lead tool functions for observations.

        Failures:
            Propagates ``CatalogError`` when derived steps reference unknown
            agents. Propagates ``AgentPermissionError`` from tool actions.
        """
        # Materialize the dependency graph the fleet can schedule later.
        workflow = build_workflow(self.spec, task)
        # Scope for the published workflow revision matches the parent task.
        scope = self._scope(task)
        # Make the proposal visible to other agents as a provisional record.
        await self.memory.publish(
            scope=scope,
            record_type=RecordType.WORKFLOW_REVISION,
            summary=f"{self.spec.display_name} proposed {len(workflow.tasks)} task(s)",
            payload=workflow.model_dump(mode="json"),
            idempotency_key=f"{task.idempotency_key}:workflow",
            agent_id=self.spec.agent_id,
            task_id=task.task_id,
            schema_record_name="eda.workflow",
            validation_state=ValidationState.PROVISIONAL,
            design_revision=task.design_revision,
        )
        # Leads may still run declared operations (often no-op until bound).
        observations = await self._invoke_declared_tools(task, context)
        # Report that children were proposed but not executed in this process.
        return TaskResult(
            task_id=task.task_id,
            outcome=TaskOutcome.COMPLETED,
            reason_code="WORKFLOW_PROPOSED",
            summary=(
                f"{self.spec.display_name} proposed a {len(workflow.tasks)}-task workflow "
                f"and invoked {len(observations)} declared operation(s). "
                "Child agents have not run."
            ),
            workflow=workflow.model_dump(mode="json"),
            observations=observations,
        )

    async def execute_tools(self, task: TaskSpec, context: Any) -> TaskResult:
        """Invoke every tool declared on the agent spec and wrap the observations.

        Workers return a partial completion with ``FRAMEWORK_UNBOUND`` because
        the default path does not run a real EDA framework. Validators defer
        to ``_validator_result``, which also records a provisional gate.

        Args:
            task: Inbound task used for permission checks and result identity.
            context: Assembled context package forwarded to declared adapters
                through their conventional ``params`` mapping.

        Returns:
            ``TaskResult`` with observations; validators include a resume
            checkpoint pointing at the published gate memory id.

        Side effects:
            Executes each declared tool callable after permission checks.
            Validators additionally publish a gate decision record.

        Failures:
            Propagates ``AgentPermissionError``, ``ImportError``, and errors
            raised by individual tool functions.
        """
        # Run every skill listed in config.yaml under action policy.
        observations = await self._invoke_declared_tools(task, context)
        # Validators must also emit a gate envelope, even when unbound.
        if self.spec.role == AgentRole.VALIDATOR:
            return await self._validator_result(task, observations)
        # Workers stop here: tools ran (or no-op'd) without engineering acceptance.
        return TaskResult(
            task_id=task.task_id,
            outcome=TaskOutcome.PARTIALLY_COMPLETED,
            reason_code="FRAMEWORK_UNBOUND",
            summary=(
                f"{self.spec.display_name} invoked {len(observations)} tool(s). "
                "No EDA framework ran, so this is not an engineering acceptance."
            ),
            observations=observations,
        )

    async def _validator_result(self, task: TaskSpec, observations: list[dict[str, Any]]) -> TaskResult:
        """Publish a provisional gate stating that independent checks did not run.

        Until a real framework is bound, validators must not claim the candidate
        passed. This method records ``passed: False``, attaches observations,
        and returns a partial completion whose ``resume_checkpoint`` is the
        gate's ``memory_id`` so a later retry can find it.

        Args:
            task: Validator task; ``inputs["candidate"]`` names the subject.
            observations: Dict payloads returned from declared tool callables.

        Returns:
            ``TaskResult`` with ``PARTIALLY_COMPLETED`` / ``FRAMEWORK_UNBOUND``
            and ``resume_checkpoint`` set to the gate record id.

        Side effects:
            Publishes a provisional ``GATE_DECISION`` into engineering memory.

        Failures:
            Propagates memory policy and store errors from ``publish``.
        """
        # Candidate under review; empty string when the task omitted it.
        candidate = str(task.inputs.get("candidate", ""))
        # Gate is written into the same design scope as the parent task.
        scope = self._scope(task)
        # Record that checks did not run; do not claim the candidate passed.
        gate = await self.memory.publish(
            scope=scope,
            record_type=RecordType.GATE_DECISION,
            summary="Independent checks did not run because no framework is bound.",
            payload={
                "passed": False,
                "candidate": candidate,
                "validator": self.spec.agent_id,
                "observations": observations,
            },
            idempotency_key=f"{task.idempotency_key}:gate",
            agent_id=self.spec.agent_id,
            task_id=task.task_id,
            validation_state=ValidationState.PROVISIONAL,
            schema_record_name="eda.gate-decision",
            design_revision=task.design_revision,
        )
        # Point resume_checkpoint at the gate so callers can resume from it.
        return TaskResult(
            task_id=task.task_id,
            outcome=TaskOutcome.PARTIALLY_COMPLETED,
            reason_code="FRAMEWORK_UNBOUND",
            summary=(
                f"{self.spec.display_name} recorded a provisional gate. "
                "The candidate was not graded."
            ),
            observations=observations,
            resume_checkpoint=gate.memory_id,
        )

    async def _invoke_declared_tools(self, task: TaskSpec, context: Any) -> list[dict[str, Any]]:
        """Permission-check and call every tool listed on ``self.spec.tools``.

        Each tool's ``action`` is asserted against role and task boundaries
        before the callable runs. Non-dict return values are wrapped as
        ``{"value": raw}`` so observations stay JSON-object shaped.

        Args:
            task: Task whose allow/forbid lists constrain tool actions.

        Returns:
            A list of observation dictionaries, one per declared tool, in
            declaration order.

        Side effects:
            Executes each tool function from the agent's ``tools.py`` module.
            May load and cache that module on first use.

        Failures:
            Raises ``AgentPermissionError`` when an action is forbidden.
            Raises ``ImportError`` when ``tools.py`` cannot be loaded.
            Raises ``AttributeError`` when a declared name is missing.
        """
        if self.skills is None:
            raise RuntimeError(
                "EdaAgent requires the SDK SkillRegistry; construct it through AgentService."
            )
        # Accumulate observation dicts in the order tools are declared.
        observations: list[dict[str, Any]] = []
        # Walk the ToolSpec list from config.yaml skills.
        for tool_spec in self.spec.tools:
            # Enforce role matrix and task allow/forbid before any side effects.
            self.assert_action(tool_spec.action, task)
            # Inputs match declared parameters; context is available to adapters
            # through their conventional ``params`` payload.
            arguments = {
                param.name: task.inputs[param.name]
                for param in tool_spec.params
                if param.name in task.inputs and param.name != "params"
            }
            if self.skills.accepts_argument(tool_spec.name, "params"):
                arguments["params"] = {
                    **task.inputs,
                    "context": self._context_payload(context),
                    "task_id": task.task_id,
                    "objective": task.objective,
                }
            # The SDK registry applies capability parameters, skill timeouts,
            # tracing, and both synchronous and asynchronous invocation rules.
            call = await self.skills.call(tool_spec.name, **arguments)
            raw = call.result
            # Normalize scalar/list returns into a JSON object observation.
            if not isinstance(raw, dict):
                raw = {"value": raw}
            # Preserve the SDK-resolved invocation contract with every
            # observation so downstream adapters can audit input/context use.
            raw.setdefault("input", call.args)
            # Keep the observation for the TaskResult payload.
            observations.append(raw)
        # Return all observations in declaration order.
        return observations

    @staticmethod
    def _context_payload(context: Any) -> dict[str, Any]:
        """Serialize assembled context for adapter parameters without coupling SDK."""
        if hasattr(context, "model_dump"):
            return context.model_dump(mode="json")
        if isinstance(context, dict):
            return context
        return {"value": str(context)}

    def assert_action(self, action: ToolAction, task: TaskSpec) -> None:
        """Raise ``AgentPermissionError`` when this agent may not perform ``action``.

        Checks run in order: task forbidden list, task allow-list (when
        non-empty), then the static ``ROLE_ACTIONS`` matrix for the agent's
        role. Any failure aborts before the tool callable runs.

        Args:
            action: The ``ToolAction`` declared on a ``ToolSpec``.
            task: The current ``TaskSpec`` carrying allow/forbid lists.

        Returns:
            None when the action is permitted.

        Side effects:
            None on success.

        Failures:
            Raises ``AgentPermissionError`` with a message naming the agent,
            action, or role that forbade the call.
        """
        # Task-level forbid list always wins, even for otherwise-legal roles.
        if action.value in task.forbidden_actions:
            raise AgentPermissionError(f"{self.spec.agent_id} cannot {action.value} on this task")
        # Non-empty allow-list is a closed set; empty means "no extra filter".
        if task.allowed_actions and action.value not in task.allowed_actions:
            raise AgentPermissionError(f"{action.value} is outside the task's allowed actions")
        # Role matrix is the last gate: leads cannot emit gates, etc.
        if action not in ROLE_ACTIONS[self.spec.role]:
            raise AgentPermissionError(f"{self.spec.role.value} agents cannot {action.value}")

    def _scope(self, task: TaskSpec) -> MemoryScope:
        """Build the engineering-memory scope for journaling and publishing.

        Args:
            task: Task whose project, revision, subsystem, block, and stage
                fields define the logical ``/programs/...`` path.

        Returns:
            A ``MemoryScope`` using the agent's configured stage when the task
            leaves ``stage`` empty.

        Side effects:
            None.

        Failures:
            None; empty strings are valid and mean "whole program" for that
            dimension at query time.
        """
        # Map task fields onto the shared MemoryScope path model.
        return MemoryScope(
            project=task.project_id,
            revision=task.design_revision,
            subsystem=task.subsystem,
            block=task.block,
            stage=task.stage or self.spec.stage,
        )

    def _failure(self, task: TaskSpec, outcome: TaskOutcome, reason: str, summary: str) -> AgentTaskResult:
        """Build a fleet failure result without journaling a finished checkpoint.

        Used when ``handle`` catches permission or timeout errors after context
        assembly may already have started. The started checkpoint (if written)
        remains; there is no matching finished append on this path.

        Args:
            task: Task whose id is copied into the result.
            outcome: Domain outcome (retryable vs non-retryable).
            reason: Machine-readable reason code such as ``PERMISSION_DENIED``.
            summary: Human-readable explanation, usually ``str(exc)``.

        Returns:
            An ``AgentTaskResult`` produced via ``TaskResult.to_agent_task_result``.

        Side effects:
            None beyond constructing the result object.

        Failures:
            None.
        """
        # Wrap the domain failure and convert it for the HTTP executor.
        return TaskResult(
            task_id=task.task_id,
            outcome=outcome,
            reason_code=reason,
            summary=summary,
        ).to_agent_task_result()


def workflow_from_result(result: AgentTaskResult) -> Optional[WorkflowSpec]:
    """Extract a typed ``WorkflowSpec`` from a fleet task result's artifacts.

    Lead agents embed the proposed workflow under ``artifacts["workflow"]``.
    Fleet planners and parent leads call this helper to recover the graph
    without re-importing the lead process.

    Args:
        result: Fleet ``AgentTaskResult`` that may carry a workflow artifact.

    Returns:
        A validated ``WorkflowSpec`` when the artifact is a dict shaped like
        a workflow; otherwise ``None``.

    Side effects:
        None.

    Failures:
        Propagates Pydantic validation errors when the dict is present but
        malformed.
    """
    # Pull the optional workflow blob from the artifacts map.
    raw = (result.artifacts or {}).get("workflow")
    # Absent or non-dict artifacts mean no recoverable workflow.
    if not isinstance(raw, dict):
        return None
    # Validate into the versioned eda.workflow/v1 model.
    return WorkflowSpec.model_validate(raw)
