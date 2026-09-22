"""Tools for the Placement Lead.

Standard-cell placement positions instances inside a partition after floorplan. The lead coordinates timing, congestion, power, and legalization across experiment workers and evaluators, then recommends which placement candidate proceeds.

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


# Register skill metadata for ``plan_placement_trials``: Plan the set of placement experiment trials for this partition.
@tool(description='Emit the placement and evaluation workflow.')
def plan_placement_trials(
    # Natural-language objective for a planned child task or workflow step.
    objective: str = '',
    # Parent task id used to nest child work in the journal.
    parent_task_id: str = '',
    # Design block/partition scope this request applies to.
    scope_block: str = '',
    # Optional dict merged into the observation payload for adapter-specific knobs.
    params: dict | None = None,
) -> dict:
    """Plan the set of placement experiment trials for this partition.

    Purpose:
        Expose ``plan_placement_trials`` as a callable skill for the Placement Lead. The
        real EDA effect (for example OpenROAD) happens only when a framework
        adapter is bound; otherwise the call records a ``not_run`` observation.

    Args:
        objective: Natural-language objective for a planned child task or workflow step.
        parent_task_id: Parent task id used to nest child work in the journal.
        scope_block: Design block/partition scope this request applies to.
        params: Optional dict merged into the observation payload for adapter-specific knobs.

    Returns:
        A ``dict`` observation produced by ``tool_observation`` for tool
        ``plan_placement_trials`` tagged with ``agent_id='placement_lead'``.

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
        'plan_placement_trials',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='placement_lead',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``request_placement_trial``: Dispatch one placement experiment worker with a hypothesis.
@tool(description='Open one isolated placement strategy.')
def request_placement_trial(
    # Natural-language objective for a planned child task or workflow step.
    objective: str = '',
    # Parent task id used to nest child work in the journal.
    parent_task_id: str = '',
    # Design block/partition scope this request applies to.
    scope_block: str = '',
    # Argument ``strategy`` forwarded into the tool observation payload for the EDA adapter.
    strategy: str = '',
    # Optional dict merged into the observation payload for adapter-specific knobs.
    params: dict | None = None,
) -> dict:
    """Dispatch one placement experiment worker with a hypothesis.

    Purpose:
        Expose ``request_placement_trial`` as a callable skill for the Placement Lead. The
        real EDA effect (for example OpenROAD) happens only when a framework
        adapter is bound; otherwise the call records a ``not_run`` observation.

    Args:
        objective: Natural-language objective for a planned child task or workflow step.
        parent_task_id: Parent task id used to nest child work in the journal.
        scope_block: Design block/partition scope this request applies to.
        strategy: Argument ``strategy`` forwarded into the tool observation payload for the EDA adapter.
        params: Optional dict merged into the observation payload for adapter-specific knobs.

    Returns:
        A ``dict`` observation produced by ``tool_observation`` for tool
        ``request_placement_trial`` tagged with ``agent_id='placement_lead'``.

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
        # Forward ``strategy`` for the placement_lead adapter.
        'strategy': strategy,
    }
    # Merge optional adapter-specific knobs last so they can override defaults carefully.
    if params:
        # In-place update keeps a single payload object for tool_observation.
        payload.update(params)
    # Hand off to tool_observation: records not_run until OpenROAD/other adapter is bound.
    return tool_observation(
        'request_placement_trial',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='placement_lead',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``request_placement_evaluation``: Ask the multi-corner evaluator to grade a placement candidate.
@tool(description='Hand a candidate to the multi-corner evaluator.')
def request_placement_evaluation(
    # Natural-language objective for a planned child task or workflow step.
    objective: str = '',
    # Parent task id used to nest child work in the journal.
    parent_task_id: str = '',
    # Design block/partition scope this request applies to.
    scope_block: str = '',
    # Optional dict merged into the observation payload for adapter-specific knobs.
    params: dict | None = None,
) -> dict:
    """Ask the multi-corner evaluator to grade a placement candidate.

    Purpose:
        Expose ``request_placement_evaluation`` as a callable skill for the Placement Lead. The
        real EDA effect (for example OpenROAD) happens only when a framework
        adapter is bound; otherwise the call records a ``not_run`` observation.

    Args:
        objective: Natural-language objective for a planned child task or workflow step.
        parent_task_id: Parent task id used to nest child work in the journal.
        scope_block: Design block/partition scope this request applies to.
        params: Optional dict merged into the observation payload for adapter-specific knobs.

    Returns:
        A ``dict`` observation produced by ``tool_observation`` for tool
        ``request_placement_evaluation`` tagged with ``agent_id='placement_lead'``.

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
        'request_placement_evaluation',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='placement_lead',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``request_boundary_check``: Ask the boundary coordinator to check abutting partition interfaces.
@tool(description='Open a cross-partition boundary check.')
def request_boundary_check(
    # Natural-language objective for a planned child task or workflow step.
    objective: str = '',
    # Parent task id used to nest child work in the journal.
    parent_task_id: str = '',
    # Design block/partition scope this request applies to.
    scope_block: str = '',
    # Optional dict merged into the observation payload for adapter-specific knobs.
    params: dict | None = None,
) -> dict:
    """Ask the boundary coordinator to check abutting partition interfaces.

    Purpose:
        Expose ``request_boundary_check`` as a callable skill for the Placement Lead. The
        real EDA effect (for example OpenROAD) happens only when a framework
        adapter is bound; otherwise the call records a ``not_run`` observation.

    Args:
        objective: Natural-language objective for a planned child task or workflow step.
        parent_task_id: Parent task id used to nest child work in the journal.
        scope_block: Design block/partition scope this request applies to.
        params: Optional dict merged into the observation payload for adapter-specific knobs.

    Returns:
        A ``dict`` observation produced by ``tool_observation`` for tool
        ``request_boundary_check`` tagged with ``agent_id='placement_lead'``.

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
        'request_boundary_check',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='placement_lead',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``read_qualified_floorplan``: Read the floorplan inputs that placement is allowed to consume.
@tool(description='Read the floorplan this placement inherits.')
def read_qualified_floorplan(
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
    """Read the floorplan inputs that placement is allowed to consume.

    Purpose:
        Expose ``read_qualified_floorplan`` as a callable skill for the Placement Lead. The
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
        ``read_qualified_floorplan`` tagged with ``agent_id='placement_lead'``.

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
        'read_qualified_floorplan',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='placement_lead',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``read_placement_metrics``: Read HPWL, density, congestion, and timing metrics for candidates.
@tool(description='Read timing, congestion, power, and legality for each trial.')
def read_placement_metrics(
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
    """Read HPWL, density, congestion, and timing metrics for candidates.

    Purpose:
        Expose ``read_placement_metrics`` as a callable skill for the Placement Lead. The
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
        ``read_placement_metrics`` tagged with ``agent_id='placement_lead'``.

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
        'read_placement_metrics',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='placement_lead',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``read_corner_coverage``: Read which PVT corners/modes have been evaluated.
@tool(description='Read which modes and corners each trial has been scored on.')
def read_corner_coverage(
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
    """Read which PVT corners/modes have been evaluated.

    Purpose:
        Expose ``read_corner_coverage`` as a callable skill for the Placement Lead. The
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
        ``read_corner_coverage`` tagged with ``agent_id='placement_lead'``.

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
        'read_corner_coverage',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='placement_lead',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``compare_placement_trials``: Compare placement trial metrics and evaluator grades.
@tool(description='Rank trials that are legal in every required corner.')
def compare_placement_trials(
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
    """Compare placement trial metrics and evaluator grades.

    Purpose:
        Expose ``compare_placement_trials`` as a callable skill for the Placement Lead. The
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
        ``compare_placement_trials`` tagged with ``agent_id='placement_lead'``.

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
        'compare_placement_trials',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='placement_lead',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``recommend_placement_candidate``: Recommend which placement candidate should advance.
@tool(description='Record which legal candidate should advance. This does not promote it.')
def recommend_placement_candidate(
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
    """Recommend which placement candidate should advance.

    Purpose:
        Expose ``recommend_placement_candidate`` as a callable skill for the Placement Lead. The
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
        ``recommend_placement_candidate`` tagged with ``agent_id='placement_lead'``.

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
        'recommend_placement_candidate',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='placement_lead',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``flag_corner_shifted_violation``: Finding: an apparent gain only moved violations to another corner.
@tool(description='Publish a gain that moved a violation into another corner.')
def flag_corner_shifted_violation(
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
    """Finding: an apparent gain only moved violations to another corner.

    Purpose:
        Expose ``flag_corner_shifted_violation`` as a callable skill for the Placement Lead. The
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
        ``flag_corner_shifted_violation`` tagged with ``agent_id='placement_lead'``.

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
        'flag_corner_shifted_violation',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='placement_lead',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``record_placement_strategy``: Journal placement strategy and trial matrix for provenance.
@tool(description='Record the next strategy after a plateau.')
def record_placement_strategy(
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
    """Journal placement strategy and trial matrix for provenance.

    Purpose:
        Expose ``record_placement_strategy`` as a callable skill for the Placement Lead. The
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
        ``record_placement_strategy`` tagged with ``agent_id='placement_lead'``.

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
        'record_placement_strategy',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='placement_lead',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``request_placement_decision``: Request an explicit decision on which placement proceeds.
@tool(description='Ask a human to choose among legal placements.')
def request_placement_decision(
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
    """Request an explicit decision on which placement proceeds.

    Purpose:
        Expose ``request_placement_decision`` as a callable skill for the Placement Lead. The
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
        ``request_placement_decision`` tagged with ``agent_id='placement_lead'``.

    Side effects:
        Does not mutate the canonical design until an adapter executes.
        Downstream journal/finding publishers may persist the observation.

    Failures:
        Unbound backend: returns ``not_run`` rather than raising. Bound
        adapters may raise on unknown recipes, missing candidates, or tool errors.
    """
    # Build the observation payload from explicit skill arguments (EDA handles).
    payload = {
        # Forward ``decision`` for the placement_lead adapter.
        'decision': decision,
        # Forward ``options`` for the placement_lead adapter.
        'options': options,
        # Comma-separated artifact URIs that support a finding.
        'evidence_refs': evidence_refs,
        # Forward ``deadline`` for the placement_lead adapter.
        'deadline': deadline,
    }
    # Merge optional adapter-specific knobs last so they can override defaults carefully.
    if params:
        # In-place update keeps a single payload object for tool_observation.
        payload.update(params)
    # Hand off to tool_observation: records not_run until OpenROAD/other adapter is bound.
    return tool_observation(
        'request_placement_decision',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='placement_lead',  # provenance tag for journal/telemetry
    )
