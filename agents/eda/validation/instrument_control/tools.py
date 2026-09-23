"""Tool callables for the Instrument Control agent (instrument_control).

Drives approved instruments under voltage/current/temperature limits.

Each function below is the stable operation contract advertised in
``config.yaml`` under ``skills``. A framework adapter (DFT tool, ATPG engine,
MBIST compiler, lab instrument bridge, ATE, etc.) performs the real work.
Until that adapter is bound, ``tool_observation`` returns a structured
``not_run`` result and does **not** invoke OpenROAD, Yosys, OpenSTA, a licensed
DFT/ATE tool, a simulator, or a physical instrument.

This module is imported when a skill is dispatched. Process bootstrap lives in
``server.py``; fleet metadata and param schemas live in ``config.yaml``.

Module lineage: Tool callables for the Instrument Control agent (instrument_control).
"""

from __future__ import annotations  # Allow modern typing constructs in skill signatures.

from packages.agent_sdk import tool  # Decorator that registers the callable as an agent skill.
from domains.eda.adapters import tool_observation  # Builds the not_run / observation envelope for adapters.


@tool(description='Execute one approved procedure through the lab adapter.')  # Fleet-facing one-line skill description for planners.
def run_instrument_procedure(
    candidate_ref: str = '',
    baseline_ref: str = '',
    recipe: str = '',
    corner: str = '',
    mode: str = '',
    procedure_ref: str = '',
    instrument: str = '',
    command: str = '',
    voltage_limit: str = '',
    current_limit: str = '',
    temperature_limit: str = '',
    params: dict | None = None,
) -> dict:
    """Execute one approved procedure through the lab adapter.

    Purpose:
        Skill ``run_instrument_procedure`` for the Instrument Control agent (``instrument_control``). Drives approved instruments under voltage/current/temperature limits.
        Silicon-validation meaning: this skill participates in bring-up, lab procedure, instrument control, firmware/test programs, telemetry analysis, characterization, failure correlation, or errata drafting under approved safety bounds. This callable only builds a ``tool_observation`` payload;
        heavy EDA or bench work happens in a bound adapter.

    Args:
        candidate_ref: Candidate the job reads. Empty may mean latest candidate for the adapter.
        baseline_ref: Baseline used when the job compares against a known result. Empty means no explicit baseline pin.
        recipe: Versioned tool recipe. The adapter rejects an unknown recipe. Empty uses the flow default recipe.
        corner: PVT corner. Empty when the job is not corner-specific. Empty reads every available corner.
        mode: Functional or analysis mode. Empty when the job is not mode-specific. Empty reads every available mode.
        procedure_ref: Approved procedure revision. Empty is invalid for instrument runs that require approval.
        instrument: Instrument id. Empty means the procedure's default instrument.
        command: Typed command the adapter may run. Empty means run the procedure's default command sequence.
        voltage_limit: Maximum voltage in volts. Copied from approved limits; must not be widened here.
        current_limit: Maximum current in amperes. Copied from approved limits; must not be widened here.
        temperature_limit: Maximum temperature in Celsius. Copied from approved limits; must not be widened here.
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
    # Observation payload for skill 'run_instrument_procedure' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Candidate the job reads.
        'baseline_ref': baseline_ref,  # Baseline used when the job compares against a known result.
        'recipe': recipe,  # Versioned tool recipe. The adapter rejects an unknown recipe.
        'corner': corner,  # PVT corner. Empty when the job is not corner-specific.
        'mode': mode,  # Functional or analysis mode. Empty when the job is not mode-specific.
        'procedure_ref': procedure_ref,  # Approved procedure revision.
        'instrument': instrument,  # Instrument id.
        'command': command,  # Typed command the adapter may run.
        'voltage_limit': voltage_limit,  # Maximum voltage in volts.
        'current_limit': current_limit,  # Maximum current in amperes.
        'temperature_limit': temperature_limit,  # Maximum temperature in Celsius.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'run_instrument_procedure',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='instrument_control',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Set a power supply inside the approved voltage and current limits.')  # Fleet-facing one-line skill description for planners.
def arm_power_supply(
    candidate_ref: str = '',
    baseline_ref: str = '',
    recipe: str = '',
    corner: str = '',
    mode: str = '',
    instrument: str = '',
    voltage_limit: str = '',
    current_limit: str = '',
    params: dict | None = None,
) -> dict:
    """Set a power supply inside the approved voltage and current limits.

    Purpose:
        Skill ``arm_power_supply`` for the Instrument Control agent (``instrument_control``). Drives approved instruments under voltage/current/temperature limits.
        Silicon-validation meaning: this skill participates in bring-up, lab procedure, instrument control, firmware/test programs, telemetry analysis, characterization, failure correlation, or errata drafting under approved safety bounds. This callable only builds a ``tool_observation`` payload;
        heavy EDA or bench work happens in a bound adapter.

    Args:
        candidate_ref: Candidate the job reads. Empty may mean latest candidate for the adapter.
        baseline_ref: Baseline used when the job compares against a known result. Empty means no explicit baseline pin.
        recipe: Versioned tool recipe. The adapter rejects an unknown recipe. Empty uses the flow default recipe.
        corner: PVT corner. Empty when the job is not corner-specific. Empty reads every available corner.
        mode: Functional or analysis mode. Empty when the job is not mode-specific. Empty reads every available mode.
        instrument: Instrument id. Empty means the procedure's default instrument.
        voltage_limit: Maximum voltage in volts. Copied from approved limits; must not be widened here.
        current_limit: Maximum current in amperes. Copied from approved limits; must not be widened here.
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
    # Observation payload for skill 'arm_power_supply' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Candidate the job reads.
        'baseline_ref': baseline_ref,  # Baseline used when the job compares against a known result.
        'recipe': recipe,  # Versioned tool recipe. The adapter rejects an unknown recipe.
        'corner': corner,  # PVT corner. Empty when the job is not corner-specific.
        'mode': mode,  # Functional or analysis mode. Empty when the job is not mode-specific.
        'instrument': instrument,  # Instrument id.
        'voltage_limit': voltage_limit,  # Maximum voltage in volts.
        'current_limit': current_limit,  # Maximum current in amperes.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'arm_power_supply',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='instrument_control',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Capture one oscilloscope waveform inside the approved setup.')  # Fleet-facing one-line skill description for planners.
def capture_oscilloscope(
    candidate_ref: str = '',
    baseline_ref: str = '',
    recipe: str = '',
    corner: str = '',
    mode: str = '',
    instrument: str = '',
    channel: str = '',
    params: dict | None = None,
) -> dict:
    """Capture one oscilloscope waveform inside the approved setup.

    Purpose:
        Skill ``capture_oscilloscope`` for the Instrument Control agent (``instrument_control``). Drives approved instruments under voltage/current/temperature limits.
        Silicon-validation meaning: this skill participates in bring-up, lab procedure, instrument control, firmware/test programs, telemetry analysis, characterization, failure correlation, or errata drafting under approved safety bounds. This callable only builds a ``tool_observation`` payload;
        heavy EDA or bench work happens in a bound adapter.

    Args:
        candidate_ref: Candidate the job reads. Empty may mean latest candidate for the adapter.
        baseline_ref: Baseline used when the job compares against a known result. Empty means no explicit baseline pin.
        recipe: Versioned tool recipe. The adapter rejects an unknown recipe. Empty uses the flow default recipe.
        corner: PVT corner. Empty when the job is not corner-specific. Empty reads every available corner.
        mode: Functional or analysis mode. Empty when the job is not mode-specific. Empty reads every available mode.
        instrument: Instrument id. Empty means the procedure's default instrument.
        channel: Channel to capture. Empty means channel 0 / default.
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
    # Observation payload for skill 'capture_oscilloscope' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Candidate the job reads.
        'baseline_ref': baseline_ref,  # Baseline used when the job compares against a known result.
        'recipe': recipe,  # Versioned tool recipe. The adapter rejects an unknown recipe.
        'corner': corner,  # PVT corner. Empty when the job is not corner-specific.
        'mode': mode,  # Functional or analysis mode. Empty when the job is not mode-specific.
        'instrument': instrument,  # Instrument id.
        'channel': channel,  # Channel to capture.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'capture_oscilloscope',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='instrument_control',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Capture one logic-analyzer trace.')  # Fleet-facing one-line skill description for planners.
def capture_logic_analyzer(
    candidate_ref: str = '',
    baseline_ref: str = '',
    recipe: str = '',
    corner: str = '',
    mode: str = '',
    instrument: str = '',
    params: dict | None = None,
) -> dict:
    """Capture one logic-analyzer trace.

    Purpose:
        Skill ``capture_logic_analyzer`` for the Instrument Control agent (``instrument_control``). Drives approved instruments under voltage/current/temperature limits.
        Silicon-validation meaning: this skill participates in bring-up, lab procedure, instrument control, firmware/test programs, telemetry analysis, characterization, failure correlation, or errata drafting under approved safety bounds. This callable only builds a ``tool_observation`` payload;
        heavy EDA or bench work happens in a bound adapter.

    Args:
        candidate_ref: Candidate the job reads. Empty may mean latest candidate for the adapter.
        baseline_ref: Baseline used when the job compares against a known result. Empty means no explicit baseline pin.
        recipe: Versioned tool recipe. The adapter rejects an unknown recipe. Empty uses the flow default recipe.
        corner: PVT corner. Empty when the job is not corner-specific. Empty reads every available corner.
        mode: Functional or analysis mode. Empty when the job is not mode-specific. Empty reads every available mode.
        instrument: Instrument id. Empty means the procedure's default instrument.
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
    # Observation payload for skill 'capture_logic_analyzer' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Candidate the job reads.
        'baseline_ref': baseline_ref,  # Baseline used when the job compares against a known result.
        'recipe': recipe,  # Versioned tool recipe. The adapter rejects an unknown recipe.
        'corner': corner,  # PVT corner. Empty when the job is not corner-specific.
        'mode': mode,  # Functional or analysis mode. Empty when the job is not mode-specific.
        'instrument': instrument,  # Instrument id.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'capture_logic_analyzer',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='instrument_control',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Set a thermal chamber or plate inside the approved temperature limit.')  # Fleet-facing one-line skill description for planners.
def set_thermal_setpoint(
    candidate_ref: str = '',
    baseline_ref: str = '',
    recipe: str = '',
    corner: str = '',
    mode: str = '',
    instrument: str = '',
    temperature_limit: str = '',
    params: dict | None = None,
) -> dict:
    """Set a thermal chamber or plate inside the approved temperature limit.

    Purpose:
        Skill ``set_thermal_setpoint`` for the Instrument Control agent (``instrument_control``). Drives approved instruments under voltage/current/temperature limits.
        Silicon-validation meaning: this skill participates in bring-up, lab procedure, instrument control, firmware/test programs, telemetry analysis, characterization, failure correlation, or errata drafting under approved safety bounds. This callable only builds a ``tool_observation`` payload;
        heavy EDA or bench work happens in a bound adapter.

    Args:
        candidate_ref: Candidate the job reads. Empty may mean latest candidate for the adapter.
        baseline_ref: Baseline used when the job compares against a known result. Empty means no explicit baseline pin.
        recipe: Versioned tool recipe. The adapter rejects an unknown recipe. Empty uses the flow default recipe.
        corner: PVT corner. Empty when the job is not corner-specific. Empty reads every available corner.
        mode: Functional or analysis mode. Empty when the job is not mode-specific. Empty reads every available mode.
        instrument: Instrument id. Empty means the procedure's default instrument.
        temperature_limit: Maximum temperature in Celsius. Copied from approved limits; must not be widened here.
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
    # Observation payload for skill 'set_thermal_setpoint' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Candidate the job reads.
        'baseline_ref': baseline_ref,  # Baseline used when the job compares against a known result.
        'recipe': recipe,  # Versioned tool recipe. The adapter rejects an unknown recipe.
        'corner': corner,  # PVT corner. Empty when the job is not corner-specific.
        'mode': mode,  # Functional or analysis mode. Empty when the job is not mode-specific.
        'instrument': instrument,  # Instrument id.
        'temperature_limit': temperature_limit,  # Maximum temperature in Celsius.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'set_thermal_setpoint',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='instrument_control',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Read the live state of one instrument.')  # Fleet-facing one-line skill description for planners.
def read_instrument_state(
    candidate_ref: str = '',
    report_ref: str = '',
    corner: str = '',
    mode: str = '',
    instrument: str = '',
    params: dict | None = None,
) -> dict:
    """Read the live state of one instrument.

    Purpose:
        Skill ``read_instrument_state`` for the Instrument Control agent (``instrument_control``). Drives approved instruments under voltage/current/temperature limits.
        Silicon-validation meaning: this skill participates in bring-up, lab procedure, instrument control, firmware/test programs, telemetry analysis, characterization, failure correlation, or errata drafting under approved safety bounds. This callable only builds a ``tool_observation`` payload;
        heavy EDA or bench work happens in a bound adapter.

    Args:
        candidate_ref: Candidate the job reads. Empty may mean latest candidate for the adapter.
        report_ref: Artifact URI of the report. Empty reads the latest report for this candidate. Empty reads the latest report for the candidate.
        corner: PVT corner. Empty when the job is not corner-specific. Empty reads every available corner.
        mode: Functional or analysis mode. Empty when the job is not mode-specific. Empty reads every available mode.
        instrument: Instrument id. Empty means the procedure's default instrument.
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
    # Observation payload for skill 'read_instrument_state' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Candidate the job reads.
        'report_ref': report_ref,  # Artifact URI of the report. Empty reads the latest report for this candidate.
        'corner': corner,  # PVT corner. Empty when the job is not corner-specific.
        'mode': mode,  # Functional or analysis mode. Empty when the job is not mode-specific.
        'instrument': instrument,  # Instrument id.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'read_instrument_state',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='instrument_control',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Read the approval record required before this procedure runs.')  # Fleet-facing one-line skill description for planners.
def read_procedure_approval(
    candidate_ref: str = '',
    report_ref: str = '',
    corner: str = '',
    mode: str = '',
    params: dict | None = None,
) -> dict:
    """Read the approval record required before this procedure runs.

    Purpose:
        Skill ``read_procedure_approval`` for the Instrument Control agent (``instrument_control``). Drives approved instruments under voltage/current/temperature limits.
        Silicon-validation meaning: this skill participates in bring-up, lab procedure, instrument control, firmware/test programs, telemetry analysis, characterization, failure correlation, or errata drafting under approved safety bounds. This callable only builds a ``tool_observation`` payload;
        heavy EDA or bench work happens in a bound adapter.

    Args:
        candidate_ref: Candidate the job reads. Empty may mean latest candidate for the adapter.
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
    # Observation payload for skill 'read_procedure_approval' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Candidate the job reads.
        'report_ref': report_ref,  # Artifact URI of the report. Empty reads the latest report for this candidate.
        'corner': corner,  # PVT corner. Empty when the job is not corner-specific.
        'mode': mode,  # Functional or analysis mode. Empty when the job is not mode-specific.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'read_procedure_approval',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='instrument_control',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Check a command against the approved voltage, current, and temperature limits.')  # Fleet-facing one-line skill description for planners.
def check_command_against_bounds(
    candidate_ref: str = '',
    report_ref: str = '',
    corner: str = '',
    mode: str = '',
    params: dict | None = None,
) -> dict:
    """Check a command against the approved voltage, current, and temperature limits.

    Purpose:
        Skill ``check_command_against_bounds`` for the Instrument Control agent (``instrument_control``). Drives approved instruments under voltage/current/temperature limits.
        Silicon-validation meaning: this skill participates in bring-up, lab procedure, instrument control, firmware/test programs, telemetry analysis, characterization, failure correlation, or errata drafting under approved safety bounds. This callable only builds a ``tool_observation`` payload;
        heavy EDA or bench work happens in a bound adapter.

    Args:
        candidate_ref: Candidate the job reads. Empty may mean latest candidate for the adapter.
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
    # Observation payload for skill 'check_command_against_bounds' — keys align with config.yaml skill params.
    payload = {
        'candidate_ref': candidate_ref,  # Candidate the job reads.
        'report_ref': report_ref,  # Artifact URI of the report. Empty reads the latest report for this candidate.
        'corner': corner,  # PVT corner. Empty when the job is not corner-specific.
        'mode': mode,  # Functional or analysis mode. Empty when the job is not mode-specific.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'check_command_against_bounds',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='instrument_control',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Record the command, instrument, limits, and operator approval ref.')  # Fleet-facing one-line skill description for planners.
def record_instrument_command(
    summary: str = '',
    evidence_refs: str = '',
    severity: str = '',
    recommended_recipient: str = '',
    params: dict | None = None,
) -> dict:
    """Record the command, instrument, limits, and operator approval ref.

    Purpose:
        Skill ``record_instrument_command`` for the Instrument Control agent (``instrument_control``). Drives approved instruments under voltage/current/temperature limits.
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
    # Observation payload for skill 'record_instrument_command' — keys align with config.yaml skill params.
    payload = {
        'summary': summary,  # One-sentence finding.
        'evidence_refs': evidence_refs,  # Comma-separated artifact URIs that support the finding.
        'severity': severity,  # low, medium, high, or critical.
        'recommended_recipient': recommended_recipient,  # Agent id that should act on the finding.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'record_instrument_command',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='instrument_control',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Store the measurement with board, voltage, temperature, and instrument state.')  # Fleet-facing one-line skill description for planners.
def record_measurement(
    summary: str = '',
    evidence_refs: str = '',
    severity: str = '',
    recommended_recipient: str = '',
    params: dict | None = None,
) -> dict:
    """Store the measurement with board, voltage, temperature, and instrument state.

    Purpose:
        Skill ``record_measurement`` for the Instrument Control agent (``instrument_control``). Drives approved instruments under voltage/current/temperature limits.
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
    # Observation payload for skill 'record_measurement' — keys align with config.yaml skill params.
    payload = {
        'summary': summary,  # One-sentence finding.
        'evidence_refs': evidence_refs,  # Comma-separated artifact URIs that support the finding.
        'severity': severity,  # low, medium, high, or critical.
        'recommended_recipient': recommended_recipient,  # Agent id that should act on the finding.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'record_measurement',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='instrument_control',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Publish a command that would exceed a configured limit. The adapter must not run it.')  # Fleet-facing one-line skill description for planners.
def flag_command_over_limit(
    summary: str = '',
    evidence_refs: str = '',
    severity: str = '',
    recommended_recipient: str = '',
    params: dict | None = None,
) -> dict:
    """Publish a command that would exceed a configured limit. The adapter must not run it.

    Purpose:
        Skill ``flag_command_over_limit`` for the Instrument Control agent (``instrument_control``). Drives approved instruments under voltage/current/temperature limits.
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
    # Observation payload for skill 'flag_command_over_limit' — keys align with config.yaml skill params.
    payload = {
        'summary': summary,  # One-sentence finding.
        'evidence_refs': evidence_refs,  # Comma-separated artifact URIs that support the finding.
        'severity': severity,  # low, medium, high, or critical.
        'recommended_recipient': recommended_recipient,  # Agent id that should act on the finding.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'flag_command_over_limit',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='instrument_control',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Publish a run requested without an approval-point record.')  # Fleet-facing one-line skill description for planners.
def flag_unapproved_procedure(
    summary: str = '',
    evidence_refs: str = '',
    severity: str = '',
    recommended_recipient: str = '',
    params: dict | None = None,
) -> dict:
    """Publish a run requested without an approval-point record.

    Purpose:
        Skill ``flag_unapproved_procedure`` for the Instrument Control agent (``instrument_control``). Drives approved instruments under voltage/current/temperature limits.
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
    # Observation payload for skill 'flag_unapproved_procedure' — keys align with config.yaml skill params.
    payload = {
        'summary': summary,  # One-sentence finding.
        'evidence_refs': evidence_refs,  # Comma-separated artifact URIs that support the finding.
        'severity': severity,  # low, medium, high, or critical.
        'recommended_recipient': recommended_recipient,  # Agent id that should act on the finding.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'flag_unapproved_procedure',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='instrument_control',  # Provenance: which specialist emitted this observation.
    )


@tool(description='Record every command and measurement in this session.')  # Fleet-facing one-line skill description for planners.
def record_instrument_session(
    summary: str = '',
    evidence_refs: str = '',
    severity: str = '',
    recommended_recipient: str = '',
    params: dict | None = None,
) -> dict:
    """Record every command and measurement in this session.

    Purpose:
        Skill ``record_instrument_session`` for the Instrument Control agent (``instrument_control``). Drives approved instruments under voltage/current/temperature limits.
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
    # Observation payload for skill 'record_instrument_session' — keys align with config.yaml skill params.
    payload = {
        'summary': summary,  # One-sentence finding.
        'evidence_refs': evidence_refs,  # Comma-separated artifact URIs that support the finding.
        'severity': severity,  # low, medium, high, or critical.
        'recommended_recipient': recommended_recipient,  # Agent id that should act on the finding.
    }
    if params:  # Merge optional adapter-specific overrides without dropping core keys.
        payload.update(params)  # Later keys win; used for framework-specific DFT/lab fields.
    return tool_observation(  # Hand off to adapter layer; may be not_run until bound.
        'record_instrument_session',  # Skill id recorded in telemetry and journals.
        payload,  # Structured arguments for the DFT/lab/program adapter.
        agent_id='instrument_control',  # Provenance: which specialist emitted this observation.
    )
