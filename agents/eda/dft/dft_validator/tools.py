"""Tool callables for the DFT Validator agent (dft_validator).

Independently grades scan, coverage, BIST, and test-mode DFT contracts.

Each function below is the stable operation contract advertised in
``config.yaml`` under ``skills``. A framework adapter (DFT tool, ATPG engine,
MBIST compiler, lab instrument bridge, ATE, etc.) performs the real work.
Until that adapter is bound, ``tool_observation`` returns a structured
``not_run`` result and does **not** invoke OpenROAD, Yosys, OpenSTA, a licensed
DFT/ATE tool, a simulator, or a physical instrument.

This module is imported when a skill is dispatched. Process bootstrap lives in
``server.py``; fleet metadata and param schemas live in ``config.yaml``.

Module lineage: Tool callables for the DFT Validator agent (dft_validator).
"""

from __future__ import annotations  # Allow modern typing constructs in skill signatures.

from packages.agent_sdk import tool  # Decorator that registers the callable as an agent skill.
from domains.eda.adapters import tool_observation  # Builds the not_run / observation envelope for adapters.


@tool(description='Read the exact candidate and pattern set being graded.')  # Fleet-facing one-line skill description for planners.
def read_dft_candidate_pin(
    candidate_ref: str = '',
    report_ref: str = '',
    corner: str = '',
    mode: str = '',
    params: dict | None = None,
) -> dict:
    """Read the exact candidate and pattern set being graded.

    Purpose:
        Skill ``read_dft_candidate_pin`` for the DFT Validator agent (``dft_validator``). Independently grades scan, coverage, BIST, and test-mode DFT contracts.
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
    # Observation payload for skill 'read_dft_candidate_pin' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Candidate whose reports are read.
        'report_ref': report_ref,  # Artifact URI of the report. Empty reads the latest report for this candidate.
        'corner': corner,  # Corner filter. Empty reads every available corner.
        'mode': mode,  # Mode filter. Empty reads every available mode.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'read_dft_candidate_pin',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='dft_validator',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Read scan, ATPG, BIST, and test-mode reports from primary artifacts.')  # Fleet-facing one-line skill description for planners.
def read_primary_dft_reports(
    candidate_ref: str = '',
    report_ref: str = '',
    corner: str = '',
    mode: str = '',
    params: dict | None = None,
) -> dict:
    """Read scan, ATPG, BIST, and test-mode reports from primary artifacts.

    Purpose:
        Skill ``read_primary_dft_reports`` for the DFT Validator agent (``dft_validator``). Independently grades scan, coverage, BIST, and test-mode DFT contracts.
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
    # Observation payload for skill 'read_primary_dft_reports' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Candidate whose reports are read.
        'report_ref': report_ref,  # Artifact URI of the report. Empty reads the latest report for this candidate.
        'corner': corner,  # Corner filter. Empty reads every available corner.
        'mode': mode,  # Mode filter. Empty reads every available mode.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'read_primary_dft_reports',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='dft_validator',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Check DFT tool versions and recipes against the frozen flow.')  # Fleet-facing one-line skill description for planners.
def check_dft_provenance(
    candidate_ref: str = '',
    report_ref: str = '',
    corner: str = '',
    mode: str = '',
    params: dict | None = None,
) -> dict:
    """Check DFT tool versions and recipes against the frozen flow.

    Purpose:
        Skill ``check_dft_provenance`` for the DFT Validator agent (``dft_validator``). Independently grades scan, coverage, BIST, and test-mode DFT contracts.
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
    # Observation payload for skill 'check_dft_provenance' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Candidate whose reports are read.
        'report_ref': report_ref,  # Artifact URI of the report. Empty reads the latest report for this candidate.
        'corner': corner,  # Corner filter. Empty reads every available corner.
        'mode': mode,  # Mode filter. Empty reads every available mode.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'check_dft_provenance',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='dft_validator',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Re-run scan connectivity and chain-integrity checks.')  # Fleet-facing one-line skill description for planners.
def reproduce_scan_integrity(
    candidate_ref: str = '',
    baseline_ref: str = '',
    recipe: str = '',
    corner: str = '',
    mode: str = '',
    params: dict | None = None,
) -> dict:
    """Re-run scan connectivity and chain-integrity checks.

    Purpose:
        Skill ``reproduce_scan_integrity`` for the DFT Validator agent (``dft_validator``). Independently grades scan, coverage, BIST, and test-mode DFT contracts.
        Design-for-Test meaning: this skill participates in scan insertion, ATPG, testability analysis, MBIST/LBIST, test-mode timing, or DFT gate grading. It never silently waives fault coverage or drops a required fault model. This callable only builds a ``tool_observation`` payload;
        heavy EDA or bench work happens in a bound adapter.

    Args:
        candidate_ref: Candidate whose reports are read. Empty may mean latest candidate for the adapter.
        baseline_ref: Baseline used when the job compares against a known result. Empty means no explicit baseline pin.
        recipe: Versioned tool recipe. The adapter rejects an unknown recipe. Empty uses the flow default recipe.
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
    # Observation payload for skill 'reproduce_scan_integrity' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Candidate whose reports are read.
        'baseline_ref': baseline_ref,  # Baseline used when the job compares against a known result.
        'recipe': recipe,  # Versioned tool recipe. The adapter rejects an unknown recipe.
        'corner': corner,  # Corner filter. Empty reads every available corner.
        'mode': mode,  # Mode filter. Empty reads every available mode.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'reproduce_scan_integrity',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='dft_validator',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Re-run fault coverage for every required model.')  # Fleet-facing one-line skill description for planners.
def reproduce_fault_coverage(
    candidate_ref: str = '',
    baseline_ref: str = '',
    recipe: str = '',
    corner: str = '',
    mode: str = '',
    params: dict | None = None,
) -> dict:
    """Re-run fault coverage for every required model.

    Purpose:
        Skill ``reproduce_fault_coverage`` for the DFT Validator agent (``dft_validator``). Independently grades scan, coverage, BIST, and test-mode DFT contracts.
        Design-for-Test meaning: this skill participates in scan insertion, ATPG, testability analysis, MBIST/LBIST, test-mode timing, or DFT gate grading. It never silently waives fault coverage or drops a required fault model. This callable only builds a ``tool_observation`` payload;
        heavy EDA or bench work happens in a bound adapter.

    Args:
        candidate_ref: Candidate whose reports are read. Empty may mean latest candidate for the adapter.
        baseline_ref: Baseline used when the job compares against a known result. Empty means no explicit baseline pin.
        recipe: Versioned tool recipe. The adapter rejects an unknown recipe. Empty uses the flow default recipe.
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
    # Observation payload for skill 'reproduce_fault_coverage' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Candidate whose reports are read.
        'baseline_ref': baseline_ref,  # Baseline used when the job compares against a known result.
        'recipe': recipe,  # Versioned tool recipe. The adapter rejects an unknown recipe.
        'corner': corner,  # Corner filter. Empty reads every available corner.
        'mode': mode,  # Mode filter. Empty reads every available mode.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'reproduce_fault_coverage',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='dft_validator',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Re-run MBIST and LBIST integration checks.')  # Fleet-facing one-line skill description for planners.
def reproduce_bist_checks(
    candidate_ref: str = '',
    baseline_ref: str = '',
    recipe: str = '',
    corner: str = '',
    mode: str = '',
    params: dict | None = None,
) -> dict:
    """Re-run MBIST and LBIST integration checks.

    Purpose:
        Skill ``reproduce_bist_checks`` for the DFT Validator agent (``dft_validator``). Independently grades scan, coverage, BIST, and test-mode DFT contracts.
        Design-for-Test meaning: this skill participates in scan insertion, ATPG, testability analysis, MBIST/LBIST, test-mode timing, or DFT gate grading. It never silently waives fault coverage or drops a required fault model. This callable only builds a ``tool_observation`` payload;
        heavy EDA or bench work happens in a bound adapter.

    Args:
        candidate_ref: Candidate whose reports are read. Empty may mean latest candidate for the adapter.
        baseline_ref: Baseline used when the job compares against a known result. Empty means no explicit baseline pin.
        recipe: Versioned tool recipe. The adapter rejects an unknown recipe. Empty uses the flow default recipe.
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
    # Observation payload for skill 'reproduce_bist_checks' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Candidate whose reports are read.
        'baseline_ref': baseline_ref,  # Baseline used when the job compares against a known result.
        'recipe': recipe,  # Versioned tool recipe. The adapter rejects an unknown recipe.
        'corner': corner,  # Corner filter. Empty reads every available corner.
        'mode': mode,  # Mode filter. Empty reads every available mode.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'reproduce_bist_checks',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='dft_validator',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Re-run test-mode timing on the physical database.')  # Fleet-facing one-line skill description for planners.
def reproduce_test_mode_timing(
    candidate_ref: str = '',
    baseline_ref: str = '',
    recipe: str = '',
    corner: str = '',
    mode: str = '',
    params: dict | None = None,
) -> dict:
    """Re-run test-mode timing on the physical database.

    Purpose:
        Skill ``reproduce_test_mode_timing`` for the DFT Validator agent (``dft_validator``). Independently grades scan, coverage, BIST, and test-mode DFT contracts.
        Design-for-Test meaning: this skill participates in scan insertion, ATPG, testability analysis, MBIST/LBIST, test-mode timing, or DFT gate grading. It never silently waives fault coverage or drops a required fault model. This callable only builds a ``tool_observation`` payload;
        heavy EDA or bench work happens in a bound adapter.

    Args:
        candidate_ref: Candidate whose reports are read. Empty may mean latest candidate for the adapter.
        baseline_ref: Baseline used when the job compares against a known result. Empty means no explicit baseline pin.
        recipe: Versioned tool recipe. The adapter rejects an unknown recipe. Empty uses the flow default recipe.
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
    # Observation payload for skill 'reproduce_test_mode_timing' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Candidate whose reports are read.
        'baseline_ref': baseline_ref,  # Baseline used when the job compares against a known result.
        'recipe': recipe,  # Versioned tool recipe. The adapter rejects an unknown recipe.
        'corner': corner,  # Corner filter. Empty reads every available corner.
        'mode': mode,  # Mode filter. Empty reads every available mode.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'reproduce_test_mode_timing',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='dft_validator',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Compare the DFT lead\'s summary with the primary reports.')  # Fleet-facing one-line skill description for planners.
def compare_dft_summary(
    candidate_ref: str = '',
    report_ref: str = '',
    corner: str = '',
    mode: str = '',
    params: dict | None = None,
) -> dict:
    """Compare the DFT lead's summary with the primary reports.

    Purpose:
        Skill ``compare_dft_summary`` for the DFT Validator agent (``dft_validator``). Independently grades scan, coverage, BIST, and test-mode DFT contracts.
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
    # Observation payload for skill 'compare_dft_summary' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Candidate whose reports are read.
        'report_ref': report_ref,  # Artifact URI of the report. Empty reads the latest report for this candidate.
        'corner': corner,  # Corner filter. Empty reads every available corner.
        'mode': mode,  # Mode filter. Empty reads every available mode.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'compare_dft_summary',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='dft_validator',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Check that every untestable fault has a traced cause.')  # Fleet-facing one-line skill description for planners.
def audit_dft_untestables(
    candidate_ref: str = '',
    report_ref: str = '',
    corner: str = '',
    mode: str = '',
    params: dict | None = None,
) -> dict:
    """Check that every untestable fault has a traced cause.

    Purpose:
        Skill ``audit_dft_untestables`` for the DFT Validator agent (``dft_validator``). Independently grades scan, coverage, BIST, and test-mode DFT contracts.
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
    # Observation payload for skill 'audit_dft_untestables' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Candidate whose reports are read.
        'report_ref': report_ref,  # Artifact URI of the report. Empty reads the latest report for this candidate.
        'corner': corner,  # Corner filter. Empty reads every available corner.
        'mode': mode,  # Mode filter. Empty reads every available mode.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'audit_dft_untestables',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='dft_validator',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Record whether the DFT contract passed.')  # Fleet-facing one-line skill description for planners.
def emit_dft_gate(
    candidate_ref: str = '',
    gate_id: str = '',
    check_refs: str = '',
    params: dict | None = None,
) -> dict:
    """Record whether the DFT contract passed.

    Purpose:
        Skill ``emit_dft_gate`` for the DFT Validator agent (``dft_validator``). Independently grades scan, coverage, BIST, and test-mode DFT contracts.
        Design-for-Test meaning: this skill participates in scan insertion, ATPG, testability analysis, MBIST/LBIST, test-mode timing, or DFT gate grading. It never silently waives fault coverage or drops a required fault model. This callable only builds a ``tool_observation`` payload;
        heavy EDA or bench work happens in a bound adapter.

    Args:
        candidate_ref: Candidate whose reports are read. Empty may mean latest candidate for the adapter.
        gate_id: Stable id for this gate decision. Empty means the current open gate.
        check_refs: Comma-separated primary report URIs the decision is based on. Empty means use the latest primary checks.
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
    # Observation payload for skill 'emit_dft_gate' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Candidate whose reports are read.
        'gate_id': gate_id,  # Stable id for this gate decision.
        'check_refs': check_refs,  # Comma-separated primary report URIs the decision is based on.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'emit_dft_gate',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='dft_validator',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Publish a place where the summary and the primary report disagree.')  # Fleet-facing one-line skill description for planners.
def publish_dft_gate_disagreement(
    summary: str = '',
    evidence_refs: str = '',
    severity: str = '',
    recommended_recipient: str = '',
    params: dict | None = None,
) -> dict:
    """Publish a place where the summary and the primary report disagree.

    Purpose:
        Skill ``publish_dft_gate_disagreement`` for the DFT Validator agent (``dft_validator``). Independently grades scan, coverage, BIST, and test-mode DFT contracts.
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
    # Observation payload for skill 'publish_dft_gate_disagreement' — keys align with config.yaml skill params.
    payload = {
        'summary': summary,  # One-sentence finding.
        'evidence_refs': evidence_refs,  # Comma-separated artifact URIs that support the finding.
        'severity': severity,  # low, medium, high, or critical.
        'recommended_recipient': recommended_recipient,  # Agent id that should act on the finding.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'publish_dft_gate_disagreement',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='dft_validator',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Publish a report or fault model required for the gate that is absent.')  # Fleet-facing one-line skill description for planners.
def publish_missing_dft_input(
    summary: str = '',
    evidence_refs: str = '',
    severity: str = '',
    recommended_recipient: str = '',
    params: dict | None = None,
) -> dict:
    """Publish a report or fault model required for the gate that is absent.

    Purpose:
        Skill ``publish_missing_dft_input`` for the DFT Validator agent (``dft_validator``). Independently grades scan, coverage, BIST, and test-mode DFT contracts.
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
    # Observation payload for skill 'publish_missing_dft_input' — keys align with config.yaml skill params.
    payload = {
        'summary': summary,  # One-sentence finding.
        'evidence_refs': evidence_refs,  # Comma-separated artifact URIs that support the finding.
        'severity': severity,  # low, medium, high, or critical.
        'recommended_recipient': recommended_recipient,  # Agent id that should act on the finding.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'publish_missing_dft_input',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='dft_validator',  # Provenance: which specialist emitted this observation.
    )
