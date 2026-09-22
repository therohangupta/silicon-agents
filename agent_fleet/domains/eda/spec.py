"""Agent identity models loaded from each agent's ``config.yaml``.

An ``AgentSpec`` is the typed view of one agent directory: who the agent is,
what role it plays (lead, worker, validator), which tools and actions it
declares, which children a lead may delegate to, how it plans, which port it
listens on, and which engineering-memory sources its context policy requests.

``AgentContext`` is the nested policy object. Include names are EDA vocabulary
resolved by ``ContextService`` into ``RecordType`` values. Precedence, protect,
and drop lists are validation-state strings consumed by the generic context
assembler. Token budget caps how much JSON is admitted into a package.

``ToolSpec`` / ``ToolParam`` describe skills listed under ``skills`` in YAML.
``PlanStep`` describes explicit workflow edges under ``plan``. Helper
``class_name_for`` turns an ``agent_id`` like ``rtl_implementation`` into the
Python class name ``RtlImplementationAgent`` used by generated agent modules.

These models are pure data. Loading and catalog validation live in
``registry.py``. Runtime use lives in ``EdaAgent`` and ``ContextService``.
"""

from __future__ import annotations

# Pydantic base and field helpers for validated, serializable specs.
from pydantic import BaseModel, Field

# Role enum and per-tool action enum enforced by ROLE_ACTIONS at runtime.
from .schemas.enums import AgentRole, ToolAction


def class_name_for(agent_id: str) -> str:
    """Derive the PascalCase agent class name from a snake_case agent id.

    Args:
        agent_id: Catalog identifier such as ``placement_lead``.

    Returns:
        A string like ``PlacementLeadAgent`` formed by capitalizing each
        underscore-separated part and appending ``Agent``.

    Side effects:
        None.

    Failures:
        None; empty parts still concatenate without validation.
    """
    # Capitalize each snake_case segment and suffix with the Agent convention.
    return "".join(part.capitalize() for part in agent_id.split("_")) + "Agent"


class ToolParam(BaseModel):
    """One named parameter declared on a tool skill in ``config.yaml``.

    Parameters are descriptive metadata for planners and documentation. The
    ``EdaAgent`` binds matching task inputs to these parameters and supplies
    the assembled context through a declared ``params`` mapping.

    Attributes:
        name: Python-identifier parameter name (validated by the catalog).
        description: Human-readable explanation of the parameter's meaning.
    """

    # Identifier used in skill param lists; must be a valid Python identifier.
    name: str
    # Free-text description shown in planner catalogs and docs.
    description: str


class ToolSpec(BaseModel):
    """One tool (skill) an agent may invoke, including its permission action.

    The ``name`` must match a callable in the agent's ``tools.py``. The
    ``action`` is checked against ``ROLE_ACTIONS`` and the task's allow/forbid
    lists before invocation. ``params`` document expected inputs for planners.

    Attributes:
        name: Callable name on the tools module.
        description: What the tool does in engineering terms.
        action: ``ToolAction`` that gates whether the role may run it.
        params: Optional list of ``ToolParam`` metadata entries.
    """

    # Must match a function attribute on the agent's tools.py module.
    name: str
    # Shown in planner_catalog capability pairs and operator UIs.
    description: str
    # Permission verb enforced by EdaAgent.assert_action and validate_catalog.
    action: ToolAction
    # Descriptive parameters; default empty when the skill lists none.
    params: list[ToolParam] = Field(default_factory=list)


class PlanStep(BaseModel):
    """One node in a lead's explicit workflow plan from ``config.yaml``.

    When ``plan`` is present in YAML, ``build_workflow`` turns each step into
    a ``WorkflowTask``. When absent, planning derives steps from
    ``delegates_to`` instead.

    Attributes:
        id: Stable step id used in ``depends_on`` edges.
        agent_type: Catalog ``agent_id`` of the child that should run.
        capability: Optional capability id; defaults via registry lookup.
        depends_on: Step ids that must finish before this one.
        objective: Optional override; otherwise inherits the parent objective.
    """

    # Unique within the plan; referenced by other steps' depends_on lists.
    id: str
    # Child agent_id that will receive this workflow task.
    agent_type: str
    # Capability string for the fleet scheduler; empty means derive later.
    capability: str = ""
    # Prerequisite step ids; empty means ready when the workflow starts.
    depends_on: list[str] = Field(default_factory=list)
    # Per-step objective; empty inherits the parent TaskSpec.objective.
    objective: str = ""


class AgentContext(BaseModel):
    """Which engineering-memory sources this agent asks for, and how to rank them.

    ``include`` names are resolved by ``ContextService`` to record types such
    as requirements or gate decisions. ``exclude`` names filter stale,
    provisional, or unrelated-block records before budgeting. ``drop`` lists
    validation states the generic assembler should discard. ``precedence``
    orders surviving validation states. ``protect`` marks states that should
    not be dropped under budget pressure. ``token_budget`` caps approximate
    JSON size admitted into the package.

    This object is loaded from the ``context:`` block of ``config.yaml`` and
    attached to ``AgentSpec.context``. Every agent must declare ``include``
    and ``precedence`` or catalog loading fails.
    """

    # Vocabulary tokens mapped through INCLUDE_TYPES in context.py.
    include: list[str]
    # Optional filters such as stale_candidates or unverified_agent_claims.
    exclude: list[str] = Field(default_factory=list)
    # Validation-state strings the assembler drops; default rejects rejected.
    drop: list[str] = Field(default_factory=lambda: ["rejected"])
    # Ordered validation-state strings from highest to lowest priority.
    precedence: list[str]
    # States shielded from budget omission when possible.
    protect: list[str] = Field(default_factory=list)
    # Approximate token cap passed to packages.memory.context.assemble.
    token_budget: int = 80_000


class AgentSpec(BaseModel):
    """Identity, boundary, tools, and context policy for one agent directory.

    Produced by ``registry.load_spec`` from ``config.yaml``. Consumed by
    ``EdaAgent`` (runtime), ``fleet.select_agents`` (compose generation),
    ``planning.build_workflow`` (lead graphs), and ``planner_catalog``
    (capability listing without importing agent processes).

    ``path`` is the directory of this agent relative to ``agents/``. Fleet
    files select agents by that path. ``category`` returns the same path.
    """

    # Stable catalog id; equals metadata.name in config.yaml.
    agent_id: str
    # PascalCase class name derived via class_name_for.
    class_name: str
    # Human-facing name for summaries and planner rows.
    display_name: str
    # Default flow stage when a task omits stage.
    stage: str
    # lead, worker, or validator; drives act() dispatch and ROLE_ACTIONS.
    role: AgentRole
    # Short responsibility blurb from YAML for planners and docs.
    responsibility: str
    # Boundary.may strings describing permitted behaviors.
    may: list[str]
    # Boundary.may_not strings describing forbidden behaviors.
    may_not: list[str]
    # Declared skills turned into ToolSpec entries.
    tools: list[ToolSpec]
    # Child agent ids a lead may schedule; used when plan is absent.
    delegates_to: list[str] = Field(default_factory=list)
    # Explicit plan steps when config.yaml defines a plan block.
    plan_steps: list[PlanStep] = Field(default_factory=list)
    # Container listen port; also seeds host port mapping in fleet compose.
    port: int
    # Declared validator agent ids that must themselves be validators.
    validators: list[str] = Field(default_factory=list)
    # Directory of this agent relative to agents/.
    path: str = ""
    # Required context policy for ContextService.assemble.
    context: AgentContext

    @property
    def category(self) -> str:
        """Return this agent's directory relative to ``agents/``.

        Returns:
            The ``path`` field, for example ``frontend/rtl/rtl_implementation``.

        Side effects:
            None.

        Failures:
            None.
        """
        return self.path

    @property
    def capability_pairs(self) -> list[tuple[str, str]]:
        """List (capability id, description) pairs for planner catalogs.

        Every tool becomes a pair. Lead agents additionally advertise
        ``delegate_tasks``, which means "propose a dependency graph; do not
        execute child tools."

        Returns:
            A list of ``(id, description)`` tuples in tool-declaration order,
            with the synthetic lead capability appended when applicable.

        Side effects:
            None.

        Failures:
            None.
        """
        # Start with one capability per declared tool.
        pairs = [(tool.name, tool.description) for tool in self.tools]
        # Leads expose an extra planner-facing capability for workflow proposal.
        if self.role == AgentRole.LEAD:
            pairs.append((
                "delegate_tasks",
                "Propose a dependency graph for the agents in this scope. Do not execute their tools.",
            ))
        # Hand the list to planner_catalog without mutating tools themselves.
        return pairs
