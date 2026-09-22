"""Tool callables for the DFT Lead agent (dft_lead).

Owns DFT strategy: scan, ATPG, BIST, physical handoff, and DFT validation.

Each function below is the stable operation contract advertised in
``config.yaml`` under ``skills``. A framework adapter (DFT tool, ATPG engine,
MBIST compiler, lab instrument bridge, ATE, etc.) performs the real work.
Until that adapter is bound, ``tool_observation`` returns a structured
``not_run`` result and does **not** invoke OpenROAD, Yosys, OpenSTA, a licensed
DFT/ATE tool, a simulator, or a physical instrument.

This module is imported when a skill is dispatched. Process bootstrap lives in
``server.py``; fleet metadata and param schemas live in ``config.yaml``.

Module lineage: Tool callables for the DFT Lead agent (dft_lead).
"""

from __future__ import annotations  # Allow modern typing constructs in skill signatures.

from packages.agent_sdk import tool  # Decorator that registers the callable as an agent skill.
from domains.eda.eda import tool_observation  # Builds the not_run / observation envelope for adapters.


@tool(description='Emit the DFT workflow for this revision.')  # Fleet-facing one-line skill description for planners.
def plan_dft_closure(
    objective: str = '',
    parent_task_id: str = '',
    scope_block: str = '',
    params: dict | None = None,
) -> dict:
    """Emit the DFT workflow for this revision.

    Purpose:
        Skill ``plan_dft_closure`` for the DFT Lead agent (``dft_lead``). Owns DFT strategy: scan, ATPG, BIST, physical handoff, and DFT validation.
        Design-for-Test meaning: this skill participates in scan insertion, ATPG, testability analysis, MBIST/LBIST, test-mode timing, or DFT gate grading. It never silently waives fault coverage or drops a required fault model. This callable only builds a ``tool_observation`` payload;
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
    # Observation payload for skill 'plan_dft_closure' — keys align with config.yaml skill params.
    payload = {
        'objective': objective,  # Outcome the child workflow must achieve.
        'parent_task_id': parent_task_id,  # Task that owns this workflow.
        'scope_block': scope_block,  # Block the workflow applies to. Empty means the task's current block.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'plan_dft_closure',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='dft_lead',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Open scan insertion for this RTL candidate.')  # Fleet-facing one-line skill description for planners.
def request_scan_insertion(
    objective: str = '',
    parent_task_id: str = '',
    scope_block: str = '',
    params: dict | None = None,
) -> dict:
    """Open scan insertion for this RTL candidate.

    Purpose:
        Skill ``request_scan_insertion`` for the DFT Lead agent (``dft_lead``). Owns DFT strategy: scan, ATPG, BIST, physical handoff, and DFT validation.
        Design-for-Test meaning: this skill participates in scan insertion, ATPG, testability analysis, MBIST/LBIST, test-mode timing, or DFT gate grading. It never silently waives fault coverage or drops a required fault model. This callable only builds a ``tool_observation`` payload;
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
    # Observation payload for skill 'request_scan_insertion' — keys align with config.yaml skill params.
    payload = {
        'objective': objective,  # Outcome the child workflow must achieve.
        'parent_task_id': parent_task_id,  # Task that owns this workflow.
        'scope_block': scope_block,  # Block the workflow applies to. Empty means the task's current block.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'request_scan_insertion',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='dft_lead',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Open an ATPG campaign for the required fault models.')  # Fleet-facing one-line skill description for planners.
def request_atpg_campaign(
    objective: str = '',
    parent_task_id: str = '',
    scope_block: str = '',
    params: dict | None = None,
) -> dict:
    """Open an ATPG campaign for the required fault models.

    Purpose:
        Skill ``request_atpg_campaign`` for the DFT Lead agent (``dft_lead``). Owns DFT strategy: scan, ATPG, BIST, physical handoff, and DFT validation.
        Design-for-Test meaning: this skill participates in scan insertion, ATPG, testability analysis, MBIST/LBIST, test-mode timing, or DFT gate grading. It never silently waives fault coverage or drops a required fault model. This callable only builds a ``tool_observation`` payload;
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
    # Observation payload for skill 'request_atpg_campaign' — keys align with config.yaml skill params.
    payload = {
        'objective': objective,  # Outcome the child workflow must achieve.
        'parent_task_id': parent_task_id,  # Task that owns this workflow.
        'scope_block': scope_block,  # Block the workflow applies to. Empty means the task's current block.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'request_atpg_campaign',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='dft_lead',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Open testability analysis against the latest ATPG report.')  # Fleet-facing one-line skill description for planners.
def request_testability_analysis(
    objective: str = '',
    parent_task_id: str = '',
    scope_block: str = '',
    params: dict | None = None,
) -> dict:
    """Open testability analysis against the latest ATPG report.

    Purpose:
        Skill ``request_testability_analysis`` for the DFT Lead agent (``dft_lead``). Owns DFT strategy: scan, ATPG, BIST, physical handoff, and DFT validation.
        Design-for-Test meaning: this skill participates in scan insertion, ATPG, testability analysis, MBIST/LBIST, test-mode timing, or DFT gate grading. It never silently waives fault coverage or drops a required fault model. This callable only builds a ``tool_observation`` payload;
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
    # Observation payload for skill 'request_testability_analysis' — keys align with config.yaml skill params.
    payload = {
        'objective': objective,  # Outcome the child workflow must achieve.
        'parent_task_id': parent_task_id,  # Task that owns this workflow.
        'scope_block': scope_block,  # Block the workflow applies to. Empty means the task's current block.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'request_testability_analysis',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='dft_lead',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Open MBIST or LBIST configuration for the memories and logic in scope.')  # Fleet-facing one-line skill description for planners.
def request_bist_configuration(
    objective: str = '',
    parent_task_id: str = '',
    scope_block: str = '',
    params: dict | None = None,
) -> dict:
    """Open MBIST or LBIST configuration for the memories and logic in scope.

    Purpose:
        Skill ``request_bist_configuration`` for the DFT Lead agent (``dft_lead``). Owns DFT strategy: scan, ATPG, BIST, physical handoff, and DFT validation.
        Design-for-Test meaning: this skill participates in scan insertion, ATPG, testability analysis, MBIST/LBIST, test-mode timing, or DFT gate grading. It never silently waives fault coverage or drops a required fault model. This callable only builds a ``tool_observation`` payload;
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
    # Observation payload for skill 'request_bist_configuration' — keys align with config.yaml skill params.
    payload = {
        'objective': objective,  # Outcome the child workflow must achieve.
        'parent_task_id': parent_task_id,  # Task that owns this workflow.
        'scope_block': scope_block,  # Block the workflow applies to. Empty means the task's current block.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'request_bist_configuration',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='dft_lead',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Open the handoff of scan and test-mode constraints into physical design.')  # Fleet-facing one-line skill description for planners.
def request_dft_physical_timing(
    objective: str = '',
    parent_task_id: str = '',
    scope_block: str = '',
    params: dict | None = None,
) -> dict:
    """Open the handoff of scan and test-mode constraints into physical design.

    Purpose:
        Skill ``request_dft_physical_timing`` for the DFT Lead agent (``dft_lead``). Owns DFT strategy: scan, ATPG, BIST, physical handoff, and DFT validation.
        Design-for-Test meaning: this skill participates in scan insertion, ATPG, testability analysis, MBIST/LBIST, test-mode timing, or DFT gate grading. It never silently waives fault coverage or drops a required fault model. This callable only builds a ``tool_observation`` payload;
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
    # Observation payload for skill 'request_dft_physical_timing' — keys align with config.yaml skill params.
    payload = {
        'objective': objective,  # Outcome the child workflow must achieve.
        'parent_task_id': parent_task_id,  # Task that owns this workflow.
        'scope_block': scope_block,  # Block the workflow applies to. Empty means the task's current block.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'request_dft_physical_timing',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='dft_lead',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Hand the candidate to the independent DFT validator.')  # Fleet-facing one-line skill description for planners.
def request_dft_gate(
    objective: str = '',
    parent_task_id: str = '',
    scope_block: str = '',
    params: dict | None = None,
) -> dict:
    """Hand the candidate to the independent DFT validator.

    Purpose:
        Skill ``request_dft_gate`` for the DFT Lead agent (``dft_lead``). Owns DFT strategy: scan, ATPG, BIST, physical handoff, and DFT validation.
        Design-for-Test meaning: this skill participates in scan insertion, ATPG, testability analysis, MBIST/LBIST, test-mode timing, or DFT gate grading. It never silently waives fault coverage or drops a required fault model. This callable only builds a ``tool_observation`` payload;
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
    # Observation payload for skill 'request_dft_gate' — keys align with config.yaml skill params.
    payload = {
        'objective': objective,  # Outcome the child workflow must achieve.
        'parent_task_id': parent_task_id,  # Task that owns this workflow.
        'scope_block': scope_block,  # Block the workflow applies to. Empty means the task's current block.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'request_dft_gate',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='dft_lead',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Read fault-coverage, test-time, area, power, and timing requirements.')  # Fleet-facing one-line skill description for planners.
def read_dft_requirements(
    candidate_ref: str = '',
    report_ref: str = '',
    corner: str = '',
    mode: str = '',
    params: dict | None = None,
) -> dict:
    """Read fault-coverage, test-time, area, power, and timing requirements.

    Purpose:
        Skill ``read_dft_requirements`` for the DFT Lead agent (``dft_lead``). Owns DFT strategy: scan, ATPG, BIST, physical handoff, and DFT validation.
        Design-for-Test meaning: this skill participates in scan insertion, ATPG, testability analysis, MBIST/LBIST, test-mode timing, or DFT gate grading. It never silently waives fault coverage or drops a required fault model. This callable only builds a ``tool_observation`` payload;
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
    # Observation payload for skill 'read_dft_requirements' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Candidate whose reports are read.
        'report_ref': report_ref,  # Artifact URI of the report. Empty reads the latest report for this candidate.
        'corner': corner,  # Corner filter. Empty reads every available corner.
        'mode': mode,  # Mode filter. Empty reads every available mode.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'read_dft_requirements',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='dft_lead',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Read scan, ATPG, BIST, and test-mode timing status.')  # Fleet-facing one-line skill description for planners.
def read_dft_status(
    candidate_ref: str = '',
    report_ref: str = '',
    corner: str = '',
    mode: str = '',
    params: dict | None = None,
) -> dict:
    """Read scan, ATPG, BIST, and test-mode timing status.

    Purpose:
        Skill ``read_dft_status`` for the DFT Lead agent (``dft_lead``). Owns DFT strategy: scan, ATPG, BIST, physical handoff, and DFT validation.
        Design-for-Test meaning: this skill participates in scan insertion, ATPG, testability analysis, MBIST/LBIST, test-mode timing, or DFT gate grading. It never silently waives fault coverage or drops a required fault model. This callable only builds a ``tool_observation`` payload;
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
    # Observation payload for skill 'read_dft_status' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Candidate whose reports are read.
        'report_ref': report_ref,  # Artifact URI of the report. Empty reads the latest report for this candidate.
        'corner': corner,  # Corner filter. Empty reads every available corner.
        'mode': mode,  # Mode filter. Empty reads every available mode.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'read_dft_status',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='dft_lead',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Read coverage by fault model.')  # Fleet-facing one-line skill description for planners.
def read_fault_coverage_summary(
    candidate_ref: str = '',
    report_ref: str = '',
    corner: str = '',
    mode: str = '',
    params: dict | None = None,
) -> dict:
    """Read coverage by fault model.

    Purpose:
        Skill ``read_fault_coverage_summary`` for the DFT Lead agent (``dft_lead``). Owns DFT strategy: scan, ATPG, BIST, physical handoff, and DFT validation.
        Design-for-Test meaning: this skill participates in scan insertion, ATPG, testability analysis, MBIST/LBIST, test-mode timing, or DFT gate grading. It never silently waives fault coverage or drops a required fault model. This callable only builds a ``tool_observation`` payload;
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
    # Observation payload for skill 'read_fault_coverage_summary' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Candidate whose reports are read.
        'report_ref': report_ref,  # Artifact URI of the report. Empty reads the latest report for this candidate.
        'corner': corner,  # Corner filter. Empty reads every available corner.
        'mode': mode,  # Mode filter. Empty reads every available mode.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'read_fault_coverage_summary',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='dft_lead',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Publish a coverage, test-time, or timing gap the strategy cannot close.')  # Fleet-facing one-line skill description for planners.
def report_dft_gap(
    summary: str = '',
    evidence_refs: str = '',
    severity: str = '',
    recommended_recipient: str = '',
    params: dict | None = None,
) -> dict:
    """Publish a coverage, test-time, or timing gap the strategy cannot close.

    Purpose:
        Skill ``report_dft_gap`` for the DFT Lead agent (``dft_lead``). Owns DFT strategy: scan, ATPG, BIST, physical handoff, and DFT validation.
        Design-for-Test meaning: this skill participates in scan insertion, ATPG, testability analysis, MBIST/LBIST, test-mode timing, or DFT gate grading. It never silently waives fault coverage or drops a required fault model. This callable only builds a ``tool_observation`` payload;
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
    # Observation payload for skill 'report_dft_gap' — keys align with config.yaml skill params.
    payload = {
        'summary': summary,  # One-sentence finding.
        'evidence_refs': evidence_refs,  # Comma-separated artifact URIs that support the finding.
        'severity': severity,  # low, medium, high, or critical.
        'recommended_recipient': recommended_recipient,  # Agent id that should act on the finding.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'report_dft_gap',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='dft_lead',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Route a testability finding to RTL or architecture.')  # Fleet-facing one-line skill description for planners.
def route_testability_finding(
    summary: str = '',
    evidence_refs: str = '',
    severity: str = '',
    recommended_recipient: str = '',
    params: dict | None = None,
) -> dict:
    """Route a testability finding to RTL or architecture.

    Purpose:
        Skill ``route_testability_finding`` for the DFT Lead agent (``dft_lead``). Owns DFT strategy: scan, ATPG, BIST, physical handoff, and DFT validation.
        Design-for-Test meaning: this skill participates in scan insertion, ATPG, testability analysis, MBIST/LBIST, test-mode timing, or DFT gate grading. It never silently waives fault coverage or drops a required fault model. This callable only builds a ``tool_observation`` payload;
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
    # Observation payload for skill 'route_testability_finding' — keys align with config.yaml skill params.
    payload = {
        'summary': summary,  # One-sentence finding.
        'evidence_refs': evidence_refs,  # Comma-separated artifact URIs that support the finding.
        'severity': severity,  # low, medium, high, or critical.
        'recommended_recipient': recommended_recipient,  # Agent id that should act on the finding.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'route_testability_finding',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='dft_lead',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Record a change in fault model, compression, or pattern budget.')  # Fleet-facing one-line skill description for planners.
def record_dft_strategy_change(
    summary: str = '',
    evidence_refs: str = '',
    severity: str = '',
    recommended_recipient: str = '',
    params: dict | None = None,
) -> dict:
    """Record a change in fault model, compression, or pattern budget.

    Purpose:
        Skill ``record_dft_strategy_change`` for the DFT Lead agent (``dft_lead``). Owns DFT strategy: scan, ATPG, BIST, physical handoff, and DFT validation.
        Design-for-Test meaning: this skill participates in scan insertion, ATPG, testability analysis, MBIST/LBIST, test-mode timing, or DFT gate grading. It never silently waives fault coverage or drops a required fault model. This callable only builds a ``tool_observation`` payload;
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
    # Observation payload for skill 'record_dft_strategy_change' — keys align with config.yaml skill params.
    payload = {
        'summary': summary,  # One-sentence finding.
        'evidence_refs': evidence_refs,  # Comma-separated artifact URIs that support the finding.
        'severity': severity,  # low, medium, high, or critical.
        'recommended_recipient': recommended_recipient,  # Agent id that should act on the finding.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'record_dft_strategy_change',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='dft_lead',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Ask a human to accept or reject a coverage miss. This agent cannot waive it.')  # Fleet-facing one-line skill description for planners.
def request_dft_coverage_decision(
    decision: str = '',
    options: str = '',
    evidence_refs: str = '',
    deadline: str = '',
    params: dict | None = None,
) -> dict:
    """Ask a human to accept or reject a coverage miss. This agent cannot waive it.

    Purpose:
        Skill ``request_dft_coverage_decision`` for the DFT Lead agent (``dft_lead``). Owns DFT strategy: scan, ATPG, BIST, physical handoff, and DFT validation.
        Design-for-Test meaning: this skill participates in scan insertion, ATPG, testability analysis, MBIST/LBIST, test-mode timing, or DFT gate grading. It never silently waives fault coverage or drops a required fault model. This callable only builds a ``tool_observation`` payload;
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
    # Observation payload for skill 'request_dft_coverage_decision' — keys align with config.yaml skill params.
    payload = {
        'decision': decision,  # The choice a human must make.
        'options': options,  # Comma-separated feasible options.
        'evidence_refs': evidence_refs,  # Comma-separated artifact URIs that support the finding.
        'deadline': deadline,  # ISO-8601 time after which the decision blocks the schedule.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'request_dft_coverage_decision',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='dft_lead',  # Provenance: which specialist emitted this observation.
    )
