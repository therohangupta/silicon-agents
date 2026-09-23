"""Inter-agent and tool-facing message schemas for the EDA domain.

These models are the typed payloads agents publish into memory, embed in
task results, or exchange as structured messages. Prose summaries are never
a substitute for the payload: ``AgentMessage`` carries a ``payload_type`` and
optional ``payload_ref``, findings carry evidence refs, gates carry pass/fail
and checks, experiments carry hypotheses and metrics, and workflows carry
dependency graphs.

``ToolObservation`` is what framework adapters return. ``status="not_run"``
means the no-op adapter recorded intent without executing a tool — metrics
from that path must not be treated as engineering evidence until a real
``EdaAdapter`` is bound.
"""

from __future__ import annotations

# Flexible typing for metrics, checks, and optional nested handles.
from typing import Any, Literal, Optional

# Pydantic models for versioned message documents.
from pydantic import BaseModel, Field

# Evidence pointers embedded in findings and experiments.
from .artifact import ArtifactRef


class Finding(BaseModel):
    """Structured agent finding with severity, scope, and evidence.

    Published as ``RecordType.AGENT_FINDING`` payloads (or cited from task
    results). ``EngineeringMemory.publish`` requires non-empty evidence for
    finding record types at the envelope layer.

    Attributes:
        schema_name: Fixed discriminator ``eda.finding/v1``.
        finding_id: Stable id for this finding.
        summary: Short description of the issue or observation.
        severity: Severity label; defaults to ``medium``.
        scope: Optional scope path or label the finding applies to.
        evidence: Artifact refs backing the claim.
        affected_requirements: Requirement ids implicated by the finding.
        recommended_recipient: Suggested next agent or human owner.
        confidence: Optional model or heuristic confidence score.
    """

    # Schema discriminator for versioned findings.
    schema_name: Literal["eda.finding/v1"] = "eda.finding/v1"
    # Stable identity for dedup and supersession.
    finding_id: str
    # Human-readable statement of what was found.
    summary: str
    # Severity band used by triage UIs.
    severity: str = "medium"
    # Optional scope string (often a MemoryScope.path).
    scope: str = ""
    # Evidence artifacts; required at publish for AGENT_FINDING envelopes.
    evidence: list[ArtifactRef] = Field(default_factory=list)
    # Requirement ids this finding touches.
    affected_requirements: list[str] = Field(default_factory=list)
    # Suggested recipient for follow-up work.
    recommended_recipient: str = ""
    # Optional confidence in [0, 1] or tool-specific scale.
    confidence: Optional[float] = None


class AgentMessage(BaseModel):
    """Typed inter-agent message. Prose is a summary, not the payload.

    Use ``payload_type`` and ``payload_ref`` (or an out-of-band memory id) to
    point at the real structured document. The ``summary`` field is for
    operators and logs only.
    """

    # Schema discriminator for versioned inter-agent messages.
    schema_name: Literal["eda.agent-message/v1"] = "eda.agent-message/v1"
    # Unique message id for transport deduplication.
    message_id: str
    # Program / project the message belongs to.
    program_id: str
    # Task that caused this message to be sent.
    task_id: str
    # Sending agent id.
    sender: str
    # Intended receiving agent id or role.
    recipient: str
    # Type name of the structured payload (e.g. eda.finding/v1).
    payload_type: str
    # Optional URI or memory id where the payload lives.
    payload_ref: str = ""
    # Operator-facing prose; must not be the only carrier of meaning.
    summary: str
    # Optional action the recipient is asked to take.
    requested_action: str = ""


class JobHandle(BaseModel):
    """Durable handle for a tool job. The scheduler owns the run, not the model session.

    Agents submit jobs and retain this handle for heartbeats, checkpoints, and
    final status. The no-op adapter returns a handle in ``not_submitted`` state
    with scheduler ``none``.
    """

    # Schema discriminator for versioned job handles.
    schema_name: Literal["eda.job-handle/v1"] = "eda.job-handle/v1"
    # Scheduler-assigned or locally generated job id.
    job_id: str
    # Scheduler implementation name (local, cluster, none, ...).
    scheduler: str = "local"
    # Native id inside that scheduler when different from job_id.
    scheduler_id: str = ""
    # Task that submitted the job.
    task_id: str = ""
    # Design revision the job inputs were taken from.
    input_revision: str = ""
    # Workspace path the job runs in.
    workspace: str = ""
    # Manifest describing the command line / script.
    command_manifest: str = ""
    # Digest of the execution environment.
    environment_digest: str = ""
    # Latest checkpoint id for resume.
    latest_checkpoint: str = ""
    # Last heartbeat timestamp or token.
    heartbeat: str = ""
    # Coarse job lifecycle state.
    state: Literal["not_submitted", "queued", "running", "succeeded", "failed"] = "not_submitted"


class GateDecision(BaseModel):
    """Validator gate outcome for a named candidate.

    Promotion via ``EngineeringMemory.promote_candidate`` requires matching
    gate records in memory with ``validation_state=validated``,
    ``payload.passed is True``, and ``payload.candidate`` equal to the
    candidate under promotion. This model is the structured payload shape.
    """

    # Schema discriminator for versioned gate decisions.
    schema_name: Literal["eda.gate-decision/v1"] = "eda.gate-decision/v1"
    # Stable gate id (often equals the memory_id or a logical name).
    gate_id: str
    # Task that produced the gate.
    task_id: str
    # Candidate revision or artifact id under review.
    candidate: str
    # Whether the candidate passed the gate's checks.
    passed: bool
    # Human-readable gate summary.
    summary: str
    # Per-check detail dicts (names and results).
    checks: list[dict[str, Any]] = Field(default_factory=list)
    # Validator agent id that emitted the gate.
    validator: str = ""


class ExperimentRecord(BaseModel):
    """Experiment hypothesis, controls, metrics, and evidence.

    ``EngineeringMemory.record_experiment`` publishes this model as an
    ``EXPERIMENT_RESULT`` with ``REGISTERED_REQUIRED`` schema status and
    provisional validation until independently confirmed.
    """

    # Schema discriminator for versioned experiments.
    schema_name: Literal["eda.experiment/v1"] = "eda.experiment/v1"
    # Stable experiment id for QoR joins and lookups.
    experiment_id: str
    # Hypothesis under test; also used as the memory summary.
    hypothesis: str
    # Baseline the experiment compares against.
    baseline: str
    # Variables intentionally changed for this run.
    variables_changed: list[str] = Field(default_factory=list)
    # Variables held fixed as controls.
    conditions_held_fixed: list[str] = Field(default_factory=list)
    # Measured metrics keyed by name.
    metrics: dict[str, Any] = Field(default_factory=dict)
    # Hard constraints evaluated during the experiment.
    hard_constraints: dict[str, Any] = Field(default_factory=dict)
    # Tool that executed the experiment.
    tool: str = ""
    # Tool version for reproducibility.
    tool_version: str = ""
    # Rule that decided when to stop iterating.
    stopping_rule: str = ""
    # Outcome label (e.g. confirmed, rejected, inconclusive).
    outcome: str = ""
    # Evidence artifacts; their URIs become envelope evidence refs.
    evidence: list[ArtifactRef] = Field(default_factory=list)


class Decision(BaseModel):
    """Recorded engineering decision with alternatives and rationale.

    When published as ``RecordType.DECISION``, the memory plane may also
    project the decision into Postgres decision tables via ``record_decision``.
    """

    # Schema discriminator for versioned decisions.
    schema_name: Literal["eda.decision/v1"] = "eda.decision/v1"
    # Stable decision id.
    decision_id: str
    # Owner agent or human responsible for the decision.
    owner: str
    # Scope path or label the decision applies to.
    scope: str
    # Short statement of what was decided.
    summary: str
    # Alternatives that were considered.
    alternatives: list[str] = Field(default_factory=list)
    # Evidence refs or memory ids supporting the choice.
    evidence: list[str] = Field(default_factory=list)
    # Why this alternative was chosen.
    rationale: str = ""
    # Condition under which the decision should be revisited.
    revisit_condition: str = ""


class ProposedTask(BaseModel):
    """One node in a lead-proposed workflow dependency graph.

    Produced by ``planning.build_workflow`` from ``EDADelegationStep`` objects. The
    fleet scheduler uses ``depends_on`` to order execution across agents.
    """

    # Step id unique within the parent WorkflowProposal.
    id: str
    # registered agent_id that should run this node.
    agent_type: str
    # Capability id the assignee must provide.
    capability: str
    # Prerequisite step ids within the same workflow.
    depends_on: list[str] = Field(default_factory=list)
    # Objective for this child task.
    objective: str = ""


class WorkflowProposal(BaseModel):
    """Versioned dependency graph a lead returns instead of doing the child work.

    Published as a provisional ``WORKFLOW_REVISION`` and also embedded under
    ``TaskResult.workflow`` / fleet artifacts for planners to extract via
    ``workflow_from_result``.
    """

    # Schema discriminator for versioned workflows.
    schema_name: Literal["eda.workflow/v1"] = "eda.workflow/v1"
    # Typically lead_agent_id:parent_task_id.
    workflow_id: str
    # Parent task that caused this proposal.
    parent_task_id: str
    # Lead agent that authored the graph.
    parent_agent: str
    # Ordered list of child workflow tasks with dependencies.
    tasks: list[ProposedTask] = Field(default_factory=list)


class ToolObservation(BaseModel):
    """What a framework adapter returns. status=not_run means nothing was executed.

    Agents must not treat metrics from ``not_run`` observations as engineering
    evidence. Bind a real ``EdaAdapter`` before trusting tool output.
    """

    # Schema discriminator for versioned tool observations.
    schema_name: Literal["eda.tool-observation/v1"] = "eda.tool-observation/v1"
    # Adapter framework name that handled the call (e.g. unbound, openroad).
    framework: str
    # Framework the operator intended via EDA_FRAMEWORK when unbound.
    intended_framework: str = ""
    # Named operation the agent requested.
    operation: str
    # Lifecycle status of the underlying tool run.
    status: Literal["not_run", "queued", "succeeded", "failed"] = "not_run"
    # Human-readable outcome of the invocation attempt.
    summary: str
    # Metrics dict; empty when nothing ran.
    metrics: dict[str, Any] = Field(default_factory=dict)
    # Artifacts produced by a real run.
    artifact_refs: list[ArtifactRef] = Field(default_factory=list)
    # Optional durable job handle for async runs.
    job: Optional[JobHandle] = None
    # Agent that requested the operation.
    agent_id: str = ""
