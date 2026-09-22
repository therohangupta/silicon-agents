"""Tools for the Clock Validation Agent.

Independent clock validation before routing: reachability of every sink, generated-clock relationships, gating enable checks, min pulse width, skew/latency/transition limits, and mode coverage. Publishes gates rather than rebuilding the tree.

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


# Register skill metadata for ``read_clock_validation_spec``: Read the independent clock validation checklist and limits.
@tool(description='Read the clocks, modes, and limits this gate must cover.')
def read_clock_validation_spec(
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
    """Read the independent clock validation checklist and limits.

    Purpose:
        Expose ``read_clock_validation_spec`` as a callable skill for the Clock Validation Agent. The
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
        ``read_clock_validation_spec`` tagged with ``agent_id='clock_validation'``.

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
        'read_clock_validation_spec',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='clock_validation',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``read_primary_cts_reports``: Read primary CTS reports that validation will re-check.
@tool(description='Read skew, latency, and transition reports from primary artifacts.')
def read_primary_cts_reports(
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
    """Read primary CTS reports that validation will re-check.

    Purpose:
        Expose ``read_primary_cts_reports`` as a callable skill for the Clock Validation Agent. The
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
        ``read_primary_cts_reports`` tagged with ``agent_id='clock_validation'``.

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
        'read_primary_cts_reports',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='clock_validation',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``check_cts_provenance``: Verify CTS provenance before trusting the tree metrics.
@tool(description='Check the CTS tool version and recipe against the frozen flow.')
def check_cts_provenance(
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
    """Verify CTS provenance before trusting the tree metrics.

    Purpose:
        Expose ``check_cts_provenance`` as a callable skill for the Clock Validation Agent. The
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
        ``check_cts_provenance`` tagged with ``agent_id='clock_validation'``.

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
        'check_cts_provenance',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='clock_validation',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``validate_clock_reachability``: Ensure every required sink is reached by its clock.
@tool(description='Check that every sink is reached in every required mode.')
def validate_clock_reachability(
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
    """Ensure every required sink is reached by its clock.

    Purpose:
        Expose ``validate_clock_reachability`` as a callable skill for the Clock Validation Agent. The
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
        ``validate_clock_reachability`` tagged with ``agent_id='clock_validation'``.

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
        'validate_clock_reachability',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='clock_validation',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``check_generated_clock_relationships``: Validate generated-clock source/divide/edge relationships.
@tool(description='Check generated-clock sources and divide ratios.')
def check_generated_clock_relationships(
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
    """Validate generated-clock source/divide/edge relationships.

    Purpose:
        Expose ``check_generated_clock_relationships`` as a callable skill for the Clock Validation Agent. The
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
        ``check_generated_clock_relationships`` tagged with ``agent_id='clock_validation'``.

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
        'check_generated_clock_relationships',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='clock_validation',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``check_clock_gating``: Check integrated clock-gating enable and timing arcs.
@tool(description='Check integrated clock gates against the declared intent.')
def check_clock_gating(
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
    """Check integrated clock-gating enable and timing arcs.

    Purpose:
        Expose ``check_clock_gating`` as a callable skill for the Clock Validation Agent. The
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
        ``check_clock_gating`` tagged with ``agent_id='clock_validation'``.

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
        'check_clock_gating',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='clock_validation',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``check_pulse_width``: Check minimum pulse-width constraints on clock pins.
@tool(description='Check pulse width at the sinks.')
def check_pulse_width(
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
    """Check minimum pulse-width constraints on clock pins.

    Purpose:
        Expose ``check_pulse_width`` as a callable skill for the Clock Validation Agent. The
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
        ``check_pulse_width`` tagged with ``agent_id='clock_validation'``.

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
        'check_pulse_width',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='clock_validation',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``check_clock_skew_limit``: Check reported skew against the allowed skew budget.
@tool(description='Check skew against the spec.')
def check_clock_skew_limit(
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
    """Check reported skew against the allowed skew budget.

    Purpose:
        Expose ``check_clock_skew_limit`` as a callable skill for the Clock Validation Agent. The
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
        ``check_clock_skew_limit`` tagged with ``agent_id='clock_validation'``.

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
        'check_clock_skew_limit',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='clock_validation',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``check_clock_mode_coverage``: Ensure every required functional/test mode was analyzed.
@tool(description='List required modes that have no clock report.')
def check_clock_mode_coverage(
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
    """Ensure every required functional/test mode was analyzed.

    Purpose:
        Expose ``check_clock_mode_coverage`` as a callable skill for the Clock Validation Agent. The
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
        ``check_clock_mode_coverage`` tagged with ``agent_id='clock_validation'``.

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
        'check_clock_mode_coverage',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='clock_validation',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``compare_cts_summary``: Compare validator summary against CTS worker claims.
@tool(description='Compare the CTS summary with the primary reports.')
def compare_cts_summary(
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
    """Compare validator summary against CTS worker claims.

    Purpose:
        Expose ``compare_cts_summary`` as a callable skill for the Clock Validation Agent. The
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
        ``compare_cts_summary`` tagged with ``agent_id='clock_validation'``.

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
        'compare_cts_summary',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='clock_validation',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``emit_clock_gate``: Emit a pass/fail clock gate before routing may begin.
@tool(description='Record whether the clock contract passed.')
def emit_clock_gate(
    # Isolated design candidate URI/id this tool reads or edits. Empty often means create from baseline.
    candidate_ref: str = '',
    # Argument ``gate_id`` forwarded into the tool observation payload for the EDA adapter.
    gate_id: str = '',
    # Argument ``check_refs`` forwarded into the tool observation payload for the EDA adapter.
    check_refs: str = '',
    # Optional dict merged into the observation payload for adapter-specific knobs.
    params: dict | None = None,
) -> dict:
    """Emit a pass/fail clock gate before routing may begin.

    Purpose:
        Expose ``emit_clock_gate`` as a callable skill for the Clock Validation Agent. The
        real EDA effect (for example OpenROAD) happens only when a framework
        adapter is bound; otherwise the call records a ``not_run`` observation.

    Args:
        candidate_ref: Isolated design candidate URI/id this tool reads or edits. Empty often means create from baseline.
        gate_id: Argument ``gate_id`` forwarded into the tool observation payload for the EDA adapter.
        check_refs: Argument ``check_refs`` forwarded into the tool observation payload for the EDA adapter.
        params: Optional dict merged into the observation payload for adapter-specific knobs.

    Returns:
        A ``dict`` observation produced by ``tool_observation`` for tool
        ``emit_clock_gate`` tagged with ``agent_id='clock_validation'``.

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
        # Forward ``gate_id`` for the clock_validation adapter.
        'gate_id': gate_id,
        # Forward ``check_refs`` for the clock_validation adapter.
        'check_refs': check_refs,
    }
    # Merge optional adapter-specific knobs last so they can override defaults carefully.
    if params:
        # In-place update keeps a single payload object for tool_observation.
        payload.update(params)
    # Hand off to tool_observation: records not_run until OpenROAD/other adapter is bound.
    return tool_observation(
        'emit_clock_gate',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='clock_validation',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``publish_uncovered_clock_mode``: Publish that a required clock mode lacks coverage.
@tool(description='Publish a required mode with no clock check.')
def publish_uncovered_clock_mode(
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
    """Publish that a required clock mode lacks coverage.

    Purpose:
        Expose ``publish_uncovered_clock_mode`` as a callable skill for the Clock Validation Agent. The
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
        ``publish_uncovered_clock_mode`` tagged with ``agent_id='clock_validation'``.

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
        'publish_uncovered_clock_mode',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='clock_validation',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``publish_clock_spec_miss``: Publish that the built tree misses part of the clock spec.
@tool(description='Publish a skew, latency, or transition miss.')
def publish_clock_spec_miss(
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
    """Publish that the built tree misses part of the clock spec.

    Purpose:
        Expose ``publish_clock_spec_miss`` as a callable skill for the Clock Validation Agent. The
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
        ``publish_clock_spec_miss`` tagged with ``agent_id='clock_validation'``.

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
        'publish_clock_spec_miss',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='clock_validation',  # provenance tag for journal/telemetry
    )
