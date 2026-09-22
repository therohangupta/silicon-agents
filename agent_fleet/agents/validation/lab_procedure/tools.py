"""Tool callables for the Lab Procedure agent (lab_procedure).

Authors versioned lab procedures with rollback and approval points.

Each function below is the stable operation contract advertised in
``config.yaml`` under ``skills``. A framework adapter (DFT tool, ATPG engine,
MBIST compiler, lab instrument bridge, ATE, etc.) performs the real work.
Until that adapter is bound, ``tool_observation`` returns a structured
``not_run`` result and does **not** invoke OpenROAD, Yosys, OpenSTA, a licensed
DFT/ATE tool, a simulator, or a physical instrument.

This module is imported when a skill is dispatched. Process bootstrap lives in
``server.py``; fleet metadata and param schemas live in ``config.yaml``.

Module lineage: Tool callables for the Lab Procedure agent (lab_procedure).
"""

from __future__ import annotations  # Allow modern typing constructs in skill signatures.

from packages.agent_sdk import tool  # Decorator that registers the callable as an agent skill.
from domains.eda.eda import tool_observation  # Builds the not_run / observation envelope for adapters.


@tool(description='Write prerequisites, steps, expected observations, and rollback.')  # Fleet-facing one-line skill description for planners.
def draft_lab_procedure(
    candidate_ref: str = '',
    baseline_ref: str = '',
    hypothesis: str = '',
    params: dict | None = None,
) -> dict:
    """Write prerequisites, steps, expected observations, and rollback.

    Purpose:
        Skill ``draft_lab_procedure`` for the Lab Procedure agent (``lab_procedure``). Authors versioned lab procedures with rollback and approval points.
        Silicon-validation meaning: this skill participates in bring-up, lab procedure, instrument control, firmware/test programs, telemetry analysis, characterization, failure correlation, or errata drafting under approved safety bounds. This callable only builds a ``tool_observation`` payload;
        heavy EDA or bench work happens in a bound adapter.

    Args:
        candidate_ref: Isolated candidate to edit. Empty means create one from the baseline. Empty may mean latest candidate for the adapter.
        baseline_ref: Immutable baseline the candidate must descend from. Empty means no explicit baseline pin.
        hypothesis: The single change this edit is testing. Empty means request a fresh ranking.
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
    # Observation payload for skill 'draft_lab_procedure' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Isolated candidate to edit. Empty means create one from the baseline.
        'baseline_ref': baseline_ref,  # Immutable baseline the candidate must descend from.
        'hypothesis': hypothesis,  # The single change this edit is testing.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'draft_lab_procedure',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='lab_procedure',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Write the setup that must be true before the first step.')  # Fleet-facing one-line skill description for planners.
def write_procedure_prerequisites(
    candidate_ref: str = '',
    baseline_ref: str = '',
    hypothesis: str = '',
    params: dict | None = None,
) -> dict:
    """Write the setup that must be true before the first step.

    Purpose:
        Skill ``write_procedure_prerequisites`` for the Lab Procedure agent (``lab_procedure``). Authors versioned lab procedures with rollback and approval points.
        Silicon-validation meaning: this skill participates in bring-up, lab procedure, instrument control, firmware/test programs, telemetry analysis, characterization, failure correlation, or errata drafting under approved safety bounds. This callable only builds a ``tool_observation`` payload;
        heavy EDA or bench work happens in a bound adapter.

    Args:
        candidate_ref: Isolated candidate to edit. Empty means create one from the baseline. Empty may mean latest candidate for the adapter.
        baseline_ref: Immutable baseline the candidate must descend from. Empty means no explicit baseline pin.
        hypothesis: The single change this edit is testing. Empty means request a fresh ranking.
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
    # Observation payload for skill 'write_procedure_prerequisites' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Isolated candidate to edit. Empty means create one from the baseline.
        'baseline_ref': baseline_ref,  # Immutable baseline the candidate must descend from.
        'hypothesis': hypothesis,  # The single change this edit is testing.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'write_procedure_prerequisites',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='lab_procedure',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Write voltage, current, and temperature bounds. Bounds may only be copied from an approved limit.')  # Fleet-facing one-line skill description for planners.
def write_safe_operating_bounds(
    candidate_ref: str = '',
    baseline_ref: str = '',
    hypothesis: str = '',
    params: dict | None = None,
) -> dict:
    """Write voltage, current, and temperature bounds. Bounds may only be copied from an approved limit.

    Purpose:
        Skill ``write_safe_operating_bounds`` for the Lab Procedure agent (``lab_procedure``). Authors versioned lab procedures with rollback and approval points.
        Silicon-validation meaning: this skill participates in bring-up, lab procedure, instrument control, firmware/test programs, telemetry analysis, characterization, failure correlation, or errata drafting under approved safety bounds. This callable only builds a ``tool_observation`` payload;
        heavy EDA or bench work happens in a bound adapter.

    Args:
        candidate_ref: Isolated candidate to edit. Empty means create one from the baseline. Empty may mean latest candidate for the adapter.
        baseline_ref: Immutable baseline the candidate must descend from. Empty means no explicit baseline pin.
        hypothesis: The single change this edit is testing. Empty means request a fresh ranking.
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
    # Observation payload for skill 'write_safe_operating_bounds' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Isolated candidate to edit. Empty means create one from the baseline.
        'baseline_ref': baseline_ref,  # Immutable baseline the candidate must descend from.
        'hypothesis': hypothesis,  # The single change this edit is testing.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'write_safe_operating_bounds',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='lab_procedure',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Write the measurements that mean the step passed.')  # Fleet-facing one-line skill description for planners.
def write_expected_observations(
    candidate_ref: str = '',
    baseline_ref: str = '',
    hypothesis: str = '',
    params: dict | None = None,
) -> dict:
    """Write the measurements that mean the step passed.

    Purpose:
        Skill ``write_expected_observations`` for the Lab Procedure agent (``lab_procedure``). Authors versioned lab procedures with rollback and approval points.
        Silicon-validation meaning: this skill participates in bring-up, lab procedure, instrument control, firmware/test programs, telemetry analysis, characterization, failure correlation, or errata drafting under approved safety bounds. This callable only builds a ``tool_observation`` payload;
        heavy EDA or bench work happens in a bound adapter.

    Args:
        candidate_ref: Isolated candidate to edit. Empty means create one from the baseline. Empty may mean latest candidate for the adapter.
        baseline_ref: Immutable baseline the candidate must descend from. Empty means no explicit baseline pin.
        hypothesis: The single change this edit is testing. Empty means request a fresh ranking.
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
    # Observation payload for skill 'write_expected_observations' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Isolated candidate to edit. Empty means create one from the baseline.
        'baseline_ref': baseline_ref,  # Immutable baseline the candidate must descend from.
        'hypothesis': hypothesis,  # The single change this edit is testing.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'write_expected_observations',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='lab_procedure',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Write how to return the bench to a safe state.')  # Fleet-facing one-line skill description for planners.
def write_rollback_steps(
    candidate_ref: str = '',
    baseline_ref: str = '',
    hypothesis: str = '',
    params: dict | None = None,
) -> dict:
    """Write how to return the bench to a safe state.

    Purpose:
        Skill ``write_rollback_steps`` for the Lab Procedure agent (``lab_procedure``). Authors versioned lab procedures with rollback and approval points.
        Silicon-validation meaning: this skill participates in bring-up, lab procedure, instrument control, firmware/test programs, telemetry analysis, characterization, failure correlation, or errata drafting under approved safety bounds. This callable only builds a ``tool_observation`` payload;
        heavy EDA or bench work happens in a bound adapter.

    Args:
        candidate_ref: Isolated candidate to edit. Empty means create one from the baseline. Empty may mean latest candidate for the adapter.
        baseline_ref: Immutable baseline the candidate must descend from. Empty means no explicit baseline pin.
        hypothesis: The single change this edit is testing. Empty means request a fresh ranking.
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
    # Observation payload for skill 'write_rollback_steps' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Isolated candidate to edit. Empty means create one from the baseline.
        'baseline_ref': baseline_ref,  # Immutable baseline the candidate must descend from.
        'hypothesis': hypothesis,  # The single change this edit is testing.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'write_rollback_steps',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='lab_procedure',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Mark the steps that require a human before they run.')  # Fleet-facing one-line skill description for planners.
def write_approval_points(
    candidate_ref: str = '',
    baseline_ref: str = '',
    hypothesis: str = '',
    params: dict | None = None,
) -> dict:
    """Mark the steps that require a human before they run.

    Purpose:
        Skill ``write_approval_points`` for the Lab Procedure agent (``lab_procedure``). Authors versioned lab procedures with rollback and approval points.
        Silicon-validation meaning: this skill participates in bring-up, lab procedure, instrument control, firmware/test programs, telemetry analysis, characterization, failure correlation, or errata drafting under approved safety bounds. This callable only builds a ``tool_observation`` payload;
        heavy EDA or bench work happens in a bound adapter.

    Args:
        candidate_ref: Isolated candidate to edit. Empty means create one from the baseline. Empty may mean latest candidate for the adapter.
        baseline_ref: Immutable baseline the candidate must descend from. Empty means no explicit baseline pin.
        hypothesis: The single change this edit is testing. Empty means request a fresh ranking.
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
    # Observation payload for skill 'write_approval_points' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Isolated candidate to edit. Empty means create one from the baseline.
        'baseline_ref': baseline_ref,  # Immutable baseline the candidate must descend from.
        'hypothesis': hypothesis,  # The single change this edit is testing.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'write_approval_points',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='lab_procedure',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Edit a draft that has not been approved.')  # Fleet-facing one-line skill description for planners.
def revise_procedure_draft(
    candidate_ref: str = '',
    baseline_ref: str = '',
    hypothesis: str = '',
    params: dict | None = None,
) -> dict:
    """Edit a draft that has not been approved.

    Purpose:
        Skill ``revise_procedure_draft`` for the Lab Procedure agent (``lab_procedure``). Authors versioned lab procedures with rollback and approval points.
        Silicon-validation meaning: this skill participates in bring-up, lab procedure, instrument control, firmware/test programs, telemetry analysis, characterization, failure correlation, or errata drafting under approved safety bounds. This callable only builds a ``tool_observation`` payload;
        heavy EDA or bench work happens in a bound adapter.

    Args:
        candidate_ref: Isolated candidate to edit. Empty means create one from the baseline. Empty may mean latest candidate for the adapter.
        baseline_ref: Immutable baseline the candidate must descend from. Empty means no explicit baseline pin.
        hypothesis: The single change this edit is testing. Empty means request a fresh ranking.
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
    # Observation payload for skill 'revise_procedure_draft' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Isolated candidate to edit. Empty means create one from the baseline.
        'baseline_ref': baseline_ref,  # Immutable baseline the candidate must descend from.
        'hypothesis': hypothesis,  # The single change this edit is testing.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'revise_procedure_draft',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='lab_procedure',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Read the bring-up intent this procedure implements.')  # Fleet-facing one-line skill description for planners.
def read_bringup_intent(
    candidate_ref: str = '',
    report_ref: str = '',
    corner: str = '',
    mode: str = '',
    params: dict | None = None,
) -> dict:
    """Read the bring-up intent this procedure implements.

    Purpose:
        Skill ``read_bringup_intent`` for the Lab Procedure agent (``lab_procedure``). Authors versioned lab procedures with rollback and approval points.
        Silicon-validation meaning: this skill participates in bring-up, lab procedure, instrument control, firmware/test programs, telemetry analysis, characterization, failure correlation, or errata drafting under approved safety bounds. This callable only builds a ``tool_observation`` payload;
        heavy EDA or bench work happens in a bound adapter.

    Args:
        candidate_ref: Isolated candidate to edit. Empty means create one from the baseline. Empty may mean latest candidate for the adapter.
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
    # Observation payload for skill 'read_bringup_intent' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Isolated candidate to edit. Empty means create one from the baseline.
        'report_ref': report_ref,  # Artifact URI of the report. Empty reads the latest report for this candidate.
        'corner': corner,  # Corner filter. Empty reads every available corner.
        'mode': mode,  # Mode filter. Empty reads every available mode.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'read_bringup_intent',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='lab_procedure',  # Provenance: which specialist emitted this observation.
    )


@tool(description='List the steps that require a human before they run.')  # Fleet-facing one-line skill description for planners.
def list_approval_points(
    candidate_ref: str = '',
    report_ref: str = '',
    corner: str = '',
    mode: str = '',
    params: dict | None = None,
) -> dict:
    """List the steps that require a human before they run.

    Purpose:
        Skill ``list_approval_points`` for the Lab Procedure agent (``lab_procedure``). Authors versioned lab procedures with rollback and approval points.
        Silicon-validation meaning: this skill participates in bring-up, lab procedure, instrument control, firmware/test programs, telemetry analysis, characterization, failure correlation, or errata drafting under approved safety bounds. This callable only builds a ``tool_observation`` payload;
        heavy EDA or bench work happens in a bound adapter.

    Args:
        candidate_ref: Isolated candidate to edit. Empty means create one from the baseline. Empty may mean latest candidate for the adapter.
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
    # Observation payload for skill 'list_approval_points' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Isolated candidate to edit. Empty means create one from the baseline.
        'report_ref': report_ref,  # Artifact URI of the report. Empty reads the latest report for this candidate.
        'corner': corner,  # Corner filter. Empty reads every available corner.
        'mode': mode,  # Mode filter. Empty reads every available mode.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'list_approval_points',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='lab_procedure',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Show what changed between two procedure revisions.')  # Fleet-facing one-line skill description for planners.
def diff_procedure_revisions(
    candidate_ref: str = '',
    report_ref: str = '',
    corner: str = '',
    mode: str = '',
    params: dict | None = None,
) -> dict:
    """Show what changed between two procedure revisions.

    Purpose:
        Skill ``diff_procedure_revisions`` for the Lab Procedure agent (``lab_procedure``). Authors versioned lab procedures with rollback and approval points.
        Silicon-validation meaning: this skill participates in bring-up, lab procedure, instrument control, firmware/test programs, telemetry analysis, characterization, failure correlation, or errata drafting under approved safety bounds. This callable only builds a ``tool_observation`` payload;
        heavy EDA or bench work happens in a bound adapter.

    Args:
        candidate_ref: Isolated candidate to edit. Empty means create one from the baseline. Empty may mean latest candidate for the adapter.
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
    # Observation payload for skill 'diff_procedure_revisions' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Isolated candidate to edit. Empty means create one from the baseline.
        'report_ref': report_ref,  # Artifact URI of the report. Empty reads the latest report for this candidate.
        'corner': corner,  # Corner filter. Empty reads every available corner.
        'mode': mode,  # Mode filter. Empty reads every available mode.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'diff_procedure_revisions',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='lab_procedure',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Publish a procedure with no rollback.')  # Fleet-facing one-line skill description for planners.
def flag_missing_rollback(
    summary: str = '',
    evidence_refs: str = '',
    severity: str = '',
    recommended_recipient: str = '',
    params: dict | None = None,
) -> dict:
    """Publish a procedure with no rollback.

    Purpose:
        Skill ``flag_missing_rollback`` for the Lab Procedure agent (``lab_procedure``). Authors versioned lab procedures with rollback and approval points.
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
    # Observation payload for skill 'flag_missing_rollback' — keys align with config.yaml skill params.
    payload = {
        'summary': summary,  # One-sentence finding.
        'evidence_refs': evidence_refs,  # Comma-separated artifact URIs that support the finding.
        'severity': severity,  # low, medium, high, or critical.
        'recommended_recipient': recommended_recipient,  # Agent id that should act on the finding.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'flag_missing_rollback',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='lab_procedure',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Publish a draft whose bounds exceed the approved limit.')  # Fleet-facing one-line skill description for planners.
def flag_widened_safety_bound(
    summary: str = '',
    evidence_refs: str = '',
    severity: str = '',
    recommended_recipient: str = '',
    params: dict | None = None,
) -> dict:
    """Publish a draft whose bounds exceed the approved limit.

    Purpose:
        Skill ``flag_widened_safety_bound`` for the Lab Procedure agent (``lab_procedure``). Authors versioned lab procedures with rollback and approval points.
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
    # Observation payload for skill 'flag_widened_safety_bound' — keys align with config.yaml skill params.
    payload = {
        'summary': summary,  # One-sentence finding.
        'evidence_refs': evidence_refs,  # Comma-separated artifact URIs that support the finding.
        'severity': severity,  # low, medium, high, or critical.
        'recommended_recipient': recommended_recipient,  # Agent id that should act on the finding.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'flag_widened_safety_bound',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='lab_procedure',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Record the procedure revision and the intent it traces to.')  # Fleet-facing one-line skill description for planners.
def record_procedure_version(
    summary: str = '',
    evidence_refs: str = '',
    severity: str = '',
    recommended_recipient: str = '',
    params: dict | None = None,
) -> dict:
    """Record the procedure revision and the intent it traces to.

    Purpose:
        Skill ``record_procedure_version`` for the Lab Procedure agent (``lab_procedure``). Authors versioned lab procedures with rollback and approval points.
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
    # Observation payload for skill 'record_procedure_version' — keys align with config.yaml skill params.
    payload = {
        'summary': summary,  # One-sentence finding.
        'evidence_refs': evidence_refs,  # Comma-separated artifact URIs that support the finding.
        'severity': severity,  # low, medium, high, or critical.
        'recommended_recipient': recommended_recipient,  # Agent id that should act on the finding.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'record_procedure_version',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='lab_procedure',  # Provenance: which specialist emitted this observation.
    )
