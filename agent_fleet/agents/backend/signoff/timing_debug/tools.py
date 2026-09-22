"""Tools for Timing-Debug Agent.

Each function below is the stable operation contract for STA query and path classification (setup/hold/recovery/removal/clock). A framework
adapter performs the real work (OpenROAD, OpenSTA, licensed DRC/LVS/IR/thermal/power
tools, or simulators) when ``EDA_FRAMEWORK`` is bound.

Until a framework is bound, every call returns status ``not_run`` and does **not** invoke
OpenROAD, Yosys, OpenSTA, a licensed tool, or a simulator. That keep-safe behavior lets
the fleet exercise planning, journaling, and telemetry without mutating silicon artifacts.

EDA focus for this module: OpenSTA report_checks, WNS/TNS, path cause tracing, unconstrained endpoints.
Observations always stamp ``agent_id='timing_debug'`` so signoff_validator and leads can audit
which worker claimed a check.
"""

from __future__ import annotations  # Allow modern ``dict | None`` annotations without runtime eval.

from packages.agent_sdk import tool  # Decorator registering the callable as an Agent Fleet skill.
from domains.eda.eda import tool_observation  # Builds the not_run/adapted observation dict for silicon memory.


@tool(description='Run static timing for one mode and corner. Adapter target: OpenSTA.')  # Registers ``run_sta`` as a discoverable signoff skill.
def run_sta(
    candidate_ref: str = '',  # Artifact URI of the isolated layout/netlist candidate under signoff analysis.
    baseline_ref: str = '',  # Artifact URI of the canonical baseline used for comparison or ECO descent.
    recipe: str = '',  # Versioned EDA tool recipe (deck/flow/version); adapters reject unknown recipes.
    corner: str = '',  # PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
    mode: str = '',  # Functional or analysis mode (for example functional vs scan); empty when unused.
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """Run static timing for one mode and corner. Adapter target: OpenSTA.

    Purpose:
        Stable operation contract for ``run_sta`` in the Timing-Debug Agent. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of STA query and path classification (setup/hold/recovery/removal/clock). Relates to OpenSTA report_checks, WNS/TNS, path cause tracing, unconstrained endpoints.

    Args:
        candidate_ref: Artifact URI of the isolated layout/netlist candidate under signoff analysis.
        baseline_ref: Artifact URI of the canonical baseline used for comparison or ECO descent.
        recipe: Versioned EDA tool recipe (deck/flow/version); adapters reject unknown recipes.
        corner: PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
        mode: Functional or analysis mode (for example functional vs scan); empty when unused.
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='timing_debug'``, and run status. Callers must not treat ``not_run``
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
    # Emit a structured observation stamped with agent_id='timing_debug' for audit and telemetry.
    return tool_observation(
        'run_sta',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='timing_debug',  # Ties the observation to this Timing-Debug Agent worker.
    )


@tool(description='Report timing checks. Adapter target: OpenSTA report_checks.')  # Registers ``report_checks`` as a discoverable signoff skill.
def report_checks(
    candidate_ref: str = '',  # Artifact URI of the isolated layout/netlist candidate under signoff analysis.
    baseline_ref: str = '',  # Artifact URI of the canonical baseline used for comparison or ECO descent.
    recipe: str = '',  # Versioned EDA tool recipe (deck/flow/version); adapters reject unknown recipes.
    corner: str = '',  # PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
    mode: str = '',  # Functional or analysis mode (for example functional vs scan); empty when unused.
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """Report timing checks. Adapter target: OpenSTA report_checks.

    Purpose:
        Stable operation contract for ``report_checks`` in the Timing-Debug Agent. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of STA query and path classification (setup/hold/recovery/removal/clock). Relates to OpenSTA report_checks, WNS/TNS, path cause tracing, unconstrained endpoints.

    Args:
        candidate_ref: Artifact URI of the isolated layout/netlist candidate under signoff analysis.
        baseline_ref: Artifact URI of the canonical baseline used for comparison or ECO descent.
        recipe: Versioned EDA tool recipe (deck/flow/version); adapters reject unknown recipes.
        corner: PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
        mode: Functional or analysis mode (for example functional vs scan); empty when unused.
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='timing_debug'``, and run status. Callers must not treat ``not_run``
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
    # Emit a structured observation stamped with agent_id='timing_debug' for audit and telemetry.
    return tool_observation(
        'report_checks',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='timing_debug',  # Ties the observation to this Timing-Debug Agent worker.
    )


@tool(description='Report worst negative slack.')  # Registers ``report_wns`` as a discoverable signoff skill.
def report_wns(
    candidate_ref: str = '',  # Artifact URI of the isolated layout/netlist candidate under signoff analysis.
    report_ref: str = '',  # Artifact URI of a prior report; empty means read the latest report for the candidate.
    corner: str = '',  # PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
    mode: str = '',  # Functional or analysis mode (for example functional vs scan); empty when unused.
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """Report worst negative slack.

    Purpose:
        Stable operation contract for ``report_wns`` in the Timing-Debug Agent. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of STA query and path classification (setup/hold/recovery/removal/clock). Relates to OpenSTA report_checks, WNS/TNS, path cause tracing, unconstrained endpoints.

    Args:
        candidate_ref: Artifact URI of the isolated layout/netlist candidate under signoff analysis.
        report_ref: Artifact URI of a prior report; empty means read the latest report for the candidate.
        corner: PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
        mode: Functional or analysis mode (for example functional vs scan); empty when unused.
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='timing_debug'``, and run status. Callers must not treat ``not_run``
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
    # Emit a structured observation stamped with agent_id='timing_debug' for audit and telemetry.
    return tool_observation(
        'report_wns',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='timing_debug',  # Ties the observation to this Timing-Debug Agent worker.
    )


@tool(description='Report total negative slack.')  # Registers ``report_tns`` as a discoverable signoff skill.
def report_tns(
    candidate_ref: str = '',  # Artifact URI of the isolated layout/netlist candidate under signoff analysis.
    report_ref: str = '',  # Artifact URI of a prior report; empty means read the latest report for the candidate.
    corner: str = '',  # PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
    mode: str = '',  # Functional or analysis mode (for example functional vs scan); empty when unused.
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """Report total negative slack.

    Purpose:
        Stable operation contract for ``report_tns`` in the Timing-Debug Agent. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of STA query and path classification (setup/hold/recovery/removal/clock). Relates to OpenSTA report_checks, WNS/TNS, path cause tracing, unconstrained endpoints.

    Args:
        candidate_ref: Artifact URI of the isolated layout/netlist candidate under signoff analysis.
        report_ref: Artifact URI of a prior report; empty means read the latest report for the candidate.
        corner: PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
        mode: Functional or analysis mode (for example functional vs scan); empty when unused.
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='timing_debug'``, and run status. Callers must not treat ``not_run``
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
    # Emit a structured observation stamped with agent_id='timing_debug' for audit and telemetry.
    return tool_observation(
        'report_tns',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='timing_debug',  # Ties the observation to this Timing-Debug Agent worker.
    )


@tool(description='Group setup, hold, recovery, and removal violations.')  # Registers ``classify_timing_paths`` as a discoverable signoff skill.
def classify_timing_paths(
    candidate_ref: str = '',  # Artifact URI of the isolated layout/netlist candidate under signoff analysis.
    report_ref: str = '',  # Artifact URI of a prior report; empty means read the latest report for the candidate.
    corner: str = '',  # PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
    mode: str = '',  # Functional or analysis mode (for example functional vs scan); empty when unused.
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """Group setup, hold, recovery, and removal violations.

    Purpose:
        Stable operation contract for ``classify_timing_paths`` in the Timing-Debug Agent. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of STA query and path classification (setup/hold/recovery/removal/clock). Relates to OpenSTA report_checks, WNS/TNS, path cause tracing, unconstrained endpoints.

    Args:
        candidate_ref: Artifact URI of the isolated layout/netlist candidate under signoff analysis.
        report_ref: Artifact URI of a prior report; empty means read the latest report for the candidate.
        corner: PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
        mode: Functional or analysis mode (for example functional vs scan); empty when unused.
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='timing_debug'``, and run status. Callers must not treat ``not_run``
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
    # Emit a structured observation stamped with agent_id='timing_debug' for audit and telemetry.
    return tool_observation(
        'classify_timing_paths',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='timing_debug',  # Ties the observation to this Timing-Debug Agent worker.
    )


@tool(description='Group clock, pulse-width, and generated-clock failures.')  # Registers ``classify_clock_path_failures`` as a discoverable signoff skill.
def classify_clock_path_failures(
    candidate_ref: str = '',  # Artifact URI of the isolated layout/netlist candidate under signoff analysis.
    report_ref: str = '',  # Artifact URI of a prior report; empty means read the latest report for the candidate.
    corner: str = '',  # PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
    mode: str = '',  # Functional or analysis mode (for example functional vs scan); empty when unused.
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """Group clock, pulse-width, and generated-clock failures.

    Purpose:
        Stable operation contract for ``classify_clock_path_failures`` in the Timing-Debug Agent. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of STA query and path classification (setup/hold/recovery/removal/clock). Relates to OpenSTA report_checks, WNS/TNS, path cause tracing, unconstrained endpoints.

    Args:
        candidate_ref: Artifact URI of the isolated layout/netlist candidate under signoff analysis.
        report_ref: Artifact URI of a prior report; empty means read the latest report for the candidate.
        corner: PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
        mode: Functional or analysis mode (for example functional vs scan); empty when unused.
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='timing_debug'``, and run status. Callers must not treat ``not_run``
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
    # Emit a structured observation stamped with agent_id='timing_debug' for audit and telemetry.
    return tool_observation(
        'classify_clock_path_failures',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='timing_debug',  # Ties the observation to this Timing-Debug Agent worker.
    )


@tool(description='Trace a path group to logic depth, placement, clock, or constraint.')  # Registers ``trace_path_cause`` as a discoverable signoff skill.
def trace_path_cause(
    summary: str = '',  # One-sentence finding text published into engineering memory for downstream owners.
    evidence_refs: str = '',  # Comma-separated artifact URIs that substantiate the finding or decision.
    severity: str = '',  # Finding severity: low, medium, high, or critical for signoff triage.
    recommended_recipient: str = '',  # Agent id expected to act on the finding (for example routing_lead or eco_lead).
    path_group: str = '',  # Named timing path group under debug or repair (reg2reg, in2reg, etc.).
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """Trace a path group to logic depth, placement, clock, or constraint.

    Purpose:
        Stable operation contract for ``trace_path_cause`` in the Timing-Debug Agent. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of STA query and path classification (setup/hold/recovery/removal/clock). Relates to OpenSTA report_checks, WNS/TNS, path cause tracing, unconstrained endpoints.

    Args:
        summary: One-sentence finding text published into engineering memory for downstream owners.
        evidence_refs: Comma-separated artifact URIs that substantiate the finding or decision.
        severity: Finding severity: low, medium, high, or critical for signoff triage.
        recommended_recipient: Agent id expected to act on the finding (for example routing_lead or eco_lead).
        path_group: Named timing path group under debug or repair (reg2reg, in2reg, etc.).
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='timing_debug'``, and run status. Callers must not treat ``not_run``
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
        'path_group': path_group,  # Timing path group being debugged or repaired.
    }
    # Merge optional adapter extras (windows, deck paths, SPEF overrides) without dropping required keys.
    if params:
        # Flatten extras into the same payload dict consumed by tool_observation / the EDA adapter.
        payload.update(params)
    # Emit a structured observation stamped with agent_id='timing_debug' for audit and telemetry.
    return tool_observation(
        'trace_path_cause',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='timing_debug',  # Ties the observation to this Timing-Debug Agent worker.
    )


@tool(description='Report startpoint, endpoint, cells, and capacitance for one path.')  # Registers ``report_path_details`` as a discoverable signoff skill.
def report_path_details(
    candidate_ref: str = '',  # Artifact URI of the isolated layout/netlist candidate under signoff analysis.
    report_ref: str = '',  # Artifact URI of a prior report; empty means read the latest report for the candidate.
    corner: str = '',  # PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
    mode: str = '',  # Functional or analysis mode (for example functional vs scan); empty when unused.
    path_index: str = '',  # Index or id of a single timing path within a report for deep inspection.
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """Report startpoint, endpoint, cells, and capacitance for one path.

    Purpose:
        Stable operation contract for ``report_path_details`` in the Timing-Debug Agent. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of STA query and path classification (setup/hold/recovery/removal/clock). Relates to OpenSTA report_checks, WNS/TNS, path cause tracing, unconstrained endpoints.

    Args:
        candidate_ref: Artifact URI of the isolated layout/netlist candidate under signoff analysis.
        report_ref: Artifact URI of a prior report; empty means read the latest report for the candidate.
        corner: PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
        mode: Functional or analysis mode (for example functional vs scan); empty when unused.
        path_index: Index or id of a single timing path within a report for deep inspection.
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='timing_debug'``, and run status. Callers must not treat ``not_run``
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
        'path_index': path_index,  # Selector for a single path inside the STA report.
    }
    # Merge optional adapter extras (windows, deck paths, SPEF overrides) without dropping required keys.
    if params:
        # Flatten extras into the same payload dict consumed by tool_observation / the EDA adapter.
        payload.update(params)
    # Emit a structured observation stamped with agent_id='timing_debug' for audit and telemetry.
    return tool_observation(
        'report_path_details',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='timing_debug',  # Ties the observation to this Timing-Debug Agent worker.
    )


@tool(description='Report the placement span and layers of one path.')  # Registers ``report_path_physical_span`` as a discoverable signoff skill.
def report_path_physical_span(
    candidate_ref: str = '',  # Artifact URI of the isolated layout/netlist candidate under signoff analysis.
    report_ref: str = '',  # Artifact URI of a prior report; empty means read the latest report for the candidate.
    corner: str = '',  # PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
    mode: str = '',  # Functional or analysis mode (for example functional vs scan); empty when unused.
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """Report the placement span and layers of one path.

    Purpose:
        Stable operation contract for ``report_path_physical_span`` in the Timing-Debug Agent. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of STA query and path classification (setup/hold/recovery/removal/clock). Relates to OpenSTA report_checks, WNS/TNS, path cause tracing, unconstrained endpoints.

    Args:
        candidate_ref: Artifact URI of the isolated layout/netlist candidate under signoff analysis.
        report_ref: Artifact URI of a prior report; empty means read the latest report for the candidate.
        corner: PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
        mode: Functional or analysis mode (for example functional vs scan); empty when unused.
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='timing_debug'``, and run status. Callers must not treat ``not_run``
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
    # Emit a structured observation stamped with agent_id='timing_debug' for audit and telemetry.
    return tool_observation(
        'report_path_physical_span',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='timing_debug',  # Ties the observation to this Timing-Debug Agent worker.
    )


@tool(description='Show paths that newly fail or newly pass.')  # Registers ``diff_timing_against_baseline`` as a discoverable signoff skill.
def diff_timing_against_baseline(
    candidate_ref: str = '',  # Artifact URI of the isolated layout/netlist candidate under signoff analysis.
    report_ref: str = '',  # Artifact URI of a prior report; empty means read the latest report for the candidate.
    corner: str = '',  # PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
    mode: str = '',  # Functional or analysis mode (for example functional vs scan); empty when unused.
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """Show paths that newly fail or newly pass.

    Purpose:
        Stable operation contract for ``diff_timing_against_baseline`` in the Timing-Debug Agent. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of STA query and path classification (setup/hold/recovery/removal/clock). Relates to OpenSTA report_checks, WNS/TNS, path cause tracing, unconstrained endpoints.

    Args:
        candidate_ref: Artifact URI of the isolated layout/netlist candidate under signoff analysis.
        report_ref: Artifact URI of a prior report; empty means read the latest report for the candidate.
        corner: PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
        mode: Functional or analysis mode (for example functional vs scan); empty when unused.
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='timing_debug'``, and run status. Callers must not treat ``not_run``
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
    # Emit a structured observation stamped with agent_id='timing_debug' for audit and telemetry.
    return tool_observation(
        'diff_timing_against_baseline',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='timing_debug',  # Ties the observation to this Timing-Debug Agent worker.
    )


@tool(description='Publish an endpoint with no timing check.')  # Registers ``flag_unconstrained_endpoint`` as a discoverable signoff skill.
def flag_unconstrained_endpoint(
    summary: str = '',  # One-sentence finding text published into engineering memory for downstream owners.
    evidence_refs: str = '',  # Comma-separated artifact URIs that substantiate the finding or decision.
    severity: str = '',  # Finding severity: low, medium, high, or critical for signoff triage.
    recommended_recipient: str = '',  # Agent id expected to act on the finding (for example routing_lead or eco_lead).
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """Publish an endpoint with no timing check.

    Purpose:
        Stable operation contract for ``flag_unconstrained_endpoint`` in the Timing-Debug Agent. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of STA query and path classification (setup/hold/recovery/removal/clock). Relates to OpenSTA report_checks, WNS/TNS, path cause tracing, unconstrained endpoints.

    Args:
        summary: One-sentence finding text published into engineering memory for downstream owners.
        evidence_refs: Comma-separated artifact URIs that substantiate the finding or decision.
        severity: Finding severity: low, medium, high, or critical for signoff triage.
        recommended_recipient: Agent id expected to act on the finding (for example routing_lead or eco_lead).
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='timing_debug'``, and run status. Callers must not treat ``not_run``
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
    # Emit a structured observation stamped with agent_id='timing_debug' for audit and telemetry.
    return tool_observation(
        'flag_unconstrained_endpoint',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='timing_debug',  # Ties the observation to this Timing-Debug Agent worker.
    )


@tool(description='Record the STA tool, version, SPEF, and SDC.')  # Registers ``record_sta_tool_version`` as a discoverable signoff skill.
def record_sta_tool_version(
    summary: str = '',  # One-sentence finding text published into engineering memory for downstream owners.
    evidence_refs: str = '',  # Comma-separated artifact URIs that substantiate the finding or decision.
    severity: str = '',  # Finding severity: low, medium, high, or critical for signoff triage.
    recommended_recipient: str = '',  # Agent id expected to act on the finding (for example routing_lead or eco_lead).
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """Record the STA tool, version, SPEF, and SDC.

    Purpose:
        Stable operation contract for ``record_sta_tool_version`` in the Timing-Debug Agent. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of STA query and path classification (setup/hold/recovery/removal/clock). Relates to OpenSTA report_checks, WNS/TNS, path cause tracing, unconstrained endpoints.

    Args:
        summary: One-sentence finding text published into engineering memory for downstream owners.
        evidence_refs: Comma-separated artifact URIs that substantiate the finding or decision.
        severity: Finding severity: low, medium, high, or critical for signoff triage.
        recommended_recipient: Agent id expected to act on the finding (for example routing_lead or eco_lead).
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='timing_debug'``, and run status. Callers must not treat ``not_run``
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
    # Emit a structured observation stamped with agent_id='timing_debug' for audit and telemetry.
    return tool_observation(
        'record_sta_tool_version',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='timing_debug',  # Ties the observation to this Timing-Debug Agent worker.
    )
