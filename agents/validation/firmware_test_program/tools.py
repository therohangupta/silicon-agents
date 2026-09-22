"""Tool callables for the Firmware / Test Program agent (firmware_test_program).

Drafts boot, diagnostics, and ATE/characterization test programs.

Each function below is the stable operation contract advertised in
``config.yaml`` under ``skills``. A framework adapter (DFT tool, ATPG engine,
MBIST compiler, lab instrument bridge, ATE, etc.) performs the real work.
Until that adapter is bound, ``tool_observation`` returns a structured
``not_run`` result and does **not** invoke OpenROAD, Yosys, OpenSTA, a licensed
DFT/ATE tool, a simulator, or a physical instrument.

This module is imported when a skill is dispatched. Process bootstrap lives in
``server.py``; fleet metadata and param schemas live in ``config.yaml``.

Module lineage: Tool callables for the Firmware / Test Program agent (firmware_test_program).
"""

from __future__ import annotations  # Allow modern typing constructs in skill signatures.

from packages.agent_sdk import tool  # Decorator that registers the callable as an agent skill.
from domains.eda.eda import tool_observation  # Builds the not_run / observation envelope for adapters.


@tool(description='Write one bounded firmware or diagnostic change.')  # Fleet-facing one-line skill description for planners.
def draft_firmware_change(
    candidate_ref: str = '',
    baseline_ref: str = '',
    hypothesis: str = '',
    params: dict | None = None,
) -> dict:
    """Write one bounded firmware or diagnostic change.

    Purpose:
        Skill ``draft_firmware_change`` for the Firmware / Test Program agent (``firmware_test_program``). Drafts boot, diagnostics, and ATE/characterization test programs.
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
    # Observation payload for skill 'draft_firmware_change' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Isolated candidate to edit. Empty means create one from the baseline.
        'baseline_ref': baseline_ref,  # Immutable baseline the candidate must descend from.
        'hypothesis': hypothesis,  # The single change this edit is testing.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'draft_firmware_change',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='firmware_test_program',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Write or edit the boot sequence on the isolated branch.')  # Fleet-facing one-line skill description for planners.
def write_boot_flow(
    candidate_ref: str = '',
    baseline_ref: str = '',
    hypothesis: str = '',
    params: dict | None = None,
) -> dict:
    """Write or edit the boot sequence on the isolated branch.

    Purpose:
        Skill ``write_boot_flow`` for the Firmware / Test Program agent (``firmware_test_program``). Drafts boot, diagnostics, and ATE/characterization test programs.
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
    # Observation payload for skill 'write_boot_flow' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Isolated candidate to edit. Empty means create one from the baseline.
        'baseline_ref': baseline_ref,  # Immutable baseline the candidate must descend from.
        'hypothesis': hypothesis,  # The single change this edit is testing.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'write_boot_flow',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='firmware_test_program',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Write one diagnostic that exercises a named block.')  # Fleet-facing one-line skill description for planners.
def write_diagnostic(
    candidate_ref: str = '',
    baseline_ref: str = '',
    hypothesis: str = '',
    block: str = '',
    params: dict | None = None,
) -> dict:
    """Write one diagnostic that exercises a named block.

    Purpose:
        Skill ``write_diagnostic`` for the Firmware / Test Program agent (``firmware_test_program``). Drafts boot, diagnostics, and ATE/characterization test programs.
        Silicon-validation meaning: this skill participates in bring-up, lab procedure, instrument control, firmware/test programs, telemetry analysis, characterization, failure correlation, or errata drafting under approved safety bounds. This callable only builds a ``tool_observation`` payload;
        heavy EDA or bench work happens in a bound adapter.

    Args:
        candidate_ref: Isolated candidate to edit. Empty means create one from the baseline. Empty may mean latest candidate for the adapter.
        baseline_ref: Immutable baseline the candidate must descend from. Empty means no explicit baseline pin.
        hypothesis: The single change this edit is testing. Empty means request a fresh ranking.
        block: Block the diagnostic exercises. Empty means the task's current block.
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
    # Observation payload for skill 'write_diagnostic' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Isolated candidate to edit. Empty means create one from the baseline.
        'baseline_ref': baseline_ref,  # Immutable baseline the candidate must descend from.
        'hypothesis': hypothesis,  # The single change this edit is testing.
        'block': block,  # Block the diagnostic exercises.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'write_diagnostic',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='firmware_test_program',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Write a characterization or production test program.')  # Fleet-facing one-line skill description for planners.
def draft_test_program(
    candidate_ref: str = '',
    baseline_ref: str = '',
    hypothesis: str = '',
    params: dict | None = None,
) -> dict:
    """Write a characterization or production test program.

    Purpose:
        Skill ``draft_test_program`` for the Firmware / Test Program agent (``firmware_test_program``). Drafts boot, diagnostics, and ATE/characterization test programs.
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
    # Observation payload for skill 'draft_test_program' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Isolated candidate to edit. Empty means create one from the baseline.
        'baseline_ref': baseline_ref,  # Immutable baseline the candidate must descend from.
        'hypothesis': hypothesis,  # The single change this edit is testing.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'draft_test_program',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='firmware_test_program',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Write pass limits copied from the approved specification. This agent cannot widen them.')  # Fleet-facing one-line skill description for planners.
def write_test_limits(
    candidate_ref: str = '',
    baseline_ref: str = '',
    hypothesis: str = '',
    params: dict | None = None,
) -> dict:
    """Write pass limits copied from the approved specification. This agent cannot widen them.

    Purpose:
        Skill ``write_test_limits`` for the Firmware / Test Program agent (``firmware_test_program``). Drafts boot, diagnostics, and ATE/characterization test programs.
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
    # Observation payload for skill 'write_test_limits' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Isolated candidate to edit. Empty means create one from the baseline.
        'baseline_ref': baseline_ref,  # Immutable baseline the candidate must descend from.
        'hypothesis': hypothesis,  # The single change this edit is testing.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'write_test_limits',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='firmware_test_program',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Write one pattern the test program applies.')  # Fleet-facing one-line skill description for planners.
def write_test_pattern(
    candidate_ref: str = '',
    baseline_ref: str = '',
    hypothesis: str = '',
    params: dict | None = None,
) -> dict:
    """Write one pattern the test program applies.

    Purpose:
        Skill ``write_test_pattern`` for the Firmware / Test Program agent (``firmware_test_program``). Drafts boot, diagnostics, and ATE/characterization test programs.
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
    # Observation payload for skill 'write_test_pattern' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Isolated candidate to edit. Empty means create one from the baseline.
        'baseline_ref': baseline_ref,  # Immutable baseline the candidate must descend from.
        'hypothesis': hypothesis,  # The single change this edit is testing.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'write_test_pattern',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='firmware_test_program',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Compile the firmware branch.')  # Fleet-facing one-line skill description for planners.
def compile_firmware(
    candidate_ref: str = '',
    baseline_ref: str = '',
    recipe: str = '',
    corner: str = '',
    mode: str = '',
    params: dict | None = None,
) -> dict:
    """Compile the firmware branch.

    Purpose:
        Skill ``compile_firmware`` for the Firmware / Test Program agent (``firmware_test_program``). Drafts boot, diagnostics, and ATE/characterization test programs.
        Silicon-validation meaning: this skill participates in bring-up, lab procedure, instrument control, firmware/test programs, telemetry analysis, characterization, failure correlation, or errata drafting under approved safety bounds. This callable only builds a ``tool_observation`` payload;
        heavy EDA or bench work happens in a bound adapter.

    Args:
        candidate_ref: Isolated candidate to edit. Empty means create one from the baseline. Empty may mean latest candidate for the adapter.
        baseline_ref: Immutable baseline the candidate must descend from. Empty means no explicit baseline pin.
        recipe: Versioned tool recipe. The adapter rejects an unknown recipe. Empty uses the flow default recipe.
        corner: PVT corner. Empty when the job is not corner-specific. Empty reads every available corner.
        mode: Functional or analysis mode. Empty when the job is not mode-specific. Empty reads every available mode.
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
    # Observation payload for skill 'compile_firmware' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Isolated candidate to edit. Empty means create one from the baseline.
        'baseline_ref': baseline_ref,  # Immutable baseline the candidate must descend from.
        'recipe': recipe,  # Versioned tool recipe. The adapter rejects an unknown recipe.
        'corner': corner,  # PVT corner. Empty when the job is not corner-specific.
        'mode': mode,  # Functional or analysis mode. Empty when the job is not mode-specific.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'compile_firmware',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='firmware_test_program',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Compile the test program.')  # Fleet-facing one-line skill description for planners.
def compile_test_program(
    candidate_ref: str = '',
    baseline_ref: str = '',
    recipe: str = '',
    corner: str = '',
    mode: str = '',
    params: dict | None = None,
) -> dict:
    """Compile the test program.

    Purpose:
        Skill ``compile_test_program`` for the Firmware / Test Program agent (``firmware_test_program``). Drafts boot, diagnostics, and ATE/characterization test programs.
        Silicon-validation meaning: this skill participates in bring-up, lab procedure, instrument control, firmware/test programs, telemetry analysis, characterization, failure correlation, or errata drafting under approved safety bounds. This callable only builds a ``tool_observation`` payload;
        heavy EDA or bench work happens in a bound adapter.

    Args:
        candidate_ref: Isolated candidate to edit. Empty means create one from the baseline. Empty may mean latest candidate for the adapter.
        baseline_ref: Immutable baseline the candidate must descend from. Empty means no explicit baseline pin.
        recipe: Versioned tool recipe. The adapter rejects an unknown recipe. Empty uses the flow default recipe.
        corner: PVT corner. Empty when the job is not corner-specific. Empty reads every available corner.
        mode: Functional or analysis mode. Empty when the job is not mode-specific. Empty reads every available mode.
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
    # Observation payload for skill 'compile_test_program' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Isolated candidate to edit. Empty means create one from the baseline.
        'baseline_ref': baseline_ref,  # Immutable baseline the candidate must descend from.
        'recipe': recipe,  # Versioned tool recipe. The adapter rejects an unknown recipe.
        'corner': corner,  # PVT corner. Empty when the job is not corner-specific.
        'mode': mode,  # Functional or analysis mode. Empty when the job is not mode-specific.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'compile_test_program',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='firmware_test_program',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Read the diff against the firmware baseline.')  # Fleet-facing one-line skill description for planners.
def read_firmware_diff(
    candidate_ref: str = '',
    report_ref: str = '',
    corner: str = '',
    mode: str = '',
    params: dict | None = None,
) -> dict:
    """Read the diff against the firmware baseline.

    Purpose:
        Skill ``read_firmware_diff`` for the Firmware / Test Program agent (``firmware_test_program``). Drafts boot, diagnostics, and ATE/characterization test programs.
        Silicon-validation meaning: this skill participates in bring-up, lab procedure, instrument control, firmware/test programs, telemetry analysis, characterization, failure correlation, or errata drafting under approved safety bounds. This callable only builds a ``tool_observation`` payload;
        heavy EDA or bench work happens in a bound adapter.

    Args:
        candidate_ref: Isolated candidate to edit. Empty means create one from the baseline. Empty may mean latest candidate for the adapter.
        report_ref: Artifact URI of the report. Empty reads the latest report for this candidate. Empty reads the latest report for the candidate.
        corner: PVT corner. Empty when the job is not corner-specific. Empty reads every available corner.
        mode: Functional or analysis mode. Empty when the job is not mode-specific. Empty reads every available mode.
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
    # Observation payload for skill 'read_firmware_diff' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Isolated candidate to edit. Empty means create one from the baseline.
        'report_ref': report_ref,  # Artifact URI of the report. Empty reads the latest report for this candidate.
        'corner': corner,  # PVT corner. Empty when the job is not corner-specific.
        'mode': mode,  # Functional or analysis mode. Empty when the job is not mode-specific.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'read_firmware_diff',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='firmware_test_program',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Publish a test program whose limits are looser than the approved specification.')  # Fleet-facing one-line skill description for planners.
def flag_limit_widening(
    summary: str = '',
    evidence_refs: str = '',
    severity: str = '',
    recommended_recipient: str = '',
    params: dict | None = None,
) -> dict:
    """Publish a test program whose limits are looser than the approved specification.

    Purpose:
        Skill ``flag_limit_widening`` for the Firmware / Test Program agent (``firmware_test_program``). Drafts boot, diagnostics, and ATE/characterization test programs.
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
    # Observation payload for skill 'flag_limit_widening' — keys align with config.yaml skill params.
    payload = {
        'summary': summary,  # One-sentence finding.
        'evidence_refs': evidence_refs,  # Comma-separated artifact URIs that support the finding.
        'severity': severity,  # low, medium, high, or critical.
        'recommended_recipient': recommended_recipient,  # Agent id that should act on the finding.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'flag_limit_widening',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='firmware_test_program',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Publish a change that has no way to observe the block it touches.')  # Fleet-facing one-line skill description for planners.
def flag_firmware_without_diagnostic(
    summary: str = '',
    evidence_refs: str = '',
    severity: str = '',
    recommended_recipient: str = '',
    params: dict | None = None,
) -> dict:
    """Publish a change that has no way to observe the block it touches.

    Purpose:
        Skill ``flag_firmware_without_diagnostic`` for the Firmware / Test Program agent (``firmware_test_program``). Drafts boot, diagnostics, and ATE/characterization test programs.
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
    # Observation payload for skill 'flag_firmware_without_diagnostic' — keys align with config.yaml skill params.
    payload = {
        'summary': summary,  # One-sentence finding.
        'evidence_refs': evidence_refs,  # Comma-separated artifact URIs that support the finding.
        'severity': severity,  # low, medium, high, or critical.
        'recommended_recipient': recommended_recipient,  # Agent id that should act on the finding.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'flag_firmware_without_diagnostic',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='firmware_test_program',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Record the firmware revision, compiler, and test program.')  # Fleet-facing one-line skill description for planners.
def record_firmware_revision(
    summary: str = '',
    evidence_refs: str = '',
    severity: str = '',
    recommended_recipient: str = '',
    params: dict | None = None,
) -> dict:
    """Record the firmware revision, compiler, and test program.

    Purpose:
        Skill ``record_firmware_revision`` for the Firmware / Test Program agent (``firmware_test_program``). Drafts boot, diagnostics, and ATE/characterization test programs.
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
    # Observation payload for skill 'record_firmware_revision' — keys align with config.yaml skill params.
    payload = {
        'summary': summary,  # One-sentence finding.
        'evidence_refs': evidence_refs,  # Comma-separated artifact URIs that support the finding.
        'severity': severity,  # low, medium, high, or critical.
        'recommended_recipient': recommended_recipient,  # Agent id that should act on the finding.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'record_firmware_revision',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='firmware_test_program',  # Provenance: which specialist emitted this observation.
    )
