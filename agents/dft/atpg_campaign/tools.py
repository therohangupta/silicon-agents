"""Tool callables for the ATPG Campaign agent (atpg_campaign).

Generates and analyzes ATPG patterns across required fault models.

Each function below is the stable operation contract advertised in
``config.yaml`` under ``skills``. A framework adapter (DFT tool, ATPG engine,
MBIST compiler, lab instrument bridge, ATE, etc.) performs the real work.
Until that adapter is bound, ``tool_observation`` returns a structured
``not_run`` result and does **not** invoke OpenROAD, Yosys, OpenSTA, a licensed
DFT/ATE tool, a simulator, or a physical instrument.

This module is imported when a skill is dispatched. Process bootstrap lives in
``server.py``; fleet metadata and param schemas live in ``config.yaml``.

Module lineage: Tool callables for the ATPG Campaign agent (atpg_campaign).
"""

from __future__ import annotations  # Allow modern typing constructs in skill signatures.

from packages.agent_sdk import tool  # Decorator that registers the callable as an agent skill.
from domains.eda.eda import tool_observation  # Builds the not_run / observation envelope for adapters.


@tool(description='Write the fault models this campaign must cover. Do not omit a required model.')  # Fleet-facing one-line skill description for planners.
def write_fault_model_list(
    candidate_ref: str = '',
    baseline_ref: str = '',
    hypothesis: str = '',
    params: dict | None = None,
) -> dict:
    """Write the fault models this campaign must cover. Do not omit a required model.

    Purpose:
        Skill ``write_fault_model_list`` for the ATPG Campaign agent (``atpg_campaign``). Generates and analyzes ATPG patterns across required fault models.
        Design-for-Test meaning: this skill participates in scan insertion, ATPG, testability analysis, MBIST/LBIST, test-mode timing, or DFT gate grading. It never silently waives fault coverage or drops a required fault model. This callable only builds a ``tool_observation`` payload;
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
    # Observation payload for skill 'write_fault_model_list' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Isolated candidate to edit. Empty means create one from the baseline.
        'baseline_ref': baseline_ref,  # Immutable baseline the candidate must descend from.
        'hypothesis': hypothesis,  # The single change this edit is testing.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'write_fault_model_list',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='atpg_campaign',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Write the pattern-count and tester-time budget.')  # Fleet-facing one-line skill description for planners.
def write_pattern_budget(
    candidate_ref: str = '',
    baseline_ref: str = '',
    hypothesis: str = '',
    params: dict | None = None,
) -> dict:
    """Write the pattern-count and tester-time budget.

    Purpose:
        Skill ``write_pattern_budget`` for the ATPG Campaign agent (``atpg_campaign``). Generates and analyzes ATPG patterns across required fault models.
        Design-for-Test meaning: this skill participates in scan insertion, ATPG, testability analysis, MBIST/LBIST, test-mode timing, or DFT gate grading. It never silently waives fault coverage or drops a required fault model. This callable only builds a ``tool_observation`` payload;
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
    # Observation payload for skill 'write_pattern_budget' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Isolated candidate to edit. Empty means create one from the baseline.
        'baseline_ref': baseline_ref,  # Immutable baseline the candidate must descend from.
        'hypothesis': hypothesis,  # The single change this edit is testing.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'write_pattern_budget',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='atpg_campaign',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Generate stuck-at patterns.')  # Fleet-facing one-line skill description for planners.
def generate_stuck_at_patterns(
    candidate_ref: str = '',
    baseline_ref: str = '',
    recipe: str = '',
    corner: str = '',
    mode: str = '',
    params: dict | None = None,
) -> dict:
    """Generate stuck-at patterns.

    Purpose:
        Skill ``generate_stuck_at_patterns`` for the ATPG Campaign agent (``atpg_campaign``). Generates and analyzes ATPG patterns across required fault models.
        Design-for-Test meaning: this skill participates in scan insertion, ATPG, testability analysis, MBIST/LBIST, test-mode timing, or DFT gate grading. It never silently waives fault coverage or drops a required fault model. This callable only builds a ``tool_observation`` payload;
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
    # Observation payload for skill 'generate_stuck_at_patterns' — keys align with config.yaml skill params.
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
        'generate_stuck_at_patterns',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='atpg_campaign',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Generate transition-delay patterns.')  # Fleet-facing one-line skill description for planners.
def generate_transition_patterns(
    candidate_ref: str = '',
    baseline_ref: str = '',
    recipe: str = '',
    corner: str = '',
    mode: str = '',
    params: dict | None = None,
) -> dict:
    """Generate transition-delay patterns.

    Purpose:
        Skill ``generate_transition_patterns`` for the ATPG Campaign agent (``atpg_campaign``). Generates and analyzes ATPG patterns across required fault models.
        Design-for-Test meaning: this skill participates in scan insertion, ATPG, testability analysis, MBIST/LBIST, test-mode timing, or DFT gate grading. It never silently waives fault coverage or drops a required fault model. This callable only builds a ``tool_observation`` payload;
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
    # Observation payload for skill 'generate_transition_patterns' — keys align with config.yaml skill params.
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
        'generate_transition_patterns',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='atpg_campaign',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Generate path-delay patterns for the listed paths.')  # Fleet-facing one-line skill description for planners.
def generate_path_delay_patterns(
    candidate_ref: str = '',
    baseline_ref: str = '',
    recipe: str = '',
    corner: str = '',
    mode: str = '',
    params: dict | None = None,
) -> dict:
    """Generate path-delay patterns for the listed paths.

    Purpose:
        Skill ``generate_path_delay_patterns`` for the ATPG Campaign agent (``atpg_campaign``). Generates and analyzes ATPG patterns across required fault models.
        Design-for-Test meaning: this skill participates in scan insertion, ATPG, testability analysis, MBIST/LBIST, test-mode timing, or DFT gate grading. It never silently waives fault coverage or drops a required fault model. This callable only builds a ``tool_observation`` payload;
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
    # Observation payload for skill 'generate_path_delay_patterns' — keys align with config.yaml skill params.
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
        'generate_path_delay_patterns',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='atpg_campaign',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Generate IDDQ patterns when the contract requires them.')  # Fleet-facing one-line skill description for planners.
def generate_iddq_patterns(
    candidate_ref: str = '',
    baseline_ref: str = '',
    recipe: str = '',
    corner: str = '',
    mode: str = '',
    params: dict | None = None,
) -> dict:
    """Generate IDDQ patterns when the contract requires them.

    Purpose:
        Skill ``generate_iddq_patterns`` for the ATPG Campaign agent (``atpg_campaign``). Generates and analyzes ATPG patterns across required fault models.
        Design-for-Test meaning: this skill participates in scan insertion, ATPG, testability analysis, MBIST/LBIST, test-mode timing, or DFT gate grading. It never silently waives fault coverage or drops a required fault model. This callable only builds a ``tool_observation`` payload;
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
    # Observation payload for skill 'generate_iddq_patterns' — keys align with config.yaml skill params.
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
        'generate_iddq_patterns',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='atpg_campaign',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Read coverage, untestable faults, and aborted faults by model.')  # Fleet-facing one-line skill description for planners.
def read_fault_coverage(
    candidate_ref: str = '',
    report_ref: str = '',
    corner: str = '',
    mode: str = '',
    params: dict | None = None,
) -> dict:
    """Read coverage, untestable faults, and aborted faults by model.

    Purpose:
        Skill ``read_fault_coverage`` for the ATPG Campaign agent (``atpg_campaign``). Generates and analyzes ATPG patterns across required fault models.
        Design-for-Test meaning: this skill participates in scan insertion, ATPG, testability analysis, MBIST/LBIST, test-mode timing, or DFT gate grading. It never silently waives fault coverage or drops a required fault model. This callable only builds a ``tool_observation`` payload;
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
    # Observation payload for skill 'read_fault_coverage' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Isolated candidate to edit. Empty means create one from the baseline.
        'report_ref': report_ref,  # Artifact URI of the report. Empty reads the latest report for this candidate.
        'corner': corner,  # PVT corner. Empty when the job is not corner-specific.
        'mode': mode,  # Functional or analysis mode. Empty when the job is not mode-specific.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'read_fault_coverage',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='atpg_campaign',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Read pattern count and estimated tester time.')  # Fleet-facing one-line skill description for planners.
def read_pattern_count(
    candidate_ref: str = '',
    report_ref: str = '',
    corner: str = '',
    mode: str = '',
    params: dict | None = None,
) -> dict:
    """Read pattern count and estimated tester time.

    Purpose:
        Skill ``read_pattern_count`` for the ATPG Campaign agent (``atpg_campaign``). Generates and analyzes ATPG patterns across required fault models.
        Design-for-Test meaning: this skill participates in scan insertion, ATPG, testability analysis, MBIST/LBIST, test-mode timing, or DFT gate grading. It never silently waives fault coverage or drops a required fault model. This callable only builds a ``tool_observation`` payload;
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
    # Observation payload for skill 'read_pattern_count' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Isolated candidate to edit. Empty means create one from the baseline.
        'report_ref': report_ref,  # Artifact URI of the report. Empty reads the latest report for this candidate.
        'corner': corner,  # PVT corner. Empty when the job is not corner-specific.
        'mode': mode,  # Functional or analysis mode. Empty when the job is not mode-specific.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'read_pattern_count',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='atpg_campaign',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Read shift and capture power.')  # Fleet-facing one-line skill description for planners.
def read_test_power(
    candidate_ref: str = '',
    report_ref: str = '',
    corner: str = '',
    mode: str = '',
    params: dict | None = None,
) -> dict:
    """Read shift and capture power.

    Purpose:
        Skill ``read_test_power`` for the ATPG Campaign agent (``atpg_campaign``). Generates and analyzes ATPG patterns across required fault models.
        Design-for-Test meaning: this skill participates in scan insertion, ATPG, testability analysis, MBIST/LBIST, test-mode timing, or DFT gate grading. It never silently waives fault coverage or drops a required fault model. This callable only builds a ``tool_observation`` payload;
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
    # Observation payload for skill 'read_test_power' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Isolated candidate to edit. Empty means create one from the baseline.
        'report_ref': report_ref,  # Artifact URI of the report. Empty reads the latest report for this candidate.
        'corner': corner,  # PVT corner. Empty when the job is not corner-specific.
        'mode': mode,  # Functional or analysis mode. Empty when the job is not mode-specific.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'read_test_power',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='atpg_campaign',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Compare each fault model with its required coverage.')  # Fleet-facing one-line skill description for planners.
def compare_coverage_to_requirement(
    candidate_ref: str = '',
    report_ref: str = '',
    corner: str = '',
    mode: str = '',
    params: dict | None = None,
) -> dict:
    """Compare each fault model with its required coverage.

    Purpose:
        Skill ``compare_coverage_to_requirement`` for the ATPG Campaign agent (``atpg_campaign``). Generates and analyzes ATPG patterns across required fault models.
        Design-for-Test meaning: this skill participates in scan insertion, ATPG, testability analysis, MBIST/LBIST, test-mode timing, or DFT gate grading. It never silently waives fault coverage or drops a required fault model. This callable only builds a ``tool_observation`` payload;
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
    # Observation payload for skill 'compare_coverage_to_requirement' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Isolated candidate to edit. Empty means create one from the baseline.
        'report_ref': report_ref,  # Artifact URI of the report. Empty reads the latest report for this candidate.
        'corner': corner,  # PVT corner. Empty when the job is not corner-specific.
        'mode': mode,  # Functional or analysis mode. Empty when the job is not mode-specific.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'compare_coverage_to_requirement',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='atpg_campaign',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Publish coverage, pattern count, tester time, and test power.')  # Fleet-facing one-line skill description for planners.
def analyze_fault_coverage(
    summary: str = '',
    evidence_refs: str = '',
    severity: str = '',
    recommended_recipient: str = '',
    params: dict | None = None,
) -> dict:
    """Publish coverage, pattern count, tester time, and test power.

    Purpose:
        Skill ``analyze_fault_coverage`` for the ATPG Campaign agent (``atpg_campaign``). Generates and analyzes ATPG patterns across required fault models.
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
    # Observation payload for skill 'analyze_fault_coverage' — keys align with config.yaml skill params.
    payload = {
        'summary': summary,  # One-sentence finding.
        'evidence_refs': evidence_refs,  # Comma-separated artifact URIs that support the finding.
        'severity': severity,  # low, medium, high, or critical.
        'recommended_recipient': recommended_recipient,  # Agent id that should act on the finding.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'analyze_fault_coverage',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='atpg_campaign',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Publish a campaign that omitted a required fault model.')  # Fleet-facing one-line skill description for planners.
def flag_dropped_fault_model(
    summary: str = '',
    evidence_refs: str = '',
    severity: str = '',
    recommended_recipient: str = '',
    params: dict | None = None,
) -> dict:
    """Publish a campaign that omitted a required fault model.

    Purpose:
        Skill ``flag_dropped_fault_model`` for the ATPG Campaign agent (``atpg_campaign``). Generates and analyzes ATPG patterns across required fault models.
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
    # Observation payload for skill 'flag_dropped_fault_model' — keys align with config.yaml skill params.
    payload = {
        'summary': summary,  # One-sentence finding.
        'evidence_refs': evidence_refs,  # Comma-separated artifact URIs that support the finding.
        'severity': severity,  # low, medium, high, or critical.
        'recommended_recipient': recommended_recipient,  # Agent id that should act on the finding.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'flag_dropped_fault_model',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='atpg_campaign',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Publish shift or capture power above the budget.')  # Fleet-facing one-line skill description for planners.
def flag_test_power_over_budget(
    summary: str = '',
    evidence_refs: str = '',
    severity: str = '',
    recommended_recipient: str = '',
    params: dict | None = None,
) -> dict:
    """Publish shift or capture power above the budget.

    Purpose:
        Skill ``flag_test_power_over_budget`` for the ATPG Campaign agent (``atpg_campaign``). Generates and analyzes ATPG patterns across required fault models.
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
    # Observation payload for skill 'flag_test_power_over_budget' — keys align with config.yaml skill params.
    payload = {
        'summary': summary,  # One-sentence finding.
        'evidence_refs': evidence_refs,  # Comma-separated artifact URIs that support the finding.
        'severity': severity,  # low, medium, high, or critical.
        'recommended_recipient': recommended_recipient,  # Agent id that should act on the finding.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'flag_test_power_over_budget',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='atpg_campaign',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Record the ATPG tool, version, and fault-model settings.')  # Fleet-facing one-line skill description for planners.
def record_atpg_tool_version(
    summary: str = '',
    evidence_refs: str = '',
    severity: str = '',
    recommended_recipient: str = '',
    params: dict | None = None,
) -> dict:
    """Record the ATPG tool, version, and fault-model settings.

    Purpose:
        Skill ``record_atpg_tool_version`` for the ATPG Campaign agent (``atpg_campaign``). Generates and analyzes ATPG patterns across required fault models.
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
    # Observation payload for skill 'record_atpg_tool_version' — keys align with config.yaml skill params.
    payload = {
        'summary': summary,  # One-sentence finding.
        'evidence_refs': evidence_refs,  # Comma-separated artifact URIs that support the finding.
        'severity': severity,  # low, medium, high, or critical.
        'recommended_recipient': recommended_recipient,  # Agent id that should act on the finding.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'record_atpg_tool_version',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='atpg_campaign',  # Provenance: which specialist emitted this observation.
    )
