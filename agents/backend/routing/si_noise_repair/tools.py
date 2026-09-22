"""Tools for the SI/Noise Repair Agent.

Signal integrity (SI) covers crosstalk, coupling capacitance, and glitches on victim nets attacked by aggressors. Repairs include spacing, shielding, and layer changes, then re-verify noise and timing impact.

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


# Register skill metadata for ``read_noise_report``: Read the SI/noise analysis report for this routed candidate.
@tool(description='Read the noise report for this candidate.')
def read_noise_report(
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
    """Read the SI/noise analysis report for this routed candidate.

    Purpose:
        Expose ``read_noise_report`` as a callable skill for the SI/Noise Repair Agent. The
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
        ``read_noise_report`` tagged with ``agent_id='si_noise_repair'``.

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
        'read_noise_report',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='si_noise_repair',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``list_aggressor_victim_pairs``: List coupled aggressor/victim net pairs that exceed noise limits.
@tool(description='List aggressor and victim pairs over the noise limit.')
def list_aggressor_victim_pairs(
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
    """List coupled aggressor/victim net pairs that exceed noise limits.

    Purpose:
        Expose ``list_aggressor_victim_pairs`` as a callable skill for the SI/Noise Repair Agent. The
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
        ``list_aggressor_victim_pairs`` tagged with ``agent_id='si_noise_repair'``.

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
        'list_aggressor_victim_pairs',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='si_noise_repair',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``classify_crosstalk_delay``: Classify delay-pushout or speedup on a victim due to crosstalk.
@tool(description='Classify crosstalk delay on one victim.')
def classify_crosstalk_delay(
    # Isolated design candidate URI/id this tool reads or edits. Empty often means create from baseline.
    candidate_ref: str = '',
    # Artifact URI of a report. Empty typically means latest report for the candidate.
    report_ref: str = '',
    # PVT corner filter (e.g. slow/fast). Empty means all available corners.
    corner: str = '',
    # Functional or analysis mode filter. Empty means all available modes.
    mode: str = '',
    # Argument ``net`` forwarded into the tool observation payload for the EDA adapter.
    net: str = '',
    # Optional dict merged into the observation payload for adapter-specific knobs.
    params: dict | None = None,
) -> dict:
    """Classify delay-pushout or speedup on a victim due to crosstalk.

    Purpose:
        Expose ``classify_crosstalk_delay`` as a callable skill for the SI/Noise Repair Agent. The
        real EDA effect (for example OpenROAD) happens only when a framework
        adapter is bound; otherwise the call records a ``not_run`` observation.

    Args:
        candidate_ref: Isolated design candidate URI/id this tool reads or edits. Empty often means create from baseline.
        report_ref: Artifact URI of a report. Empty typically means latest report for the candidate.
        corner: PVT corner filter (e.g. slow/fast). Empty means all available corners.
        mode: Functional or analysis mode filter. Empty means all available modes.
        net: Argument ``net`` forwarded into the tool observation payload for the EDA adapter.
        params: Optional dict merged into the observation payload for adapter-specific knobs.

    Returns:
        A ``dict`` observation produced by ``tool_observation`` for tool
        ``classify_crosstalk_delay`` tagged with ``agent_id='si_noise_repair'``.

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
        # Forward ``net`` for the si_noise_repair adapter.
        'net': net,
    }
    # Merge optional adapter-specific knobs last so they can override defaults carefully.
    if params:
        # In-place update keeps a single payload object for tool_observation.
        payload.update(params)
    # Hand off to tool_observation: records not_run until OpenROAD/other adapter is bound.
    return tool_observation(
        'classify_crosstalk_delay',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='si_noise_repair',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``classify_glitch``: Classify static/dynamic glitch noise on a victim net.
@tool(description='Classify glitches on one victim.')
def classify_glitch(
    # Isolated design candidate URI/id this tool reads or edits. Empty often means create from baseline.
    candidate_ref: str = '',
    # Artifact URI of a report. Empty typically means latest report for the candidate.
    report_ref: str = '',
    # PVT corner filter (e.g. slow/fast). Empty means all available corners.
    corner: str = '',
    # Functional or analysis mode filter. Empty means all available modes.
    mode: str = '',
    # Argument ``net`` forwarded into the tool observation payload for the EDA adapter.
    net: str = '',
    # Optional dict merged into the observation payload for adapter-specific knobs.
    params: dict | None = None,
) -> dict:
    """Classify static/dynamic glitch noise on a victim net.

    Purpose:
        Expose ``classify_glitch`` as a callable skill for the SI/Noise Repair Agent. The
        real EDA effect (for example OpenROAD) happens only when a framework
        adapter is bound; otherwise the call records a ``not_run`` observation.

    Args:
        candidate_ref: Isolated design candidate URI/id this tool reads or edits. Empty often means create from baseline.
        report_ref: Artifact URI of a report. Empty typically means latest report for the candidate.
        corner: PVT corner filter (e.g. slow/fast). Empty means all available corners.
        mode: Functional or analysis mode filter. Empty means all available modes.
        net: Argument ``net`` forwarded into the tool observation payload for the EDA adapter.
        params: Optional dict merged into the observation payload for adapter-specific knobs.

    Returns:
        A ``dict`` observation produced by ``tool_observation`` for tool
        ``classify_glitch`` tagged with ``agent_id='si_noise_repair'``.

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
        # Forward ``net`` for the si_noise_repair adapter.
        'net': net,
    }
    # Merge optional adapter-specific knobs last so they can override defaults carefully.
    if params:
        # In-place update keeps a single payload object for tool_observation.
        payload.update(params)
    # Hand off to tool_observation: records not_run until OpenROAD/other adapter is bound.
    return tool_observation(
        'classify_glitch',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='si_noise_repair',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``propose_spacing_repair``: Propose increasing spacing (and track cost) to cut coupling.
@tool(description='Publish a spacing change and the tracks it consumes.')
def propose_spacing_repair(
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
    """Propose increasing spacing (and track cost) to cut coupling.

    Purpose:
        Expose ``propose_spacing_repair`` as a callable skill for the SI/Noise Repair Agent. The
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
        ``propose_spacing_repair`` tagged with ``agent_id='si_noise_repair'``.

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
        'propose_spacing_repair',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='si_noise_repair',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``propose_shield``: Propose inserting a grounded/power shield net between aggressor and victim.
@tool(description='Publish a shield net and the layer it uses.')
def propose_shield(
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
    """Propose inserting a grounded/power shield net between aggressor and victim.

    Purpose:
        Expose ``propose_shield`` as a callable skill for the SI/Noise Repair Agent. The
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
        ``propose_shield`` tagged with ``agent_id='si_noise_repair'``.

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
        'propose_shield',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='si_noise_repair',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``propose_noise_layer_change``: Propose moving a net to another metal layer to reduce coupling.
@tool(description='Publish a layer change for one victim or aggressor.')
def propose_noise_layer_change(
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
    """Propose moving a net to another metal layer to reduce coupling.

    Purpose:
        Expose ``propose_noise_layer_change`` as a callable skill for the SI/Noise Repair Agent. The
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
        ``propose_noise_layer_change`` tagged with ``agent_id='si_noise_repair'``.

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
        'propose_noise_layer_change',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='si_noise_repair',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``apply_noise_repair``: Apply one spacing, shield, or layer change on an isolated candidate.
@tool(description='Apply one spacing, shield, or layer change on an isolated candidate.')
def apply_noise_repair(
    # Isolated design candidate URI/id this tool reads or edits. Empty often means create from baseline.
    candidate_ref: str = '',
    # Immutable baseline the candidate must descend from; used for diffs and provenance.
    baseline_ref: str = '',
    # The single experimental change this edit or trial is testing.
    hypothesis: str = '',
    # Argument ``net`` forwarded into the tool observation payload for the EDA adapter.
    net: str = '',
    # Optional dict merged into the observation payload for adapter-specific knobs.
    params: dict | None = None,
) -> dict:
    """Apply one spacing, shield, or layer change on an isolated candidate.

    Purpose:
        Expose ``apply_noise_repair`` as a callable skill for the SI/Noise Repair Agent. The
        real EDA effect (for example OpenROAD) happens only when a framework
        adapter is bound; otherwise the call records a ``not_run`` observation.

    Args:
        candidate_ref: Isolated design candidate URI/id this tool reads or edits. Empty often means create from baseline.
        baseline_ref: Immutable baseline the candidate must descend from; used for diffs and provenance.
        hypothesis: The single experimental change this edit or trial is testing.
        net: Argument ``net`` forwarded into the tool observation payload for the EDA adapter.
        params: Optional dict merged into the observation payload for adapter-specific knobs.

    Returns:
        A ``dict`` observation produced by ``tool_observation`` for tool
        ``apply_noise_repair`` tagged with ``agent_id='si_noise_repair'``.

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
        # Forward ``net`` for the si_noise_repair adapter.
        'net': net,
    }
    # Merge optional adapter-specific knobs last so they can override defaults carefully.
    if params:
        # In-place update keeps a single payload object for tool_observation.
        payload.update(params)
    # Hand off to tool_observation: records not_run until OpenROAD/other adapter is bound.
    return tool_observation(
        'apply_noise_repair',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='si_noise_repair',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``verify_noise_after_repair``: Re-run noise analysis after the SI repair.
@tool(description='Re-run noise analysis on the repaired candidate.')
def verify_noise_after_repair(
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
    """Re-run noise analysis after the SI repair.

    Purpose:
        Expose ``verify_noise_after_repair`` as a callable skill for the SI/Noise Repair Agent. The
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
        ``verify_noise_after_repair`` tagged with ``agent_id='si_noise_repair'``.

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
        'verify_noise_after_repair',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='si_noise_repair',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``report_noise_timing_impact``: Report setup/hold impact of the SI repair.
@tool(description='Report setup and hold change caused by the noise repair.')
def report_noise_timing_impact(
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
    """Report setup/hold impact of the SI repair.

    Purpose:
        Expose ``report_noise_timing_impact`` as a callable skill for the SI/Noise Repair Agent. The
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
        ``report_noise_timing_impact`` tagged with ``agent_id='si_noise_repair'``.

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
        'report_noise_timing_impact',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='si_noise_repair',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``flag_noise_still_over_limit``: Finding: a pair remains over the noise limit after repair.
@tool(description='Publish a pair that is still over the noise limit.')
def flag_noise_still_over_limit(
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
    """Finding: a pair remains over the noise limit after repair.

    Purpose:
        Expose ``flag_noise_still_over_limit`` as a callable skill for the SI/Noise Repair Agent. The
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
        ``flag_noise_still_over_limit`` tagged with ``agent_id='si_noise_repair'``.

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
        'flag_noise_still_over_limit',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='si_noise_repair',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``flag_unverified_noise_repair``: Finding: a repair was applied without noise or timing re-check.
@tool(description='Publish a repair that has no noise or timing check.')
def flag_unverified_noise_repair(
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
    """Finding: a repair was applied without noise or timing re-check.

    Purpose:
        Expose ``flag_unverified_noise_repair`` as a callable skill for the SI/Noise Repair Agent. The
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
        ``flag_unverified_noise_repair`` tagged with ``agent_id='si_noise_repair'``.

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
        'flag_unverified_noise_repair',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='si_noise_repair',  # provenance tag for journal/telemetry
    )

# Register skill metadata for ``record_si_tool_version``: Record SI tool, version, and limit deck for provenance.
@tool(description='Record the SI tool, version, and limits used.')
def record_si_tool_version(
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
    """Record SI tool, version, and limit deck for provenance.

    Purpose:
        Expose ``record_si_tool_version`` as a callable skill for the SI/Noise Repair Agent. The
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
        ``record_si_tool_version`` tagged with ``agent_id='si_noise_repair'``.

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
        'record_si_tool_version',  # stable skill id matching config.yaml skills[].callable
        payload,  # argument bundle for the future EDA adapter
        agent_id='si_noise_repair',  # provenance tag for journal/telemetry
    )
