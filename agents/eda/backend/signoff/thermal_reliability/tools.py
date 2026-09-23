"""Tools for Thermal and Reliability Agent.

Each function below is the stable operation contract for thermal, aging, variation, and reliability margins. A framework
adapter performs the real work (OpenROAD, OpenSTA, licensed DRC/LVS/IR/thermal/power
tools, or simulators) when ``EDA_FRAMEWORK`` is bound.

Until a framework is bound, every call returns status ``not_run`` and does **not** invoke
OpenROAD, Yosys, OpenSTA, a licensed tool, or a simulator. That keep-safe behavior lets
the fleet exercise planning, journaling, and telemetry without mutating silicon artifacts.

EDA focus for this module: hotspots, aging margins, thermal feedback to leakage/delay, package assumptions.
Observations always stamp ``agent_id='thermal_reliability'`` so signoff_validator and leads can audit
which worker claimed a check.
"""

from __future__ import annotations  # Allow modern ``dict | None`` annotations without runtime eval.

from packages.agent_sdk import tool  # Decorator registering the callable as an Agent Fleet skill.
from domains.eda.adapters import tool_observation  # Builds the not_run/adapted observation dict for silicon memory.


@tool(description='Read the temperature distribution.')  # Registers ``read_thermal_map`` as a discoverable signoff skill.
def read_thermal_map(
    candidate_ref: str = '',  # Artifact URI of the isolated layout/netlist candidate under signoff analysis.
    report_ref: str = '',  # Artifact URI of a prior report; empty means read the latest report for the candidate.
    corner: str = '',  # PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
    mode: str = '',  # Functional or analysis mode (for example functional vs scan); empty when unused.
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """Read the temperature distribution.

    Purpose:
        Stable operation contract for ``read_thermal_map`` in the Thermal and Reliability Agent. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of thermal, aging, variation, and reliability margins. Relates to hotspots, aging margins, thermal feedback to leakage/delay, package assumptions.

    Args:
        candidate_ref: Artifact URI of the isolated layout/netlist candidate under signoff analysis.
        report_ref: Artifact URI of a prior report; empty means read the latest report for the candidate.
        corner: PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
        mode: Functional or analysis mode (for example functional vs scan); empty when unused.
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='thermal_reliability'``, and run status. Callers must not treat ``not_run``
        as a passing signoff result.

    Side effects:
        None on the layout/netlist until an adapter is bound. May append to local journal
        memory when the AgentService records the skill invocation.

    Failures:
        Does not raise for unbound frameworks; returns ``not_run``. Adapters may raise or
        return error statuses for unknown recipes, missing candidates, or tool crashes.
    """
    # Assemble the explicit signoff arguments into a flat adapter payload.
    payload = {
        'candidate_ref': candidate_ref,  # Which candidate layout/netlist this signoff operation reads.
        'report_ref': report_ref,  # Which report artifact to parse; empty selects latest for the candidate.
        'corner': corner,  # Which PVT/extraction/timing corner scopes the job.
        'mode': mode,  # Which functional/analysis mode scopes the job.
    }
    # Merge optional adapter extras (windows, deck paths, SPEF overrides) without dropping required keys.
    if params:
        # Flatten extras into the same payload dict consumed by tool_observation / the EDA adapter.
        payload.update(params)
    # Emit a structured observation stamped with agent_id='thermal_reliability' for audit and telemetry.
    return tool_observation(
        'read_thermal_map',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='thermal_reliability',  # Ties the observation to this Thermal and Reliability Agent worker.
    )


@tool(description='Summarize hotspots and the power sources under them.')  # Registers ``evaluate_thermal_map`` as a discoverable signoff skill.
def evaluate_thermal_map(
    candidate_ref: str = '',  # Artifact URI of the isolated layout/netlist candidate under signoff analysis.
    report_ref: str = '',  # Artifact URI of a prior report; empty means read the latest report for the candidate.
    corner: str = '',  # PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
    mode: str = '',  # Functional or analysis mode (for example functional vs scan); empty when unused.
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """Summarize hotspots and the power sources under them.

    Purpose:
        Stable operation contract for ``evaluate_thermal_map`` in the Thermal and Reliability Agent. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of thermal, aging, variation, and reliability margins. Relates to hotspots, aging margins, thermal feedback to leakage/delay, package assumptions.

    Args:
        candidate_ref: Artifact URI of the isolated layout/netlist candidate under signoff analysis.
        report_ref: Artifact URI of a prior report; empty means read the latest report for the candidate.
        corner: PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
        mode: Functional or analysis mode (for example functional vs scan); empty when unused.
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='thermal_reliability'``, and run status. Callers must not treat ``not_run``
        as a passing signoff result.

    Side effects:
        None on the layout/netlist until an adapter is bound. May append to local journal
        memory when the AgentService records the skill invocation.

    Failures:
        Does not raise for unbound frameworks; returns ``not_run``. Adapters may raise or
        return error statuses for unknown recipes, missing candidates, or tool crashes.
    """
    # Assemble the explicit signoff arguments into a flat adapter payload.
    payload = {
        'candidate_ref': candidate_ref,  # Which candidate layout/netlist this signoff operation reads.
        'report_ref': report_ref,  # Which report artifact to parse; empty selects latest for the candidate.
        'corner': corner,  # Which PVT/extraction/timing corner scopes the job.
        'mode': mode,  # Which functional/analysis mode scopes the job.
    }
    # Merge optional adapter extras (windows, deck paths, SPEF overrides) without dropping required keys.
    if params:
        # Flatten extras into the same payload dict consumed by tool_observation / the EDA adapter.
        payload.update(params)
    # Emit a structured observation stamped with agent_id='thermal_reliability' for audit and telemetry.
    return tool_observation(
        'evaluate_thermal_map',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='thermal_reliability',  # Ties the observation to this Thermal and Reliability Agent worker.
    )


@tool(description='Read aging and variation margins.')  # Registers ``read_aging_report`` as a discoverable signoff skill.
def read_aging_report(
    candidate_ref: str = '',  # Artifact URI of the isolated layout/netlist candidate under signoff analysis.
    report_ref: str = '',  # Artifact URI of a prior report; empty means read the latest report for the candidate.
    corner: str = '',  # PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
    mode: str = '',  # Functional or analysis mode (for example functional vs scan); empty when unused.
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """Read aging and variation margins.

    Purpose:
        Stable operation contract for ``read_aging_report`` in the Thermal and Reliability Agent. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of thermal, aging, variation, and reliability margins. Relates to hotspots, aging margins, thermal feedback to leakage/delay, package assumptions.

    Args:
        candidate_ref: Artifact URI of the isolated layout/netlist candidate under signoff analysis.
        report_ref: Artifact URI of a prior report; empty means read the latest report for the candidate.
        corner: PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
        mode: Functional or analysis mode (for example functional vs scan); empty when unused.
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='thermal_reliability'``, and run status. Callers must not treat ``not_run``
        as a passing signoff result.

    Side effects:
        None on the layout/netlist until an adapter is bound. May append to local journal
        memory when the AgentService records the skill invocation.

    Failures:
        Does not raise for unbound frameworks; returns ``not_run``. Adapters may raise or
        return error statuses for unknown recipes, missing candidates, or tool crashes.
    """
    # Assemble the explicit signoff arguments into a flat adapter payload.
    payload = {
        'candidate_ref': candidate_ref,  # Which candidate layout/netlist this signoff operation reads.
        'report_ref': report_ref,  # Which report artifact to parse; empty selects latest for the candidate.
        'corner': corner,  # Which PVT/extraction/timing corner scopes the job.
        'mode': mode,  # Which functional/analysis mode scopes the job.
    }
    # Merge optional adapter extras (windows, deck paths, SPEF overrides) without dropping required keys.
    if params:
        # Flatten extras into the same payload dict consumed by tool_observation / the EDA adapter.
        payload.update(params)
    # Emit a structured observation stamped with agent_id='thermal_reliability' for audit and telemetry.
    return tool_observation(
        'read_aging_report',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='thermal_reliability',  # Ties the observation to this Thermal and Reliability Agent worker.
    )


@tool(description='Report aging and variation margins that miss the requirement.')  # Registers ``evaluate_aging_margin`` as a discoverable signoff skill.
def evaluate_aging_margin(
    summary: str = '',  # One-sentence finding text published into engineering memory for downstream owners.
    evidence_refs: str = '',  # Comma-separated artifact URIs that substantiate the finding or decision.
    severity: str = '',  # Finding severity: low, medium, high, or critical for signoff triage.
    recommended_recipient: str = '',  # Agent id expected to act on the finding (for example routing_lead or eco_lead).
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """Report aging and variation margins that miss the requirement.

    Purpose:
        Stable operation contract for ``evaluate_aging_margin`` in the Thermal and Reliability Agent. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of thermal, aging, variation, and reliability margins. Relates to hotspots, aging margins, thermal feedback to leakage/delay, package assumptions.

    Args:
        summary: One-sentence finding text published into engineering memory for downstream owners.
        evidence_refs: Comma-separated artifact URIs that substantiate the finding or decision.
        severity: Finding severity: low, medium, high, or critical for signoff triage.
        recommended_recipient: Agent id expected to act on the finding (for example routing_lead or eco_lead).
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='thermal_reliability'``, and run status. Callers must not treat ``not_run``
        as a passing signoff result.

    Side effects:
        None on the layout/netlist until an adapter is bound. May append to local journal
        memory when the AgentService records the skill invocation.

    Failures:
        Does not raise for unbound frameworks; returns ``not_run``. Adapters may raise or
        return error statuses for unknown recipes, missing candidates, or tool crashes.
    """
    # Assemble the explicit signoff arguments into a flat adapter payload.
    payload = {
        'summary': summary,  # Finding text that downstream owners and signoff_validator will read.
        'evidence_refs': evidence_refs,  # Artifact URIs backing the finding for auditability.
        'severity': severity,  # Triage severity for the published finding.
        'recommended_recipient': recommended_recipient,  # Intended owner agent for the next repair or decision.
    }
    # Merge optional adapter extras (windows, deck paths, SPEF overrides) without dropping required keys.
    if params:
        # Flatten extras into the same payload dict consumed by tool_observation / the EDA adapter.
        payload.update(params)
    # Emit a structured observation stamped with agent_id='thermal_reliability' for audit and telemetry.
    return tool_observation(
        'evaluate_aging_margin',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='thermal_reliability',  # Ties the observation to this Thermal and Reliability Agent worker.
    )


@tool(description='Read the temperature, EM, and aging limits.')  # Registers ``read_reliability_limits`` as a discoverable signoff skill.
def read_reliability_limits(
    candidate_ref: str = '',  # Artifact URI of the isolated layout/netlist candidate under signoff analysis.
    report_ref: str = '',  # Artifact URI of a prior report; empty means read the latest report for the candidate.
    corner: str = '',  # PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
    mode: str = '',  # Functional or analysis mode (for example functional vs scan); empty when unused.
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """Read the temperature, EM, and aging limits.

    Purpose:
        Stable operation contract for ``read_reliability_limits`` in the Thermal and Reliability Agent. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of thermal, aging, variation, and reliability margins. Relates to hotspots, aging margins, thermal feedback to leakage/delay, package assumptions.

    Args:
        candidate_ref: Artifact URI of the isolated layout/netlist candidate under signoff analysis.
        report_ref: Artifact URI of a prior report; empty means read the latest report for the candidate.
        corner: PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
        mode: Functional or analysis mode (for example functional vs scan); empty when unused.
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='thermal_reliability'``, and run status. Callers must not treat ``not_run``
        as a passing signoff result.

    Side effects:
        None on the layout/netlist until an adapter is bound. May append to local journal
        memory when the AgentService records the skill invocation.

    Failures:
        Does not raise for unbound frameworks; returns ``not_run``. Adapters may raise or
        return error statuses for unknown recipes, missing candidates, or tool crashes.
    """
    # Assemble the explicit signoff arguments into a flat adapter payload.
    payload = {
        'candidate_ref': candidate_ref,  # Which candidate layout/netlist this signoff operation reads.
        'report_ref': report_ref,  # Which report artifact to parse; empty selects latest for the candidate.
        'corner': corner,  # Which PVT/extraction/timing corner scopes the job.
        'mode': mode,  # Which functional/analysis mode scopes the job.
    }
    # Merge optional adapter extras (windows, deck paths, SPEF overrides) without dropping required keys.
    if params:
        # Flatten extras into the same payload dict consumed by tool_observation / the EDA adapter.
        payload.update(params)
    # Emit a structured observation stamped with agent_id='thermal_reliability' for audit and telemetry.
    return tool_observation(
        'read_reliability_limits',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='thermal_reliability',  # Ties the observation to this Thermal and Reliability Agent worker.
    )


@tool(description='Write a proposed timing or placement constraint. This does not edit the canonical constraints.')  # Registers ``write_thermal_constraint_proposal`` as a discoverable signoff skill.
def write_thermal_constraint_proposal(
    candidate_ref: str = '',  # Artifact URI of the isolated layout/netlist candidate under signoff analysis.
    baseline_ref: str = '',  # Artifact URI of the canonical baseline used for comparison or ECO descent.
    hypothesis: str = '',  # Design-change hypothesis describing what the write/apply step will attempt.
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """Write a proposed timing or placement constraint. This does not edit the canonical constraints.

    Purpose:
        Stable operation contract for ``write_thermal_constraint_proposal`` in the Thermal and Reliability Agent. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of thermal, aging, variation, and reliability margins. Relates to hotspots, aging margins, thermal feedback to leakage/delay, package assumptions.

    Args:
        candidate_ref: Artifact URI of the isolated layout/netlist candidate under signoff analysis.
        baseline_ref: Artifact URI of the canonical baseline used for comparison or ECO descent.
        hypothesis: Design-change hypothesis describing what the write/apply step will attempt.
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='thermal_reliability'``, and run status. Callers must not treat ``not_run``
        as a passing signoff result.

    Side effects:
        None on the layout/netlist until an adapter is bound. May append to local journal
        memory when the AgentService records the skill invocation.

    Failures:
        Does not raise for unbound frameworks; returns ``not_run``. Adapters may raise or
        return error statuses for unknown recipes, missing candidates, or tool crashes.
    """
    # Assemble the explicit signoff arguments into a flat adapter payload.
    payload = {
        'candidate_ref': candidate_ref,  # Which candidate layout/netlist this signoff operation reads.
        'baseline_ref': baseline_ref,  # Which canonical baseline to compare against or descend from for ECO.
        'hypothesis': hypothesis,  # Intended physical or constraint change under test.
    }
    # Merge optional adapter extras (windows, deck paths, SPEF overrides) without dropping required keys.
    if params:
        # Flatten extras into the same payload dict consumed by tool_observation / the EDA adapter.
        payload.update(params)
    # Emit a structured observation stamped with agent_id='thermal_reliability' for audit and telemetry.
    return tool_observation(
        'write_thermal_constraint_proposal',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='thermal_reliability',  # Ties the observation to this Thermal and Reliability Agent worker.
    )


@tool(description='Apply one physical change on an isolated candidate.')  # Registers ``apply_thermal_physical_change`` as a discoverable signoff skill.
def apply_thermal_physical_change(
    candidate_ref: str = '',  # Artifact URI of the isolated layout/netlist candidate under signoff analysis.
    baseline_ref: str = '',  # Artifact URI of the canonical baseline used for comparison or ECO descent.
    hypothesis: str = '',  # Design-change hypothesis describing what the write/apply step will attempt.
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """Apply one physical change on an isolated candidate.

    Purpose:
        Stable operation contract for ``apply_thermal_physical_change`` in the Thermal and Reliability Agent. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of thermal, aging, variation, and reliability margins. Relates to hotspots, aging margins, thermal feedback to leakage/delay, package assumptions.

    Args:
        candidate_ref: Artifact URI of the isolated layout/netlist candidate under signoff analysis.
        baseline_ref: Artifact URI of the canonical baseline used for comparison or ECO descent.
        hypothesis: Design-change hypothesis describing what the write/apply step will attempt.
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='thermal_reliability'``, and run status. Callers must not treat ``not_run``
        as a passing signoff result.

    Side effects:
        None on the layout/netlist until an adapter is bound. May append to local journal
        memory when the AgentService records the skill invocation.

    Failures:
        Does not raise for unbound frameworks; returns ``not_run``. Adapters may raise or
        return error statuses for unknown recipes, missing candidates, or tool crashes.
    """
    # Assemble the explicit signoff arguments into a flat adapter payload.
    payload = {
        'candidate_ref': candidate_ref,  # Which candidate layout/netlist this signoff operation reads.
        'baseline_ref': baseline_ref,  # Which canonical baseline to compare against or descend from for ECO.
        'hypothesis': hypothesis,  # Intended physical or constraint change under test.
    }
    # Merge optional adapter extras (windows, deck paths, SPEF overrides) without dropping required keys.
    if params:
        # Flatten extras into the same payload dict consumed by tool_observation / the EDA adapter.
        payload.update(params)
    # Emit a structured observation stamped with agent_id='thermal_reliability' for audit and telemetry.
    return tool_observation(
        'apply_thermal_physical_change',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='thermal_reliability',  # Ties the observation to this Thermal and Reliability Agent worker.
    )


@tool(description='Check how the temperature map changes leakage and delay.')  # Registers ``check_thermal_feedback`` as a discoverable signoff skill.
def check_thermal_feedback(
    candidate_ref: str = '',  # Artifact URI of the isolated layout/netlist candidate under signoff analysis.
    baseline_ref: str = '',  # Artifact URI of the canonical baseline used for comparison or ECO descent.
    recipe: str = '',  # Versioned EDA tool recipe (deck/flow/version); adapters reject unknown recipes.
    corner: str = '',  # PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
    mode: str = '',  # Functional or analysis mode (for example functional vs scan); empty when unused.
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """Check how the temperature map changes leakage and delay.

    Purpose:
        Stable operation contract for ``check_thermal_feedback`` in the Thermal and Reliability Agent. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of thermal, aging, variation, and reliability margins. Relates to hotspots, aging margins, thermal feedback to leakage/delay, package assumptions.

    Args:
        candidate_ref: Artifact URI of the isolated layout/netlist candidate under signoff analysis.
        baseline_ref: Artifact URI of the canonical baseline used for comparison or ECO descent.
        recipe: Versioned EDA tool recipe (deck/flow/version); adapters reject unknown recipes.
        corner: PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
        mode: Functional or analysis mode (for example functional vs scan); empty when unused.
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='thermal_reliability'``, and run status. Callers must not treat ``not_run``
        as a passing signoff result.

    Side effects:
        None on the layout/netlist until an adapter is bound. May append to local journal
        memory when the AgentService records the skill invocation.

    Failures:
        Does not raise for unbound frameworks; returns ``not_run``. Adapters may raise or
        return error statuses for unknown recipes, missing candidates, or tool crashes.
    """
    # Assemble the explicit signoff arguments into a flat adapter payload.
    payload = {
        'candidate_ref': candidate_ref,  # Which candidate layout/netlist this signoff operation reads.
        'baseline_ref': baseline_ref,  # Which canonical baseline to compare against or descend from for ECO.
        'recipe': recipe,  # Which versioned EDA recipe/deck the adapter must load.
        'corner': corner,  # Which PVT/extraction/timing corner scopes the job.
        'mode': mode,  # Which functional/analysis mode scopes the job.
    }
    # Merge optional adapter extras (windows, deck paths, SPEF overrides) without dropping required keys.
    if params:
        # Flatten extras into the same payload dict consumed by tool_observation / the EDA adapter.
        payload.update(params)
    # Emit a structured observation stamped with agent_id='thermal_reliability' for audit and telemetry.
    return tool_observation(
        'check_thermal_feedback',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='thermal_reliability',  # Ties the observation to this Thermal and Reliability Agent worker.
    )


@tool(description='Compare hotspot temperature with the limit.')  # Registers ``compare_thermal_to_limit`` as a discoverable signoff skill.
def compare_thermal_to_limit(
    candidate_ref: str = '',  # Artifact URI of the isolated layout/netlist candidate under signoff analysis.
    report_ref: str = '',  # Artifact URI of a prior report; empty means read the latest report for the candidate.
    corner: str = '',  # PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
    mode: str = '',  # Functional or analysis mode (for example functional vs scan); empty when unused.
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """Compare hotspot temperature with the limit.

    Purpose:
        Stable operation contract for ``compare_thermal_to_limit`` in the Thermal and Reliability Agent. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of thermal, aging, variation, and reliability margins. Relates to hotspots, aging margins, thermal feedback to leakage/delay, package assumptions.

    Args:
        candidate_ref: Artifact URI of the isolated layout/netlist candidate under signoff analysis.
        report_ref: Artifact URI of a prior report; empty means read the latest report for the candidate.
        corner: PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
        mode: Functional or analysis mode (for example functional vs scan); empty when unused.
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='thermal_reliability'``, and run status. Callers must not treat ``not_run``
        as a passing signoff result.

    Side effects:
        None on the layout/netlist until an adapter is bound. May append to local journal
        memory when the AgentService records the skill invocation.

    Failures:
        Does not raise for unbound frameworks; returns ``not_run``. Adapters may raise or
        return error statuses for unknown recipes, missing candidates, or tool crashes.
    """
    # Assemble the explicit signoff arguments into a flat adapter payload.
    payload = {
        'candidate_ref': candidate_ref,  # Which candidate layout/netlist this signoff operation reads.
        'report_ref': report_ref,  # Which report artifact to parse; empty selects latest for the candidate.
        'corner': corner,  # Which PVT/extraction/timing corner scopes the job.
        'mode': mode,  # Which functional/analysis mode scopes the job.
    }
    # Merge optional adapter extras (windows, deck paths, SPEF overrides) without dropping required keys.
    if params:
        # Flatten extras into the same payload dict consumed by tool_observation / the EDA adapter.
        payload.update(params)
    # Emit a structured observation stamped with agent_id='thermal_reliability' for audit and telemetry.
    return tool_observation(
        'compare_thermal_to_limit',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='thermal_reliability',  # Ties the observation to this Thermal and Reliability Agent worker.
    )


@tool(description='Publish a hotspot over the temperature limit.')  # Registers ``flag_hotspot_over_limit`` as a discoverable signoff skill.
def flag_hotspot_over_limit(
    summary: str = '',  # One-sentence finding text published into engineering memory for downstream owners.
    evidence_refs: str = '',  # Comma-separated artifact URIs that substantiate the finding or decision.
    severity: str = '',  # Finding severity: low, medium, high, or critical for signoff triage.
    recommended_recipient: str = '',  # Agent id expected to act on the finding (for example routing_lead or eco_lead).
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """Publish a hotspot over the temperature limit.

    Purpose:
        Stable operation contract for ``flag_hotspot_over_limit`` in the Thermal and Reliability Agent. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of thermal, aging, variation, and reliability margins. Relates to hotspots, aging margins, thermal feedback to leakage/delay, package assumptions.

    Args:
        summary: One-sentence finding text published into engineering memory for downstream owners.
        evidence_refs: Comma-separated artifact URIs that substantiate the finding or decision.
        severity: Finding severity: low, medium, high, or critical for signoff triage.
        recommended_recipient: Agent id expected to act on the finding (for example routing_lead or eco_lead).
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='thermal_reliability'``, and run status. Callers must not treat ``not_run``
        as a passing signoff result.

    Side effects:
        None on the layout/netlist until an adapter is bound. May append to local journal
        memory when the AgentService records the skill invocation.

    Failures:
        Does not raise for unbound frameworks; returns ``not_run``. Adapters may raise or
        return error statuses for unknown recipes, missing candidates, or tool crashes.
    """
    # Assemble the explicit signoff arguments into a flat adapter payload.
    payload = {
        'summary': summary,  # Finding text that downstream owners and signoff_validator will read.
        'evidence_refs': evidence_refs,  # Artifact URIs backing the finding for auditability.
        'severity': severity,  # Triage severity for the published finding.
        'recommended_recipient': recommended_recipient,  # Intended owner agent for the next repair or decision.
    }
    # Merge optional adapter extras (windows, deck paths, SPEF overrides) without dropping required keys.
    if params:
        # Flatten extras into the same payload dict consumed by tool_observation / the EDA adapter.
        payload.update(params)
    # Emit a structured observation stamped with agent_id='thermal_reliability' for audit and telemetry.
    return tool_observation(
        'flag_hotspot_over_limit',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='thermal_reliability',  # Ties the observation to this Thermal and Reliability Agent worker.
    )


@tool(description='Publish an analysis that passed only because a limit was raised.')  # Registers ``flag_raised_thermal_limit`` as a discoverable signoff skill.
def flag_raised_thermal_limit(
    summary: str = '',  # One-sentence finding text published into engineering memory for downstream owners.
    evidence_refs: str = '',  # Comma-separated artifact URIs that substantiate the finding or decision.
    severity: str = '',  # Finding severity: low, medium, high, or critical for signoff triage.
    recommended_recipient: str = '',  # Agent id expected to act on the finding (for example routing_lead or eco_lead).
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """Publish an analysis that passed only because a limit was raised.

    Purpose:
        Stable operation contract for ``flag_raised_thermal_limit`` in the Thermal and Reliability Agent. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of thermal, aging, variation, and reliability margins. Relates to hotspots, aging margins, thermal feedback to leakage/delay, package assumptions.

    Args:
        summary: One-sentence finding text published into engineering memory for downstream owners.
        evidence_refs: Comma-separated artifact URIs that substantiate the finding or decision.
        severity: Finding severity: low, medium, high, or critical for signoff triage.
        recommended_recipient: Agent id expected to act on the finding (for example routing_lead or eco_lead).
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='thermal_reliability'``, and run status. Callers must not treat ``not_run``
        as a passing signoff result.

    Side effects:
        None on the layout/netlist until an adapter is bound. May append to local journal
        memory when the AgentService records the skill invocation.

    Failures:
        Does not raise for unbound frameworks; returns ``not_run``. Adapters may raise or
        return error statuses for unknown recipes, missing candidates, or tool crashes.
    """
    # Assemble the explicit signoff arguments into a flat adapter payload.
    payload = {
        'summary': summary,  # Finding text that downstream owners and signoff_validator will read.
        'evidence_refs': evidence_refs,  # Artifact URIs backing the finding for auditability.
        'severity': severity,  # Triage severity for the published finding.
        'recommended_recipient': recommended_recipient,  # Intended owner agent for the next repair or decision.
    }
    # Merge optional adapter extras (windows, deck paths, SPEF overrides) without dropping required keys.
    if params:
        # Flatten extras into the same payload dict consumed by tool_observation / the EDA adapter.
        payload.update(params)
    # Emit a structured observation stamped with agent_id='thermal_reliability' for audit and telemetry.
    return tool_observation(
        'flag_raised_thermal_limit',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='thermal_reliability',  # Ties the observation to this Thermal and Reliability Agent worker.
    )


@tool(description='Record the thermal model, power map, and package assumption.')  # Registers ``record_thermal_provenance`` as a discoverable signoff skill.
def record_thermal_provenance(
    summary: str = '',  # One-sentence finding text published into engineering memory for downstream owners.
    evidence_refs: str = '',  # Comma-separated artifact URIs that substantiate the finding or decision.
    severity: str = '',  # Finding severity: low, medium, high, or critical for signoff triage.
    recommended_recipient: str = '',  # Agent id expected to act on the finding (for example routing_lead or eco_lead).
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """Record the thermal model, power map, and package assumption.

    Purpose:
        Stable operation contract for ``record_thermal_provenance`` in the Thermal and Reliability Agent. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of thermal, aging, variation, and reliability margins. Relates to hotspots, aging margins, thermal feedback to leakage/delay, package assumptions.

    Args:
        summary: One-sentence finding text published into engineering memory for downstream owners.
        evidence_refs: Comma-separated artifact URIs that substantiate the finding or decision.
        severity: Finding severity: low, medium, high, or critical for signoff triage.
        recommended_recipient: Agent id expected to act on the finding (for example routing_lead or eco_lead).
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='thermal_reliability'``, and run status. Callers must not treat ``not_run``
        as a passing signoff result.

    Side effects:
        None on the layout/netlist until an adapter is bound. May append to local journal
        memory when the AgentService records the skill invocation.

    Failures:
        Does not raise for unbound frameworks; returns ``not_run``. Adapters may raise or
        return error statuses for unknown recipes, missing candidates, or tool crashes.
    """
    # Assemble the explicit signoff arguments into a flat adapter payload.
    payload = {
        'summary': summary,  # Finding text that downstream owners and signoff_validator will read.
        'evidence_refs': evidence_refs,  # Artifact URIs backing the finding for auditability.
        'severity': severity,  # Triage severity for the published finding.
        'recommended_recipient': recommended_recipient,  # Intended owner agent for the next repair or decision.
    }
    # Merge optional adapter extras (windows, deck paths, SPEF overrides) without dropping required keys.
    if params:
        # Flatten extras into the same payload dict consumed by tool_observation / the EDA adapter.
        payload.update(params)
    # Emit a structured observation stamped with agent_id='thermal_reliability' for audit and telemetry.
    return tool_observation(
        'record_thermal_provenance',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='thermal_reliability',  # Ties the observation to this Thermal and Reliability Agent worker.
    )
