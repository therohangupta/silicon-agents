"""Enumerations that define EDA task outcomes, memory kinds, roles, and actions.

Every chip-design agent shares these closed sets. They appear on task results,
memory envelopes, agent specs, and permission checks:

* ``TaskOutcome`` tells the parent workflow whether to continue, retry, replan,
  or escalate to a human.
* ``RecordType`` names the engineering-memory envelope kinds placements and
  publish rules key off of.
* ``ValidationState`` ranks trust for context assembly and promotion gates.
* ``PayloadSchemaStatus`` describes how strictly a payload schema is registered.
* ``AuthorKind`` distinguishes human-authored intent/waivers from agent writes.
* ``AgentRole`` selects lead / worker / validator behavior in ``EdaAgent.act``.
* ``ToolAction`` is the permission verb each skill declares in ``config.yaml``.
* ``ROLE_ACTIONS`` is the static matrix ``assert_action`` and catalog validation
  enforce so leads cannot emit gates, workers cannot create workflows, etc.

These enums are string enums so JSON serialization stays human-readable in
memory payloads and fleet artifacts.
"""

from __future__ import annotations

# Standard library enum base for string-valued closed sets.
from enum import Enum


class TaskOutcome(str, Enum):
    """What the parent workflow should do with a finished task.

    ``COMPLETED`` and ``PARTIALLY_COMPLETED`` map to fleet ``success=True``.
    ``REPLAN_REQUIRED`` and ``UPSTREAM_CHANGE_REQUIRED`` set ``replan=True``.
    Other outcomes are failures from the executor's point of view; the richer
    engineering status remains in the ``outcome`` artifact field.
    """

    # Work finished successfully from an engineering perspective.
    COMPLETED = "COMPLETED"
    # Useful progress without full acceptance (e.g. framework still unbound).
    PARTIALLY_COMPLETED = "PARTIALLY_COMPLETED"
    # Cannot proceed until an external blocker clears.
    BLOCKED = "BLOCKED"
    # Transient failure; the fleet may retry the same task.
    RETRYABLE_FAILURE = "RETRYABLE_FAILURE"
    # Permanent failure for this attempt (e.g. permission denied).
    NONRETRYABLE_FAILURE = "NONRETRYABLE_FAILURE"
    # The plan itself is wrong; ask the planner to revise.
    REPLAN_REQUIRED = "REPLAN_REQUIRED"
    # An upstream artifact or decision must change before retrying.
    UPSTREAM_CHANGE_REQUIRED = "UPSTREAM_CHANGE_REQUIRED"
    # A human must choose among alternatives before the flow continues.
    HUMAN_DECISION_REQUIRED = "HUMAN_DECISION_REQUIRED"


class RecordType(str, Enum):
    """Kinds of engineering-memory envelopes written by agents and humans.

    Placement defaults in ``memory.placements`` and publish checks in
    ``EngineeringMemory._check_publish`` key off these values. Context
    include vocabulary maps onto subsets of this set via ``INCLUDE_TYPES``.
    """

    # Human-authored design intent; agents may not publish this type.
    HUMAN_INTENT = "HumanIntent"
    # Requirements the design must satisfy.
    REQUIREMENT = "Requirement"
    # Contracts describing interfaces between blocks or IPs.
    INTERFACE_CONTRACT = "InterfaceContract"
    # Agent findings; publish requires evidence references.
    AGENT_FINDING = "AgentFinding"
    # Experiment hypotheses, metrics, and evidence.
    EXPERIMENT_RESULT = "ExperimentResult"
    # Recorded engineering decisions with rationale.
    DECISION = "Decision"
    # Pointers to versioned artifacts in object storage.
    ARTIFACT_REF = "ArtifactRef"
    # Task-local journal checkpoints (started/finished).
    TASK_CHECKPOINT = "TaskCheckpoint"
    # Proposed or revised lead workflows.
    WORKFLOW_REVISION = "WorkflowRevision"
    # Validator gate outcomes for a candidate.
    GATE_DECISION = "GateDecision"
    # Human-approved waivers; agents may not author them.
    WAIVER = "Waiver"
    # Links to issues in external trackers.
    ISSUE_LINK = "IssueLink"
    # Canonical baseline; only promote_candidate may create these.
    DESIGN_BASELINE = "DesignBaseline"


class ValidationState(str, Enum):
    """Trust ranking for a memory record used by context and promotion.

    Context policies list these as precedence/protect/drop strings. Promotion
    requires gates in the ``validated`` state with ``passed: true``.
    """

    # Written by a human and treated as authoritative input.
    HUMAN_AUTHORED = "human-authored"
    # Passed independent checks; eligible for promotion evidence.
    VALIDATED = "validated"
    # Agent-published but not yet independently confirmed.
    PROVISIONAL = "provisional"
    # Explicitly rejected; always dropped from context.
    REJECTED = "rejected"
    # Replaced by a newer record via supersedes links.
    SUPERSEDED = "superseded"


class PayloadSchemaStatus(str, Enum):
    """How strictly the payload's schema is registered in the platform.

    Experiments use ``REGISTERED_REQUIRED``. Most agent payloads remain
    ``AGENT_DEFINED`` until a schema is formally registered.
    """

    # Payload shape is owned by the writing agent only.
    AGENT_DEFINED = "agent-defined"
    # A registry schema exists but validation is optional.
    REGISTERED_OPTIONAL = "registered-optional"
    # A registry schema exists and must be satisfied.
    REGISTERED_REQUIRED = "registered-required"


class AuthorKind(str, Enum):
    """Who authored the memory envelope.

    Publish rules forbid agents from writing ``HUMAN_INTENT`` or ``WAIVER``
    records; those require ``AuthorKind.HUMAN``.
    """

    # Envelope originated from a human operator or intake path.
    HUMAN = "human"
    # Envelope originated from an agent process.
    AGENT = "agent"


class AgentRole(str, Enum):
    """Runtime role that selects plan vs execute behavior and allowed actions.

    Leads call ``plan``. Workers call ``execute_tools``. Validators call
    ``execute_tools`` then publish a gate via ``_validator_result``.
    """

    # Proposes child workflows; does not execute child tools itself.
    LEAD = "lead"
    # Produces candidates and findings via declared tools.
    WORKER = "worker"
    # Runs checks and emits gate decisions on candidates.
    VALIDATOR = "validator"


# Actions a tool may declare. The role policy allows a subset.
class ToolAction(str, Enum):
    """Permission verb attached to each skill in ``config.yaml``.

    ``EdaAgent.assert_action`` checks the action against the task allow/forbid
    lists and against ``ROLE_ACTIONS[role]`` before invoking the callable.
    """

    # Lead-only: propose a dependency graph for children.
    CREATE_WORKFLOW = "create_workflow"
    # Publish an agent finding (requires evidence at memory publish time).
    PUBLISH_FINDING = "publish_finding"
    # Read reports and memory without mutating candidates.
    READ_REPORTS = "read_reports"
    # Escalate a choice to a human decision-maker.
    REQUEST_HUMAN_DECISION = "request_human_decision"
    # Worker: write a design candidate artifact or revision.
    WRITE_CANDIDATE = "write_candidate"
    # Submit a durable tool job to a scheduler.
    SUBMIT_TOOL_JOB = "submit_tool_job"
    # Validator: emit a gate decision for a candidate.
    EMIT_GATE = "emit_gate"


# Closed matrix of which ToolAction values each AgentRole may declare/use.
ROLE_ACTIONS: dict[AgentRole, frozenset[ToolAction]] = {
    # Leads plan, read, publish findings, and request human decisions.
    AgentRole.LEAD: frozenset({
        ToolAction.CREATE_WORKFLOW,
        ToolAction.PUBLISH_FINDING,
        ToolAction.READ_REPORTS,
        ToolAction.REQUEST_HUMAN_DECISION,
    }),
    # Workers produce candidates, submit jobs, read, and publish findings.
    AgentRole.WORKER: frozenset({
        ToolAction.WRITE_CANDIDATE,
        ToolAction.SUBMIT_TOOL_JOB,
        ToolAction.READ_REPORTS,
        ToolAction.PUBLISH_FINDING,
    }),
    # Validators submit check jobs, read, emit gates, and publish findings.
    AgentRole.VALIDATOR: frozenset({
        ToolAction.SUBMIT_TOOL_JOB,
        ToolAction.READ_REPORTS,
        ToolAction.EMIT_GATE,
        ToolAction.PUBLISH_FINDING,
    }),
}
