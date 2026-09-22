"""Tools for the Global-Routing Experiment Agent.

Global routing (GR) assigns nets to coarse tracks and layers before detailed routing. Congestion maps, overflow nets, and route guides feed OpenROAD global_route experiments without editing the detailed route DB.

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
from domains.eda.eda import tool_observation


# Register skill metadata for ``write_routing_layer_directive``: Constrain which metal layers the GR trial may use (OpenROAD set_routing_layers).
@tool(description='Write the layers this experiment may use. Adapter target: OpenROAD set_routing_layers.')
def write_routing_layer_directive(
    # Isolated design candidate URI/id this tool reads or edits. Empty often means create from baseline.
    candidate_ref: str = '',
    # Immutable baseline the candidate must descend from; used for diffs and provenance.
    baseline_ref: str = '',
    # The single experimental change this edit or trial is testing.
    hypothesis: str = '',
    # Optional dict merged into the observation payload for adapter-specific knobs.
    params: dict | None = None,
) -> dict:
    """Constrain which metal layers the GR trial may use (OpenROAD set_routing_layers).

    Purpose:
        Expose ``write_routing_layer_directive`` as a callable skill for the Global-Routing Experiment Agent. The
        real EDA effect (for example OpenROAD) happens only when a framework
        adapter is bound; otherwise the call records a ``not_run`` observation.

    Args:
        candidate_ref: Isolated design candidate URI/id this tool reads or edits. Empty often means create from baseline.
        baseline_ref: Immutable baseline the candidate must descend from; used for diffs and provenance.
        hypothesis: The single experimental change this edit or trial is testing.
        params: Optional dict merged into the observation payload for adapter-specific knobs.

    Returns:
        A ``dict`` observation produced by ``tool_observation`` for tool
        ``write_routing_layer_directive`` tagged with ``agent_id='global_routing'``.

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
        # Immutable baseline the candidate must descend from; used for diffs and provenance.
        'baseline_ref': baseline_ref,
        # The single experimental change this edit or trial is testing.
        'hypothesis': hypothesis,
    }
    # Merge optional adapter-specific knobs last so they can override defaults carefully.
    if params:
        # In-place update keeps a single payload object for tool_observation.
        payload.update(params)
    # Hand off to tool_observation: records not_run until OpenROAD/other adapter is bound.
    return tool_observation(
        'write_routing_layer_directive',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='global_routing',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``write_layer_adjustment``: Apply a per-layer congestion resource adjustment so GR avoids or favors a layer.
@tool(description='Write a congestion adjustment for one layer.')
def write_layer_adjustment(
    # Isolated design candidate URI/id this tool reads or edits. Empty often means create from baseline.
    candidate_ref: str = '',
    # Immutable baseline the candidate must descend from; used for diffs and provenance.
    baseline_ref: str = '',
    # The single experimental change this edit or trial is testing.
    hypothesis: str = '',
    # Metal/via layer name being adjusted or targeted.
    layer: str = '',
    # Congestion resource adjustment factor for a layer.
    adjustment: str = '',
    # Optional dict merged into the observation payload for adapter-specific knobs.
    params: dict | None = None,
) -> dict:
    """Apply a per-layer congestion resource adjustment so GR avoids or favors a layer.

    Purpose:
        Expose ``write_layer_adjustment`` as a callable skill for the Global-Routing Experiment Agent. The
        real EDA effect (for example OpenROAD) happens only when a framework
        adapter is bound; otherwise the call records a ``not_run`` observation.

    Args:
        candidate_ref: Isolated design candidate URI/id this tool reads or edits. Empty often means create from baseline.
        baseline_ref: Immutable baseline the candidate must descend from; used for diffs and provenance.
        hypothesis: The single experimental change this edit or trial is testing.
        layer: Metal/via layer name being adjusted or targeted.
        adjustment: Congestion resource adjustment factor for a layer.
        params: Optional dict merged into the observation payload for adapter-specific knobs.

    Returns:
        A ``dict`` observation produced by ``tool_observation`` for tool
        ``write_layer_adjustment`` tagged with ``agent_id='global_routing'``.

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
        # Immutable baseline the candidate must descend from; used for diffs and provenance.
        'baseline_ref': baseline_ref,
        # The single experimental change this edit or trial is testing.
        'hypothesis': hypothesis,
        # Metal/via layer name being adjusted or targeted.
        'layer': layer,
        # Congestion resource adjustment factor for a layer.
        'adjustment': adjustment,
    }
    # Merge optional adapter-specific knobs last so they can override defaults carefully.
    if params:
        # In-place update keeps a single payload object for tool_observation.
        payload.update(params)
    # Hand off to tool_observation: records not_run until OpenROAD/other adapter is bound.
    return tool_observation(
        'write_layer_adjustment',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='global_routing',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``write_global_route_guides_spec``: Write topology/buffering guidance that shapes how GR builds guides.
@tool(description='Write topology and buffering guidance for this trial.')
def write_global_route_guides_spec(
    # Isolated design candidate URI/id this tool reads or edits. Empty often means create from baseline.
    candidate_ref: str = '',
    # Immutable baseline the candidate must descend from; used for diffs and provenance.
    baseline_ref: str = '',
    # The single experimental change this edit or trial is testing.
    hypothesis: str = '',
    # Optional dict merged into the observation payload for adapter-specific knobs.
    params: dict | None = None,
) -> dict:
    """Write topology/buffering guidance that shapes how GR builds guides.

    Purpose:
        Expose ``write_global_route_guides_spec`` as a callable skill for the Global-Routing Experiment Agent. The
        real EDA effect (for example OpenROAD) happens only when a framework
        adapter is bound; otherwise the call records a ``not_run`` observation.

    Args:
        candidate_ref: Isolated design candidate URI/id this tool reads or edits. Empty often means create from baseline.
        baseline_ref: Immutable baseline the candidate must descend from; used for diffs and provenance.
        hypothesis: The single experimental change this edit or trial is testing.
        params: Optional dict merged into the observation payload for adapter-specific knobs.

    Returns:
        A ``dict`` observation produced by ``tool_observation`` for tool
        ``write_global_route_guides_spec`` tagged with ``agent_id='global_routing'``.

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
        # Immutable baseline the candidate must descend from; used for diffs and provenance.
        'baseline_ref': baseline_ref,
        # The single experimental change this edit or trial is testing.
        'hypothesis': hypothesis,
    }
    # Merge optional adapter-specific knobs last so they can override defaults carefully.
    if params:
        # In-place update keeps a single payload object for tool_observation.
        payload.update(params)
    # Hand off to tool_observation: records not_run until OpenROAD/other adapter is bound.
    return tool_observation(
        'write_global_route_guides_spec',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='global_routing',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``explore_global_route``: Submit one OpenROAD global_route experiment on an isolated candidate.
@tool(description='Run one global-route experiment. Adapter target: OpenROAD global_route.')
def explore_global_route(
    # Isolated design candidate URI/id this tool reads or edits. Empty often means create from baseline.
    candidate_ref: str = '',
    # Immutable baseline the candidate must descend from; used for diffs and provenance.
    baseline_ref: str = '',
    # Versioned tool recipe id; adapters reject unknown recipes.
    recipe: str = '',
    # PVT corner filter (e.g. slow/fast). Empty means all available corners.
    corner: str = '',
    # Functional or analysis mode filter. Empty means all available modes.
    mode: str = '',
    # Optional dict merged into the observation payload for adapter-specific knobs.
    params: dict | None = None,
) -> dict:
    """Submit one OpenROAD global_route experiment on an isolated candidate.

    Purpose:
        Expose ``explore_global_route`` as a callable skill for the Global-Routing Experiment Agent. The
        real EDA effect (for example OpenROAD) happens only when a framework
        adapter is bound; otherwise the call records a ``not_run`` observation.

    Args:
        candidate_ref: Isolated design candidate URI/id this tool reads or edits. Empty often means create from baseline.
        baseline_ref: Immutable baseline the candidate must descend from; used for diffs and provenance.
        recipe: Versioned tool recipe id; adapters reject unknown recipes.
        corner: PVT corner filter (e.g. slow/fast). Empty means all available corners.
        mode: Functional or analysis mode filter. Empty means all available modes.
        params: Optional dict merged into the observation payload for adapter-specific knobs.

    Returns:
        A ``dict`` observation produced by ``tool_observation`` for tool
        ``explore_global_route`` tagged with ``agent_id='global_routing'``.

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
        # Immutable baseline the candidate must descend from; used for diffs and provenance.
        'baseline_ref': baseline_ref,
        # Versioned tool recipe id; adapters reject unknown recipes.
        'recipe': recipe,
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
        'explore_global_route',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='global_routing',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``report_global_congestion``: Return overflow and demand/supply congestion by layer and GCell region.
@tool(description='Return congestion by layer and region.')
def report_global_congestion(
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
    """Return overflow and demand/supply congestion by layer and GCell region.

    Purpose:
        Expose ``report_global_congestion`` as a callable skill for the Global-Routing Experiment Agent. The
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
        ``report_global_congestion`` tagged with ``agent_id='global_routing'``.

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
        'report_global_congestion',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='global_routing',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``read_route_guides``: Read the guide rectangles/tracks this GR trial produced for detailed routing.
@tool(description='Read the route guides this trial produced.')
def read_route_guides(
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
    """Read the guide rectangles/tracks this GR trial produced for detailed routing.

    Purpose:
        Expose ``read_route_guides`` as a callable skill for the Global-Routing Experiment Agent. The
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
        ``read_route_guides`` tagged with ``agent_id='global_routing'``.

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
        'read_route_guides',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='global_routing',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``read_overflow_nets``: List nets whose demand exceeds GR track capacity (overflow).
@tool(description='List nets with overflow.')
def read_overflow_nets(
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
    """List nets whose demand exceeds GR track capacity (overflow).

    Purpose:
        Expose ``read_overflow_nets`` as a callable skill for the Global-Routing Experiment Agent. The
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
        ``read_overflow_nets`` tagged with ``agent_id='global_routing'``.

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
        'read_overflow_nets',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='global_routing',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``compare_congestion_to_baseline``: Diff congestion of this trial against the parent/baseline route.
@tool(description='Compare congestion with the parent route.')
def compare_congestion_to_baseline(
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
    """Diff congestion of this trial against the parent/baseline route.

    Purpose:
        Expose ``compare_congestion_to_baseline`` as a callable skill for the Global-Routing Experiment Agent. The
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
        ``compare_congestion_to_baseline`` tagged with ``agent_id='global_routing'``.

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
        'compare_congestion_to_baseline',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='global_routing',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``write_route_guides``: Persist guide artifacts so detailed routing can follow them.
@tool(description='Write the guide artifact for detailed routing.')
def write_route_guides(
    # Isolated design candidate URI/id this tool reads or edits. Empty often means create from baseline.
    candidate_ref: str = '',
    # Immutable baseline the candidate must descend from; used for diffs and provenance.
    baseline_ref: str = '',
    # The single experimental change this edit or trial is testing.
    hypothesis: str = '',
    # Optional dict merged into the observation payload for adapter-specific knobs.
    params: dict | None = None,
) -> dict:
    """Persist guide artifacts so detailed routing can follow them.

    Purpose:
        Expose ``write_route_guides`` as a callable skill for the Global-Routing Experiment Agent. The
        real EDA effect (for example OpenROAD) happens only when a framework
        adapter is bound; otherwise the call records a ``not_run`` observation.

    Args:
        candidate_ref: Isolated design candidate URI/id this tool reads or edits. Empty often means create from baseline.
        baseline_ref: Immutable baseline the candidate must descend from; used for diffs and provenance.
        hypothesis: The single experimental change this edit or trial is testing.
        params: Optional dict merged into the observation payload for adapter-specific knobs.

    Returns:
        A ``dict`` observation produced by ``tool_observation`` for tool
        ``write_route_guides`` tagged with ``agent_id='global_routing'``.

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
        # Immutable baseline the candidate must descend from; used for diffs and provenance.
        'baseline_ref': baseline_ref,
        # The single experimental change this edit or trial is testing.
        'hypothesis': hypothesis,
    }
    # Merge optional adapter-specific knobs last so they can override defaults carefully.
    if params:
        # In-place update keeps a single payload object for tool_observation.
        payload.update(params)
    # Hand off to tool_observation: records not_run until OpenROAD/other adapter is bound.
    return tool_observation(
        'write_route_guides',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='global_routing',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``flag_hidden_congested_layer``: Finding: a report omitted a layer that is still over the congestion limit.
@tool(description='Publish a report that omitted a layer over the congestion limit.')
def flag_hidden_congested_layer(
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
    """Finding: a report omitted a layer that is still over the congestion limit.

    Purpose:
        Expose ``flag_hidden_congested_layer`` as a callable skill for the Global-Routing Experiment Agent. The
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
        ``flag_hidden_congested_layer`` tagged with ``agent_id='global_routing'``.

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
        'flag_hidden_congested_layer',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='global_routing',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``flag_global_route_overflow``: Finding: regions remain over the overflow limit after the trial.
@tool(description='Publish regions that remain over the overflow limit.')
def flag_global_route_overflow(
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
    """Finding: regions remain over the overflow limit after the trial.

    Purpose:
        Expose ``flag_global_route_overflow`` as a callable skill for the Global-Routing Experiment Agent. The
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
        ``flag_global_route_overflow`` tagged with ``agent_id='global_routing'``.

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
        'flag_global_route_overflow',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='global_routing',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``record_global_route_recipe``: Record layers, adjustments, and OpenROAD recipe id for provenance.
@tool(description='Record layers, adjustments, and the OpenROAD recipe id.')
def record_global_route_recipe(
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
    """Record layers, adjustments, and OpenROAD recipe id for provenance.

    Purpose:
        Expose ``record_global_route_recipe`` as a callable skill for the Global-Routing Experiment Agent. The
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
        ``record_global_route_recipe`` tagged with ``agent_id='global_routing'``.

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
        'record_global_route_recipe',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='global_routing',  # provenance tag for journal/telemetry
    )
