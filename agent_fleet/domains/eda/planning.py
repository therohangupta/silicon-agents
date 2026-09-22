"""Lead planning helpers: turn agent specs into executable workflow graphs.

When a lead ``EdaAgent`` runs ``plan``, it needs a ``WorkflowSpec`` the fleet
can schedule later. This module builds that graph without executing child
agents. Two sources of structure are supported:

* Explicit ``plan_steps`` on the ``AgentSpec`` (from the YAML ``plan`` block).
* Derived steps from ``delegates_to`` when no plan is declared: workers become
  independent first-wave tasks; validators depend on every worker step so
  gates run after producers finish.

Each ``PlanStep`` becomes a ``WorkflowTask`` with id, agent type, capability,
dependencies, and objective. Capability defaults come from the child spec:
leads advertise ``delegate_tasks``, workers/validators use their first tool
name, and a bare ``agent_type`` is the last resort.

``get_spec`` is imported lazily inside helpers so importing ``planning`` does
not force a full catalog load until derivation actually needs child metadata.
"""

from __future__ import annotations

# Lead identity and the PlanStep model used when deriving or copying plans.
from .spec import AgentSpec, PlanStep
# Role enum distinguishes workers from validators during derivation.
from .schemas.enums import AgentRole
# Versioned workflow graph models returned to EdaAgent.plan for publishing.
from .schemas.messages import WorkflowSpec, WorkflowTask
# Parent task whose objective is copied onto steps that omit their own.
from .schemas.task import TaskSpec


def build_workflow(spec: AgentSpec, task: TaskSpec) -> WorkflowSpec:
    """Turn a lead's declared children into a workflow the fleet can execute later.

    Prefers explicit ``spec.plan_steps``. When that list is empty, derives a
    default graph from ``spec.delegates_to`` via ``_derived_steps``. Does not
    run child agents and does not write memory; the caller publishes the
    result.

    Args:
        spec: Lead ``AgentSpec`` owning the plan or delegates list.
        task: Parent ``TaskSpec``; its objective fills empty step objectives.
            Its ``task_id`` and the lead ``agent_id`` form ``workflow_id``.

    Returns:
        A ``WorkflowSpec`` with one ``WorkflowTask`` per step, including
        dependency edges and capability strings.

    Side effects:
        May load the agent catalog when deriving steps or capabilities.

    Failures:
        Propagates ``CatalogError`` when a delegated or planned agent id is
        unknown to the registry.
    """
    # Use YAML plan when present; otherwise synthesize from delegates_to.
    steps = list(spec.plan_steps) or _derived_steps(spec)
    # Accumulate WorkflowTask models in step order.
    tasks: list[WorkflowTask] = []
    # Convert each PlanStep into a fleet-facing WorkflowTask.
    for step in steps:
        tasks.append(WorkflowTask(
            id=step.id,
            agent_type=step.agent_type,
            # Prefer explicit capability; else look up a sensible default.
            capability=step.capability or _primary_capability(step.agent_type),
            depends_on=list(step.depends_on),
            # Inherit parent objective when the step left it blank.
            objective=step.objective or task.objective,
        ))
    # Identify the workflow by lead + parent task for idempotent publishing.
    return WorkflowSpec(
        workflow_id=f"{spec.agent_id}:{task.task_id}",
        parent_task_id=task.task_id,
        parent_agent=spec.agent_id,
        tasks=tasks,
    )


def _derived_steps(spec: AgentSpec) -> list[PlanStep]:
    """Derive plan steps from ``delegates_to`` when no explicit plan exists.

    Workers become independent steps. Validators are appended afterward with
    ``depends_on`` listing every prior step id, so validation waits for all
    worker outputs in the default topology.

    Args:
        spec: Lead spec whose ``delegates_to`` lists child agent ids.

    Returns:
        A list of ``PlanStep`` objects ready for ``build_workflow``.

    Side effects:
        Loads child specs through ``get_spec`` (may warm the catalog cache).

    Failures:
        Propagates ``CatalogError`` for unknown delegate ids.
    """
    # Lazy import avoids circular import and defers catalog I/O.
    from .registry import get_spec

    # Partition delegates into producers vs gate agents.
    workers: list[str] = []
    validators: list[str] = []
    # Classify each delegated agent by role.
    for agent_id in spec.delegates_to:
        child = get_spec(agent_id)
        # Validators always run after workers in the derived graph.
        if child.role == AgentRole.VALIDATOR:
            validators.append(agent_id)
        else:
            workers.append(agent_id)
    # First wave: one step per worker with no dependencies.
    steps = [PlanStep(id=agent_id, agent_type=agent_id) for agent_id in workers]
    # Second wave: validators depend on every step collected so far.
    for agent_id in validators:
        steps.append(PlanStep(
            id=agent_id,
            agent_type=agent_id,
            depends_on=[step.id for step in steps],
        ))
    # Return the combined ordered list (workers then validators).
    return steps


def _primary_capability(agent_type: str) -> str:
    """Choose a default capability string for a workflow task's agent type.

    Args:
        agent_type: Catalog ``agent_id`` of the child agent.

    Returns:
        ``delegate_tasks`` for leads, the first tool name when tools exist,
        otherwise the raw ``agent_type`` string.

    Side effects:
        May load the catalog via ``get_spec``.

    Failures:
        Propagates ``CatalogError`` when ``agent_type`` is unknown.
    """
    # Lazy import for the same circular-import reasons as _derived_steps.
    from .registry import get_spec

    # Resolve the child so we can inspect role and tools.
    spec = get_spec(agent_type)
    # Nested leads advertise workflow proposal rather than a concrete tool.
    if spec.role == AgentRole.LEAD:
        return "delegate_tasks"
    # Prefer the first declared tool as the primary capability id.
    if spec.tools:
        return spec.tools[0].name
    # Last resort: use the agent id itself as the capability token.
    return agent_type
