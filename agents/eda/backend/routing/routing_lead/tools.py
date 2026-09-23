"""Tools for the Routing Lead.

Global and detailed routing closure. Coordinates congestion relief, timing-driven route choices, signal-integrity (SI) noise repair, antenna fixes, and manufacturability checks before any routed candidate advances.

Each function below is the stable operation contract the lead/workflow invokes.
A framework adapter (for example OpenROAD) is responsible for performing the
physical-design action. Until a framework is bound, every callable returns an
observation with status ``not_run`` via ``tool_observation`` and does **not**
invoke OpenROAD, Yosys, OpenSTA, a licensed vendor tool, or a simulator.

Importing this module only registers ``@tool`` metadata for the agent SDK; it
does not open the design database. Side effects begin when the HTTP agent
service dispatches a skill listed in ``config.yaml`` to one of these callables.
"""

# Postpone evaluation of annotations so ``dict | None`` works on older type checkers uniformly.
from __future__ import annotations

# ``tool`` decorator registers description/metadata for AgentService skill dispatch.
from packages.agent_sdk import tool
# ``tool_observation`` builds the standard not_run/adapter observation payload.
from domains.eda.adapters import tool_observation


# Register skill metadata for ``plan_routing_closure``: Emit the child workflow that sequences global route, detailed repair, SI, and antenna work until routing closure.
@tool(description='Emit the routing and repair workflow.')
def plan_routing_closure(
    # Natural-language objective for a planned child task or workflow step.
    objective: str = '',
    # Parent task id used to nest child work in the journal.
    parent_task_id: str = '',
    # Design block/partition scope this request applies to.
    scope_block: str = '',
    # Optional dict merged into the observation payload for adapter-specific knobs.
    params: dict | None = None,
) -> dict:
    """Emit the child workflow that sequences global route, detailed repair, SI, and antenna work until routing closure.

    Purpose:
        Expose ``plan_routing_closure`` as a callable skill for the Routing Lead. The
        real EDA effect (for example OpenROAD) happens only when a framework
        adapter is bound; otherwise the call records a ``not_run`` observation.

    Args:
        objective: Natural-language objective for a planned child task or workflow step.
        parent_task_id: Parent task id used to nest child work in the journal.
        scope_block: Design block/partition scope this request applies to.
        params: Optional dict merged into the observation payload for adapter-specific knobs.

    Returns:
        A ``dict`` observation produced by ``tool_observation`` for tool
        ``plan_routing_closure`` tagged with ``agent_id='routing_lead'``.

    Side effects:
        Does not mutate the canonical design until an adapter executes.
        Downstream journal/finding publishers may persist the observation.

    Failures:
        Unbound backend: returns ``not_run`` rather than raising. Bound
        adapters may raise on unknown recipes, missing candidates, or tool errors.
    """
    # Build the observation payload from explicit skill arguments (EDA handles).
    payload = {
        # Natural-language objective for a planned child task or workflow step.
        'objective': objective,
        # Parent task id used to nest child work in the journal.
        'parent_task_id': parent_task_id,
        # Design block/partition scope this request applies to.
        'scope_block': scope_block,
    }
    # Merge optional adapter-specific knobs last so they can override defaults carefully.
    if params:
        # In-place update keeps a single payload object for tool_observation.
        payload.update(params)
    # Hand off to tool_observation: records not_run until OpenROAD/other adapter is bound.
    return tool_observation(
        'plan_routing_closure',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='routing_lead',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``request_global_route_trial``: Ask the global-routing worker to run one coarse-route congestion experiment.
@tool(description='Open one global-route experiment.')
def request_global_route_trial(
    # Natural-language objective for a planned child task or workflow step.
    objective: str = '',
    # Parent task id used to nest child work in the journal.
    parent_task_id: str = '',
    # Design block/partition scope this request applies to.
    scope_block: str = '',
    # Optional dict merged into the observation payload for adapter-specific knobs.
    params: dict | None = None,
) -> dict:
    """Ask the global-routing worker to run one coarse-route congestion experiment.

    Purpose:
        Expose ``request_global_route_trial`` as a callable skill for the Routing Lead. The
        real EDA effect (for example OpenROAD) happens only when a framework
        adapter is bound; otherwise the call records a ``not_run`` observation.

    Args:
        objective: Natural-language objective for a planned child task or workflow step.
        parent_task_id: Parent task id used to nest child work in the journal.
        scope_block: Design block/partition scope this request applies to.
        params: Optional dict merged into the observation payload for adapter-specific knobs.

    Returns:
        A ``dict`` observation produced by ``tool_observation`` for tool
        ``request_global_route_trial`` tagged with ``agent_id='routing_lead'``.

    Side effects:
        Does not mutate the canonical design until an adapter executes.
        Downstream journal/finding publishers may persist the observation.

    Failures:
        Unbound backend: returns ``not_run`` rather than raising. Bound
        adapters may raise on unknown recipes, missing candidates, or tool errors.
    """
    # Build the observation payload from explicit skill arguments (EDA handles).
    payload = {
        # Natural-language objective for a planned child task or workflow step.
        'objective': objective,
        # Parent task id used to nest child work in the journal.
        'parent_task_id': parent_task_id,
        # Design block/partition scope this request applies to.
        'scope_block': scope_block,
    }
    # Merge optional adapter-specific knobs last so they can override defaults carefully.
    if params:
        # In-place update keeps a single payload object for tool_observation.
        payload.update(params)
    # Hand off to tool_observation: records not_run until OpenROAD/other adapter is bound.
    return tool_observation(
        'request_global_route_trial',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='routing_lead',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``request_detailed_route_repair``: Ask detailed-routing repair to fix a localized DRC hotspot.
@tool(description='Open a localized detailed-route repair.')
def request_detailed_route_repair(
    # Natural-language objective for a planned child task or workflow step.
    objective: str = '',
    # Parent task id used to nest child work in the journal.
    parent_task_id: str = '',
    # Design block/partition scope this request applies to.
    scope_block: str = '',
    # Optional dict merged into the observation payload for adapter-specific knobs.
    params: dict | None = None,
) -> dict:
    """Ask detailed-routing repair to fix a localized DRC hotspot.

    Purpose:
        Expose ``request_detailed_route_repair`` as a callable skill for the Routing Lead. The
        real EDA effect (for example OpenROAD) happens only when a framework
        adapter is bound; otherwise the call records a ``not_run`` observation.

    Args:
        objective: Natural-language objective for a planned child task or workflow step.
        parent_task_id: Parent task id used to nest child work in the journal.
        scope_block: Design block/partition scope this request applies to.
        params: Optional dict merged into the observation payload for adapter-specific knobs.

    Returns:
        A ``dict`` observation produced by ``tool_observation`` for tool
        ``request_detailed_route_repair`` tagged with ``agent_id='routing_lead'``.

    Side effects:
        Does not mutate the canonical design until an adapter executes.
        Downstream journal/finding publishers may persist the observation.

    Failures:
        Unbound backend: returns ``not_run`` rather than raising. Bound
        adapters may raise on unknown recipes, missing candidates, or tool errors.
    """
    # Build the observation payload from explicit skill arguments (EDA handles).
    payload = {
        # Natural-language objective for a planned child task or workflow step.
        'objective': objective,
        # Parent task id used to nest child work in the journal.
        'parent_task_id': parent_task_id,
        # Design block/partition scope this request applies to.
        'scope_block': scope_block,
    }
    # Merge optional adapter-specific knobs last so they can override defaults carefully.
    if params:
        # In-place update keeps a single payload object for tool_observation.
        payload.update(params)
    # Hand off to tool_observation: records not_run until OpenROAD/other adapter is bound.
    return tool_observation(
        'request_detailed_route_repair',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='routing_lead',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``request_si_repair``: Ask SI/noise repair to fix aggressor/victim pairs over the noise limit.
@tool(description='Open an SI repair for nets over the noise limit.')
def request_si_repair(
    # Natural-language objective for a planned child task or workflow step.
    objective: str = '',
    # Parent task id used to nest child work in the journal.
    parent_task_id: str = '',
    # Design block/partition scope this request applies to.
    scope_block: str = '',
    # Optional dict merged into the observation payload for adapter-specific knobs.
    params: dict | None = None,
) -> dict:
    """Ask SI/noise repair to fix aggressor/victim pairs over the noise limit.

    Purpose:
        Expose ``request_si_repair`` as a callable skill for the Routing Lead. The
        real EDA effect (for example OpenROAD) happens only when a framework
        adapter is bound; otherwise the call records a ``not_run`` observation.

    Args:
        objective: Natural-language objective for a planned child task or workflow step.
        parent_task_id: Parent task id used to nest child work in the journal.
        scope_block: Design block/partition scope this request applies to.
        params: Optional dict merged into the observation payload for adapter-specific knobs.

    Returns:
        A ``dict`` observation produced by ``tool_observation`` for tool
        ``request_si_repair`` tagged with ``agent_id='routing_lead'``.

    Side effects:
        Does not mutate the canonical design until an adapter executes.
        Downstream journal/finding publishers may persist the observation.

    Failures:
        Unbound backend: returns ``not_run`` rather than raising. Bound
        adapters may raise on unknown recipes, missing candidates, or tool errors.
    """
    # Build the observation payload from explicit skill arguments (EDA handles).
    payload = {
        # Natural-language objective for a planned child task or workflow step.
        'objective': objective,
        # Parent task id used to nest child work in the journal.
        'parent_task_id': parent_task_id,
        # Design block/partition scope this request applies to.
        'scope_block': scope_block,
    }
    # Merge optional adapter-specific knobs last so they can override defaults carefully.
    if params:
        # In-place update keeps a single payload object for tool_observation.
        payload.update(params)
    # Hand off to tool_observation: records not_run until OpenROAD/other adapter is bound.
    return tool_observation(
        'request_si_repair',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='routing_lead',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``request_antenna_repair``: Ask antenna/manufacturability to clear process-antenna and density risks.
@tool(description='Open antenna and manufacturability repair.')
def request_antenna_repair(
    # Natural-language objective for a planned child task or workflow step.
    objective: str = '',
    # Parent task id used to nest child work in the journal.
    parent_task_id: str = '',
    # Design block/partition scope this request applies to.
    scope_block: str = '',
    # Optional dict merged into the observation payload for adapter-specific knobs.
    params: dict | None = None,
) -> dict:
    """Ask antenna/manufacturability to clear process-antenna and density risks.

    Purpose:
        Expose ``request_antenna_repair`` as a callable skill for the Routing Lead. The
        real EDA effect (for example OpenROAD) happens only when a framework
        adapter is bound; otherwise the call records a ``not_run`` observation.

    Args:
        objective: Natural-language objective for a planned child task or workflow step.
        parent_task_id: Parent task id used to nest child work in the journal.
        scope_block: Design block/partition scope this request applies to.
        params: Optional dict merged into the observation payload for adapter-specific knobs.

    Returns:
        A ``dict`` observation produced by ``tool_observation`` for tool
        ``request_antenna_repair`` tagged with ``agent_id='routing_lead'``.

    Side effects:
        Does not mutate the canonical design until an adapter executes.
        Downstream journal/finding publishers may persist the observation.

    Failures:
        Unbound backend: returns ``not_run`` rather than raising. Bound
        adapters may raise on unknown recipes, missing candidates, or tool errors.
    """
    # Build the observation payload from explicit skill arguments (EDA handles).
    payload = {
        # Natural-language objective for a planned child task or workflow step.
        'objective': objective,
        # Parent task id used to nest child work in the journal.
        'parent_task_id': parent_task_id,
        # Design block/partition scope this request applies to.
        'scope_block': scope_block,
    }
    # Merge optional adapter-specific knobs last so they can override defaults carefully.
    if params:
        # In-place update keeps a single payload object for tool_observation.
        payload.update(params)
    # Hand off to tool_observation: records not_run until OpenROAD/other adapter is bound.
    return tool_observation(
        'request_antenna_repair',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='routing_lead',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``read_routing_status``: Read live congestion, DRC, SI, and antenna status for the routed candidate.
@tool(description='Read congestion, DRC, SI, antenna, and timing for each routed candidate.')
def read_routing_status(
    # Isolated design candidate URI/id this tool reads or edits. Empty often means create from baseline.
    candidate_ref: str = '',
    # Artifact URI of a report. Empty typically means latest report for the candidate.
    report_ref: str = '',
    # PVT corner filter (e.g. slow/fast). Empty means all available corners.
    corner: str = '',
    # Functional or analysis mode filter. Empty means all available modes.
    mode: str = '',
    # Optional dict merged into the observation payload for adapter-specific knobs.
    params: dict | None = None,
) -> dict:
    """Read live congestion, DRC, SI, and antenna status for the routed candidate.

    Purpose:
        Expose ``read_routing_status`` as a callable skill for the Routing Lead. The
        real EDA effect (for example OpenROAD) happens only when a framework
        adapter is bound; otherwise the call records a ``not_run`` observation.

    Args:
        candidate_ref: Isolated design candidate URI/id this tool reads or edits. Empty often means create from baseline.
        report_ref: Artifact URI of a report. Empty typically means latest report for the candidate.
        corner: PVT corner filter (e.g. slow/fast). Empty means all available corners.
        mode: Functional or analysis mode filter. Empty means all available modes.
        params: Optional dict merged into the observation payload for adapter-specific knobs.

    Returns:
        A ``dict`` observation produced by ``tool_observation`` for tool
        ``read_routing_status`` tagged with ``agent_id='routing_lead'``.

    Side effects:
        Does not mutate the canonical design until an adapter executes.
        Downstream journal/finding publishers may persist the observation.

    Failures:
        Unbound backend: returns ``not_run`` rather than raising. Bound
        adapters may raise on unknown recipes, missing candidates, or tool errors.
    """
    # Build the observation payload from explicit skill arguments (EDA handles).
    payload = {
        # Isolated design candidate URI/id this tool reads or edits. Empty often means create from baseline.
        'candidate_ref': candidate_ref,
        # Artifact URI of a report. Empty typically means latest report for the candidate.
        'report_ref': report_ref,
        # PVT corner filter (e.g. slow/fast). Empty means all available corners.
        'corner': corner,
        # Functional or analysis mode filter. Empty means all available modes.
        'mode': mode,
    }
    # Merge optional adapter-specific knobs last so they can override defaults carefully.
    if params:
        # In-place update keeps a single payload object for tool_observation.
        payload.update(params)
    # Hand off to tool_observation: records not_run until OpenROAD/other adapter is bound.
    return tool_observation(
        'read_routing_status',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='routing_lead',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``read_routing_acceptance``: Read whether acceptance gates for routing closure are satisfied.
@tool(description='Read the DRC, SI, antenna, and timing criteria for advancement.')
def read_routing_acceptance(
    # Isolated design candidate URI/id this tool reads or edits. Empty often means create from baseline.
    candidate_ref: str = '',
    # Artifact URI of a report. Empty typically means latest report for the candidate.
    report_ref: str = '',
    # PVT corner filter (e.g. slow/fast). Empty means all available corners.
    corner: str = '',
    # Functional or analysis mode filter. Empty means all available modes.
    mode: str = '',
    # Optional dict merged into the observation payload for adapter-specific knobs.
    params: dict | None = None,
) -> dict:
    """Read whether acceptance gates for routing closure are satisfied.

    Purpose:
        Expose ``read_routing_acceptance`` as a callable skill for the Routing Lead. The
        real EDA effect (for example OpenROAD) happens only when a framework
        adapter is bound; otherwise the call records a ``not_run`` observation.

    Args:
        candidate_ref: Isolated design candidate URI/id this tool reads or edits. Empty often means create from baseline.
        report_ref: Artifact URI of a report. Empty typically means latest report for the candidate.
        corner: PVT corner filter (e.g. slow/fast). Empty means all available corners.
        mode: Functional or analysis mode filter. Empty means all available modes.
        params: Optional dict merged into the observation payload for adapter-specific knobs.

    Returns:
        A ``dict`` observation produced by ``tool_observation`` for tool
        ``read_routing_acceptance`` tagged with ``agent_id='routing_lead'``.

    Side effects:
        Does not mutate the canonical design until an adapter executes.
        Downstream journal/finding publishers may persist the observation.

    Failures:
        Unbound backend: returns ``not_run`` rather than raising. Bound
        adapters may raise on unknown recipes, missing candidates, or tool errors.
    """
    # Build the observation payload from explicit skill arguments (EDA handles).
    payload = {
        # Isolated design candidate URI/id this tool reads or edits. Empty often means create from baseline.
        'candidate_ref': candidate_ref,
        # Artifact URI of a report. Empty typically means latest report for the candidate.
        'report_ref': report_ref,
        # PVT corner filter (e.g. slow/fast). Empty means all available corners.
        'corner': corner,
        # Functional or analysis mode filter. Empty means all available modes.
        'mode': mode,
    }
    # Merge optional adapter-specific knobs last so they can override defaults carefully.
    if params:
        # In-place update keeps a single payload object for tool_observation.
        payload.update(params)
    # Hand off to tool_observation: records not_run until OpenROAD/other adapter is bound.
    return tool_observation(
        'read_routing_acceptance',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='routing_lead',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``compare_routed_candidates``: Compare two routed candidates on congestion, DRC, SI, and timing.
@tool(description='Rank routed candidates that meet every hard check.')
def compare_routed_candidates(
    # Isolated design candidate URI/id this tool reads or edits. Empty often means create from baseline.
    candidate_ref: str = '',
    # Artifact URI of a report. Empty typically means latest report for the candidate.
    report_ref: str = '',
    # PVT corner filter (e.g. slow/fast). Empty means all available corners.
    corner: str = '',
    # Functional or analysis mode filter. Empty means all available modes.
    mode: str = '',
    # Optional dict merged into the observation payload for adapter-specific knobs.
    params: dict | None = None,
) -> dict:
    """Compare two routed candidates on congestion, DRC, SI, and timing.

    Purpose:
        Expose ``compare_routed_candidates`` as a callable skill for the Routing Lead. The
        real EDA effect (for example OpenROAD) happens only when a framework
        adapter is bound; otherwise the call records a ``not_run`` observation.

    Args:
        candidate_ref: Isolated design candidate URI/id this tool reads or edits. Empty often means create from baseline.
        report_ref: Artifact URI of a report. Empty typically means latest report for the candidate.
        corner: PVT corner filter (e.g. slow/fast). Empty means all available corners.
        mode: Functional or analysis mode filter. Empty means all available modes.
        params: Optional dict merged into the observation payload for adapter-specific knobs.

    Returns:
        A ``dict`` observation produced by ``tool_observation`` for tool
        ``compare_routed_candidates`` tagged with ``agent_id='routing_lead'``.

    Side effects:
        Does not mutate the canonical design until an adapter executes.
        Downstream journal/finding publishers may persist the observation.

    Failures:
        Unbound backend: returns ``not_run`` rather than raising. Bound
        adapters may raise on unknown recipes, missing candidates, or tool errors.
    """
    # Build the observation payload from explicit skill arguments (EDA handles).
    payload = {
        # Isolated design candidate URI/id this tool reads or edits. Empty often means create from baseline.
        'candidate_ref': candidate_ref,
        # Artifact URI of a report. Empty typically means latest report for the candidate.
        'report_ref': report_ref,
        # PVT corner filter (e.g. slow/fast). Empty means all available corners.
        'corner': corner,
        # Functional or analysis mode filter. Empty means all available modes.
        'mode': mode,
    }
    # Merge optional adapter-specific knobs last so they can override defaults carefully.
    if params:
        # In-place update keeps a single payload object for tool_observation.
        payload.update(params)
    # Hand off to tool_observation: records not_run until OpenROAD/other adapter is bound.
    return tool_observation(
        'compare_routed_candidates',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='routing_lead',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``recommend_routed_candidate``: Recommend which routed candidate should advance (does not promote itself).
@tool(description='Record which routed candidate should advance to extraction. This does not promote it.')
def recommend_routed_candidate(
    # One-sentence finding summary published into engineering memory.
    summary: str = '',
    # Comma-separated artifact URIs that support a finding.
    evidence_refs: str = '',
    # Finding severity: low, medium, high, or critical.
    severity: str = '',
    # Agent id that should act on a published finding.
    recommended_recipient: str = '',
    # Optional dict merged into the observation payload for adapter-specific knobs.
    params: dict | None = None,
) -> dict:
    """Recommend which routed candidate should advance (does not promote itself).

    Purpose:
        Expose ``recommend_routed_candidate`` as a callable skill for the Routing Lead. The
        real EDA effect (for example OpenROAD) happens only when a framework
        adapter is bound; otherwise the call records a ``not_run`` observation.

    Args:
        summary: One-sentence finding summary published into engineering memory.
        evidence_refs: Comma-separated artifact URIs that support a finding.
        severity: Finding severity: low, medium, high, or critical.
        recommended_recipient: Agent id that should act on a published finding.
        params: Optional dict merged into the observation payload for adapter-specific knobs.

    Returns:
        A ``dict`` observation produced by ``tool_observation`` for tool
        ``recommend_routed_candidate`` tagged with ``agent_id='routing_lead'``.

    Side effects:
        Does not mutate the canonical design until an adapter executes.
        Downstream journal/finding publishers may persist the observation.

    Failures:
        Unbound backend: returns ``not_run`` rather than raising. Bound
        adapters may raise on unknown recipes, missing candidates, or tool errors.
    """
    # Build the observation payload from explicit skill arguments (EDA handles).
    payload = {
        # One-sentence finding summary published into engineering memory.
        'summary': summary,
        # Comma-separated artifact URIs that support a finding.
        'evidence_refs': evidence_refs,
        # Finding severity: low, medium, high, or critical.
        'severity': severity,
        # Agent id that should act on a published finding.
        'recommended_recipient': recommended_recipient,
    }
    # Merge optional adapter-specific knobs last so they can override defaults carefully.
    if params:
        # In-place update keeps a single payload object for tool_observation.
        payload.update(params)
    # Hand off to tool_observation: records not_run until OpenROAD/other adapter is bound.
    return tool_observation(
        'recommend_routed_candidate',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='routing_lead',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``flag_failed_route_check``: Publish a finding when a hard routing check failed.
@tool(description='Publish a candidate that improved congestion and failed antenna, SI, or DRC.')
def flag_failed_route_check(
    # One-sentence finding summary published into engineering memory.
    summary: str = '',
    # Comma-separated artifact URIs that support a finding.
    evidence_refs: str = '',
    # Finding severity: low, medium, high, or critical.
    severity: str = '',
    # Agent id that should act on a published finding.
    recommended_recipient: str = '',
    # Optional dict merged into the observation payload for adapter-specific knobs.
    params: dict | None = None,
) -> dict:
    """Publish a finding when a hard routing check failed.

    Purpose:
        Expose ``flag_failed_route_check`` as a callable skill for the Routing Lead. The
        real EDA effect (for example OpenROAD) happens only when a framework
        adapter is bound; otherwise the call records a ``not_run`` observation.

    Args:
        summary: One-sentence finding summary published into engineering memory.
        evidence_refs: Comma-separated artifact URIs that support a finding.
        severity: Finding severity: low, medium, high, or critical.
        recommended_recipient: Agent id that should act on a published finding.
        params: Optional dict merged into the observation payload for adapter-specific knobs.

    Returns:
        A ``dict`` observation produced by ``tool_observation`` for tool
        ``flag_failed_route_check`` tagged with ``agent_id='routing_lead'``.

    Side effects:
        Does not mutate the canonical design until an adapter executes.
        Downstream journal/finding publishers may persist the observation.

    Failures:
        Unbound backend: returns ``not_run`` rather than raising. Bound
        adapters may raise on unknown recipes, missing candidates, or tool errors.
    """
    # Build the observation payload from explicit skill arguments (EDA handles).
    payload = {
        # One-sentence finding summary published into engineering memory.
        'summary': summary,
        # Comma-separated artifact URIs that support a finding.
        'evidence_refs': evidence_refs,
        # Finding severity: low, medium, high, or critical.
        'severity': severity,
        # Agent id that should act on a published finding.
        'recommended_recipient': recommended_recipient,
    }
    # Merge optional adapter-specific knobs last so they can override defaults carefully.
    if params:
        # In-place update keeps a single payload object for tool_observation.
        payload.update(params)
    # Hand off to tool_observation: records not_run until OpenROAD/other adapter is bound.
    return tool_observation(
        'flag_failed_route_check',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='routing_lead',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``record_routing_strategy``: Journal the routing strategy and worker assignment for provenance.
@tool(description='Record the layer, cost, or repair change for the next trial.')
def record_routing_strategy(
    # One-sentence finding summary published into engineering memory.
    summary: str = '',
    # Comma-separated artifact URIs that support a finding.
    evidence_refs: str = '',
    # Finding severity: low, medium, high, or critical.
    severity: str = '',
    # Agent id that should act on a published finding.
    recommended_recipient: str = '',
    # Optional dict merged into the observation payload for adapter-specific knobs.
    params: dict | None = None,
) -> dict:
    """Journal the routing strategy and worker assignment for provenance.

    Purpose:
        Expose ``record_routing_strategy`` as a callable skill for the Routing Lead. The
        real EDA effect (for example OpenROAD) happens only when a framework
        adapter is bound; otherwise the call records a ``not_run`` observation.

    Args:
        summary: One-sentence finding summary published into engineering memory.
        evidence_refs: Comma-separated artifact URIs that support a finding.
        severity: Finding severity: low, medium, high, or critical.
        recommended_recipient: Agent id that should act on a published finding.
        params: Optional dict merged into the observation payload for adapter-specific knobs.

    Returns:
        A ``dict`` observation produced by ``tool_observation`` for tool
        ``record_routing_strategy`` tagged with ``agent_id='routing_lead'``.

    Side effects:
        Does not mutate the canonical design until an adapter executes.
        Downstream journal/finding publishers may persist the observation.

    Failures:
        Unbound backend: returns ``not_run`` rather than raising. Bound
        adapters may raise on unknown recipes, missing candidates, or tool errors.
    """
    # Build the observation payload from explicit skill arguments (EDA handles).
    payload = {
        # One-sentence finding summary published into engineering memory.
        'summary': summary,
        # Comma-separated artifact URIs that support a finding.
        'evidence_refs': evidence_refs,
        # Finding severity: low, medium, high, or critical.
        'severity': severity,
        # Agent id that should act on a published finding.
        'recommended_recipient': recommended_recipient,
    }
    # Merge optional adapter-specific knobs last so they can override defaults carefully.
    if params:
        # In-place update keeps a single payload object for tool_observation.
        payload.update(params)
    # Hand off to tool_observation: records not_run until OpenROAD/other adapter is bound.
    return tool_observation(
        'record_routing_strategy',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='routing_lead',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``request_routing_decision``: Request an explicit human/lead decision on the routing candidate.
@tool(description='Ask a human to choose among routed candidates or to change a physical limit.')
def request_routing_decision(
    # Argument ``decision`` forwarded into the tool observation payload for the EDA adapter.
    decision: str = '',
    # Argument ``options`` forwarded into the tool observation payload for the EDA adapter.
    options: str = '',
    # Comma-separated artifact URIs that support a finding.
    evidence_refs: str = '',
    # Argument ``deadline`` forwarded into the tool observation payload for the EDA adapter.
    deadline: str = '',
    # Optional dict merged into the observation payload for adapter-specific knobs.
    params: dict | None = None,
) -> dict:
    """Request an explicit human/lead decision on the routing candidate.

    Purpose:
        Expose ``request_routing_decision`` as a callable skill for the Routing Lead. The
        real EDA effect (for example OpenROAD) happens only when a framework
        adapter is bound; otherwise the call records a ``not_run`` observation.

    Args:
        decision: Argument ``decision`` forwarded into the tool observation payload for the EDA adapter.
        options: Argument ``options`` forwarded into the tool observation payload for the EDA adapter.
        evidence_refs: Comma-separated artifact URIs that support a finding.
        deadline: Argument ``deadline`` forwarded into the tool observation payload for the EDA adapter.
        params: Optional dict merged into the observation payload for adapter-specific knobs.

    Returns:
        A ``dict`` observation produced by ``tool_observation`` for tool
        ``request_routing_decision`` tagged with ``agent_id='routing_lead'``.

    Side effects:
        Does not mutate the canonical design until an adapter executes.
        Downstream journal/finding publishers may persist the observation.

    Failures:
        Unbound backend: returns ``not_run`` rather than raising. Bound
        adapters may raise on unknown recipes, missing candidates, or tool errors.
    """
    # Build the observation payload from explicit skill arguments (EDA handles).
    payload = {
        # Forward ``decision`` for the routing_lead adapter.
        'decision': decision,
        # Forward ``options`` for the routing_lead adapter.
        'options': options,
        # Comma-separated artifact URIs that support a finding.
        'evidence_refs': evidence_refs,
        # Forward ``deadline`` for the routing_lead adapter.
        'deadline': deadline,
    }
    # Merge optional adapter-specific knobs last so they can override defaults carefully.
    if params:
        # In-place update keeps a single payload object for tool_observation.
        payload.update(params)
    # Hand off to tool_observation: records not_run until OpenROAD/other adapter is bound.
    return tool_observation(
        'request_routing_decision',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='routing_lead',  # provenance tag for journal/telemetry
    )
