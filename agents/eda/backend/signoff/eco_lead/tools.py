"""Tools for ECO Lead.

Each function below is the stable operation contract for engineering change orders (ECO) for late RTL/timing/power/physical fixes. A framework
adapter performs the real work (OpenROAD, OpenSTA, licensed DRC/LVS/IR/thermal/power
tools, or simulators) when ``EDA_FRAMEWORK`` is bound.

Until a framework is bound, every call returns status ``not_run`` and does **not** invoke
OpenROAD, Yosys, OpenSTA, a licensed tool, or a simulator. That keep-safe behavior lets
the fleet exercise planning, journaling, and telemetry without mutating silicon artifacts.

EDA focus for this module: ECO scope, equivalence, impacted STA/DRC/LVS gates, human authorization.
Observations always stamp ``agent_id='eco_lead'`` so signoff_validator and leads can audit
which worker claimed a check.
"""

from __future__ import annotations  # Allow modern ``dict | None`` annotations without runtime eval.

from packages.agent_sdk import tool  # Decorator registering the callable as an Agent Fleet skill.
from domains.eda.adapters import tool_observation  # Builds the not_run/adapted observation dict for silicon memory.


@tool(description='Emit the smallest workflow that implements and revalidates one ECO.')  # Registers ``plan_eco`` as a discoverable signoff skill.
def plan_eco(
    objective: str = '',  # Human-readable goal for the planned workflow or ECO/timing task.
    parent_task_id: str = '',  # Upstream task id that spawned this plan request for journal correlation.
    scope_block: str = '',  # Hierarchical block or partition that bounds the ECO or timing work.
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """Emit the smallest workflow that implements and revalidates one ECO.

    Purpose:
        Stable operation contract for ``plan_eco`` in the ECO Lead. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of engineering change orders (ECO) for late RTL/timing/power/physical fixes. Relates to ECO scope, equivalence, impacted STA/DRC/LVS gates, human authorization.

    Args:
        objective: Human-readable goal for the planned workflow or ECO/timing task.
        parent_task_id: Upstream task id that spawned this plan request for journal correlation.
        scope_block: Hierarchical block or partition that bounds the ECO or timing work.
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='eco_lead'``, and run status. Callers must not treat ``not_run``
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
    # Emit a structured observation stamped with agent_id='eco_lead' for audit and telemetry.
    return tool_observation(
        'plan_eco',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='eco_lead',  # Ties the observation to this ECO Lead worker.
    )


@tool(description='Open one bounded RTL edit for a functional ECO.')  # Registers ``request_eco_rtl_edit`` as a discoverable signoff skill.
def request_eco_rtl_edit(
    objective: str = '',  # Human-readable goal for the planned workflow or ECO/timing task.
    parent_task_id: str = '',  # Upstream task id that spawned this plan request for journal correlation.
    scope_block: str = '',  # Hierarchical block or partition that bounds the ECO or timing work.
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """Open one bounded RTL edit for a functional ECO.

    Purpose:
        Stable operation contract for ``request_eco_rtl_edit`` in the ECO Lead. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of engineering change orders (ECO) for late RTL/timing/power/physical fixes. Relates to ECO scope, equivalence, impacted STA/DRC/LVS gates, human authorization.

    Args:
        objective: Human-readable goal for the planned workflow or ECO/timing task.
        parent_task_id: Upstream task id that spawned this plan request for journal correlation.
        scope_block: Hierarchical block or partition that bounds the ECO or timing work.
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='eco_lead'``, and run status. Callers must not treat ``not_run``
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
    # Emit a structured observation stamped with agent_id='eco_lead' for audit and telemetry.
    return tool_observation(
        'request_eco_rtl_edit',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='eco_lead',  # Ties the observation to this ECO Lead worker.
    )


@tool(description='Open equivalence for an ECO that changes logic.')  # Registers ``request_eco_equivalence`` as a discoverable signoff skill.
def request_eco_equivalence(
    objective: str = '',  # Human-readable goal for the planned workflow or ECO/timing task.
    parent_task_id: str = '',  # Upstream task id that spawned this plan request for journal correlation.
    scope_block: str = '',  # Hierarchical block or partition that bounds the ECO or timing work.
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """Open equivalence for an ECO that changes logic.

    Purpose:
        Stable operation contract for ``request_eco_equivalence`` in the ECO Lead. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of engineering change orders (ECO) for late RTL/timing/power/physical fixes. Relates to ECO scope, equivalence, impacted STA/DRC/LVS gates, human authorization.

    Args:
        objective: Human-readable goal for the planned workflow or ECO/timing task.
        parent_task_id: Upstream task id that spawned this plan request for journal correlation.
        scope_block: Hierarchical block or partition that bounds the ECO or timing work.
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='eco_lead'``, and run status. Callers must not treat ``not_run``
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
    # Emit a structured observation stamped with agent_id='eco_lead' for audit and telemetry.
    return tool_observation(
        'request_eco_equivalence',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='eco_lead',  # Ties the observation to this ECO Lead worker.
    )


@tool(description='Open timing on the paths the ECO can move.')  # Registers ``request_eco_timing`` as a discoverable signoff skill.
def request_eco_timing(
    objective: str = '',  # Human-readable goal for the planned workflow or ECO/timing task.
    parent_task_id: str = '',  # Upstream task id that spawned this plan request for journal correlation.
    scope_block: str = '',  # Hierarchical block or partition that bounds the ECO or timing work.
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """Open timing on the paths the ECO can move.

    Purpose:
        Stable operation contract for ``request_eco_timing`` in the ECO Lead. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of engineering change orders (ECO) for late RTL/timing/power/physical fixes. Relates to ECO scope, equivalence, impacted STA/DRC/LVS gates, human authorization.

    Args:
        objective: Human-readable goal for the planned workflow or ECO/timing task.
        parent_task_id: Upstream task id that spawned this plan request for journal correlation.
        scope_block: Hierarchical block or partition that bounds the ECO or timing work.
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='eco_lead'``, and run status. Callers must not treat ``not_run``
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
    # Emit a structured observation stamped with agent_id='eco_lead' for audit and telemetry.
    return tool_observation(
        'request_eco_timing',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='eco_lead',  # Ties the observation to this ECO Lead worker.
    )


@tool(description='Open DRC and LVS for a physical ECO.')  # Registers ``request_eco_physical_verification`` as a discoverable signoff skill.
def request_eco_physical_verification(
    objective: str = '',  # Human-readable goal for the planned workflow or ECO/timing task.
    parent_task_id: str = '',  # Upstream task id that spawned this plan request for journal correlation.
    scope_block: str = '',  # Hierarchical block or partition that bounds the ECO or timing work.
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """Open DRC and LVS for a physical ECO.

    Purpose:
        Stable operation contract for ``request_eco_physical_verification`` in the ECO Lead. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of engineering change orders (ECO) for late RTL/timing/power/physical fixes. Relates to ECO scope, equivalence, impacted STA/DRC/LVS gates, human authorization.

    Args:
        objective: Human-readable goal for the planned workflow or ECO/timing task.
        parent_task_id: Upstream task id that spawned this plan request for journal correlation.
        scope_block: Hierarchical block or partition that bounds the ECO or timing work.
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='eco_lead'``, and run status. Callers must not treat ``not_run``
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
    # Emit a structured observation stamped with agent_id='eco_lead' for audit and telemetry.
    return tool_observation(
        'request_eco_physical_verification',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='eco_lead',  # Ties the observation to this ECO Lead worker.
    )


@tool(description='List the gates this ECO invalidates.')  # Registers ``list_impacted_checks`` as a discoverable signoff skill.
def list_impacted_checks(
    candidate_ref: str = '',  # Artifact URI of the isolated layout/netlist candidate under signoff analysis.
    report_ref: str = '',  # Artifact URI of a prior report; empty means read the latest report for the candidate.
    corner: str = '',  # PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
    mode: str = '',  # Functional or analysis mode (for example functional vs scan); empty when unused.
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """List the gates this ECO invalidates.

    Purpose:
        Stable operation contract for ``list_impacted_checks`` in the ECO Lead. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of engineering change orders (ECO) for late RTL/timing/power/physical fixes. Relates to ECO scope, equivalence, impacted STA/DRC/LVS gates, human authorization.

    Args:
        candidate_ref: Artifact URI of the isolated layout/netlist candidate under signoff analysis.
        report_ref: Artifact URI of a prior report; empty means read the latest report for the candidate.
        corner: PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
        mode: Functional or analysis mode (for example functional vs scan); empty when unused.
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='eco_lead'``, and run status. Callers must not treat ``not_run``
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
    # Emit a structured observation stamped with agent_id='eco_lead' for audit and telemetry.
    return tool_observation(
        'list_impacted_checks',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='eco_lead',  # Ties the observation to this ECO Lead worker.
    )


@tool(description='Read the finding this ECO is supposed to close.')  # Registers ``read_eco_finding`` as a discoverable signoff skill.
def read_eco_finding(
    candidate_ref: str = '',  # Artifact URI of the isolated layout/netlist candidate under signoff analysis.
    report_ref: str = '',  # Artifact URI of a prior report; empty means read the latest report for the candidate.
    corner: str = '',  # PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
    mode: str = '',  # Functional or analysis mode (for example functional vs scan); empty when unused.
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """Read the finding this ECO is supposed to close.

    Purpose:
        Stable operation contract for ``read_eco_finding`` in the ECO Lead. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of engineering change orders (ECO) for late RTL/timing/power/physical fixes. Relates to ECO scope, equivalence, impacted STA/DRC/LVS gates, human authorization.

    Args:
        candidate_ref: Artifact URI of the isolated layout/netlist candidate under signoff analysis.
        report_ref: Artifact URI of a prior report; empty means read the latest report for the candidate.
        corner: PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
        mode: Functional or analysis mode (for example functional vs scan); empty when unused.
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='eco_lead'``, and run status. Callers must not treat ``not_run``
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
    # Emit a structured observation stamped with agent_id='eco_lead' for audit and telemetry.
    return tool_observation(
        'read_eco_finding',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='eco_lead',  # Ties the observation to this ECO Lead worker.
    )


@tool(description='Read the baseline the ECO must descend from.')  # Registers ``read_eco_baseline`` as a discoverable signoff skill.
def read_eco_baseline(
    candidate_ref: str = '',  # Artifact URI of the isolated layout/netlist candidate under signoff analysis.
    report_ref: str = '',  # Artifact URI of a prior report; empty means read the latest report for the candidate.
    corner: str = '',  # PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
    mode: str = '',  # Functional or analysis mode (for example functional vs scan); empty when unused.
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """Read the baseline the ECO must descend from.

    Purpose:
        Stable operation contract for ``read_eco_baseline`` in the ECO Lead. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of engineering change orders (ECO) for late RTL/timing/power/physical fixes. Relates to ECO scope, equivalence, impacted STA/DRC/LVS gates, human authorization.

    Args:
        candidate_ref: Artifact URI of the isolated layout/netlist candidate under signoff analysis.
        report_ref: Artifact URI of a prior report; empty means read the latest report for the candidate.
        corner: PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
        mode: Functional or analysis mode (for example functional vs scan); empty when unused.
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='eco_lead'``, and run status. Callers must not treat ``not_run``
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
    # Emit a structured observation stamped with agent_id='eco_lead' for audit and telemetry.
    return tool_observation(
        'read_eco_baseline',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='eco_lead',  # Ties the observation to this ECO Lead worker.
    )


@tool(description='List files, nets, and path groups the ECO touches.')  # Registers ``estimate_eco_disruption`` as a discoverable signoff skill.
def estimate_eco_disruption(
    candidate_ref: str = '',  # Artifact URI of the isolated layout/netlist candidate under signoff analysis.
    report_ref: str = '',  # Artifact URI of a prior report; empty means read the latest report for the candidate.
    corner: str = '',  # PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
    mode: str = '',  # Functional or analysis mode (for example functional vs scan); empty when unused.
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """List files, nets, and path groups the ECO touches.

    Purpose:
        Stable operation contract for ``estimate_eco_disruption`` in the ECO Lead. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of engineering change orders (ECO) for late RTL/timing/power/physical fixes. Relates to ECO scope, equivalence, impacted STA/DRC/LVS gates, human authorization.

    Args:
        candidate_ref: Artifact URI of the isolated layout/netlist candidate under signoff analysis.
        report_ref: Artifact URI of a prior report; empty means read the latest report for the candidate.
        corner: PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
        mode: Functional or analysis mode (for example functional vs scan); empty when unused.
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='eco_lead'``, and run status. Callers must not treat ``not_run``
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
    # Emit a structured observation stamped with agent_id='eco_lead' for audit and telemetry.
    return tool_observation(
        'estimate_eco_disruption',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='eco_lead',  # Ties the observation to this ECO Lead worker.
    )


@tool(description='Publish an impacted check the workflow does not rerun.')  # Registers ``flag_missing_eco_check`` as a discoverable signoff skill.
def flag_missing_eco_check(
    summary: str = '',  # One-sentence finding text published into engineering memory for downstream owners.
    evidence_refs: str = '',  # Comma-separated artifact URIs that substantiate the finding or decision.
    severity: str = '',  # Finding severity: low, medium, high, or critical for signoff triage.
    recommended_recipient: str = '',  # Agent id expected to act on the finding (for example routing_lead or eco_lead).
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """Publish an impacted check the workflow does not rerun.

    Purpose:
        Stable operation contract for ``flag_missing_eco_check`` in the ECO Lead. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of engineering change orders (ECO) for late RTL/timing/power/physical fixes. Relates to ECO scope, equivalence, impacted STA/DRC/LVS gates, human authorization.

    Args:
        summary: One-sentence finding text published into engineering memory for downstream owners.
        evidence_refs: Comma-separated artifact URIs that substantiate the finding or decision.
        severity: Finding severity: low, medium, high, or critical for signoff triage.
        recommended_recipient: Agent id expected to act on the finding (for example routing_lead or eco_lead).
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='eco_lead'``, and run status. Callers must not treat ``not_run``
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
    # Emit a structured observation stamped with agent_id='eco_lead' for audit and telemetry.
    return tool_observation(
        'flag_missing_eco_check',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='eco_lead',  # Ties the observation to this ECO Lead worker.
    )


@tool(description='Record the hypothesis, the baseline, and the checks that must rerun.')  # Registers ``record_eco_scope`` as a discoverable signoff skill.
def record_eco_scope(
    summary: str = '',  # One-sentence finding text published into engineering memory for downstream owners.
    evidence_refs: str = '',  # Comma-separated artifact URIs that substantiate the finding or decision.
    severity: str = '',  # Finding severity: low, medium, high, or critical for signoff triage.
    recommended_recipient: str = '',  # Agent id expected to act on the finding (for example routing_lead or eco_lead).
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """Record the hypothesis, the baseline, and the checks that must rerun.

    Purpose:
        Stable operation contract for ``record_eco_scope`` in the ECO Lead. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of engineering change orders (ECO) for late RTL/timing/power/physical fixes. Relates to ECO scope, equivalence, impacted STA/DRC/LVS gates, human authorization.

    Args:
        summary: One-sentence finding text published into engineering memory for downstream owners.
        evidence_refs: Comma-separated artifact URIs that substantiate the finding or decision.
        severity: Finding severity: low, medium, high, or critical for signoff triage.
        recommended_recipient: Agent id expected to act on the finding (for example routing_lead or eco_lead).
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='eco_lead'``, and run status. Callers must not treat ``not_run``
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
    # Emit a structured observation stamped with agent_id='eco_lead' for audit and telemetry.
    return tool_observation(
        'record_eco_scope',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='eco_lead',  # Ties the observation to this ECO Lead worker.
    )


@tool(description='Ask a human to authorize the ECO before it is applied.')  # Registers ``request_eco_authorization`` as a discoverable signoff skill.
def request_eco_authorization(
    decision: str = '',  # Decision question posed to a human (authorize ECO, accept violation, edit SDC).
    options: str = '',  # Comma-separated options the human may choose among.
    evidence_refs: str = '',  # Comma-separated artifact URIs that substantiate the finding or decision.
    deadline: str = '',  # Optional wall-clock deadline for the human decision.
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """Ask a human to authorize the ECO before it is applied.

    Purpose:
        Stable operation contract for ``request_eco_authorization`` in the ECO Lead. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of engineering change orders (ECO) for late RTL/timing/power/physical fixes. Relates to ECO scope, equivalence, impacted STA/DRC/LVS gates, human authorization.

    Args:
        decision: Decision question posed to a human (authorize ECO, accept violation, edit SDC).
        options: Comma-separated options the human may choose among.
        evidence_refs: Comma-separated artifact URIs that substantiate the finding or decision.
        deadline: Optional wall-clock deadline for the human decision.
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='eco_lead'``, and run status. Callers must not treat ``not_run``
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
    # Emit a structured observation stamped with agent_id='eco_lead' for audit and telemetry.
    return tool_observation(
        'request_eco_authorization',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='eco_lead',  # Ties the observation to this ECO Lead worker.
    )
