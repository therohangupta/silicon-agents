"""Tool callables for the Chip Flow Lead agent (chip_flow_lead).

Owns program plan, gates, cross-stage routing, and human decisions.

Each function below is the stable operation contract advertised in
``config.yaml`` under ``skills``. A framework adapter (DFT tool, ATPG engine,
MBIST compiler, lab instrument bridge, ATE, etc.) performs the real work.
Until that adapter is bound, ``tool_observation`` returns a structured
``not_run`` result and does **not** invoke OpenROAD, Yosys, OpenSTA, a licensed
DFT/ATE tool, a simulator, or a physical instrument.

This module is imported when a skill is dispatched. Process bootstrap lives in
``server.py``; fleet metadata and param schemas live in ``config.yaml``.

Module lineage: Tool callables for the Chip Flow Lead agent (chip_flow_lead).
"""

from __future__ import annotations  # Allow modern typing constructs in skill signatures.

from packages.agent_sdk import tool  # Decorator that registers the callable as an agent skill.
from domains.eda.adapters import tool_observation  # Builds the not_run / observation envelope for adapters.


@tool(description='Publish a revised program workflow from current gate status and open findings.')  # Fleet-facing one-line skill description for planners.
def revise_program_plan(
    objective: str = '',
    parent_task_id: str = '',
    scope_block: str = '',
    params: dict | None = None,
) -> dict:
    """Publish a revised program workflow from current gate status and open findings.

    Purpose:
        Skill ``revise_program_plan`` for the Chip Flow Lead agent (``chip_flow_lead``). Owns program plan, gates, cross-stage routing, and human decisions.
        Program-flow meaning: this skill revises the cross-stage plan, routes findings upstream, checks budget, or packages human decisions for gates, promotion, and waivers. This callable only builds a ``tool_observation`` payload;
        heavy EDA or bench work happens in a bound adapter.

    Args:
        objective: Outcome the child workflow must achieve. Empty reuses the parent task objective.
        parent_task_id: Task that owns this workflow. Empty when invoked outside a nested workflow.
        scope_block: Block the workflow applies to. Empty means the task's current block. Empty means the parent task's current block.
        params: Optional adapter-specific key/value overrides merged into the payload. None skips the merge.

    Returns:
        Structured observation dict from ``tool_observation``. Until a framework
        adapter is bound, status is typically ``not_run`` and no OpenROAD, Yosys,
        OpenSTA, licensed ATPG/DFT/ATE tool, simulator, or physical instrument runs.

    Side effects:
        None locally beyond constructing the payload. Journals, child workflows,
        and instrument commands occur only when adapters honor the observation.

    Failures:
        Does not raise on missing adapters; callers interpret ``not_run`` / error
        fields. Safety adapters must still refuse over-limit lab commands.
    """
    # Observation payload for skill 'revise_program_plan' — keys align with config.yaml skill params.
    payload = {
        'objective': objective,  # Outcome the child workflow must achieve.
        'parent_task_id': parent_task_id,  # Task that owns this workflow.
        'scope_block': scope_block,  # Block the workflow applies to. Empty means the task's current block.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'revise_program_plan',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='chip_flow_lead',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Open a new workflow for one stage whose strategy has stalled.')  # Fleet-facing one-line skill description for planners.
def request_stage_replan(
    objective: str = '',
    parent_task_id: str = '',
    scope_block: str = '',
    stage_agent: str = '',
    params: dict | None = None,
) -> dict:
    """Open a new workflow for one stage whose strategy has stalled.

    Purpose:
        Skill ``request_stage_replan`` for the Chip Flow Lead agent (``chip_flow_lead``). Owns program plan, gates, cross-stage routing, and human decisions.
        Program-flow meaning: this skill revises the cross-stage plan, routes findings upstream, checks budget, or packages human decisions for gates, promotion, and waivers. This callable only builds a ``tool_observation`` payload;
        heavy EDA or bench work happens in a bound adapter.

    Args:
        objective: Outcome the child workflow must achieve. Empty reuses the parent task objective.
        parent_task_id: Task that owns this workflow. Empty when invoked outside a nested workflow.
        scope_block: Block the workflow applies to. Empty means the task's current block. Empty means the parent task's current block.
        stage_agent: Lead agent that must replan. Empty is invalid for stage-specific replans.
        params: Optional adapter-specific key/value overrides merged into the payload. None skips the merge.

    Returns:
        Structured observation dict from ``tool_observation``. Until a framework
        adapter is bound, status is typically ``not_run`` and no OpenROAD, Yosys,
        OpenSTA, licensed ATPG/DFT/ATE tool, simulator, or physical instrument runs.

    Side effects:
        None locally beyond constructing the payload. Journals, child workflows,
        and instrument commands occur only when adapters honor the observation.

    Failures:
        Does not raise on missing adapters; callers interpret ``not_run`` / error
        fields. Safety adapters must still refuse over-limit lab commands.
    """
    # Observation payload for skill 'request_stage_replan' — keys align with config.yaml skill params.
    payload = {
        'objective': objective,  # Outcome the child workflow must achieve.
        'parent_task_id': parent_task_id,  # Task that owns this workflow.
        'scope_block': scope_block,  # Block the workflow applies to. Empty means the task's current block.
        'stage_agent': stage_agent,  # Lead agent that must replan.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'request_stage_replan',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='chip_flow_lead',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Replace a broad objective with a smaller workflow the stage can finish.')  # Fleet-facing one-line skill description for planners.
def narrow_program_scope(
    objective: str = '',
    parent_task_id: str = '',
    scope_block: str = '',
    params: dict | None = None,
) -> dict:
    """Replace a broad objective with a smaller workflow the stage can finish.

    Purpose:
        Skill ``narrow_program_scope`` for the Chip Flow Lead agent (``chip_flow_lead``). Owns program plan, gates, cross-stage routing, and human decisions.
        Program-flow meaning: this skill revises the cross-stage plan, routes findings upstream, checks budget, or packages human decisions for gates, promotion, and waivers. This callable only builds a ``tool_observation`` payload;
        heavy EDA or bench work happens in a bound adapter.

    Args:
        objective: Outcome the child workflow must achieve. Empty reuses the parent task objective.
        parent_task_id: Task that owns this workflow. Empty when invoked outside a nested workflow.
        scope_block: Block the workflow applies to. Empty means the task's current block. Empty means the parent task's current block.
        params: Optional adapter-specific key/value overrides merged into the payload. None skips the merge.

    Returns:
        Structured observation dict from ``tool_observation``. Until a framework
        adapter is bound, status is typically ``not_run`` and no OpenROAD, Yosys,
        OpenSTA, licensed ATPG/DFT/ATE tool, simulator, or physical instrument runs.

    Side effects:
        None locally beyond constructing the payload. Journals, child workflows,
        and instrument commands occur only when adapters honor the observation.

    Failures:
        Does not raise on missing adapters; callers interpret ``not_run`` / error
        fields. Safety adapters must still refuse over-limit lab commands.
    """
    # Observation payload for skill 'narrow_program_scope' — keys align with config.yaml skill params.
    payload = {
        'objective': objective,  # Outcome the child workflow must achieve.
        'parent_task_id': parent_task_id,  # Task that owns this workflow.
        'scope_block': scope_block,  # Block the workflow applies to. Empty means the task's current block.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'narrow_program_scope',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='chip_flow_lead',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Read milestone status for every active stage.')  # Fleet-facing one-line skill description for planners.
def read_program_status(
    candidate_ref: str = '',
    report_ref: str = '',
    corner: str = '',
    mode: str = '',
    params: dict | None = None,
) -> dict:
    """Read milestone status for every active stage.

    Purpose:
        Skill ``read_program_status`` for the Chip Flow Lead agent (``chip_flow_lead``). Owns program plan, gates, cross-stage routing, and human decisions.
        Program-flow meaning: this skill revises the cross-stage plan, routes findings upstream, checks budget, or packages human decisions for gates, promotion, and waivers. This callable only builds a ``tool_observation`` payload;
        heavy EDA or bench work happens in a bound adapter.

    Args:
        candidate_ref: Candidate whose reports are read. Empty may mean latest candidate for the adapter.
        report_ref: Artifact URI of the report. Empty reads the latest report for this candidate. Empty reads the latest report for the candidate.
        corner: Corner filter. Empty reads every available corner. Empty reads every available corner.
        mode: Mode filter. Empty reads every available mode. Empty reads every available mode.
        params: Optional adapter-specific key/value overrides merged into the payload. None skips the merge.

    Returns:
        Structured observation dict from ``tool_observation``. Until a framework
        adapter is bound, status is typically ``not_run`` and no OpenROAD, Yosys,
        OpenSTA, licensed ATPG/DFT/ATE tool, simulator, or physical instrument runs.

    Side effects:
        None locally beyond constructing the payload. Journals, child workflows,
        and instrument commands occur only when adapters honor the observation.

    Failures:
        Does not raise on missing adapters; callers interpret ``not_run`` / error
        fields. Safety adapters must still refuse over-limit lab commands.
    """
    # Observation payload for skill 'read_program_status' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Candidate whose reports are read.
        'report_ref': report_ref,  # Artifact URI of the report. Empty reads the latest report for this candidate.
        'corner': corner,  # Corner filter. Empty reads every available corner.
        'mode': mode,  # Mode filter. Empty reads every available mode.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'read_program_status',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='chip_flow_lead',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Read the latest gate decision for each milestone.')  # Fleet-facing one-line skill description for planners.
def read_milestone_gates(
    candidate_ref: str = '',
    report_ref: str = '',
    corner: str = '',
    mode: str = '',
    params: dict | None = None,
) -> dict:
    """Read the latest gate decision for each milestone.

    Purpose:
        Skill ``read_milestone_gates`` for the Chip Flow Lead agent (``chip_flow_lead``). Owns program plan, gates, cross-stage routing, and human decisions.
        Program-flow meaning: this skill revises the cross-stage plan, routes findings upstream, checks budget, or packages human decisions for gates, promotion, and waivers. This callable only builds a ``tool_observation`` payload;
        heavy EDA or bench work happens in a bound adapter.

    Args:
        candidate_ref: Candidate whose reports are read. Empty may mean latest candidate for the adapter.
        report_ref: Artifact URI of the report. Empty reads the latest report for this candidate. Empty reads the latest report for the candidate.
        corner: Corner filter. Empty reads every available corner. Empty reads every available corner.
        mode: Mode filter. Empty reads every available mode. Empty reads every available mode.
        params: Optional adapter-specific key/value overrides merged into the payload. None skips the merge.

    Returns:
        Structured observation dict from ``tool_observation``. Until a framework
        adapter is bound, status is typically ``not_run`` and no OpenROAD, Yosys,
        OpenSTA, licensed ATPG/DFT/ATE tool, simulator, or physical instrument runs.

    Side effects:
        None locally beyond constructing the payload. Journals, child workflows,
        and instrument commands occur only when adapters honor the observation.

    Failures:
        Does not raise on missing adapters; callers interpret ``not_run`` / error
        fields. Safety adapters must still refuse over-limit lab commands.
    """
    # Observation payload for skill 'read_milestone_gates' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Candidate whose reports are read.
        'report_ref': report_ref,  # Artifact URI of the report. Empty reads the latest report for this candidate.
        'corner': corner,  # Corner filter. Empty reads every available corner.
        'mode': mode,  # Mode filter. Empty reads every available mode.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'read_milestone_gates',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='chip_flow_lead',  # Provenance: which specialist emitted this observation.
    )


@tool(description='List findings that no stage has closed.')  # Fleet-facing one-line skill description for planners.
def list_open_findings(
    candidate_ref: str = '',
    report_ref: str = '',
    corner: str = '',
    mode: str = '',
    params: dict | None = None,
) -> dict:
    """List findings that no stage has closed.

    Purpose:
        Skill ``list_open_findings`` for the Chip Flow Lead agent (``chip_flow_lead``). Owns program plan, gates, cross-stage routing, and human decisions.
        Program-flow meaning: this skill revises the cross-stage plan, routes findings upstream, checks budget, or packages human decisions for gates, promotion, and waivers. This callable only builds a ``tool_observation`` payload;
        heavy EDA or bench work happens in a bound adapter.

    Args:
        candidate_ref: Candidate whose reports are read. Empty may mean latest candidate for the adapter.
        report_ref: Artifact URI of the report. Empty reads the latest report for this candidate. Empty reads the latest report for the candidate.
        corner: Corner filter. Empty reads every available corner. Empty reads every available corner.
        mode: Mode filter. Empty reads every available mode. Empty reads every available mode.
        params: Optional adapter-specific key/value overrides merged into the payload. None skips the merge.

    Returns:
        Structured observation dict from ``tool_observation``. Until a framework
        adapter is bound, status is typically ``not_run`` and no OpenROAD, Yosys,
        OpenSTA, licensed ATPG/DFT/ATE tool, simulator, or physical instrument runs.

    Side effects:
        None locally beyond constructing the payload. Journals, child workflows,
        and instrument commands occur only when adapters honor the observation.

    Failures:
        Does not raise on missing adapters; callers interpret ``not_run`` / error
        fields. Safety adapters must still refuse over-limit lab commands.
    """
    # Observation payload for skill 'list_open_findings' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Candidate whose reports are read.
        'report_ref': report_ref,  # Artifact URI of the report. Empty reads the latest report for this candidate.
        'corner': corner,  # Corner filter. Empty reads every available corner.
        'mode': mode,  # Mode filter. Empty reads every available mode.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'list_open_findings',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='chip_flow_lead',  # Provenance: which specialist emitted this observation.
    )


@tool(description='List tasks waiting on a dependency, license, or human decision.')  # Fleet-facing one-line skill description for planners.
def list_blocked_tasks(
    candidate_ref: str = '',
    report_ref: str = '',
    corner: str = '',
    mode: str = '',
    params: dict | None = None,
) -> dict:
    """List tasks waiting on a dependency, license, or human decision.

    Purpose:
        Skill ``list_blocked_tasks`` for the Chip Flow Lead agent (``chip_flow_lead``). Owns program plan, gates, cross-stage routing, and human decisions.
        Program-flow meaning: this skill revises the cross-stage plan, routes findings upstream, checks budget, or packages human decisions for gates, promotion, and waivers. This callable only builds a ``tool_observation`` payload;
        heavy EDA or bench work happens in a bound adapter.

    Args:
        candidate_ref: Candidate whose reports are read. Empty may mean latest candidate for the adapter.
        report_ref: Artifact URI of the report. Empty reads the latest report for this candidate. Empty reads the latest report for the candidate.
        corner: Corner filter. Empty reads every available corner. Empty reads every available corner.
        mode: Mode filter. Empty reads every available mode. Empty reads every available mode.
        params: Optional adapter-specific key/value overrides merged into the payload. None skips the merge.

    Returns:
        Structured observation dict from ``tool_observation``. Until a framework
        adapter is bound, status is typically ``not_run`` and no OpenROAD, Yosys,
        OpenSTA, licensed ATPG/DFT/ATE tool, simulator, or physical instrument runs.

    Side effects:
        None locally beyond constructing the payload. Journals, child workflows,
        and instrument commands occur only when adapters honor the observation.

    Failures:
        Does not raise on missing adapters; callers interpret ``not_run`` / error
        fields. Safety adapters must still refuse over-limit lab commands.
    """
    # Observation payload for skill 'list_blocked_tasks' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Candidate whose reports are read.
        'report_ref': report_ref,  # Artifact URI of the report. Empty reads the latest report for this candidate.
        'corner': corner,  # Corner filter. Empty reads every available corner.
        'mode': mode,  # Mode filter. Empty reads every available mode.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'list_blocked_tasks',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='chip_flow_lead',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Compare prior experiments so the program does not repeat a dead end.')  # Fleet-facing one-line skill description for planners.
def compare_experiment_history(
    candidate_ref: str = '',
    report_ref: str = '',
    corner: str = '',
    mode: str = '',
    params: dict | None = None,
) -> dict:
    """Compare prior experiments so the program does not repeat a dead end.

    Purpose:
        Skill ``compare_experiment_history`` for the Chip Flow Lead agent (``chip_flow_lead``). Owns program plan, gates, cross-stage routing, and human decisions.
        Program-flow meaning: this skill revises the cross-stage plan, routes findings upstream, checks budget, or packages human decisions for gates, promotion, and waivers. This callable only builds a ``tool_observation`` payload;
        heavy EDA or bench work happens in a bound adapter.

    Args:
        candidate_ref: Candidate whose reports are read. Empty may mean latest candidate for the adapter.
        report_ref: Artifact URI of the report. Empty reads the latest report for this candidate. Empty reads the latest report for the candidate.
        corner: Corner filter. Empty reads every available corner. Empty reads every available corner.
        mode: Mode filter. Empty reads every available mode. Empty reads every available mode.
        params: Optional adapter-specific key/value overrides merged into the payload. None skips the merge.

    Returns:
        Structured observation dict from ``tool_observation``. Until a framework
        adapter is bound, status is typically ``not_run`` and no OpenROAD, Yosys,
        OpenSTA, licensed ATPG/DFT/ATE tool, simulator, or physical instrument runs.

    Side effects:
        None locally beyond constructing the payload. Journals, child workflows,
        and instrument commands occur only when adapters honor the observation.

    Failures:
        Does not raise on missing adapters; callers interpret ``not_run`` / error
        fields. Safety adapters must still refuse over-limit lab commands.
    """
    # Observation payload for skill 'compare_experiment_history' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Candidate whose reports are read.
        'report_ref': report_ref,  # Artifact URI of the report. Empty reads the latest report for this candidate.
        'corner': corner,  # Corner filter. Empty reads every available corner.
        'mode': mode,  # Mode filter. Empty reads every available mode.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'compare_experiment_history',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='chip_flow_lead',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Read remaining compute, license, and schedule budget.')  # Fleet-facing one-line skill description for planners.
def check_program_budget(
    candidate_ref: str = '',
    report_ref: str = '',
    corner: str = '',
    mode: str = '',
    params: dict | None = None,
) -> dict:
    """Read remaining compute, license, and schedule budget.

    Purpose:
        Skill ``check_program_budget`` for the Chip Flow Lead agent (``chip_flow_lead``). Owns program plan, gates, cross-stage routing, and human decisions.
        Program-flow meaning: this skill revises the cross-stage plan, routes findings upstream, checks budget, or packages human decisions for gates, promotion, and waivers. This callable only builds a ``tool_observation`` payload;
        heavy EDA or bench work happens in a bound adapter.

    Args:
        candidate_ref: Candidate whose reports are read. Empty may mean latest candidate for the adapter.
        report_ref: Artifact URI of the report. Empty reads the latest report for this candidate. Empty reads the latest report for the candidate.
        corner: Corner filter. Empty reads every available corner. Empty reads every available corner.
        mode: Mode filter. Empty reads every available mode. Empty reads every available mode.
        params: Optional adapter-specific key/value overrides merged into the payload. None skips the merge.

    Returns:
        Structured observation dict from ``tool_observation``. Until a framework
        adapter is bound, status is typically ``not_run`` and no OpenROAD, Yosys,
        OpenSTA, licensed ATPG/DFT/ATE tool, simulator, or physical instrument runs.

    Side effects:
        None locally beyond constructing the payload. Journals, child workflows,
        and instrument commands occur only when adapters honor the observation.

    Failures:
        Does not raise on missing adapters; callers interpret ``not_run`` / error
        fields. Safety adapters must still refuse over-limit lab commands.
    """
    # Observation payload for skill 'check_program_budget' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Candidate whose reports are read.
        'report_ref': report_ref,  # Artifact URI of the report. Empty reads the latest report for this candidate.
        'corner': corner,  # Corner filter. Empty reads every available corner.
        'mode': mode,  # Mode filter. Empty reads every available mode.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'check_program_budget',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='chip_flow_lead',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Attach a downstream finding to the earliest stage that can change the cause.')  # Fleet-facing one-line skill description for planners.
def route_upstream_finding(
    summary: str = '',
    evidence_refs: str = '',
    severity: str = '',
    recommended_recipient: str = '',
    destination_agent: str = '',
    params: dict | None = None,
) -> dict:
    """Attach a downstream finding to the earliest stage that can change the cause.

    Purpose:
        Skill ``route_upstream_finding`` for the Chip Flow Lead agent (``chip_flow_lead``). Owns program plan, gates, cross-stage routing, and human decisions.
        Program-flow meaning: this skill revises the cross-stage plan, routes findings upstream, checks budget, or packages human decisions for gates, promotion, and waivers. This callable only builds a ``tool_observation`` payload;
        heavy EDA or bench work happens in a bound adapter.

    Args:
        summary: One-sentence finding. Empty leaves text for the planner to fill.
        evidence_refs: Comma-separated artifact URIs that support the finding. Empty marks the claim as under-evidenced.
        severity: low, medium, high, or critical. Empty defers severity classification.
        recommended_recipient: Agent id that should act on the finding. Empty leaves routing to the lead.
        destination_agent: Agent that should receive the finding. Empty leaves routing to chip_flow_lead heuristics.
        params: Optional adapter-specific key/value overrides merged into the payload. None skips the merge.

    Returns:
        Structured observation dict from ``tool_observation``. Until a framework
        adapter is bound, status is typically ``not_run`` and no OpenROAD, Yosys,
        OpenSTA, licensed ATPG/DFT/ATE tool, simulator, or physical instrument runs.

    Side effects:
        None locally beyond constructing the payload. Journals, child workflows,
        and instrument commands occur only when adapters honor the observation.

    Failures:
        Does not raise on missing adapters; callers interpret ``not_run`` / error
        fields. Safety adapters must still refuse over-limit lab commands.
    """
    # Observation payload for skill 'route_upstream_finding' — keys align with config.yaml skill params.
    payload = {
        'summary': summary,  # One-sentence finding.
        'evidence_refs': evidence_refs,  # Comma-separated artifact URIs that support the finding.
        'severity': severity,  # low, medium, high, or critical.
        'recommended_recipient': recommended_recipient,  # Agent id that should act on the finding.
        'destination_agent': destination_agent,  # Agent that should receive the finding.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'route_upstream_finding',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='chip_flow_lead',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Record the evidence bundle currently attached to a milestone.')  # Fleet-facing one-line skill description for planners.
def record_milestone_evidence(
    summary: str = '',
    evidence_refs: str = '',
    severity: str = '',
    recommended_recipient: str = '',
    params: dict | None = None,
) -> dict:
    """Record the evidence bundle currently attached to a milestone.

    Purpose:
        Skill ``record_milestone_evidence`` for the Chip Flow Lead agent (``chip_flow_lead``). Owns program plan, gates, cross-stage routing, and human decisions.
        Program-flow meaning: this skill revises the cross-stage plan, routes findings upstream, checks budget, or packages human decisions for gates, promotion, and waivers. This callable only builds a ``tool_observation`` payload;
        heavy EDA or bench work happens in a bound adapter.

    Args:
        summary: One-sentence finding. Empty leaves text for the planner to fill.
        evidence_refs: Comma-separated artifact URIs that support the finding. Empty marks the claim as under-evidenced.
        severity: low, medium, high, or critical. Empty defers severity classification.
        recommended_recipient: Agent id that should act on the finding. Empty leaves routing to the lead.
        params: Optional adapter-specific key/value overrides merged into the payload. None skips the merge.

    Returns:
        Structured observation dict from ``tool_observation``. Until a framework
        adapter is bound, status is typically ``not_run`` and no OpenROAD, Yosys,
        OpenSTA, licensed ATPG/DFT/ATE tool, simulator, or physical instrument runs.

    Side effects:
        None locally beyond constructing the payload. Journals, child workflows,
        and instrument commands occur only when adapters honor the observation.

    Failures:
        Does not raise on missing adapters; callers interpret ``not_run`` / error
        fields. Safety adapters must still refuse over-limit lab commands.
    """
    # Observation payload for skill 'record_milestone_evidence' — keys align with config.yaml skill params.
    payload = {
        'summary': summary,  # One-sentence finding.
        'evidence_refs': evidence_refs,  # Comma-separated artifact URIs that support the finding.
        'severity': severity,  # low, medium, high, or critical.
        'recommended_recipient': recommended_recipient,  # Agent id that should act on the finding.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'record_milestone_evidence',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='chip_flow_lead',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Record an outer-loop change to how the program searches, without relaxing a hard requirement.')  # Fleet-facing one-line skill description for planners.
def record_strategy_change(
    summary: str = '',
    evidence_refs: str = '',
    severity: str = '',
    recommended_recipient: str = '',
    params: dict | None = None,
) -> dict:
    """Record an outer-loop change to how the program searches, without relaxing a hard requirement.

    Purpose:
        Skill ``record_strategy_change`` for the Chip Flow Lead agent (``chip_flow_lead``). Owns program plan, gates, cross-stage routing, and human decisions.
        Program-flow meaning: this skill revises the cross-stage plan, routes findings upstream, checks budget, or packages human decisions for gates, promotion, and waivers. This callable only builds a ``tool_observation`` payload;
        heavy EDA or bench work happens in a bound adapter.

    Args:
        summary: One-sentence finding. Empty leaves text for the planner to fill.
        evidence_refs: Comma-separated artifact URIs that support the finding. Empty marks the claim as under-evidenced.
        severity: low, medium, high, or critical. Empty defers severity classification.
        recommended_recipient: Agent id that should act on the finding. Empty leaves routing to the lead.
        params: Optional adapter-specific key/value overrides merged into the payload. None skips the merge.

    Returns:
        Structured observation dict from ``tool_observation``. Until a framework
        adapter is bound, status is typically ``not_run`` and no OpenROAD, Yosys,
        OpenSTA, licensed ATPG/DFT/ATE tool, simulator, or physical instrument runs.

    Side effects:
        None locally beyond constructing the payload. Journals, child workflows,
        and instrument commands occur only when adapters honor the observation.

    Failures:
        Does not raise on missing adapters; callers interpret ``not_run`` / error
        fields. Safety adapters must still refuse over-limit lab commands.
    """
    # Observation payload for skill 'record_strategy_change' — keys align with config.yaml skill params.
    payload = {
        'summary': summary,  # One-sentence finding.
        'evidence_refs': evidence_refs,  # Comma-separated artifact URIs that support the finding.
        'severity': severity,  # low, medium, high, or critical.
        'recommended_recipient': recommended_recipient,  # Agent id that should act on the finding.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'record_strategy_change',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='chip_flow_lead',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Package a tradeoff that needs a human owner, with options and evidence.')  # Fleet-facing one-line skill description for planners.
def request_program_decision(
    decision: str = '',
    options: str = '',
    evidence_refs: str = '',
    deadline: str = '',
    params: dict | None = None,
) -> dict:
    """Package a tradeoff that needs a human owner, with options and evidence.

    Purpose:
        Skill ``request_program_decision`` for the Chip Flow Lead agent (``chip_flow_lead``). Owns program plan, gates, cross-stage routing, and human decisions.
        Program-flow meaning: this skill revises the cross-stage plan, routes findings upstream, checks budget, or packages human decisions for gates, promotion, and waivers. This callable only builds a ``tool_observation`` payload;
        heavy EDA or bench work happens in a bound adapter.

    Args:
        decision: The choice a human must make. Must be filled for real requests.
        options: Comma-separated feasible options. Empty allows free-form UI input.
        evidence_refs: Comma-separated artifact URIs that support the finding. Empty marks the claim as under-evidenced.
        deadline: ISO-8601 time after which the decision blocks the schedule. Empty means no hard schedule gate.
        params: Optional adapter-specific key/value overrides merged into the payload. None skips the merge.

    Returns:
        Structured observation dict from ``tool_observation``. Until a framework
        adapter is bound, status is typically ``not_run`` and no OpenROAD, Yosys,
        OpenSTA, licensed ATPG/DFT/ATE tool, simulator, or physical instrument runs.

    Side effects:
        None locally beyond constructing the payload. Journals, child workflows,
        and instrument commands occur only when adapters honor the observation.

    Failures:
        Does not raise on missing adapters; callers interpret ``not_run`` / error
        fields. Safety adapters must still refuse over-limit lab commands.
    """
    # Observation payload for skill 'request_program_decision' — keys align with config.yaml skill params.
    payload = {
        'decision': decision,  # The choice a human must make.
        'options': options,  # Comma-separated feasible options.
        'evidence_refs': evidence_refs,  # Comma-separated artifact URIs that support the finding.
        'deadline': deadline,  # ISO-8601 time after which the decision blocks the schedule.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'request_program_decision',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='chip_flow_lead',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Ask a human to promote a candidate after the required gates have passed.')  # Fleet-facing one-line skill description for planners.
def request_baseline_promotion(
    decision: str = '',
    options: str = '',
    evidence_refs: str = '',
    deadline: str = '',
    params: dict | None = None,
) -> dict:
    """Ask a human to promote a candidate after the required gates have passed.

    Purpose:
        Skill ``request_baseline_promotion`` for the Chip Flow Lead agent (``chip_flow_lead``). Owns program plan, gates, cross-stage routing, and human decisions.
        Program-flow meaning: this skill revises the cross-stage plan, routes findings upstream, checks budget, or packages human decisions for gates, promotion, and waivers. This callable only builds a ``tool_observation`` payload;
        heavy EDA or bench work happens in a bound adapter.

    Args:
        decision: The choice a human must make. Must be filled for real requests.
        options: Comma-separated feasible options. Empty allows free-form UI input.
        evidence_refs: Comma-separated artifact URIs that support the finding. Empty marks the claim as under-evidenced.
        deadline: ISO-8601 time after which the decision blocks the schedule. Empty means no hard schedule gate.
        params: Optional adapter-specific key/value overrides merged into the payload. None skips the merge.

    Returns:
        Structured observation dict from ``tool_observation``. Until a framework
        adapter is bound, status is typically ``not_run`` and no OpenROAD, Yosys,
        OpenSTA, licensed ATPG/DFT/ATE tool, simulator, or physical instrument runs.

    Side effects:
        None locally beyond constructing the payload. Journals, child workflows,
        and instrument commands occur only when adapters honor the observation.

    Failures:
        Does not raise on missing adapters; callers interpret ``not_run`` / error
        fields. Safety adapters must still refuse over-limit lab commands.
    """
    # Observation payload for skill 'request_baseline_promotion' — keys align with config.yaml skill params.
    payload = {
        'decision': decision,  # The choice a human must make.
        'options': options,  # Comma-separated feasible options.
        'evidence_refs': evidence_refs,  # Comma-separated artifact URIs that support the finding.
        'deadline': deadline,  # ISO-8601 time after which the decision blocks the schedule.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'request_baseline_promotion',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='chip_flow_lead',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Ask a named human to approve or reject a waiver. This agent cannot approve it.')  # Fleet-facing one-line skill description for planners.
def request_waiver_decision(
    decision: str = '',
    options: str = '',
    evidence_refs: str = '',
    deadline: str = '',
    params: dict | None = None,
) -> dict:
    """Ask a named human to approve or reject a waiver. This agent cannot approve it.

    Purpose:
        Skill ``request_waiver_decision`` for the Chip Flow Lead agent (``chip_flow_lead``). Owns program plan, gates, cross-stage routing, and human decisions.
        Program-flow meaning: this skill revises the cross-stage plan, routes findings upstream, checks budget, or packages human decisions for gates, promotion, and waivers. This callable only builds a ``tool_observation`` payload;
        heavy EDA or bench work happens in a bound adapter.

    Args:
        decision: The choice a human must make. Must be filled for real requests.
        options: Comma-separated feasible options. Empty allows free-form UI input.
        evidence_refs: Comma-separated artifact URIs that support the finding. Empty marks the claim as under-evidenced.
        deadline: ISO-8601 time after which the decision blocks the schedule. Empty means no hard schedule gate.
        params: Optional adapter-specific key/value overrides merged into the payload. None skips the merge.

    Returns:
        Structured observation dict from ``tool_observation``. Until a framework
        adapter is bound, status is typically ``not_run`` and no OpenROAD, Yosys,
        OpenSTA, licensed ATPG/DFT/ATE tool, simulator, or physical instrument runs.

    Side effects:
        None locally beyond constructing the payload. Journals, child workflows,
        and instrument commands occur only when adapters honor the observation.

    Failures:
        Does not raise on missing adapters; callers interpret ``not_run`` / error
        fields. Safety adapters must still refuse over-limit lab commands.
    """
    # Observation payload for skill 'request_waiver_decision' — keys align with config.yaml skill params.
    payload = {
        'decision': decision,  # The choice a human must make.
        'options': options,  # Comma-separated feasible options.
        'evidence_refs': evidence_refs,  # Comma-separated artifact URIs that support the finding.
        'deadline': deadline,  # ISO-8601 time after which the decision blocks the schedule.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'request_waiver_decision',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='chip_flow_lead',  # Provenance: which specialist emitted this observation.
    )
