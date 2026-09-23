"""Tool callables for the Scan Insertion agent (scan_insertion).

Inserts scan chains, compression, test clocks, and lockups on a candidate.

Each function below is the stable operation contract advertised in
``config.yaml`` under ``skills``. A framework adapter (DFT tool, ATPG engine,
MBIST compiler, lab instrument bridge, ATE, etc.) performs the real work.
Until that adapter is bound, ``tool_observation`` returns a structured
``not_run`` result and does **not** invoke OpenROAD, Yosys, OpenSTA, a licensed
DFT/ATE tool, a simulator, or a physical instrument.

This module is imported when a skill is dispatched. Process bootstrap lives in
``server.py``; fleet metadata and param schemas live in ``config.yaml``.

Module lineage: Tool callables for the Scan Insertion agent (scan_insertion).
"""

from __future__ import annotations  # Allow modern typing constructs in skill signatures.

from packages.agent_sdk import tool  # Decorator that registers the callable as an agent skill.
from domains.eda.adapters import tool_observation  # Builds the not_run / observation envelope for adapters.


@tool(description='Write chain count, scan clocks, and compression settings for this candidate.')  # Fleet-facing one-line skill description for planners.
def write_scan_configuration(
    candidate_ref: str = '',
    baseline_ref: str = '',
    hypothesis: str = '',
    params: dict | None = None,
) -> dict:
    """Write chain count, scan clocks, and compression settings for this candidate.

    Purpose:
        Skill ``write_scan_configuration`` for the Scan Insertion agent (``scan_insertion``). Inserts scan chains, compression, test clocks, and lockups on a candidate.
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
    # Observation payload for skill 'write_scan_configuration' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Isolated candidate to edit. Empty means create one from the baseline.
        'baseline_ref': baseline_ref,  # Immutable baseline the candidate must descend from.
        'hypothesis': hypothesis,  # The single change this edit is testing.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'write_scan_configuration',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='scan_insertion',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Add the test-mode ports required by the scan configuration.')  # Fleet-facing one-line skill description for planners.
def write_test_mode_ports(
    candidate_ref: str = '',
    baseline_ref: str = '',
    hypothesis: str = '',
    params: dict | None = None,
) -> dict:
    """Add the test-mode ports required by the scan configuration.

    Purpose:
        Skill ``write_test_mode_ports`` for the Scan Insertion agent (``scan_insertion``). Inserts scan chains, compression, test clocks, and lockups on a candidate.
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
    # Observation payload for skill 'write_test_mode_ports' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Isolated candidate to edit. Empty means create one from the baseline.
        'baseline_ref': baseline_ref,  # Immutable baseline the candidate must descend from.
        'hypothesis': hypothesis,  # The single change this edit is testing.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'write_test_mode_ports',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='scan_insertion',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Insert scan on an isolated candidate. Adapter target: scan insertion in the bound DFT tool.')  # Fleet-facing one-line skill description for planners.
def insert_scan(
    candidate_ref: str = '',
    baseline_ref: str = '',
    recipe: str = '',
    corner: str = '',
    mode: str = '',
    params: dict | None = None,
) -> dict:
    """Insert scan on an isolated candidate. Adapter target: scan insertion in the bound DFT tool.

    Purpose:
        Skill ``insert_scan`` for the Scan Insertion agent (``scan_insertion``). Inserts scan chains, compression, test clocks, and lockups on a candidate.
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
    # Observation payload for skill 'insert_scan' — keys align with config.yaml skill params.
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
        'insert_scan',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='scan_insertion',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Insert scan compression and decompression logic.')  # Fleet-facing one-line skill description for planners.
def insert_compression(
    candidate_ref: str = '',
    baseline_ref: str = '',
    recipe: str = '',
    corner: str = '',
    mode: str = '',
    params: dict | None = None,
) -> dict:
    """Insert scan compression and decompression logic.

    Purpose:
        Skill ``insert_compression`` for the Scan Insertion agent (``scan_insertion``). Inserts scan chains, compression, test clocks, and lockups on a candidate.
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
    # Observation payload for skill 'insert_compression' — keys align with config.yaml skill params.
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
        'insert_compression',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='scan_insertion',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Insert lockup latches or flops on cross-clock scan paths.')  # Fleet-facing one-line skill description for planners.
def insert_lockup_elements(
    candidate_ref: str = '',
    baseline_ref: str = '',
    recipe: str = '',
    corner: str = '',
    mode: str = '',
    params: dict | None = None,
) -> dict:
    """Insert lockup latches or flops on cross-clock scan paths.

    Purpose:
        Skill ``insert_lockup_elements`` for the Scan Insertion agent (``scan_insertion``). Inserts scan chains, compression, test clocks, and lockups on a candidate.
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
    # Observation payload for skill 'insert_lockup_elements' — keys align with config.yaml skill params.
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
        'insert_lockup_elements',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='scan_insertion',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Insert the dedicated test clocks named in the configuration.')  # Fleet-facing one-line skill description for planners.
def insert_test_clocks(
    candidate_ref: str = '',
    baseline_ref: str = '',
    recipe: str = '',
    corner: str = '',
    mode: str = '',
    params: dict | None = None,
) -> dict:
    """Insert the dedicated test clocks named in the configuration.

    Purpose:
        Skill ``insert_test_clocks`` for the Scan Insertion agent (``scan_insertion``). Inserts scan chains, compression, test clocks, and lockups on a candidate.
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
    # Observation payload for skill 'insert_test_clocks' — keys align with config.yaml skill params.
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
        'insert_test_clocks',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='scan_insertion',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Write scan chain order into the candidate database.')  # Fleet-facing one-line skill description for planners.
def write_scan_def(
    candidate_ref: str = '',
    baseline_ref: str = '',
    hypothesis: str = '',
    params: dict | None = None,
) -> dict:
    """Write scan chain order into the candidate database.

    Purpose:
        Skill ``write_scan_def`` for the Scan Insertion agent (``scan_insertion``). Inserts scan chains, compression, test clocks, and lockups on a candidate.
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
    # Observation payload for skill 'write_scan_def' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Isolated candidate to edit. Empty means create one from the baseline.
        'baseline_ref': baseline_ref,  # Immutable baseline the candidate must descend from.
        'hypothesis': hypothesis,  # The single change this edit is testing.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'write_scan_def',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='scan_insertion',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Read chain counts, lockup cells, and broken connections.')  # Fleet-facing one-line skill description for planners.
def read_scan_connectivity(
    candidate_ref: str = '',
    report_ref: str = '',
    corner: str = '',
    mode: str = '',
    params: dict | None = None,
) -> dict:
    """Read chain counts, lockup cells, and broken connections.

    Purpose:
        Skill ``read_scan_connectivity`` for the Scan Insertion agent (``scan_insertion``). Inserts scan chains, compression, test clocks, and lockups on a candidate.
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
    # Observation payload for skill 'read_scan_connectivity' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Isolated candidate to edit. Empty means create one from the baseline.
        'report_ref': report_ref,  # Artifact URI of the report. Empty reads the latest report for this candidate.
        'corner': corner,  # PVT corner. Empty when the job is not corner-specific.
        'mode': mode,  # Functional or analysis mode. Empty when the job is not mode-specific.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'read_scan_connectivity',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='scan_insertion',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Read the length of every scan chain.')  # Fleet-facing one-line skill description for planners.
def read_scan_chain_lengths(
    candidate_ref: str = '',
    report_ref: str = '',
    corner: str = '',
    mode: str = '',
    params: dict | None = None,
) -> dict:
    """Read the length of every scan chain.

    Purpose:
        Skill ``read_scan_chain_lengths`` for the Scan Insertion agent (``scan_insertion``). Inserts scan chains, compression, test clocks, and lockups on a candidate.
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
    # Observation payload for skill 'read_scan_chain_lengths' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Isolated candidate to edit. Empty means create one from the baseline.
        'report_ref': report_ref,  # Artifact URI of the report. Empty reads the latest report for this candidate.
        'corner': corner,  # PVT corner. Empty when the job is not corner-specific.
        'mode': mode,  # Functional or analysis mode. Empty when the job is not mode-specific.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'read_scan_chain_lengths',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='scan_insertion',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Check that functional ports were not retimed or removed.')  # Fleet-facing one-line skill description for planners.
def check_scan_vs_functional_ports(
    candidate_ref: str = '',
    report_ref: str = '',
    corner: str = '',
    mode: str = '',
    params: dict | None = None,
) -> dict:
    """Check that functional ports were not retimed or removed.

    Purpose:
        Skill ``check_scan_vs_functional_ports`` for the Scan Insertion agent (``scan_insertion``). Inserts scan chains, compression, test clocks, and lockups on a candidate.
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
    # Observation payload for skill 'check_scan_vs_functional_ports' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Isolated candidate to edit. Empty means create one from the baseline.
        'report_ref': report_ref,  # Artifact URI of the report. Empty reads the latest report for this candidate.
        'corner': corner,  # PVT corner. Empty when the job is not corner-specific.
        'mode': mode,  # Functional or analysis mode. Empty when the job is not mode-specific.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'check_scan_vs_functional_ports',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='scan_insertion',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Publish chain counts, lockup cells, and connectivity evidence.')  # Fleet-facing one-line skill description for planners.
def report_scan_connectivity(
    summary: str = '',
    evidence_refs: str = '',
    severity: str = '',
    recommended_recipient: str = '',
    params: dict | None = None,
) -> dict:
    """Publish chain counts, lockup cells, and connectivity evidence.

    Purpose:
        Skill ``report_scan_connectivity`` for the Scan Insertion agent (``scan_insertion``). Inserts scan chains, compression, test clocks, and lockups on a candidate.
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
    # Observation payload for skill 'report_scan_connectivity' — keys align with config.yaml skill params.
    payload = {
        'summary': summary,  # One-sentence finding.
        'evidence_refs': evidence_refs,  # Comma-separated artifact URIs that support the finding.
        'severity': severity,  # low, medium, high, or critical.
        'recommended_recipient': recommended_recipient,  # Agent id that should act on the finding.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'report_scan_connectivity',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='scan_insertion',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Publish a chain whose length exceeds the test-time budget.')  # Fleet-facing one-line skill description for planners.
def flag_unbalanced_scan_chain(
    summary: str = '',
    evidence_refs: str = '',
    severity: str = '',
    recommended_recipient: str = '',
    params: dict | None = None,
) -> dict:
    """Publish a chain whose length exceeds the test-time budget.

    Purpose:
        Skill ``flag_unbalanced_scan_chain`` for the Scan Insertion agent (``scan_insertion``). Inserts scan chains, compression, test clocks, and lockups on a candidate.
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
    # Observation payload for skill 'flag_unbalanced_scan_chain' — keys align with config.yaml skill params.
    payload = {
        'summary': summary,  # One-sentence finding.
        'evidence_refs': evidence_refs,  # Comma-separated artifact URIs that support the finding.
        'severity': severity,  # low, medium, high, or critical.
        'recommended_recipient': recommended_recipient,  # Agent id that should act on the finding.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'flag_unbalanced_scan_chain',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='scan_insertion',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Publish a cross-clock scan path with no lockup element.')  # Fleet-facing one-line skill description for planners.
def flag_missing_lockup(
    summary: str = '',
    evidence_refs: str = '',
    severity: str = '',
    recommended_recipient: str = '',
    params: dict | None = None,
) -> dict:
    """Publish a cross-clock scan path with no lockup element.

    Purpose:
        Skill ``flag_missing_lockup`` for the Scan Insertion agent (``scan_insertion``). Inserts scan chains, compression, test clocks, and lockups on a candidate.
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
    # Observation payload for skill 'flag_missing_lockup' — keys align with config.yaml skill params.
    payload = {
        'summary': summary,  # One-sentence finding.
        'evidence_refs': evidence_refs,  # Comma-separated artifact URIs that support the finding.
        'severity': severity,  # low, medium, high, or critical.
        'recommended_recipient': recommended_recipient,  # Agent id that should act on the finding.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'flag_missing_lockup',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='scan_insertion',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Record the DFT tool, version, and scan recipe.')  # Fleet-facing one-line skill description for planners.
def record_scan_tool_version(
    summary: str = '',
    evidence_refs: str = '',
    severity: str = '',
    recommended_recipient: str = '',
    params: dict | None = None,
) -> dict:
    """Record the DFT tool, version, and scan recipe.

    Purpose:
        Skill ``record_scan_tool_version`` for the Scan Insertion agent (``scan_insertion``). Inserts scan chains, compression, test clocks, and lockups on a candidate.
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
    # Observation payload for skill 'record_scan_tool_version' — keys align with config.yaml skill params.
    payload = {
        'summary': summary,  # One-sentence finding.
        'evidence_refs': evidence_refs,  # Comma-separated artifact URIs that support the finding.
        'severity': severity,  # low, medium, high, or critical.
        'recommended_recipient': recommended_recipient,  # Agent id that should act on the finding.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'record_scan_tool_version',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='scan_insertion',  # Provenance: which specialist emitted this observation.
    )
