"""Tools for STA Lead.

Each function below is the stable operation contract for multi-mode multi-corner (MMMC) static timing ownership. A framework
adapter performs the real work (OpenROAD, OpenSTA, licensed DRC/LVS/IR/thermal/power
tools, or simulators) when ``EDA_FRAMEWORK`` is bound.

Until a framework is bound, every call returns status ``not_run`` and does **not** invoke
OpenROAD, Yosys, OpenSTA, a licensed tool, or a simulator. That keep-safe behavior lets
the fleet exercise planning, journaling, and telemetry without mutating silicon artifacts.

EDA focus for this module: MMMC coverage, path-group repair coordination, constraint edit requests.
Observations always stamp ``agent_id='sta_lead'`` so signoff_validator and leads can audit
which worker claimed a check.
"""

from __future__ import annotations  # Allow modern ``dict | None`` annotations without runtime eval.

from packages.agent_sdk import tool  # Decorator registering the callable as an Agent Fleet skill.
from domains.eda.adapters import tool_observation  # Builds the not_run/adapted observation dict for silicon memory.


@tool(description='Emit the timing-debug workflow for the open violations.')  # Registers ``plan_timing_closure`` as a discoverable signoff skill.
def plan_timing_closure(
    objective: str = '',  # Human-readable goal for the planned workflow or ECO/timing task.
    parent_task_id: str = '',  # Upstream task id that spawned this plan request for journal correlation.
    scope_block: str = '',  # Hierarchical block or partition that bounds the ECO or timing work.
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """Emit the timing-debug workflow for the open violations.

    Purpose:
        Stable operation contract for ``plan_timing_closure`` in the STA Lead. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of multi-mode multi-corner (MMMC) static timing ownership. Relates to MMMC coverage, path-group repair coordination, constraint edit requests.

    Args:
        objective: Human-readable goal for the planned workflow or ECO/timing task.
        parent_task_id: Upstream task id that spawned this plan request for journal correlation.
        scope_block: Hierarchical block or partition that bounds the ECO or timing work.
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='sta_lead'``, and run status. Callers must not treat ``not_run``
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
        'objective': objective,  # Planner objective string for the workflow or ECO.
        'parent_task_id': parent_task_id,  # Parent task correlation for the fleet journal.
        'scope_block': scope_block,  # Block/partition limit for disruption and revalidation scope.
    }
    # Merge optional adapter extras (windows, deck paths, SPEF overrides) without dropping required keys.
    if params:
        # Flatten extras into the same payload dict consumed by tool_observation / the EDA adapter.
        payload.update(params)
    # Emit a structured observation stamped with agent_id='sta_lead' for audit and telemetry.
    return tool_observation(
        'plan_timing_closure',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='sta_lead',  # Ties the observation to this STA Lead worker.
    )


@tool(description='Open debug for one path group and check type.')  # Registers ``request_path_group_debug`` as a discoverable signoff skill.
def request_path_group_debug(
    objective: str = '',  # Human-readable goal for the planned workflow or ECO/timing task.
    parent_task_id: str = '',  # Upstream task id that spawned this plan request for journal correlation.
    scope_block: str = '',  # Hierarchical block or partition that bounds the ECO or timing work.
    path_group: str = '',  # Named timing path group under debug or repair (reg2reg, in2reg, etc.).
    check_type: str = '',  # Timing check type filter such as setup, hold, recovery, or removal.
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """Open debug for one path group and check type.

    Purpose:
        Stable operation contract for ``request_path_group_debug`` in the STA Lead. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of multi-mode multi-corner (MMMC) static timing ownership. Relates to MMMC coverage, path-group repair coordination, constraint edit requests.

    Args:
        objective: Human-readable goal for the planned workflow or ECO/timing task.
        parent_task_id: Upstream task id that spawned this plan request for journal correlation.
        scope_block: Hierarchical block or partition that bounds the ECO or timing work.
        path_group: Named timing path group under debug or repair (reg2reg, in2reg, etc.).
        check_type: Timing check type filter such as setup, hold, recovery, or removal.
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='sta_lead'``, and run status. Callers must not treat ``not_run``
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
        'objective': objective,  # Planner objective string for the workflow or ECO.
        'parent_task_id': parent_task_id,  # Parent task correlation for the fleet journal.
        'scope_block': scope_block,  # Block/partition limit for disruption and revalidation scope.
        'path_group': path_group,  # Timing path group being debugged or repaired.
        'check_type': check_type,  # Setup/hold/recovery/removal (or similar) check class.
    }
    # Merge optional adapter extras (windows, deck paths, SPEF overrides) without dropping required keys.
    if params:
        # Flatten extras into the same payload dict consumed by tool_observation / the EDA adapter.
        payload.update(params)
    # Emit a structured observation stamped with agent_id='sta_lead' for audit and telemetry.
    return tool_observation(
        'request_path_group_debug',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='sta_lead',  # Ties the observation to this STA Lead worker.
    )


@tool(description='Open STA across the required modes and corners.')  # Registers ``request_timing_corner_sweep`` as a discoverable signoff skill.
def request_timing_corner_sweep(
    objective: str = '',  # Human-readable goal for the planned workflow or ECO/timing task.
    parent_task_id: str = '',  # Upstream task id that spawned this plan request for journal correlation.
    scope_block: str = '',  # Hierarchical block or partition that bounds the ECO or timing work.
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """Open STA across the required modes and corners.

    Purpose:
        Stable operation contract for ``request_timing_corner_sweep`` in the STA Lead. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of multi-mode multi-corner (MMMC) static timing ownership. Relates to MMMC coverage, path-group repair coordination, constraint edit requests.

    Args:
        objective: Human-readable goal for the planned workflow or ECO/timing task.
        parent_task_id: Upstream task id that spawned this plan request for journal correlation.
        scope_block: Hierarchical block or partition that bounds the ECO or timing work.
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='sta_lead'``, and run status. Callers must not treat ``not_run``
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
        'objective': objective,  # Planner objective string for the workflow or ECO.
        'parent_task_id': parent_task_id,  # Parent task correlation for the fleet journal.
        'scope_block': scope_block,  # Block/partition limit for disruption and revalidation scope.
    }
    # Merge optional adapter extras (windows, deck paths, SPEF overrides) without dropping required keys.
    if params:
        # Flatten extras into the same payload dict consumed by tool_observation / the EDA adapter.
        payload.update(params)
    # Emit a structured observation stamped with agent_id='sta_lead' for audit and telemetry.
    return tool_observation(
        'request_timing_corner_sweep',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='sta_lead',  # Ties the observation to this STA Lead worker.
    )


@tool(description='Read which modes and corners have reports.')  # Registers ``read_mmmc_status`` as a discoverable signoff skill.
def read_mmmc_status(
    candidate_ref: str = '',  # Artifact URI of the isolated layout/netlist candidate under signoff analysis.
    report_ref: str = '',  # Artifact URI of a prior report; empty means read the latest report for the candidate.
    corner: str = '',  # PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
    mode: str = '',  # Functional or analysis mode (for example functional vs scan); empty when unused.
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """Read which modes and corners have reports.

    Purpose:
        Stable operation contract for ``read_mmmc_status`` in the STA Lead. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of multi-mode multi-corner (MMMC) static timing ownership. Relates to MMMC coverage, path-group repair coordination, constraint edit requests.

    Args:
        candidate_ref: Artifact URI of the isolated layout/netlist candidate under signoff analysis.
        report_ref: Artifact URI of a prior report; empty means read the latest report for the candidate.
        corner: PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
        mode: Functional or analysis mode (for example functional vs scan); empty when unused.
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='sta_lead'``, and run status. Callers must not treat ``not_run``
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
    # Emit a structured observation stamped with agent_id='sta_lead' for audit and telemetry.
    return tool_observation(
        'read_mmmc_status',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='sta_lead',  # Ties the observation to this STA Lead worker.
    )


@tool(description='Read the worst setup and hold paths.')  # Registers ``read_worst_paths`` as a discoverable signoff skill.
def read_worst_paths(
    candidate_ref: str = '',  # Artifact URI of the isolated layout/netlist candidate under signoff analysis.
    report_ref: str = '',  # Artifact URI of a prior report; empty means read the latest report for the candidate.
    corner: str = '',  # PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
    mode: str = '',  # Functional or analysis mode (for example functional vs scan); empty when unused.
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """Read the worst setup and hold paths.

    Purpose:
        Stable operation contract for ``read_worst_paths`` in the STA Lead. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of multi-mode multi-corner (MMMC) static timing ownership. Relates to MMMC coverage, path-group repair coordination, constraint edit requests.

    Args:
        candidate_ref: Artifact URI of the isolated layout/netlist candidate under signoff analysis.
        report_ref: Artifact URI of a prior report; empty means read the latest report for the candidate.
        corner: PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
        mode: Functional or analysis mode (for example functional vs scan); empty when unused.
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='sta_lead'``, and run status. Callers must not treat ``not_run``
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
    # Emit a structured observation stamped with agent_id='sta_lead' for audit and telemetry.
    return tool_observation(
        'read_worst_paths',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='sta_lead',  # Ties the observation to this STA Lead worker.
    )


@tool(description='Read the constraints the current STA used.')  # Registers ``read_timing_constraints_in_force`` as a discoverable signoff skill.
def read_timing_constraints_in_force(
    candidate_ref: str = '',  # Artifact URI of the isolated layout/netlist candidate under signoff analysis.
    report_ref: str = '',  # Artifact URI of a prior report; empty means read the latest report for the candidate.
    corner: str = '',  # PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
    mode: str = '',  # Functional or analysis mode (for example functional vs scan); empty when unused.
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """Read the constraints the current STA used.

    Purpose:
        Stable operation contract for ``read_timing_constraints_in_force`` in the STA Lead. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of multi-mode multi-corner (MMMC) static timing ownership. Relates to MMMC coverage, path-group repair coordination, constraint edit requests.

    Args:
        candidate_ref: Artifact URI of the isolated layout/netlist candidate under signoff analysis.
        report_ref: Artifact URI of a prior report; empty means read the latest report for the candidate.
        corner: PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
        mode: Functional or analysis mode (for example functional vs scan); empty when unused.
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='sta_lead'``, and run status. Callers must not treat ``not_run``
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
    # Emit a structured observation stamped with agent_id='sta_lead' for audit and telemetry.
    return tool_observation(
        'read_timing_constraints_in_force',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='sta_lead',  # Ties the observation to this STA Lead worker.
    )


@tool(description='Send a classified path group to the owner who can change it.')  # Registers ``request_timing_repair`` as a discoverable signoff skill.
def request_timing_repair(
    summary: str = '',  # One-sentence finding text published into engineering memory for downstream owners.
    evidence_refs: str = '',  # Comma-separated artifact URIs that substantiate the finding or decision.
    severity: str = '',  # Finding severity: low, medium, high, or critical for signoff triage.
    recommended_recipient: str = '',  # Agent id expected to act on the finding (for example routing_lead or eco_lead).
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """Send a classified path group to the owner who can change it.

    Purpose:
        Stable operation contract for ``request_timing_repair`` in the STA Lead. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of multi-mode multi-corner (MMMC) static timing ownership. Relates to MMMC coverage, path-group repair coordination, constraint edit requests.

    Args:
        summary: One-sentence finding text published into engineering memory for downstream owners.
        evidence_refs: Comma-separated artifact URIs that substantiate the finding or decision.
        severity: Finding severity: low, medium, high, or critical for signoff triage.
        recommended_recipient: Agent id expected to act on the finding (for example routing_lead or eco_lead).
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='sta_lead'``, and run status. Callers must not treat ``not_run``
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
    # Emit a structured observation stamped with agent_id='sta_lead' for audit and telemetry.
    return tool_observation(
        'request_timing_repair',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='sta_lead',  # Ties the observation to this STA Lead worker.
    )


@tool(description='Publish a signoff claim that is missing a required corner.')  # Registers ``flag_single_corner_signoff`` as a discoverable signoff skill.
def flag_single_corner_signoff(
    summary: str = '',  # One-sentence finding text published into engineering memory for downstream owners.
    evidence_refs: str = '',  # Comma-separated artifact URIs that substantiate the finding or decision.
    severity: str = '',  # Finding severity: low, medium, high, or critical for signoff triage.
    recommended_recipient: str = '',  # Agent id expected to act on the finding (for example routing_lead or eco_lead).
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """Publish a signoff claim that is missing a required corner.

    Purpose:
        Stable operation contract for ``flag_single_corner_signoff`` in the STA Lead. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of multi-mode multi-corner (MMMC) static timing ownership. Relates to MMMC coverage, path-group repair coordination, constraint edit requests.

    Args:
        summary: One-sentence finding text published into engineering memory for downstream owners.
        evidence_refs: Comma-separated artifact URIs that substantiate the finding or decision.
        severity: Finding severity: low, medium, high, or critical for signoff triage.
        recommended_recipient: Agent id expected to act on the finding (for example routing_lead or eco_lead).
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='sta_lead'``, and run status. Callers must not treat ``not_run``
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
    # Emit a structured observation stamped with agent_id='sta_lead' for audit and telemetry.
    return tool_observation(
        'flag_single_corner_signoff',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='sta_lead',  # Ties the observation to this STA Lead worker.
    )


@tool(description='Publish a proposed constraint edit so a human can judge it. This agent does not apply it.')  # Registers ``flag_constraint_edit_request`` as a discoverable signoff skill.
def flag_constraint_edit_request(
    summary: str = '',  # One-sentence finding text published into engineering memory for downstream owners.
    evidence_refs: str = '',  # Comma-separated artifact URIs that substantiate the finding or decision.
    severity: str = '',  # Finding severity: low, medium, high, or critical for signoff triage.
    recommended_recipient: str = '',  # Agent id expected to act on the finding (for example routing_lead or eco_lead).
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """Publish a proposed constraint edit so a human can judge it. This agent does not apply it.

    Purpose:
        Stable operation contract for ``flag_constraint_edit_request`` in the STA Lead. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of multi-mode multi-corner (MMMC) static timing ownership. Relates to MMMC coverage, path-group repair coordination, constraint edit requests.

    Args:
        summary: One-sentence finding text published into engineering memory for downstream owners.
        evidence_refs: Comma-separated artifact URIs that substantiate the finding or decision.
        severity: Finding severity: low, medium, high, or critical for signoff triage.
        recommended_recipient: Agent id expected to act on the finding (for example routing_lead or eco_lead).
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='sta_lead'``, and run status. Callers must not treat ``not_run``
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
    # Emit a structured observation stamped with agent_id='sta_lead' for audit and telemetry.
    return tool_observation(
        'flag_constraint_edit_request',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='sta_lead',  # Ties the observation to this STA Lead worker.
    )


@tool(description='Record which path group the next repair will target.')  # Registers ``record_timing_strategy`` as a discoverable signoff skill.
def record_timing_strategy(
    summary: str = '',  # One-sentence finding text published into engineering memory for downstream owners.
    evidence_refs: str = '',  # Comma-separated artifact URIs that substantiate the finding or decision.
    severity: str = '',  # Finding severity: low, medium, high, or critical for signoff triage.
    recommended_recipient: str = '',  # Agent id expected to act on the finding (for example routing_lead or eco_lead).
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """Record which path group the next repair will target.

    Purpose:
        Stable operation contract for ``record_timing_strategy`` in the STA Lead. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of multi-mode multi-corner (MMMC) static timing ownership. Relates to MMMC coverage, path-group repair coordination, constraint edit requests.

    Args:
        summary: One-sentence finding text published into engineering memory for downstream owners.
        evidence_refs: Comma-separated artifact URIs that substantiate the finding or decision.
        severity: Finding severity: low, medium, high, or critical for signoff triage.
        recommended_recipient: Agent id expected to act on the finding (for example routing_lead or eco_lead).
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='sta_lead'``, and run status. Callers must not treat ``not_run``
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
    # Emit a structured observation stamped with agent_id='sta_lead' for audit and telemetry.
    return tool_observation(
        'record_timing_strategy',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='sta_lead',  # Ties the observation to this STA Lead worker.
    )


@tool(description='Record which repaired candidate should be rechecked. This does not promote it.')  # Registers ``recommend_timing_candidate`` as a discoverable signoff skill.
def recommend_timing_candidate(
    summary: str = '',  # One-sentence finding text published into engineering memory for downstream owners.
    evidence_refs: str = '',  # Comma-separated artifact URIs that substantiate the finding or decision.
    severity: str = '',  # Finding severity: low, medium, high, or critical for signoff triage.
    recommended_recipient: str = '',  # Agent id expected to act on the finding (for example routing_lead or eco_lead).
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """Record which repaired candidate should be rechecked. This does not promote it.

    Purpose:
        Stable operation contract for ``recommend_timing_candidate`` in the STA Lead. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of multi-mode multi-corner (MMMC) static timing ownership. Relates to MMMC coverage, path-group repair coordination, constraint edit requests.

    Args:
        summary: One-sentence finding text published into engineering memory for downstream owners.
        evidence_refs: Comma-separated artifact URIs that substantiate the finding or decision.
        severity: Finding severity: low, medium, high, or critical for signoff triage.
        recommended_recipient: Agent id expected to act on the finding (for example routing_lead or eco_lead).
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='sta_lead'``, and run status. Callers must not treat ``not_run``
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
    # Emit a structured observation stamped with agent_id='sta_lead' for audit and telemetry.
    return tool_observation(
        'recommend_timing_candidate',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='sta_lead',  # Ties the observation to this STA Lead worker.
    )


@tool(description='Ask a human to accept a remaining violation or change a constraint.')  # Registers ``request_timing_decision`` as a discoverable signoff skill.
def request_timing_decision(
    decision: str = '',  # Decision question posed to a human (authorize ECO, accept violation, edit SDC).
    options: str = '',  # Comma-separated options the human may choose among.
    evidence_refs: str = '',  # Comma-separated artifact URIs that substantiate the finding or decision.
    deadline: str = '',  # Optional wall-clock deadline for the human decision.
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """Ask a human to accept a remaining violation or change a constraint.

    Purpose:
        Stable operation contract for ``request_timing_decision`` in the STA Lead. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of multi-mode multi-corner (MMMC) static timing ownership. Relates to MMMC coverage, path-group repair coordination, constraint edit requests.

    Args:
        decision: Decision question posed to a human (authorize ECO, accept violation, edit SDC).
        options: Comma-separated options the human may choose among.
        evidence_refs: Comma-separated artifact URIs that substantiate the finding or decision.
        deadline: Optional wall-clock deadline for the human decision.
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='sta_lead'``, and run status. Callers must not treat ``not_run``
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
        'decision': decision,  # Human-decision prompt payload.
        'options': options,  # Allowed human answers for the decision.
        'evidence_refs': evidence_refs,  # Artifact URIs backing the finding for auditability.
        'deadline': deadline,  # When the human decision is due.
    }
    # Merge optional adapter extras (windows, deck paths, SPEF overrides) without dropping required keys.
    if params:
        # Flatten extras into the same payload dict consumed by tool_observation / the EDA adapter.
        payload.update(params)
    # Emit a structured observation stamped with agent_id='sta_lead' for audit and telemetry.
    return tool_observation(
        'request_timing_decision',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='sta_lead',  # Ties the observation to this STA Lead worker.
    )
