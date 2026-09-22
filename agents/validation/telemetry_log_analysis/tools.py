"""Tool callables for the Telemetry / Log Analysis agent (telemetry_log_analysis).

Normalizes and correlates firmware logs, counters, and captures.

Each function below is the stable operation contract advertised in
``config.yaml`` under ``skills``. A framework adapter (DFT tool, ATPG engine,
MBIST compiler, lab instrument bridge, ATE, etc.) performs the real work.
Until that adapter is bound, ``tool_observation`` returns a structured
``not_run`` result and does **not** invoke OpenROAD, Yosys, OpenSTA, a licensed
DFT/ATE tool, a simulator, or a physical instrument.

This module is imported when a skill is dispatched. Process bootstrap lives in
``server.py``; fleet metadata and param schemas live in ``config.yaml``.

Module lineage: Tool callables for the Telemetry / Log Analysis agent (telemetry_log_analysis).
"""

from __future__ import annotations  # Allow modern typing constructs in skill signatures.

from packages.agent_sdk import tool  # Decorator that registers the callable as an agent skill.
from domains.eda.eda import tool_observation  # Builds the not_run / observation envelope for adapters.


@tool(description='Normalize firmware logs into a common record.')  # Fleet-facing one-line skill description for planners.
def normalize_firmware_logs(
    candidate_ref: str = '',
    report_ref: str = '',
    corner: str = '',
    mode: str = '',
    params: dict | None = None,
) -> dict:
    """Normalize firmware logs into a common record.

    Purpose:
        Skill ``normalize_firmware_logs`` for the Telemetry / Log Analysis agent (``telemetry_log_analysis``). Normalizes and correlates firmware logs, counters, and captures.
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
    # Observation payload for skill 'normalize_firmware_logs' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Candidate whose reports are read.
        'report_ref': report_ref,  # Artifact URI of the report. Empty reads the latest report for this candidate.
        'corner': corner,  # Corner filter. Empty reads every available corner.
        'mode': mode,  # Mode filter. Empty reads every available mode.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'normalize_firmware_logs',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='telemetry_log_analysis',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Normalize instrument captures and environmental metadata.')  # Fleet-facing one-line skill description for planners.
def normalize_instrument_metadata(
    candidate_ref: str = '',
    report_ref: str = '',
    corner: str = '',
    mode: str = '',
    params: dict | None = None,
) -> dict:
    """Normalize instrument captures and environmental metadata.

    Purpose:
        Skill ``normalize_instrument_metadata`` for the Telemetry / Log Analysis agent (``telemetry_log_analysis``). Normalizes and correlates firmware logs, counters, and captures.
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
    # Observation payload for skill 'normalize_instrument_metadata' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Candidate whose reports are read.
        'report_ref': report_ref,  # Artifact URI of the report. Empty reads the latest report for this candidate.
        'corner': corner,  # Corner filter. Empty reads every available corner.
        'mode': mode,  # Mode filter. Empty reads every available mode.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'normalize_instrument_metadata',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='telemetry_log_analysis',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Read hardware performance counters.')  # Fleet-facing one-line skill description for planners.
def read_hardware_counters(
    candidate_ref: str = '',
    report_ref: str = '',
    corner: str = '',
    mode: str = '',
    params: dict | None = None,
) -> dict:
    """Read hardware performance counters.

    Purpose:
        Skill ``read_hardware_counters`` for the Telemetry / Log Analysis agent (``telemetry_log_analysis``). Normalizes and correlates firmware logs, counters, and captures.
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
    # Observation payload for skill 'read_hardware_counters' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Candidate whose reports are read.
        'report_ref': report_ref,  # Artifact URI of the report. Empty reads the latest report for this candidate.
        'corner': corner,  # Corner filter. Empty reads every available corner.
        'mode': mode,  # Mode filter. Empty reads every available mode.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'read_hardware_counters',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='telemetry_log_analysis',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Read the trace and capture index.')  # Fleet-facing one-line skill description for planners.
def read_trace_index(
    candidate_ref: str = '',
    report_ref: str = '',
    corner: str = '',
    mode: str = '',
    params: dict | None = None,
) -> dict:
    """Read the trace and capture index.

    Purpose:
        Skill ``read_trace_index`` for the Telemetry / Log Analysis agent (``telemetry_log_analysis``). Normalizes and correlates firmware logs, counters, and captures.
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
    # Observation payload for skill 'read_trace_index' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Candidate whose reports are read.
        'report_ref': report_ref,  # Artifact URI of the report. Empty reads the latest report for this candidate.
        'corner': corner,  # Corner filter. Empty reads every available corner.
        'mode': mode,  # Mode filter. Empty reads every available mode.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'read_trace_index',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='telemetry_log_analysis',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Search normalized logs for one signature.')  # Fleet-facing one-line skill description for planners.
def search_logs(
    candidate_ref: str = '',
    report_ref: str = '',
    corner: str = '',
    mode: str = '',
    query: str = '',
    params: dict | None = None,
) -> dict:
    """Search normalized logs for one signature.

    Purpose:
        Skill ``search_logs`` for the Telemetry / Log Analysis agent (``telemetry_log_analysis``). Normalizes and correlates firmware logs, counters, and captures.
        Silicon-validation meaning: this skill participates in bring-up, lab procedure, instrument control, firmware/test programs, telemetry analysis, characterization, failure correlation, or errata drafting under approved safety bounds. This callable only builds a ``tool_observation`` payload;
        heavy EDA or bench work happens in a bound adapter.

    Args:
        candidate_ref: Candidate whose reports are read. Empty may mean latest candidate for the adapter.
        report_ref: Artifact URI of the report. Empty reads the latest report for this candidate. Empty reads the latest report for the candidate.
        corner: Corner filter. Empty reads every available corner. Empty reads every available corner.
        mode: Mode filter. Empty reads every available mode. Empty reads every available mode.
        query: Text or counter signature to find. Empty returns an unfiltered window.
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
    # Observation payload for skill 'search_logs' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Candidate whose reports are read.
        'report_ref': report_ref,  # Artifact URI of the report. Empty reads the latest report for this candidate.
        'corner': corner,  # Corner filter. Empty reads every available corner.
        'mode': mode,  # Mode filter. Empty reads every available mode.
        'query': query,  # Text or counter signature to find.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'search_logs',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='telemetry_log_analysis',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Correlate counters, traces, and environment metadata.')  # Fleet-facing one-line skill description for planners.
def correlate_traces(
    summary: str = '',
    evidence_refs: str = '',
    severity: str = '',
    recommended_recipient: str = '',
    params: dict | None = None,
) -> dict:
    """Correlate counters, traces, and environment metadata.

    Purpose:
        Skill ``correlate_traces`` for the Telemetry / Log Analysis agent (``telemetry_log_analysis``). Normalizes and correlates firmware logs, counters, and captures.
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
    # Observation payload for skill 'correlate_traces' — keys align with config.yaml skill params.
    payload = {
        'summary': summary,  # One-sentence finding.
        'evidence_refs': evidence_refs,  # Comma-separated artifact URIs that support the finding.
        'severity': severity,  # low, medium, high, or critical.
        'recommended_recipient': recommended_recipient,  # Agent id that should act on the finding.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'correlate_traces',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='telemetry_log_analysis',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Align firmware timestamps with instrument captures.')  # Fleet-facing one-line skill description for planners.
def align_logs_to_captures(
    candidate_ref: str = '',
    report_ref: str = '',
    corner: str = '',
    mode: str = '',
    params: dict | None = None,
) -> dict:
    """Align firmware timestamps with instrument captures.

    Purpose:
        Skill ``align_logs_to_captures`` for the Telemetry / Log Analysis agent (``telemetry_log_analysis``). Normalizes and correlates firmware logs, counters, and captures.
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
    # Observation payload for skill 'align_logs_to_captures' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Candidate whose reports are read.
        'report_ref': report_ref,  # Artifact URI of the report. Empty reads the latest report for this candidate.
        'corner': corner,  # Corner filter. Empty reads every available corner.
        'mode': mode,  # Mode filter. Empty reads every available mode.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'align_logs_to_captures',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='telemetry_log_analysis',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Summarize one lab session and link every claim to a primary capture.')  # Fleet-facing one-line skill description for planners.
def summarize_session(
    summary: str = '',
    evidence_refs: str = '',
    severity: str = '',
    recommended_recipient: str = '',
    params: dict | None = None,
) -> dict:
    """Summarize one lab session and link every claim to a primary capture.

    Purpose:
        Skill ``summarize_session`` for the Telemetry / Log Analysis agent (``telemetry_log_analysis``). Normalizes and correlates firmware logs, counters, and captures.
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
    # Observation payload for skill 'summarize_session' — keys align with config.yaml skill params.
    payload = {
        'summary': summary,  # One-sentence finding.
        'evidence_refs': evidence_refs,  # Comma-separated artifact URIs that support the finding.
        'severity': severity,  # low, medium, high, or critical.
        'recommended_recipient': recommended_recipient,  # Agent id that should act on the finding.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'summarize_session',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='telemetry_log_analysis',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Publish a capture that contradicts the session summary.')  # Fleet-facing one-line skill description for planners.
def flag_contradictory_capture(
    summary: str = '',
    evidence_refs: str = '',
    severity: str = '',
    recommended_recipient: str = '',
    params: dict | None = None,
) -> dict:
    """Publish a capture that contradicts the session summary.

    Purpose:
        Skill ``flag_contradictory_capture`` for the Telemetry / Log Analysis agent (``telemetry_log_analysis``). Normalizes and correlates firmware logs, counters, and captures.
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
    # Observation payload for skill 'flag_contradictory_capture' — keys align with config.yaml skill params.
    payload = {
        'summary': summary,  # One-sentence finding.
        'evidence_refs': evidence_refs,  # Comma-separated artifact URIs that support the finding.
        'severity': severity,  # low, medium, high, or critical.
        'recommended_recipient': recommended_recipient,  # Agent id that should act on the finding.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'flag_contradictory_capture',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='telemetry_log_analysis',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Publish a summary sentence with no primary evidence.')  # Fleet-facing one-line skill description for planners.
def flag_unlinked_summary_claim(
    summary: str = '',
    evidence_refs: str = '',
    severity: str = '',
    recommended_recipient: str = '',
    params: dict | None = None,
) -> dict:
    """Publish a summary sentence with no primary evidence.

    Purpose:
        Skill ``flag_unlinked_summary_claim`` for the Telemetry / Log Analysis agent (``telemetry_log_analysis``). Normalizes and correlates firmware logs, counters, and captures.
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
    # Observation payload for skill 'flag_unlinked_summary_claim' — keys align with config.yaml skill params.
    payload = {
        'summary': summary,  # One-sentence finding.
        'evidence_refs': evidence_refs,  # Comma-separated artifact URIs that support the finding.
        'severity': severity,  # low, medium, high, or critical.
        'recommended_recipient': recommended_recipient,  # Agent id that should act on the finding.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'flag_unlinked_summary_claim',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='telemetry_log_analysis',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Record the log, counter, and capture refs included in an analysis.')  # Fleet-facing one-line skill description for planners.
def record_telemetry_sources(
    summary: str = '',
    evidence_refs: str = '',
    severity: str = '',
    recommended_recipient: str = '',
    params: dict | None = None,
) -> dict:
    """Record the log, counter, and capture refs included in an analysis.

    Purpose:
        Skill ``record_telemetry_sources`` for the Telemetry / Log Analysis agent (``telemetry_log_analysis``). Normalizes and correlates firmware logs, counters, and captures.
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
    # Observation payload for skill 'record_telemetry_sources' — keys align with config.yaml skill params.
    payload = {
        'summary': summary,  # One-sentence finding.
        'evidence_refs': evidence_refs,  # Comma-separated artifact URIs that support the finding.
        'severity': severity,  # low, medium, high, or critical.
        'recommended_recipient': recommended_recipient,  # Agent id that should act on the finding.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'record_telemetry_sources',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='telemetry_log_analysis',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Publish the correlation and its evidence refs.')  # Fleet-facing one-line skill description for planners.
def publish_telemetry_correlation(
    summary: str = '',
    evidence_refs: str = '',
    severity: str = '',
    recommended_recipient: str = '',
    params: dict | None = None,
) -> dict:
    """Publish the correlation and its evidence refs.

    Purpose:
        Skill ``publish_telemetry_correlation`` for the Telemetry / Log Analysis agent (``telemetry_log_analysis``). Normalizes and correlates firmware logs, counters, and captures.
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
    # Observation payload for skill 'publish_telemetry_correlation' — keys align with config.yaml skill params.
    payload = {
        'summary': summary,  # One-sentence finding.
        'evidence_refs': evidence_refs,  # Comma-separated artifact URIs that support the finding.
        'severity': severity,  # low, medium, high, or critical.
        'recommended_recipient': recommended_recipient,  # Agent id that should act on the finding.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'publish_telemetry_correlation',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='telemetry_log_analysis',  # Provenance: which specialist emitted this observation.
    )
