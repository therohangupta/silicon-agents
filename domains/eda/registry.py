"""Load an agent spec from the ``config.yaml`` beside that agent's code.

The spec's ``path`` is the agent directory relative to ``agents/``.
``agents/frontend/rtl/rtl_implementation`` has path
``frontend/rtl/rtl_implementation``. Fleet files select agents by that path.

This module also owns the process-wide catalog cache. ``all_specs`` walks
every ``config.yaml`` under ``AGENTS_ROOT``, validates uniqueness and
structural rules (tool counts, role actions, delegate targets, plan edges,
validator roles), then caches specs by ``agent_id``. ``get_spec`` reads that
cache. ``planner_catalog`` exposes a JSON-friendly capability view so a
planner process can reason about the fleet without importing agent runtimes.

Validation is strict by design: duplicate ids/ports/class names, leads with
no children, tools outside the 10–40 count band, duplicate tool names across
agents, and invalid parameter identifiers all fail the catalog load.
"""

from __future__ import annotations

# Path arithmetic for AGENTS_ROOT and the relative agent directory.
from pathlib import Path

# Parse each agent's config.yaml into plain Python dicts.
import yaml

# Role/action matrices used when checking each skill's declared action.
from .schemas.enums import ROLE_ACTIONS, AgentRole, ToolAction
# Spec models and the class-name helper applied to metadata.name.
from .spec import AgentContext, AgentSpec, PlanStep, ToolParam, ToolSpec, class_name_for

# Root of all agent packages: agents relative to domains/eda.
AGENTS_ROOT = Path(__file__).resolve().parents[2] / "agents"


class CatalogError(ValueError):
    """Raised when an agent config or the aggregate catalog is invalid.

    Used for missing context policy, duplicate ids/ports,
    illegal tool actions for a role, unknown delegates, and similar structural
    problems. Callers treat it as a configuration error, not a transient fault.
    """


def iter_configs() -> list[Path]:
    """Return sorted paths to every agent ``config.yaml`` under ``AGENTS_ROOT``.

    Skips configs nested under ``runtime`` or ``__pycache__`` directories so
    generated or cache trees do not enter the catalog.

    Returns:
        A sorted list of ``Path`` objects pointing at config files.

    Side effects:
        Walks the filesystem under ``AGENTS_ROOT``.

    Failures:
        Propagates OS errors if the agents tree is unreadable.
    """
    # Accumulate discovered config paths before sorting.
    configs = []
    # Recursively find every config.yaml under the agents package tree.
    for path in AGENTS_ROOT.rglob("config.yaml"):
        # Relative parts let us skip runtime and bytecode directories.
        parts = path.relative_to(AGENTS_ROOT).parts
        # Ignore generated runtime trees and Python cache folders.
        if "runtime" in parts or "__pycache__" in parts:
            continue
        # Keep this config for catalog loading.
        configs.append(path)
    # Stable order makes catalog validation deterministic across runs.
    return sorted(configs)


def path_for(directory: Path) -> str:
    """Return the agent directory relative to ``agents/``.

    Args:
        directory: Absolute or relative path to an agent package under
            ``AGENTS_ROOT``.

    Returns:
        A slash-joined path such as ``frontend/rtl/rtl_implementation``.

    Side effects:
        None beyond path relative-to arithmetic.

    Failures:
        Raises ``ValueError`` when ``directory`` is not under ``AGENTS_ROOT``.
    """
    return directory.relative_to(AGENTS_ROOT).as_posix()


def load_spec(directory: str | Path) -> AgentSpec:
    """Parse one agent directory's ``config.yaml`` into a validated ``AgentSpec``.

    Requires every skill to declare an ``action``. Requires
    ``context.include`` and ``context.precedence``. Builds tools, plan steps,
    boundary lists, and the nested ``AgentContext``.

    Args:
        directory: Path to the agent package containing ``config.yaml``.

    Returns:
        A fully populated ``AgentSpec``.

    Side effects:
        Reads ``config.yaml`` from disk.

    Failures:
        Raises ``CatalogError`` on missing skill actions or
        missing context fields. Propagates YAML and I/O errors. Raises
        ``KeyError``/``ValidationError``-class errors when required keys or
        enum values are absent or invalid.
    """
    # Normalize to Path for join and relative_to operations.
    directory = Path(directory)
    # Load the YAML document as a plain dict.
    document = yaml.safe_load((directory / "config.yaml").read_text())
    # Metadata block holds name, display_name, description, labels.
    metadata = document["metadata"]
    # Labels may be omitted; treat null as empty dict.
    labels = metadata.get("labels") or {}
    # Directory of this agent relative to agents/.
    path = path_for(directory)
    # Build ToolSpec list from the skills array.
    tools = []
    # Each skill becomes one ToolSpec with action and params.
    for skill in document.get("skills") or []:
        # Every skill must declare a ToolAction for role enforcement.
        if "action" not in skill:
            raise CatalogError(f"{metadata.get('name')} skill {skill.get('callable')} has no action")
        # Map YAML param dicts into ToolParam models.
        params = [
            ToolParam(name=item["name"], description=str(item.get("description") or ""))
            for item in skill.get("params") or []
        ]
        # callable is the Python function name in tools.py.
        tools.append(ToolSpec(
            name=skill["callable"],
            description=str(skill.get("description") or ""),
            action=ToolAction(skill["action"]),
            params=params,
        ))
    # Build PlanStep list from the optional plan array.
    steps = []
    # Support both "agent" and "agent_type" keys for child references.
    for item in document.get("plan") or []:
        steps.append(PlanStep(
            id=item["id"],
            agent_type=item.get("agent") or item["agent_type"],
            capability=str(item.get("capability") or ""),
            depends_on=list(item.get("depends_on") or []),
            objective=str(item.get("objective") or ""),
        ))
    # Boundary may/may_not lists document intent; runtime uses ToolAction.
    boundary = document.get("boundary") or {}
    # Context policy is mandatory for every agent.
    raw_context = document.get("context")
    # Require include and precedence so ContextService always has a policy.
    if not isinstance(raw_context, dict) or not raw_context.get("include") or not raw_context.get("precedence"):
        raise CatalogError(f"{metadata.get('name')} must declare context.include and context.precedence")
    # Agent id is the metadata name string.
    agent_id = str(metadata["name"])
    # Assemble the full AgentSpec for this directory.
    return AgentSpec(
        agent_id=agent_id,
        class_name=class_name_for(agent_id),
        display_name=str(metadata.get("display_name") or agent_id),
        stage=str(document.get("stage") or labels.get("stage") or ""),
        role=AgentRole(document.get("role") or labels.get("role")),
        responsibility=str(document.get("responsibility") or metadata.get("description") or ""),
        may=list(boundary.get("may") or []),
        may_not=list(boundary.get("may_not") or []),
        tools=tools,
        delegates_to=list(document.get("delegates_to") or []),
        plan_steps=steps,
        port=int(document["connection"]["port"]),
        validators=list(document.get("validators") or []),
        path=path,
        context=AgentContext(
            include=list(raw_context["include"]),
            exclude=list(raw_context.get("exclude") or []),
            drop=list(raw_context.get("drop") or ["rejected"]),
            precedence=list(raw_context["precedence"]),
            protect=list(raw_context.get("protect") or []),
            token_budget=int(raw_context.get("token_budget") or 80_000),
        ),
    )


# Process-wide cache: None until all_specs() warms it; then agent_id -> AgentSpec.
_CACHE: dict[str, AgentSpec] | None = None


def validate_catalog(specs: list[AgentSpec] | None = None) -> None:
    """Assert structural invariants across the full agent catalog.

    Checks uniqueness of agent ids, ports, and class names; lead child
    presence; per-agent tool count (10–40) and uniqueness; parameter
    identifier rules; globally unique tool names; role-allowed actions;
    known delegates; plan dependency closure; and validator role identity.

    Args:
        specs: Optional explicit list. When ``None``, loads every config via
            ``iter_configs`` and ``load_spec``.

    Returns:
        None on success.

    Side effects:
        May read every ``config.yaml`` when ``specs`` is omitted.

    Failures:
        Raises ``CatalogError`` describing the first invariant violated.
    """
    # Materialize the list we will validate.
    specs = list(specs) if specs is not None else [load_spec(path.parent) for path in iter_configs()]
    # Agent ids must be unique across the fleet.
    ids = [spec.agent_id for spec in specs]
    if len(ids) != len(set(ids)):
        raise CatalogError("Duplicate agent id")
    # Ports must be unique so compose publishing does not collide.
    ports = [spec.port for spec in specs]
    if len(ports) != len(set(ports)):
        raise CatalogError("Duplicate agent port")
    # Generated class names must not collide either.
    names = [spec.class_name for spec in specs]
    if len(names) != len(set(names)):
        raise CatalogError("Duplicate class name")
    # Index for delegate/plan/validator membership checks.
    by_id = {spec.agent_id: spec for spec in specs}
    # Track first owner of each tool name for global uniqueness.
    seen_tools: dict[str, str] = {}
    # Validate each agent individually, then cross-links.
    for spec in specs:
        # Leads must declare children somehow or they cannot plan.
        if spec.role == AgentRole.LEAD and not spec.delegates_to and not spec.plan_steps:
            raise CatalogError(f"{spec.agent_id} is a lead with no children")
        # Collect tool names for count and duplicate checks.
        tool_names = [item.name for item in spec.tools]
        # Enforce the fleet-wide skill-count band.
        if not 10 <= len(tool_names) <= 40:
            raise CatalogError(f"{spec.agent_id} has {len(tool_names)} tools; expected 10 to 40")
        # No duplicate callables inside one agent.
        if len(tool_names) != len(set(tool_names)):
            raise CatalogError(f"{spec.agent_id} has duplicate tools")
        # Inspect each tool for params, identifiers, global uniqueness, actions.
        for item in spec.tools:
            param_names = [param.name for param in item.params]
            # Params must be unique within the tool.
            if len(param_names) != len(set(param_names)):
                raise CatalogError(f"{spec.agent_id} tool {item.name} has duplicate parameters")
            # Params must be identifiers and not shadow a reserved name.
            for param_name in param_names:
                if not param_name.isidentifier() or param_name == "params":
                    raise CatalogError(f"{spec.agent_id} tool {item.name} parameter {param_name} is invalid")
            # Tool name itself must be a valid Python identifier.
            if not item.name.isidentifier():
                raise CatalogError(f"{spec.agent_id} tool {item.name} is not an identifier")
            # Globally unique tool names avoid ambiguous planner capability ids.
            if item.name in seen_tools:
                raise CatalogError(f"Tool {item.name} is declared by both {seen_tools[item.name]} and {spec.agent_id}")
            # Remember this owner for later collision detection.
            seen_tools[item.name] = spec.agent_id
            # Action must be in the role's allowed set.
            if item.action not in ROLE_ACTIONS[spec.role]:
                raise CatalogError(
                    f"{spec.agent_id} tool {item.name} action {item.action.value} "
                    f"is not allowed for {spec.role.value}"
                )
        # Every delegated child must exist in the catalog.
        for child in spec.delegates_to:
            if child not in by_id:
                raise CatalogError(f"{spec.agent_id} delegates to unknown agent {child}")
        # Plan step ids form the universe for depends_on checks.
        step_ids = {item.id for item in spec.plan_steps}
        # Each plan step must reference a known agent and known dependencies.
        for plan_step in spec.plan_steps:
            if plan_step.agent_type not in by_id:
                raise CatalogError(f"{spec.agent_id} plan references unknown agent {plan_step.agent_type}")
            missing = [dep for dep in plan_step.depends_on if dep not in step_ids]
            if missing:
                raise CatalogError(f"{spec.agent_id} step {plan_step.id} depends on {missing}")
        # Declared validators must exist and actually be validator-role agents.
        for validator in spec.validators:
            target = by_id.get(validator)
            if target is None or target.role != AgentRole.VALIDATOR:
                raise CatalogError(f"{spec.agent_id} validator {validator} is not a validator")


def all_specs() -> list[AgentSpec]:
    """Return every validated agent spec, ordered by listen port.

    Warms ``_CACHE`` on first call. Subsequent calls return a fresh list
    view of the cached specs without re-reading YAML.

    Returns:
        Specs sorted by ``port`` ascending (stable for compose and catalogs).

    Side effects:
        On first call, reads all configs, validates, and fills ``_CACHE``.

    Failures:
        Propagates ``CatalogError`` and I/O errors from load/validate.
    """
    # Allow assignment to the module-level cache.
    global _CACHE
    # Cold start: load, validate, and index by agent_id.
    if _CACHE is None:
        specs = [load_spec(path.parent) for path in iter_configs()]
        validate_catalog(specs)
        _CACHE = {spec.agent_id: spec for spec in specs}
    # Return a port-ordered list without exposing the mutable cache dict.
    return [spec for _, spec in sorted(_CACHE.items(), key=lambda item: item[1].port)]


def get_spec(agent_id: str) -> AgentSpec:
    """Return one cached ``AgentSpec`` by agent id.

    Args:
        agent_id: Catalog identifier such as ``routing_lead``.

    Returns:
        The matching ``AgentSpec``.

    Side effects:
        May call ``all_specs()`` to warm the cache on first use.

    Failures:
        Raises ``CatalogError`` when the id is not in the catalog.
    """
    # Ensure the cache is populated before indexing.
    if _CACHE is None:
        all_specs()
    # Help the type checker: all_specs() guarantees a dict.
    assert _CACHE is not None
    try:
        # Direct lookup by stable agent_id.
        return _CACHE[agent_id]
    except KeyError as exc:
        # Normalize KeyError into a catalog-level configuration error.
        raise CatalogError(f"Unknown agent {agent_id}") from exc


def planner_catalog() -> list[dict]:
    """Capability view a planner can read without importing agent processes.

    Each row includes identity, path, role, port, responsibility,
    boundary lists, capability pairs, delegates, and validators. Values are
    plain JSON-friendly types (strings, lists, dicts).

    Returns:
        A list of dictionaries, one per agent, in ``all_specs`` port order.

    Side effects:
        May warm the catalog cache via ``all_specs``.

    Failures:
        Propagates catalog load/validation errors.
    """
    # Accumulate planner-facing rows.
    rows = []
    # Walk every spec in port order.
    for spec in all_specs():
        rows.append({
            "agent_id": spec.agent_id,
            "display_name": spec.display_name,
            "stage": spec.stage,
            "path": spec.path,
            "role": spec.role.value,
            "port": spec.port,
            "responsibility": spec.responsibility,
            "may": spec.may,
            "may_not": spec.may_not,
            "capabilities": [
                {"id": capability_id, "description": description}
                for capability_id, description in spec.capability_pairs
            ],
            "delegates_to": spec.delegates_to,
            "validators": spec.validators,
        })
    # Hand the catalog to the planner as plain data.
    return rows
