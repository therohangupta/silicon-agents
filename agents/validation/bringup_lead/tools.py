"""Tool callables for the Bring-up Lead agent (bringup_lead).

Sequences post-silicon bring-up with safety bounds and human approvals.

Each function below is the stable operation contract advertised in
``config.yaml`` under ``skills``. A framework adapter (DFT tool, ATPG engine,
MBIST compiler, lab instrument bridge, ATE, etc.) performs the real work.
Until that adapter is bound, ``tool_observation`` returns a structured
``not_run`` result and does **not** invoke OpenROAD, Yosys, OpenSTA, a licensed
DFT/ATE tool, a simulator, or a physical instrument.

This module is imported when a skill is dispatched. Process bootstrap lives in
``server.py``; fleet metadata and param schemas live in ``config.yaml``.

Module lineage: Tool callables for the Bring-up Lead agent (bringup_lead).
"""

from __future__ import annotations  # Allow modern typing constructs in skill signatures.

from packages.agent_sdk import tool  # Decorator that registers the callable as an agent skill.
from domains.eda.eda import tool_observation  # Builds the not_run / observation envelope for adapters.


@tool(description='Emit the staged bring-up workflow with explicit approval points.')  # Fleet-facing one-line skill description for planners.
def plan_bringup(
    objective: str = '',
    parent_task_id: str = '',
    scope_block: str = '',
    params: dict | None = None,
) -> dict:
    """Emit the staged bring-up workflow with explicit approval points.

    Purpose:
        Skill ``plan_bringup`` for the Bring-up Lead agent (``bringup_lead``). Sequences post-silicon bring-up with safety bounds and human approvals.
        Silicon-validation meaning: this skill participates in bring-up, lab procedure, instrument control, firmware/test programs, telemetry analysis, characterization, failure correlation, or errata drafting under approved safety bounds. This callable only builds a ``tool_observation`` payload;
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
    # Observation payload for skill 'plan_bringup' — keys align with config.yaml skill params.
    payload = {
        'objective': objective,  # Outcome the child workflow must achieve.
        'parent_task_id': parent_task_id,  # Task that owns this workflow.
        'scope_block': scope_block,  # Block the workflow applies to. Empty means the task's current block.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'plan_bringup',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='bringup_lead',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Open a versioned procedure for the next stage.')  # Fleet-facing one-line skill description for planners.
def request_lab_procedure(
    objective: str = '',
    parent_task_id: str = '',
    scope_block: str = '',
    params: dict | None = None,
) -> dict:
    """Open a versioned procedure for the next stage.

    Purpose:
        Skill ``request_lab_procedure`` for the Bring-up Lead agent (``bringup_lead``). Sequences post-silicon bring-up with safety bounds and human approvals.
        Silicon-validation meaning: this skill participates in bring-up, lab procedure, instrument control, firmware/test programs, telemetry analysis, characterization, failure correlation, or errata drafting under approved safety bounds. This callable only builds a ``tool_observation`` payload;
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
    # Observation payload for skill 'request_lab_procedure' — keys align with config.yaml skill params.
    payload = {
        'objective': objective,  # Outcome the child workflow must achieve.
        'parent_task_id': parent_task_id,  # Task that owns this workflow.
        'scope_block': scope_block,  # Block the workflow applies to. Empty means the task's current block.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'request_lab_procedure',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='bringup_lead',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Open an instrument run of one approved procedure.')  # Fleet-facing one-line skill description for planners.
def request_instrument_run(
    objective: str = '',
    parent_task_id: str = '',
    scope_block: str = '',
    params: dict | None = None,
) -> dict:
    """Open an instrument run of one approved procedure.

    Purpose:
        Skill ``request_instrument_run`` for the Bring-up Lead agent (``bringup_lead``). Sequences post-silicon bring-up with safety bounds and human approvals.
        Silicon-validation meaning: this skill participates in bring-up, lab procedure, instrument control, firmware/test programs, telemetry analysis, characterization, failure correlation, or errata drafting under approved safety bounds. This callable only builds a ``tool_observation`` payload;
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
    # Observation payload for skill 'request_instrument_run' — keys align with config.yaml skill params.
    payload = {
        'objective': objective,  # Outcome the child workflow must achieve.
        'parent_task_id': parent_task_id,  # Task that owns this workflow.
        'scope_block': scope_block,  # Block the workflow applies to. Empty means the task's current block.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'request_instrument_run',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='bringup_lead',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Open a firmware or test-program change.')  # Fleet-facing one-line skill description for planners.
def request_firmware_change(
    objective: str = '',
    parent_task_id: str = '',
    scope_block: str = '',
    params: dict | None = None,
) -> dict:
    """Open a firmware or test-program change.

    Purpose:
        Skill ``request_firmware_change`` for the Bring-up Lead agent (``bringup_lead``). Sequences post-silicon bring-up with safety bounds and human approvals.
        Silicon-validation meaning: this skill participates in bring-up, lab procedure, instrument control, firmware/test programs, telemetry analysis, characterization, failure correlation, or errata drafting under approved safety bounds. This callable only builds a ``tool_observation`` payload;
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
    # Observation payload for skill 'request_firmware_change' — keys align with config.yaml skill params.
    payload = {
        'objective': objective,  # Outcome the child workflow must achieve.
        'parent_task_id': parent_task_id,  # Task that owns this workflow.
        'scope_block': scope_block,  # Block the workflow applies to. Empty means the task's current block.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'request_firmware_change',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='bringup_lead',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Open log and trace review for the latest run.')  # Fleet-facing one-line skill description for planners.
def request_telemetry_review(
    objective: str = '',
    parent_task_id: str = '',
    scope_block: str = '',
    params: dict | None = None,
) -> dict:
    """Open log and trace review for the latest run.

    Purpose:
        Skill ``request_telemetry_review`` for the Bring-up Lead agent (``bringup_lead``). Sequences post-silicon bring-up with safety bounds and human approvals.
        Silicon-validation meaning: this skill participates in bring-up, lab procedure, instrument control, firmware/test programs, telemetry analysis, characterization, failure correlation, or errata drafting under approved safety bounds. This callable only builds a ``tool_observation`` payload;
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
    # Observation payload for skill 'request_telemetry_review' — keys align with config.yaml skill params.
    payload = {
        'objective': objective,  # Outcome the child workflow must achieve.
        'parent_task_id': parent_task_id,  # Task that owns this workflow.
        'scope_block': scope_block,  # Block the workflow applies to. Empty means the task's current block.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'request_telemetry_review',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='bringup_lead',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Open a characterization sweep inside approved bounds.')  # Fleet-facing one-line skill description for planners.
def request_characterization_sweep(
    objective: str = '',
    parent_task_id: str = '',
    scope_block: str = '',
    params: dict | None = None,
) -> dict:
    """Open a characterization sweep inside approved bounds.

    Purpose:
        Skill ``request_characterization_sweep`` for the Bring-up Lead agent (``bringup_lead``). Sequences post-silicon bring-up with safety bounds and human approvals.
        Silicon-validation meaning: this skill participates in bring-up, lab procedure, instrument control, firmware/test programs, telemetry analysis, characterization, failure correlation, or errata drafting under approved safety bounds. This callable only builds a ``tool_observation`` payload;
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
    # Observation payload for skill 'request_characterization_sweep' — keys align with config.yaml skill params.
    payload = {
        'objective': objective,  # Outcome the child workflow must achieve.
        'parent_task_id': parent_task_id,  # Task that owns this workflow.
        'scope_block': scope_block,  # Block the workflow applies to. Empty means the task's current block.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'request_characterization_sweep',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='bringup_lead',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Open correlation of a silicon symptom with pre-silicon evidence.')  # Fleet-facing one-line skill description for planners.
def request_failure_correlation(
    objective: str = '',
    parent_task_id: str = '',
    scope_block: str = '',
    params: dict | None = None,
) -> dict:
    """Open correlation of a silicon symptom with pre-silicon evidence.

    Purpose:
        Skill ``request_failure_correlation`` for the Bring-up Lead agent (``bringup_lead``). Sequences post-silicon bring-up with safety bounds and human approvals.
        Silicon-validation meaning: this skill participates in bring-up, lab procedure, instrument control, firmware/test programs, telemetry analysis, characterization, failure correlation, or errata drafting under approved safety bounds. This callable only builds a ``tool_observation`` payload;
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
    # Observation payload for skill 'request_failure_correlation' — keys align with config.yaml skill params.
    payload = {
        'objective': objective,  # Outcome the child workflow must achieve.
        'parent_task_id': parent_task_id,  # Task that owns this workflow.
        'scope_block': scope_block,  # Block the workflow applies to. Empty means the task's current block.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'request_failure_correlation',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='bringup_lead',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Open an errata draft for a validated finding.')  # Fleet-facing one-line skill description for planners.
def request_errata_draft(
    objective: str = '',
    parent_task_id: str = '',
    scope_block: str = '',
    params: dict | None = None,
) -> dict:
    """Open an errata draft for a validated finding.

    Purpose:
        Skill ``request_errata_draft`` for the Bring-up Lead agent (``bringup_lead``). Sequences post-silicon bring-up with safety bounds and human approvals.
        Silicon-validation meaning: this skill participates in bring-up, lab procedure, instrument control, firmware/test programs, telemetry analysis, characterization, failure correlation, or errata drafting under approved safety bounds. This callable only builds a ``tool_observation`` payload;
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
    # Observation payload for skill 'request_errata_draft' — keys align with config.yaml skill params.
    payload = {
        'objective': objective,  # Outcome the child workflow must achieve.
        'parent_task_id': parent_task_id,  # Task that owns this workflow.
        'scope_block': scope_block,  # Block the workflow applies to. Empty means the task's current block.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'request_errata_draft',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='bringup_lead',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Read which stages have passed and which approval points are open.')  # Fleet-facing one-line skill description for planners.
def read_bringup_status(
    candidate_ref: str = '',
    report_ref: str = '',
    corner: str = '',
    mode: str = '',
    params: dict | None = None,
) -> dict:
    """Read which stages have passed and which approval points are open.

    Purpose:
        Skill ``read_bringup_status`` for the Bring-up Lead agent (``bringup_lead``). Sequences post-silicon bring-up with safety bounds and human approvals.
        Silicon-validation meaning: this skill participates in bring-up, lab procedure, instrument control, firmware/test programs, telemetry analysis, characterization, failure correlation, or errata drafting under approved safety bounds. This callable only builds a ``tool_observation`` payload;
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
    # Observation payload for skill 'read_bringup_status' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Candidate whose reports are read.
        'report_ref': report_ref,  # Artifact URI of the report. Empty reads the latest report for this candidate.
        'corner': corner,  # Corner filter. Empty reads every available corner.
        'mode': mode,  # Mode filter. Empty reads every available mode.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'read_bringup_status',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='bringup_lead',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Read the voltage, current, and temperature bounds in force.')  # Fleet-facing one-line skill description for planners.
def read_safety_bounds(
    candidate_ref: str = '',
    report_ref: str = '',
    corner: str = '',
    mode: str = '',
    params: dict | None = None,
) -> dict:
    """Read the voltage, current, and temperature bounds in force.

    Purpose:
        Skill ``read_safety_bounds`` for the Bring-up Lead agent (``bringup_lead``). Sequences post-silicon bring-up with safety bounds and human approvals.
        Silicon-validation meaning: this skill participates in bring-up, lab procedure, instrument control, firmware/test programs, telemetry analysis, characterization, failure correlation, or errata drafting under approved safety bounds. This callable only builds a ``tool_observation`` payload;
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
    # Observation payload for skill 'read_safety_bounds' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Candidate whose reports are read.
        'report_ref': report_ref,  # Artifact URI of the report. Empty reads the latest report for this candidate.
        'corner': corner,  # Corner filter. Empty reads every available corner.
        'mode': mode,  # Mode filter. Empty reads every available mode.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'read_safety_bounds',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='bringup_lead',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Record a human decision and the evidence it used.')  # Fleet-facing one-line skill description for planners.
def record_bringup_decision(
    summary: str = '',
    evidence_refs: str = '',
    severity: str = '',
    recommended_recipient: str = '',
    params: dict | None = None,
) -> dict:
    """Record a human decision and the evidence it used.

    Purpose:
        Skill ``record_bringup_decision`` for the Bring-up Lead agent (``bringup_lead``). Sequences post-silicon bring-up with safety bounds and human approvals.
        Silicon-validation meaning: this skill participates in bring-up, lab procedure, instrument control, firmware/test programs, telemetry analysis, characterization, failure correlation, or errata drafting under approved safety bounds. This callable only builds a ``tool_observation`` payload;
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
    # Observation payload for skill 'record_bringup_decision' — keys align with config.yaml skill params.
    payload = {
        'summary': summary,  # One-sentence finding.
        'evidence_refs': evidence_refs,  # Comma-separated artifact URIs that support the finding.
        'severity': severity,  # low, medium, high, or critical.
        'recommended_recipient': recommended_recipient,  # Agent id that should act on the finding.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'record_bringup_decision',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='bringup_lead',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Publish a stage that started before its safety check.')  # Fleet-facing one-line skill description for planners.
def flag_skipped_safety_check(
    summary: str = '',
    evidence_refs: str = '',
    severity: str = '',
    recommended_recipient: str = '',
    params: dict | None = None,
) -> dict:
    """Publish a stage that started before its safety check.

    Purpose:
        Skill ``flag_skipped_safety_check`` for the Bring-up Lead agent (``bringup_lead``). Sequences post-silicon bring-up with safety bounds and human approvals.
        Silicon-validation meaning: this skill participates in bring-up, lab procedure, instrument control, firmware/test programs, telemetry analysis, characterization, failure correlation, or errata drafting under approved safety bounds. This callable only builds a ``tool_observation`` payload;
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
    # Observation payload for skill 'flag_skipped_safety_check' — keys align with config.yaml skill params.
    payload = {
        'summary': summary,  # One-sentence finding.
        'evidence_refs': evidence_refs,  # Comma-separated artifact URIs that support the finding.
        'severity': severity,  # low, medium, high, or critical.
        'recommended_recipient': recommended_recipient,  # Agent id that should act on the finding.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'flag_skipped_safety_check',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='bringup_lead',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Escalate an irreversible or out-of-bounds lab choice.')  # Fleet-facing one-line skill description for planners.
def request_bringup_decision(
    decision: str = '',
    options: str = '',
    evidence_refs: str = '',
    deadline: str = '',
    params: dict | None = None,
) -> dict:
    """Escalate an irreversible or out-of-bounds lab choice.

    Purpose:
        Skill ``request_bringup_decision`` for the Bring-up Lead agent (``bringup_lead``). Sequences post-silicon bring-up with safety bounds and human approvals.
        Silicon-validation meaning: this skill participates in bring-up, lab procedure, instrument control, firmware/test programs, telemetry analysis, characterization, failure correlation, or errata drafting under approved safety bounds. This callable only builds a ``tool_observation`` payload;
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
    # Observation payload for skill 'request_bringup_decision' — keys align with config.yaml skill params.
    payload = {
        'decision': decision,  # The choice a human must make.
        'options': options,  # Comma-separated feasible options.
        'evidence_refs': evidence_refs,  # Comma-separated artifact URIs that support the finding.
        'deadline': deadline,  # ISO-8601 time after which the decision blocks the schedule.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'request_bringup_decision',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='bringup_lead',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Ask a human before a destructive or one-way lab action.')  # Fleet-facing one-line skill description for planners.
def request_destructive_action_decision(
    decision: str = '',
    options: str = '',
    evidence_refs: str = '',
    deadline: str = '',
    params: dict | None = None,
) -> dict:
    """Ask a human before a destructive or one-way lab action.

    Purpose:
        Skill ``request_destructive_action_decision`` for the Bring-up Lead agent (``bringup_lead``). Sequences post-silicon bring-up with safety bounds and human approvals.
        Silicon-validation meaning: this skill participates in bring-up, lab procedure, instrument control, firmware/test programs, telemetry analysis, characterization, failure correlation, or errata drafting under approved safety bounds. This callable only builds a ``tool_observation`` payload;
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
    # Observation payload for skill 'request_destructive_action_decision' — keys align with config.yaml skill params.
    payload = {
        'decision': decision,  # The choice a human must make.
        'options': options,  # Comma-separated feasible options.
        'evidence_refs': evidence_refs,  # Comma-separated artifact URIs that support the finding.
        'deadline': deadline,  # ISO-8601 time after which the decision blocks the schedule.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'request_destructive_action_decision',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='bringup_lead',  # Provenance: which specialist emitted this observation.
    )
