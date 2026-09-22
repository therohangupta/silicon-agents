"""Tools for the CTS Agent.

Clock-tree synthesis (CTS) builds a buffered tree or mesh so every sink sees acceptable skew, insertion delay, and transition. Targets OpenROAD clock_tree_synthesis, repair_clock_nets, and related clock repairs.

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


# Register skill metadata for ``read_clock_spec``: Read clocks, generated clocks, targets, and test clocks from constraints.
@tool(description='Read clocks, generated clocks, targets, and test clocks.')
def read_clock_spec(
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
    """Read clocks, generated clocks, targets, and test clocks from constraints.

    Purpose:
        Expose ``read_clock_spec`` as a callable skill for the CTS Agent. The
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
        ``read_clock_spec`` tagged with ``agent_id='cts'``.

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
        'read_clock_spec',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='cts',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``write_clock_transition_target``: Write the max transition target for one clock network.
@tool(description='Write the transition target for one clock.')
def write_clock_transition_target(
    # Isolated design candidate URI/id this tool reads or edits. Empty often means create from baseline.
    candidate_ref: str = '',
    # Immutable baseline the candidate must descend from; used for diffs and provenance.
    baseline_ref: str = '',
    # The single experimental change this edit or trial is testing.
    hypothesis: str = '',
    # Argument ``clock_name`` forwarded into the tool observation payload for the EDA adapter.
    clock_name: str = '',
    # Optional dict merged into the observation payload for adapter-specific knobs.
    params: dict | None = None,
) -> dict:
    """Write the max transition target for one clock network.

    Purpose:
        Expose ``write_clock_transition_target`` as a callable skill for the CTS Agent. The
        real EDA effect (for example OpenROAD) happens only when a framework
        adapter is bound; otherwise the call records a ``not_run`` observation.

    Args:
        candidate_ref: Isolated design candidate URI/id this tool reads or edits. Empty often means create from baseline.
        baseline_ref: Immutable baseline the candidate must descend from; used for diffs and provenance.
        hypothesis: The single experimental change this edit or trial is testing.
        clock_name: Argument ``clock_name`` forwarded into the tool observation payload for the EDA adapter.
        params: Optional dict merged into the observation payload for adapter-specific knobs.

    Returns:
        A ``dict`` observation produced by ``tool_observation`` for tool
        ``write_clock_transition_target`` tagged with ``agent_id='cts'``.

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
        # Forward ``clock_name`` for the cts adapter.
        'clock_name': clock_name,
    }
    # Merge optional adapter-specific knobs last so they can override defaults carefully.
    if params:
        # In-place update keeps a single payload object for tool_observation.
        payload.update(params)
    # Hand off to tool_observation: records not_run until OpenROAD/other adapter is bound.
    return tool_observation(
        'write_clock_transition_target',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='cts',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``write_clock_skew_target``: Write the skew target for one clock network.
@tool(description='Write the skew target for one clock.')
def write_clock_skew_target(
    # Isolated design candidate URI/id this tool reads or edits. Empty often means create from baseline.
    candidate_ref: str = '',
    # Immutable baseline the candidate must descend from; used for diffs and provenance.
    baseline_ref: str = '',
    # The single experimental change this edit or trial is testing.
    hypothesis: str = '',
    # Argument ``clock_name`` forwarded into the tool observation payload for the EDA adapter.
    clock_name: str = '',
    # Optional dict merged into the observation payload for adapter-specific knobs.
    params: dict | None = None,
) -> dict:
    """Write the skew target for one clock network.

    Purpose:
        Expose ``write_clock_skew_target`` as a callable skill for the CTS Agent. The
        real EDA effect (for example OpenROAD) happens only when a framework
        adapter is bound; otherwise the call records a ``not_run`` observation.

    Args:
        candidate_ref: Isolated design candidate URI/id this tool reads or edits. Empty often means create from baseline.
        baseline_ref: Immutable baseline the candidate must descend from; used for diffs and provenance.
        hypothesis: The single experimental change this edit or trial is testing.
        clock_name: Argument ``clock_name`` forwarded into the tool observation payload for the EDA adapter.
        params: Optional dict merged into the observation payload for adapter-specific knobs.

    Returns:
        A ``dict`` observation produced by ``tool_observation`` for tool
        ``write_clock_skew_target`` tagged with ``agent_id='cts'``.

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
        # Forward ``clock_name`` for the cts adapter.
        'clock_name': clock_name,
    }
    # Merge optional adapter-specific knobs last so they can override defaults carefully.
    if params:
        # In-place update keeps a single payload object for tool_observation.
        payload.update(params)
    # Hand off to tool_observation: records not_run until OpenROAD/other adapter is bound.
    return tool_observation(
        'write_clock_skew_target',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='cts',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``write_clock_sink_rules``: Write sink clustering and buffer/inverter rules for CTS.
@tool(description='Write sink clustering and buffer rules.')
def write_clock_sink_rules(
    # Isolated design candidate URI/id this tool reads or edits. Empty often means create from baseline.
    candidate_ref: str = '',
    # Immutable baseline the candidate must descend from; used for diffs and provenance.
    baseline_ref: str = '',
    # The single experimental change this edit or trial is testing.
    hypothesis: str = '',
    # Optional dict merged into the observation payload for adapter-specific knobs.
    params: dict | None = None,
) -> dict:
    """Write sink clustering and buffer/inverter rules for CTS.

    Purpose:
        Expose ``write_clock_sink_rules`` as a callable skill for the CTS Agent. The
        real EDA effect (for example OpenROAD) happens only when a framework
        adapter is bound; otherwise the call records a ``not_run`` observation.

    Args:
        candidate_ref: Isolated design candidate URI/id this tool reads or edits. Empty often means create from baseline.
        baseline_ref: Immutable baseline the candidate must descend from; used for diffs and provenance.
        hypothesis: The single experimental change this edit or trial is testing.
        params: Optional dict merged into the observation payload for adapter-specific knobs.

    Returns:
        A ``dict`` observation produced by ``tool_observation`` for tool
        ``write_clock_sink_rules`` tagged with ``agent_id='cts'``.

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
        'write_clock_sink_rules',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='cts',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``build_clock_tree``: Run OpenROAD clock_tree_synthesis for the required modes.
@tool(description='Run clock-tree synthesis for the required modes. Adapter target: OpenROAD clock_tree_synthesis.')
def build_clock_tree(
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
    """Run OpenROAD clock_tree_synthesis for the required modes.

    Purpose:
        Expose ``build_clock_tree`` as a callable skill for the CTS Agent. The
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
        ``build_clock_tree`` tagged with ``agent_id='cts'``.

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
        'build_clock_tree',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='cts',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``repair_clock_nets``: Repair clock nets on the isolated candidate (OpenROAD repair_clock_nets).
@tool(description='Repair clock nets on the isolated candidate. Adapter target: OpenROAD repair_clock_nets.')
def repair_clock_nets(
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
    """Repair clock nets on the isolated candidate (OpenROAD repair_clock_nets).

    Purpose:
        Expose ``repair_clock_nets`` as a callable skill for the CTS Agent. The
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
        ``repair_clock_nets`` tagged with ``agent_id='cts'``.

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
        'repair_clock_nets',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='cts',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``repair_clock_inverters``: Balance or fix clock inverter stages on the candidate.
@tool(description='Balance clock inverters on the isolated candidate.')
def repair_clock_inverters(
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
    """Balance or fix clock inverter stages on the candidate.

    Purpose:
        Expose ``repair_clock_inverters`` as a callable skill for the CTS Agent. The
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
        ``repair_clock_inverters`` tagged with ``agent_id='cts'``.

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
        'repair_clock_inverters',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='cts',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``report_skew_and_insertion``: Report skew, insertion delay, transition, and clock power.
@tool(description='Report skew, insertion delay, transition, and power.')
def report_skew_and_insertion(
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
    """Report skew, insertion delay, transition, and clock power.

    Purpose:
        Expose ``report_skew_and_insertion`` as a callable skill for the CTS Agent. The
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
        ``report_skew_and_insertion`` tagged with ``agent_id='cts'``.

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
        'report_skew_and_insertion',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='cts',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``report_clock_latency``: Report latency by sink region for the built tree.
@tool(description='Report latency by sink region.')
def report_clock_latency(
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
    """Report latency by sink region for the built tree.

    Purpose:
        Expose ``report_clock_latency`` as a callable skill for the CTS Agent. The
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
        ``report_clock_latency`` tagged with ``agent_id='cts'``.

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
        'report_clock_latency',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='cts',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``report_clock_transition``: Report sinks still over the transition limit.
@tool(description='Report sinks over the transition limit.')
def report_clock_transition(
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
    """Report sinks still over the transition limit.

    Purpose:
        Expose ``report_clock_transition`` as a callable skill for the CTS Agent. The
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
        ``report_clock_transition`` tagged with ``agent_id='cts'``.

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
        'report_clock_transition',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='cts',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``report_clock_power``: Report clock-network dynamic/leakage power.
@tool(description='Report clock-network power.')
def report_clock_power(
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
    """Report clock-network dynamic/leakage power.

    Purpose:
        Expose ``report_clock_power`` as a callable skill for the CTS Agent. The
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
        ``report_clock_power`` tagged with ``agent_id='cts'``.

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
        'report_clock_power',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='cts',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``check_test_clock_built``: Check that every required DFT/test clock was constructed.
@tool(description='Check that every required test clock was built.')
def check_test_clock_built(
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
    """Check that every required DFT/test clock was constructed.

    Purpose:
        Expose ``check_test_clock_built`` as a callable skill for the CTS Agent. The
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
        ``check_test_clock_built`` tagged with ``agent_id='cts'``.

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
        'check_test_clock_built',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='cts',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``write_cts_def``: Write the clocked DEF/ODB artifact after CTS.
@tool(description='Write the clocked DEF.')
def write_cts_def(
    # Isolated design candidate URI/id this tool reads or edits. Empty often means create from baseline.
    candidate_ref: str = '',
    # Immutable baseline the candidate must descend from; used for diffs and provenance.
    baseline_ref: str = '',
    # The single experimental change this edit or trial is testing.
    hypothesis: str = '',
    # Optional dict merged into the observation payload for adapter-specific knobs.
    params: dict | None = None,
) -> dict:
    """Write the clocked DEF/ODB artifact after CTS.

    Purpose:
        Expose ``write_cts_def`` as a callable skill for the CTS Agent. The
        real EDA effect (for example OpenROAD) happens only when a framework
        adapter is bound; otherwise the call records a ``not_run`` observation.

    Args:
        candidate_ref: Isolated design candidate URI/id this tool reads or edits. Empty often means create from baseline.
        baseline_ref: Immutable baseline the candidate must descend from; used for diffs and provenance.
        hypothesis: The single experimental change this edit or trial is testing.
        params: Optional dict merged into the observation payload for adapter-specific knobs.

    Returns:
        A ``dict`` observation produced by ``tool_observation`` for tool
        ``write_cts_def`` tagged with ``agent_id='cts'``.

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
        'write_cts_def',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='cts',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``flag_dropped_test_clock``: Finding: a required test clock was dropped from the tree.
@tool(description='Publish a required test clock that CTS did not build.')
def flag_dropped_test_clock(
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
    """Finding: a required test clock was dropped from the tree.

    Purpose:
        Expose ``flag_dropped_test_clock`` as a callable skill for the CTS Agent. The
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
        ``flag_dropped_test_clock`` tagged with ``agent_id='cts'``.

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
        'flag_dropped_test_clock',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='cts',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``record_cts_provenance``: Record CTS recipe, targets, and tool versions.
@tool(description='Record the CTS recipe, corners, and DEF ref.')
def record_cts_provenance(
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
    """Record CTS recipe, targets, and tool versions.

    Purpose:
        Expose ``record_cts_provenance`` as a callable skill for the CTS Agent. The
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
        ``record_cts_provenance`` tagged with ``agent_id='cts'``.

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
        'record_cts_provenance',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='cts',  # provenance tag for journal/telemetry
    )
