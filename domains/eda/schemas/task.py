"""Task and result schemas that bound agent work for the EDA fleet.

Conversations are not the contract. A ``TaskSpec`` is a bounded unit of work
with objective, design scope, constraints, allow/forbid action lists, and an
optional resource budget. Agents receive it either embedded under
``request.inputs["task"]`` or synthesized from the looser fleet
``AgentTaskRequest`` fields via ``TaskSpec.from_request``.

``TaskResult`` is the domain answer: outcome enum, reason code, summary,
evidence, observations, and optional workflow payload. ``to_agent_task_result``
maps that into the fleet ``AgentTaskResult`` the HTTP executor stores.
Engineering status stays in ``outcome``; fleet ``success`` only means the
executor can keep the result and continue, which includes partial completions
when frameworks are still unbound.
"""

from __future__ import annotations

# Flexible typing for inputs, constraints, and observation payloads.
from typing import Any, Literal, Optional

# Pydantic models for validated task contracts.
from pydantic import BaseModel, Field

# Fleet request/result envelopes we convert to and from.
from packages.agent_sdk.src.models import AgentTaskRequest, AgentTaskResult
# Evidence pointers attached to results.
from .artifact import ArtifactRef
# Outcome enum that drives success/replan mapping.
from .enums import TaskOutcome


class ResourceBudget(BaseModel):
    """Optional caps on compute, experiments, licenses, and model tokens.

    Planners and schedulers may read these fields; the default ``EdaAgent``
    path does not enforce them itself. Empty/None values mean "unspecified".

    Attributes:
        max_cpu_hours: Soft or hard CPU-hour budget for the task.
        max_experiments: Cap on experiment iterations.
        wall_clock_deadline: ISO-like deadline string when set.
        eda_licenses: Named licenses the task is allowed to consume.
        max_model_tokens: Cap on LLM tokens for agents that call models.
    """

    # Optional CPU-hour ceiling for tool jobs under this task.
    max_cpu_hours: Optional[float] = None
    # Optional limit on how many experiments may be run.
    max_experiments: Optional[int] = None
    # Optional wall-clock deadline string interpreted by the scheduler.
    wall_clock_deadline: str = ""
    # License names the task may draw from the shared pool.
    eda_licenses: list[str] = Field(default_factory=list)
    # Optional LLM token budget for model-using agents.
    max_model_tokens: Optional[int] = None


class TaskSpec(BaseModel):
    """Bounded unit of work. Conversations are not the contract.

    Carries design scope (project, revision, subsystem, block, stage), hard
    and soft objectives, free-form inputs, permission lists, resource budget,
    and idempotency key. ``EdaAgent.handle`` fills missing idempotency and
    stage from the agent identity when they are empty.

    Attributes:
        schema_name: Fixed discriminator ``eda.task/v1``.
        task_id: Stable id for journaling and results.
        objective: Human-readable goal for this unit of work.
        project_id: Engineering-memory project; defaults to ``sandbox``.
        design_revision: Revision string for scope filtering.
        subsystem: Optional subsystem label under the project.
        block: Optional block label under the subsystem.
        stage: Flow stage; may default from the agent spec.
        hard_constraints: Must-satisfy constraint map.
        soft_objectives: Preferential objective map.
        inputs: Free-form input bag (e.g. ``candidate`` for validators).
        allowed_actions: When non-empty, closed set of permitted ToolActions.
        forbidden_actions: Always-denied ToolAction values.
        resources: Optional ``ResourceBudget``.
        validator: Optional preferred validator agent id.
        idempotency_key: Dedup key for memory append/publish.
        required_capabilities: Capability ids the assignee must advertise.
    """

    # Schema discriminator for versioned task documents.
    schema_name: Literal["eda.task/v1"] = "eda.task/v1"
    # Identity used in TaskResult and memory journal keys.
    task_id: str
    # What the agent is asked to accomplish.
    objective: str
    # Memory project namespace; sandbox for ad-hoc local runs.
    project_id: str = "sandbox"
    # Design revision for scope and baseline compatibility.
    design_revision: str = ""
    # Optional subsystem segment in MemoryScope.
    subsystem: str = ""
    # Optional block segment in MemoryScope.
    block: str = ""
    # Optional stage; EdaAgent fills from AgentSpec.stage when empty.
    stage: str = ""
    # Constraints that must hold for acceptance.
    hard_constraints: dict[str, Any] = Field(default_factory=dict)
    # Soft goals the agent should optimize toward.
    soft_objectives: dict[str, Any] = Field(default_factory=dict)
    # Free-form inputs such as candidate ids or prior artifact uris.
    inputs: dict[str, Any] = Field(default_factory=dict)
    # Closed allow-list of ToolAction values when non-empty.
    allowed_actions: list[str] = Field(default_factory=list)
    # Absolute deny-list of ToolAction values.
    forbidden_actions: list[str] = Field(default_factory=list)
    # Optional resource caps for schedulers.
    resources: ResourceBudget = Field(default_factory=ResourceBudget)
    # Preferred validator agent id when the producer names one.
    validator: str = ""
    # Dedup key; defaulted to agent_id:task_id when empty at handle time.
    idempotency_key: str = ""
    # Capability ids required of the assignee.
    required_capabilities: list[str] = Field(default_factory=list)

    @classmethod
    def from_request(cls, request: AgentTaskRequest) -> "TaskSpec":
        """Build a ``TaskSpec`` from a fleet ``AgentTaskRequest``.

        Preferentially validates ``request.inputs["task"]`` when it is a dict,
        filling ``task_id`` and ``objective`` from the request when missing.
        Otherwise synthesizes a minimal spec from description, plan id,
        inputs, and required capabilities.

        Args:
            request: Inbound fleet task request.

        Returns:
            A validated ``TaskSpec``.

        Side effects:
            None.

        Failures:
            Propagates Pydantic validation errors when the embedded task dict
            is present but malformed.
        """
        # Prefer a fully embedded eda.task/v1 document under inputs["task"].
        raw = request.inputs.get("task") if isinstance(request.inputs, dict) else None
        if isinstance(raw, dict):
            # Copy so we can fill defaults without mutating the request.
            data = dict(raw)
            # Ensure identity fields exist even if the embed omitted them.
            data.setdefault("task_id", request.task_id)
            data.setdefault("objective", request.description)
            # Validate into the TaskSpec model.
            return cls.model_validate(data)
        # No embed: derive project from plan_id when the fleet provided one.
        project = str(request.plan_id) if request.plan_id is not None else "sandbox"
        # Synthesize a minimal task from the loose fleet fields.
        return cls(
            task_id=request.task_id,
            objective=request.description,
            project_id=project,
            inputs=dict(request.inputs or {}),
            required_capabilities=list(request.required_capabilities or []),
        )


class TaskResult(BaseModel):
    """Domain result returned by ``EdaAgent`` before fleet conversion.

    Carries the engineering ``TaskOutcome``, a machine-readable reason code,
    human summary, evidence refs, observations from tools, and an optional
    workflow dict when a lead proposed children.

    Attributes:
        schema_name: Fixed discriminator ``eda.task-result/v1``.
        task_id: Echo of the inbound task id.
        outcome: Engineering outcome enum.
        reason_code: Short machine code (e.g. ``WORKFLOW_PROPOSED``).
        summary: Human-readable explanation.
        evidence: Artifact refs supporting the result.
        affected_requirements: Requirement ids touched by the work.
        recommended_recipient: Suggested next agent or human role.
        resume_checkpoint: Memory id to resume from (e.g. gate id).
        observations: Tool observation dicts.
        workflow: Serialized ``WorkflowSpec`` when a lead proposed one.
    """

    # Schema discriminator for versioned task results.
    schema_name: Literal["eda.task-result/v1"] = "eda.task-result/v1"
    # Must match the TaskSpec.task_id that produced this result.
    task_id: str
    # Engineering outcome the parent workflow interprets.
    outcome: TaskOutcome
    # Machine-readable reason alongside the outcome.
    reason_code: str = ""
    # Operator-facing summary string.
    summary: str
    # Evidence artifacts cited by the agent.
    evidence: list[ArtifactRef] = Field(default_factory=list)
    # Requirement ids affected by this result.
    affected_requirements: list[str] = Field(default_factory=list)
    # Suggested next recipient for findings or handoffs.
    recommended_recipient: str = ""
    # Memory id useful for resume (validator gates use this).
    resume_checkpoint: str = ""
    # Raw tool observation dicts from declared skills.
    observations: list[dict[str, Any]] = Field(default_factory=list)
    # Optional serialized workflow graph from a lead plan.
    workflow: Optional[dict[str, Any]] = None

    def to_agent_task_result(self) -> AgentTaskResult:
        """Convert this domain result into a fleet ``AgentTaskResult``.

        The fleet executor marks a task failed whenever ``success`` is false,
        and the default policy then replans. Engineering status stays in
        ``outcome``. ``success`` means the agent returned a result the current
        executor can store and continue from (completed or partially
        completed). Replan outcomes set ``replan=True``.

        Returns:
            An ``AgentTaskResult`` with artifacts mirroring outcome, reason,
            observations, optional workflow, and optional recipient.

        Side effects:
            None.

        Failures:
            None beyond construction of nested fleet artifact refs.
        """
        # The fleet executor marks a task failed whenever success is false,
        # and the default policy then replans. Engineering status stays in
        # `outcome`. success means the agent returned a result the current
        # executor can store and continue from.
        # Outcomes that should trigger planner revision.
        replan = self.outcome in {
            TaskOutcome.REPLAN_REQUIRED,
            TaskOutcome.UPSTREAM_CHANGE_REQUIRED,
        }
        # Outcomes the executor treats as storable successes (including partial).
        success = self.outcome in {
            TaskOutcome.COMPLETED,
            TaskOutcome.PARTIALLY_COMPLETED,
        }
        # Always embed outcome/reason/observations for downstream consumers.
        artifacts: dict[str, Any] = {
            "outcome": self.outcome.value,
            "reason_code": self.reason_code,
            "observations": self.observations,
        }
        # Leads attach the proposed workflow graph here.
        if self.workflow is not None:
            artifacts["workflow"] = self.workflow
        # Optional routing hint for the next hop.
        if self.recommended_recipient:
            artifacts["recommended_recipient"] = self.recommended_recipient
        # Build the fleet envelope with converted evidence refs.
        return AgentTaskResult(
            success=success,
            message=self.summary,
            artifacts=artifacts,
            artifact_refs=[ref.to_fleet_ref() for ref in self.evidence],
            replan=replan,
            outcome=self.outcome.value,
            reason_code=self.reason_code,
            # Populate error only when the executor should treat this as failure.
            error=None if success else (self.reason_code or self.outcome.value),
        )
