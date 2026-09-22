"""Tool callables for the MBIST/LBIST agent (mbist_lbist).

Configures memory/logic BIST controllers, algorithms, repair, and diagnostics.

Each function below is the stable operation contract advertised in
``config.yaml`` under ``skills``. A framework adapter (DFT tool, ATPG engine,
MBIST compiler, lab instrument bridge, ATE, etc.) performs the real work.
Until that adapter is bound, ``tool_observation`` returns a structured
``not_run`` result and does **not** invoke OpenROAD, Yosys, OpenSTA, a licensed
DFT/ATE tool, a simulator, or a physical instrument.

This module is imported when a skill is dispatched. Process bootstrap lives in
``server.py``; fleet metadata and param schemas live in ``config.yaml``.

Module lineage: Tool callables for the MBIST/LBIST agent (mbist_lbist).
"""

from __future__ import annotations  # Allow modern typing constructs in skill signatures.

from packages.agent_sdk import tool  # Decorator that registers the callable as an agent skill.
from domains.eda.eda import tool_observation  # Builds the not_run / observation envelope for adapters.


@tool(description='Configure the MBIST controller for the memories in scope.')  # Fleet-facing one-line skill description for planners.
def write_mbist_controller(
    candidate_ref: str = '',
    baseline_ref: str = '',
    hypothesis: str = '',
    params: dict | None = None,
) -> dict:
    """Configure the MBIST controller for the memories in scope.

    Purpose:
        Skill ``write_mbist_controller`` for the MBIST/LBIST agent (``mbist_lbist``). Configures memory/logic BIST controllers, algorithms, repair, and diagnostics.
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
    # Observation payload for skill 'write_mbist_controller' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Isolated candidate to edit. Empty means create one from the baseline.
        'baseline_ref': baseline_ref,  # Immutable baseline the candidate must descend from.
        'hypothesis': hypothesis,  # The single change this edit is testing.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'write_mbist_controller',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='mbist_lbist',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Select and write the March algorithm for each memory.')  # Fleet-facing one-line skill description for planners.
def write_mbist_algorithm(
    candidate_ref: str = '',
    baseline_ref: str = '',
    hypothesis: str = '',
    memory_id: str = '',
    params: dict | None = None,
) -> dict:
    """Select and write the March algorithm for each memory.

    Purpose:
        Skill ``write_mbist_algorithm`` for the MBIST/LBIST agent (``mbist_lbist``). Configures memory/logic BIST controllers, algorithms, repair, and diagnostics.
        Design-for-Test meaning: this skill participates in scan insertion, ATPG, testability analysis, MBIST/LBIST, test-mode timing, or DFT gate grading. It never silently waives fault coverage or drops a required fault model. This callable only builds a ``tool_observation`` payload;
        heavy EDA or bench work happens in a bound adapter.

    Args:
        candidate_ref: Isolated candidate to edit. Empty means create one from the baseline. Empty may mean latest candidate for the adapter.
        baseline_ref: Immutable baseline the candidate must descend from. Empty means no explicit baseline pin.
        hypothesis: The single change this edit is testing. Empty means request a fresh ranking.
        memory_id: Memory the algorithm targets. Empty means all memories in scope.
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
    # Observation payload for skill 'write_mbist_algorithm' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Isolated candidate to edit. Empty means create one from the baseline.
        'baseline_ref': baseline_ref,  # Immutable baseline the candidate must descend from.
        'hypothesis': hypothesis,  # The single change this edit is testing.
        'memory_id': memory_id,  # Memory the algorithm targets.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'write_mbist_algorithm',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='mbist_lbist',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Write the repair interface and redundancy map.')  # Fleet-facing one-line skill description for planners.
def write_memory_repair_interface(
    candidate_ref: str = '',
    baseline_ref: str = '',
    hypothesis: str = '',
    params: dict | None = None,
) -> dict:
    """Write the repair interface and redundancy map.

    Purpose:
        Skill ``write_memory_repair_interface`` for the MBIST/LBIST agent (``mbist_lbist``). Configures memory/logic BIST controllers, algorithms, repair, and diagnostics.
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
    # Observation payload for skill 'write_memory_repair_interface' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Isolated candidate to edit. Empty means create one from the baseline.
        'baseline_ref': baseline_ref,  # Immutable baseline the candidate must descend from.
        'hypothesis': hypothesis,  # The single change this edit is testing.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'write_memory_repair_interface',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='mbist_lbist',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Write the diagnostic mode that reports failing address and bit.')  # Fleet-facing one-line skill description for planners.
def write_mbist_diagnostic_mode(
    candidate_ref: str = '',
    baseline_ref: str = '',
    hypothesis: str = '',
    params: dict | None = None,
) -> dict:
    """Write the diagnostic mode that reports failing address and bit.

    Purpose:
        Skill ``write_mbist_diagnostic_mode`` for the MBIST/LBIST agent (``mbist_lbist``). Configures memory/logic BIST controllers, algorithms, repair, and diagnostics.
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
    # Observation payload for skill 'write_mbist_diagnostic_mode' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Isolated candidate to edit. Empty means create one from the baseline.
        'baseline_ref': baseline_ref,  # Immutable baseline the candidate must descend from.
        'hypothesis': hypothesis,  # The single change this edit is testing.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'write_mbist_diagnostic_mode',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='mbist_lbist',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Configure the LBIST controller, PRPG, and MISR.')  # Fleet-facing one-line skill description for planners.
def write_lbist_controller(
    candidate_ref: str = '',
    baseline_ref: str = '',
    hypothesis: str = '',
    params: dict | None = None,
) -> dict:
    """Configure the LBIST controller, PRPG, and MISR.

    Purpose:
        Skill ``write_lbist_controller`` for the MBIST/LBIST agent (``mbist_lbist``). Configures memory/logic BIST controllers, algorithms, repair, and diagnostics.
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
    # Observation payload for skill 'write_lbist_controller' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Isolated candidate to edit. Empty means create one from the baseline.
        'baseline_ref': baseline_ref,  # Immutable baseline the candidate must descend from.
        'hypothesis': hypothesis,  # The single change this edit is testing.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'write_lbist_controller',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='mbist_lbist',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Write the LBIST seed set.')  # Fleet-facing one-line skill description for planners.
def write_lbist_seed(
    candidate_ref: str = '',
    baseline_ref: str = '',
    hypothesis: str = '',
    params: dict | None = None,
) -> dict:
    """Write the LBIST seed set.

    Purpose:
        Skill ``write_lbist_seed`` for the MBIST/LBIST agent (``mbist_lbist``). Configures memory/logic BIST controllers, algorithms, repair, and diagnostics.
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
    # Observation payload for skill 'write_lbist_seed' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Isolated candidate to edit. Empty means create one from the baseline.
        'baseline_ref': baseline_ref,  # Immutable baseline the candidate must descend from.
        'hypothesis': hypothesis,  # The single change this edit is testing.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'write_lbist_seed',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='mbist_lbist',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Bind controllers to the memory instances in the candidate.')  # Fleet-facing one-line skill description for planners.
def bind_bist_to_memories(
    candidate_ref: str = '',
    baseline_ref: str = '',
    hypothesis: str = '',
    params: dict | None = None,
) -> dict:
    """Bind controllers to the memory instances in the candidate.

    Purpose:
        Skill ``bind_bist_to_memories`` for the MBIST/LBIST agent (``mbist_lbist``). Configures memory/logic BIST controllers, algorithms, repair, and diagnostics.
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
    # Observation payload for skill 'bind_bist_to_memories' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Isolated candidate to edit. Empty means create one from the baseline.
        'baseline_ref': baseline_ref,  # Immutable baseline the candidate must descend from.
        'hypothesis': hypothesis,  # The single change this edit is testing.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'bind_bist_to_memories',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='mbist_lbist',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Check that BIST ports, clocks, and resets integrate with the functional design.')  # Fleet-facing one-line skill description for planners.
def check_bist_integration(
    candidate_ref: str = '',
    baseline_ref: str = '',
    recipe: str = '',
    corner: str = '',
    mode: str = '',
    params: dict | None = None,
) -> dict:
    """Check that BIST ports, clocks, and resets integrate with the functional design.

    Purpose:
        Skill ``check_bist_integration`` for the MBIST/LBIST agent (``mbist_lbist``). Configures memory/logic BIST controllers, algorithms, repair, and diagnostics.
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
    # Observation payload for skill 'check_bist_integration' — keys align with config.yaml skill params.
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
        'check_bist_integration',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='mbist_lbist',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Read MBIST and LBIST coverage from the BIST report.')  # Fleet-facing one-line skill description for planners.
def read_bist_coverage(
    candidate_ref: str = '',
    report_ref: str = '',
    corner: str = '',
    mode: str = '',
    params: dict | None = None,
) -> dict:
    """Read MBIST and LBIST coverage from the BIST report.

    Purpose:
        Skill ``read_bist_coverage`` for the MBIST/LBIST agent (``mbist_lbist``). Configures memory/logic BIST controllers, algorithms, repair, and diagnostics.
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
    # Observation payload for skill 'read_bist_coverage' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Isolated candidate to edit. Empty means create one from the baseline.
        'report_ref': report_ref,  # Artifact URI of the report. Empty reads the latest report for this candidate.
        'corner': corner,  # PVT corner. Empty when the job is not corner-specific.
        'mode': mode,  # Functional or analysis mode. Empty when the job is not mode-specific.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'read_bist_coverage',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='mbist_lbist',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Read the test-mode clocks and false paths BIST requires.')  # Fleet-facing one-line skill description for planners.
def read_bist_timing_constraints(
    candidate_ref: str = '',
    report_ref: str = '',
    corner: str = '',
    mode: str = '',
    params: dict | None = None,
) -> dict:
    """Read the test-mode clocks and false paths BIST requires.

    Purpose:
        Skill ``read_bist_timing_constraints`` for the MBIST/LBIST agent (``mbist_lbist``). Configures memory/logic BIST controllers, algorithms, repair, and diagnostics.
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
    # Observation payload for skill 'read_bist_timing_constraints' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Isolated candidate to edit. Empty means create one from the baseline.
        'report_ref': report_ref,  # Artifact URI of the report. Empty reads the latest report for this candidate.
        'corner': corner,  # PVT corner. Empty when the job is not corner-specific.
        'mode': mode,  # Functional or analysis mode. Empty when the job is not mode-specific.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'read_bist_timing_constraints',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='mbist_lbist',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Publish a memory with no MBIST algorithm.')  # Fleet-facing one-line skill description for planners.
def flag_uncovered_memory(
    summary: str = '',
    evidence_refs: str = '',
    severity: str = '',
    recommended_recipient: str = '',
    params: dict | None = None,
) -> dict:
    """Publish a memory with no MBIST algorithm.

    Purpose:
        Skill ``flag_uncovered_memory`` for the MBIST/LBIST agent (``mbist_lbist``). Configures memory/logic BIST controllers, algorithms, repair, and diagnostics.
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
    # Observation payload for skill 'flag_uncovered_memory' — keys align with config.yaml skill params.
    payload = {
        'summary': summary,  # One-sentence finding.
        'evidence_refs': evidence_refs,  # Comma-separated artifact URIs that support the finding.
        'severity': severity,  # low, medium, high, or critical.
        'recommended_recipient': recommended_recipient,  # Agent id that should act on the finding.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'flag_uncovered_memory',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='mbist_lbist',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Publish a BIST port, clock, or reset that does not integrate.')  # Fleet-facing one-line skill description for planners.
def flag_bist_integration_error(
    summary: str = '',
    evidence_refs: str = '',
    severity: str = '',
    recommended_recipient: str = '',
    params: dict | None = None,
) -> dict:
    """Publish a BIST port, clock, or reset that does not integrate.

    Purpose:
        Skill ``flag_bist_integration_error`` for the MBIST/LBIST agent (``mbist_lbist``). Configures memory/logic BIST controllers, algorithms, repair, and diagnostics.
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
    # Observation payload for skill 'flag_bist_integration_error' — keys align with config.yaml skill params.
    payload = {
        'summary': summary,  # One-sentence finding.
        'evidence_refs': evidence_refs,  # Comma-separated artifact URIs that support the finding.
        'severity': severity,  # low, medium, high, or critical.
        'recommended_recipient': recommended_recipient,  # Agent id that should act on the finding.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'flag_bist_integration_error',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='mbist_lbist',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Record algorithms, seeds, and the candidate they were applied to.')  # Fleet-facing one-line skill description for planners.
def record_bist_configuration(
    summary: str = '',
    evidence_refs: str = '',
    severity: str = '',
    recommended_recipient: str = '',
    params: dict | None = None,
) -> dict:
    """Record algorithms, seeds, and the candidate they were applied to.

    Purpose:
        Skill ``record_bist_configuration`` for the MBIST/LBIST agent (``mbist_lbist``). Configures memory/logic BIST controllers, algorithms, repair, and diagnostics.
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
    # Observation payload for skill 'record_bist_configuration' — keys align with config.yaml skill params.
    payload = {
        'summary': summary,  # One-sentence finding.
        'evidence_refs': evidence_refs,  # Comma-separated artifact URIs that support the finding.
        'severity': severity,  # low, medium, high, or critical.
        'recommended_recipient': recommended_recipient,  # Agent id that should act on the finding.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'record_bist_configuration',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='mbist_lbist',  # Provenance: which specialist emitted this observation.
    )
