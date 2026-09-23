"""Tools for Extraction Agent.

Each function below is the stable operation contract for parasitic extraction (SPEF) for signoff STA and power. A framework
adapter performs the real work (OpenROAD, OpenSTA, licensed DRC/LVS/IR/thermal/power
tools, or simulators) when ``EDA_FRAMEWORK`` is bound.

Until a framework is bound, every call returns status ``not_run`` and does **not** invoke
OpenROAD, Yosys, OpenSTA, a licensed tool, or a simulator. That keep-safe behavior lets
the fleet exercise planning, journaling, and telemetry without mutating silicon artifacts.

EDA focus for this module: SPEF completeness, extraction corners, OpenROAD estimate_parasitics.
Observations always stamp ``agent_id='extraction'`` so signoff_validator and leads can audit
which worker claimed a check.
"""

from __future__ import annotations  # Allow modern ``dict | None`` annotations without runtime eval.

from packages.agent_sdk import tool  # Decorator registering the callable as an Agent Fleet skill.
from domains.eda.adapters import tool_observation  # Builds the not_run/adapted observation dict for silicon memory.


@tool(description='Read the corners extraction must produce.')  # Registers ``read_required_extraction_corners`` as a discoverable signoff skill.
def read_required_extraction_corners(
    candidate_ref: str = '',  # Artifact URI of the isolated layout/netlist candidate under signoff analysis.
    report_ref: str = '',  # Artifact URI of a prior report; empty means read the latest report for the candidate.
    corner: str = '',  # PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
    mode: str = '',  # Functional or analysis mode (for example functional vs scan); empty when unused.
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """Read the corners extraction must produce.

    Purpose:
        Stable operation contract for ``read_required_extraction_corners`` in the Extraction Agent. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of parasitic extraction (SPEF) for signoff STA and power. Relates to SPEF completeness, extraction corners, OpenROAD estimate_parasitics.

    Args:
        candidate_ref: Artifact URI of the isolated layout/netlist candidate under signoff analysis.
        report_ref: Artifact URI of a prior report; empty means read the latest report for the candidate.
        corner: PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
        mode: Functional or analysis mode (for example functional vs scan); empty when unused.
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='extraction'``, and run status. Callers must not treat ``not_run``
        as a passing signoff result.

    Side effects:
        None on the layout/netlist until an adapter is bound. May append to local journal
        memory when the AgentService records the skill invocation.

    Failures:
        Does not raise for unbound frameworks; returns ``not_run``. Adapters may raise or
        return error statuses for unknown recipes, missing candidates, or tool crashes.
    """
    # Assemble the explicit signoff arguments into a flat adapter payload.
    payload = {
        'candidate_ref': candidate_ref,  # Which candidate layout/netlist this signoff operation reads.
        'report_ref': report_ref,  # Which report artifact to parse; empty selects latest for the candidate.
        'corner': corner,  # Which PVT/extraction/timing corner scopes the job.
        'mode': mode,  # Which functional/analysis mode scopes the job.
    }
    # Merge optional adapter extras (windows, deck paths, SPEF overrides) without dropping required keys.
    if params:
        # Flatten extras into the same payload dict consumed by tool_observation / the EDA adapter.
        payload.update(params)
    # Emit a structured observation stamped with agent_id='extraction' for audit and telemetry.
    return tool_observation(
        'read_required_extraction_corners',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='extraction',  # Ties the observation to this Extraction Agent worker.
    )


@tool(description='Write the extraction configuration and corner list.')  # Registers ``write_extraction_config`` as a discoverable signoff skill.
def write_extraction_config(
    candidate_ref: str = '',  # Artifact URI of the isolated layout/netlist candidate under signoff analysis.
    baseline_ref: str = '',  # Artifact URI of the canonical baseline used for comparison or ECO descent.
    hypothesis: str = '',  # Design-change hypothesis describing what the write/apply step will attempt.
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """Write the extraction configuration and corner list.

    Purpose:
        Stable operation contract for ``write_extraction_config`` in the Extraction Agent. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of parasitic extraction (SPEF) for signoff STA and power. Relates to SPEF completeness, extraction corners, OpenROAD estimate_parasitics.

    Args:
        candidate_ref: Artifact URI of the isolated layout/netlist candidate under signoff analysis.
        baseline_ref: Artifact URI of the canonical baseline used for comparison or ECO descent.
        hypothesis: Design-change hypothesis describing what the write/apply step will attempt.
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='extraction'``, and run status. Callers must not treat ``not_run``
        as a passing signoff result.

    Side effects:
        None on the layout/netlist until an adapter is bound. May append to local journal
        memory when the AgentService records the skill invocation.

    Failures:
        Does not raise for unbound frameworks; returns ``not_run``. Adapters may raise or
        return error statuses for unknown recipes, missing candidates, or tool crashes.
    """
    # Assemble the explicit signoff arguments into a flat adapter payload.
    payload = {
        'candidate_ref': candidate_ref,  # Which candidate layout/netlist this signoff operation reads.
        'baseline_ref': baseline_ref,  # Which canonical baseline to compare against or descend from for ECO.
        'hypothesis': hypothesis,  # Intended physical or constraint change under test.
    }
    # Merge optional adapter extras (windows, deck paths, SPEF overrides) without dropping required keys.
    if params:
        # Flatten extras into the same payload dict consumed by tool_observation / the EDA adapter.
        payload.update(params)
    # Emit a structured observation stamped with agent_id='extraction' for audit and telemetry.
    return tool_observation(
        'write_extraction_config',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='extraction',  # Ties the observation to this Extraction Agent worker.
    )


@tool(description='Extract parasitics for the configured corners. Adapter target: OpenROAD estimate_parasitics or the bound extractor.')  # Registers ``extract_parasitics`` as a discoverable signoff skill.
def extract_parasitics(
    candidate_ref: str = '',  # Artifact URI of the isolated layout/netlist candidate under signoff analysis.
    baseline_ref: str = '',  # Artifact URI of the canonical baseline used for comparison or ECO descent.
    recipe: str = '',  # Versioned EDA tool recipe (deck/flow/version); adapters reject unknown recipes.
    corner: str = '',  # PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
    mode: str = '',  # Functional or analysis mode (for example functional vs scan); empty when unused.
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """Extract parasitics for the configured corners. Adapter target: OpenROAD estimate_parasitics or the bound extractor.

    Purpose:
        Stable operation contract for ``extract_parasitics`` in the Extraction Agent. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of parasitic extraction (SPEF) for signoff STA and power. Relates to SPEF completeness, extraction corners, OpenROAD estimate_parasitics.

    Args:
        candidate_ref: Artifact URI of the isolated layout/netlist candidate under signoff analysis.
        baseline_ref: Artifact URI of the canonical baseline used for comparison or ECO descent.
        recipe: Versioned EDA tool recipe (deck/flow/version); adapters reject unknown recipes.
        corner: PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
        mode: Functional or analysis mode (for example functional vs scan); empty when unused.
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='extraction'``, and run status. Callers must not treat ``not_run``
        as a passing signoff result.

    Side effects:
        None on the layout/netlist until an adapter is bound. May append to local journal
        memory when the AgentService records the skill invocation.

    Failures:
        Does not raise for unbound frameworks; returns ``not_run``. Adapters may raise or
        return error statuses for unknown recipes, missing candidates, or tool crashes.
    """
    # Assemble the explicit signoff arguments into a flat adapter payload.
    payload = {
        'candidate_ref': candidate_ref,  # Which candidate layout/netlist this signoff operation reads.
        'baseline_ref': baseline_ref,  # Which canonical baseline to compare against or descend from for ECO.
        'recipe': recipe,  # Which versioned EDA recipe/deck the adapter must load.
        'corner': corner,  # Which PVT/extraction/timing corner scopes the job.
        'mode': mode,  # Which functional/analysis mode scopes the job.
    }
    # Merge optional adapter extras (windows, deck paths, SPEF overrides) without dropping required keys.
    if params:
        # Flatten extras into the same payload dict consumed by tool_observation / the EDA adapter.
        payload.update(params)
    # Emit a structured observation stamped with agent_id='extraction' for audit and telemetry.
    return tool_observation(
        'extract_parasitics',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='extraction',  # Ties the observation to this Extraction Agent worker.
    )


@tool(description='Write the SPEF for one corner.')  # Registers ``write_spef`` as a discoverable signoff skill.
def write_spef(
    candidate_ref: str = '',  # Artifact URI of the isolated layout/netlist candidate under signoff analysis.
    baseline_ref: str = '',  # Artifact URI of the canonical baseline used for comparison or ECO descent.
    recipe: str = '',  # Versioned EDA tool recipe (deck/flow/version); adapters reject unknown recipes.
    corner: str = '',  # PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
    mode: str = '',  # Functional or analysis mode (for example functional vs scan); empty when unused.
    corner_name: str = '',  # Explicit SPEF corner tag written into the parasitic artifact name.
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """Write the SPEF for one corner.

    Purpose:
        Stable operation contract for ``write_spef`` in the Extraction Agent. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of parasitic extraction (SPEF) for signoff STA and power. Relates to SPEF completeness, extraction corners, OpenROAD estimate_parasitics.

    Args:
        candidate_ref: Artifact URI of the isolated layout/netlist candidate under signoff analysis.
        baseline_ref: Artifact URI of the canonical baseline used for comparison or ECO descent.
        recipe: Versioned EDA tool recipe (deck/flow/version); adapters reject unknown recipes.
        corner: PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
        mode: Functional or analysis mode (for example functional vs scan); empty when unused.
        corner_name: Explicit SPEF corner tag written into the parasitic artifact name.
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='extraction'``, and run status. Callers must not treat ``not_run``
        as a passing signoff result.

    Side effects:
        None on the layout/netlist until an adapter is bound. May append to local journal
        memory when the AgentService records the skill invocation.

    Failures:
        Does not raise for unbound frameworks; returns ``not_run``. Adapters may raise or
        return error statuses for unknown recipes, missing candidates, or tool crashes.
    """
    # Assemble the explicit signoff arguments into a flat adapter payload.
    payload = {
        'candidate_ref': candidate_ref,  # Which candidate layout/netlist this signoff operation reads.
        'baseline_ref': baseline_ref,  # Which canonical baseline to compare against or descend from for ECO.
        'recipe': recipe,  # Which versioned EDA recipe/deck the adapter must load.
        'corner': corner,  # Which PVT/extraction/timing corner scopes the job.
        'mode': mode,  # Which functional/analysis mode scopes the job.
        'corner_name': corner_name,  # SPEF corner name embedded in the written parasitic artifact.
    }
    # Merge optional adapter extras (windows, deck paths, SPEF overrides) without dropping required keys.
    if params:
        # Flatten extras into the same payload dict consumed by tool_observation / the EDA adapter.
        payload.update(params)
    # Emit a structured observation stamped with agent_id='extraction' for audit and telemetry.
    return tool_observation(
        'write_spef',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='extraction',  # Ties the observation to this Extraction Agent worker.
    )


@tool(description='Check that every required corner was extracted.')  # Registers ``validate_extraction_corners`` as a discoverable signoff skill.
def validate_extraction_corners(
    candidate_ref: str = '',  # Artifact URI of the isolated layout/netlist candidate under signoff analysis.
    report_ref: str = '',  # Artifact URI of a prior report; empty means read the latest report for the candidate.
    corner: str = '',  # PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
    mode: str = '',  # Functional or analysis mode (for example functional vs scan); empty when unused.
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """Check that every required corner was extracted.

    Purpose:
        Stable operation contract for ``validate_extraction_corners`` in the Extraction Agent. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of parasitic extraction (SPEF) for signoff STA and power. Relates to SPEF completeness, extraction corners, OpenROAD estimate_parasitics.

    Args:
        candidate_ref: Artifact URI of the isolated layout/netlist candidate under signoff analysis.
        report_ref: Artifact URI of a prior report; empty means read the latest report for the candidate.
        corner: PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
        mode: Functional or analysis mode (for example functional vs scan); empty when unused.
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='extraction'``, and run status. Callers must not treat ``not_run``
        as a passing signoff result.

    Side effects:
        None on the layout/netlist until an adapter is bound. May append to local journal
        memory when the AgentService records the skill invocation.

    Failures:
        Does not raise for unbound frameworks; returns ``not_run``. Adapters may raise or
        return error statuses for unknown recipes, missing candidates, or tool crashes.
    """
    # Assemble the explicit signoff arguments into a flat adapter payload.
    payload = {
        'candidate_ref': candidate_ref,  # Which candidate layout/netlist this signoff operation reads.
        'report_ref': report_ref,  # Which report artifact to parse; empty selects latest for the candidate.
        'corner': corner,  # Which PVT/extraction/timing corner scopes the job.
        'mode': mode,  # Which functional/analysis mode scopes the job.
    }
    # Merge optional adapter extras (windows, deck paths, SPEF overrides) without dropping required keys.
    if params:
        # Flatten extras into the same payload dict consumed by tool_observation / the EDA adapter.
        payload.update(params)
    # Emit a structured observation stamped with agent_id='extraction' for audit and telemetry.
    return tool_observation(
        'validate_extraction_corners',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='extraction',  # Ties the observation to this Extraction Agent worker.
    )


@tool(description='Check for missing nets, layers, and couplings.')  # Registers ``check_extraction_completeness`` as a discoverable signoff skill.
def check_extraction_completeness(
    candidate_ref: str = '',  # Artifact URI of the isolated layout/netlist candidate under signoff analysis.
    report_ref: str = '',  # Artifact URI of a prior report; empty means read the latest report for the candidate.
    corner: str = '',  # PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
    mode: str = '',  # Functional or analysis mode (for example functional vs scan); empty when unused.
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """Check for missing nets, layers, and couplings.

    Purpose:
        Stable operation contract for ``check_extraction_completeness`` in the Extraction Agent. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of parasitic extraction (SPEF) for signoff STA and power. Relates to SPEF completeness, extraction corners, OpenROAD estimate_parasitics.

    Args:
        candidate_ref: Artifact URI of the isolated layout/netlist candidate under signoff analysis.
        report_ref: Artifact URI of a prior report; empty means read the latest report for the candidate.
        corner: PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
        mode: Functional or analysis mode (for example functional vs scan); empty when unused.
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='extraction'``, and run status. Callers must not treat ``not_run``
        as a passing signoff result.

    Side effects:
        None on the layout/netlist until an adapter is bound. May append to local journal
        memory when the AgentService records the skill invocation.

    Failures:
        Does not raise for unbound frameworks; returns ``not_run``. Adapters may raise or
        return error statuses for unknown recipes, missing candidates, or tool crashes.
    """
    # Assemble the explicit signoff arguments into a flat adapter payload.
    payload = {
        'candidate_ref': candidate_ref,  # Which candidate layout/netlist this signoff operation reads.
        'report_ref': report_ref,  # Which report artifact to parse; empty selects latest for the candidate.
        'corner': corner,  # Which PVT/extraction/timing corner scopes the job.
        'mode': mode,  # Which functional/analysis mode scopes the job.
    }
    # Merge optional adapter extras (windows, deck paths, SPEF overrides) without dropping required keys.
    if params:
        # Flatten extras into the same payload dict consumed by tool_observation / the EDA adapter.
        payload.update(params)
    # Emit a structured observation stamped with agent_id='extraction' for audit and telemetry.
    return tool_observation(
        'check_extraction_completeness',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='extraction',  # Ties the observation to this Extraction Agent worker.
    )


@tool(description='Check design name, units, and divider in the SPEF header.')  # Registers ``check_spef_header`` as a discoverable signoff skill.
def check_spef_header(
    candidate_ref: str = '',  # Artifact URI of the isolated layout/netlist candidate under signoff analysis.
    report_ref: str = '',  # Artifact URI of a prior report; empty means read the latest report for the candidate.
    corner: str = '',  # PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
    mode: str = '',  # Functional or analysis mode (for example functional vs scan); empty when unused.
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """Check design name, units, and divider in the SPEF header.

    Purpose:
        Stable operation contract for ``check_spef_header`` in the Extraction Agent. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of parasitic extraction (SPEF) for signoff STA and power. Relates to SPEF completeness, extraction corners, OpenROAD estimate_parasitics.

    Args:
        candidate_ref: Artifact URI of the isolated layout/netlist candidate under signoff analysis.
        report_ref: Artifact URI of a prior report; empty means read the latest report for the candidate.
        corner: PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
        mode: Functional or analysis mode (for example functional vs scan); empty when unused.
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='extraction'``, and run status. Callers must not treat ``not_run``
        as a passing signoff result.

    Side effects:
        None on the layout/netlist until an adapter is bound. May append to local journal
        memory when the AgentService records the skill invocation.

    Failures:
        Does not raise for unbound frameworks; returns ``not_run``. Adapters may raise or
        return error statuses for unknown recipes, missing candidates, or tool crashes.
    """
    # Assemble the explicit signoff arguments into a flat adapter payload.
    payload = {
        'candidate_ref': candidate_ref,  # Which candidate layout/netlist this signoff operation reads.
        'report_ref': report_ref,  # Which report artifact to parse; empty selects latest for the candidate.
        'corner': corner,  # Which PVT/extraction/timing corner scopes the job.
        'mode': mode,  # Which functional/analysis mode scopes the job.
    }
    # Merge optional adapter extras (windows, deck paths, SPEF overrides) without dropping required keys.
    if params:
        # Flatten extras into the same payload dict consumed by tool_observation / the EDA adapter.
        payload.update(params)
    # Emit a structured observation stamped with agent_id='extraction' for audit and telemetry.
    return tool_observation(
        'check_spef_header',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='extraction',  # Ties the observation to this Extraction Agent worker.
    )


@tool(description='Compare extracted nets with the routed netlist.')  # Registers ``compare_spef_to_routed_nets`` as a discoverable signoff skill.
def compare_spef_to_routed_nets(
    candidate_ref: str = '',  # Artifact URI of the isolated layout/netlist candidate under signoff analysis.
    report_ref: str = '',  # Artifact URI of a prior report; empty means read the latest report for the candidate.
    corner: str = '',  # PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
    mode: str = '',  # Functional or analysis mode (for example functional vs scan); empty when unused.
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """Compare extracted nets with the routed netlist.

    Purpose:
        Stable operation contract for ``compare_spef_to_routed_nets`` in the Extraction Agent. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of parasitic extraction (SPEF) for signoff STA and power. Relates to SPEF completeness, extraction corners, OpenROAD estimate_parasitics.

    Args:
        candidate_ref: Artifact URI of the isolated layout/netlist candidate under signoff analysis.
        report_ref: Artifact URI of a prior report; empty means read the latest report for the candidate.
        corner: PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
        mode: Functional or analysis mode (for example functional vs scan); empty when unused.
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='extraction'``, and run status. Callers must not treat ``not_run``
        as a passing signoff result.

    Side effects:
        None on the layout/netlist until an adapter is bound. May append to local journal
        memory when the AgentService records the skill invocation.

    Failures:
        Does not raise for unbound frameworks; returns ``not_run``. Adapters may raise or
        return error statuses for unknown recipes, missing candidates, or tool crashes.
    """
    # Assemble the explicit signoff arguments into a flat adapter payload.
    payload = {
        'candidate_ref': candidate_ref,  # Which candidate layout/netlist this signoff operation reads.
        'report_ref': report_ref,  # Which report artifact to parse; empty selects latest for the candidate.
        'corner': corner,  # Which PVT/extraction/timing corner scopes the job.
        'mode': mode,  # Which functional/analysis mode scopes the job.
    }
    # Merge optional adapter extras (windows, deck paths, SPEF overrides) without dropping required keys.
    if params:
        # Flatten extras into the same payload dict consumed by tool_observation / the EDA adapter.
        payload.update(params)
    # Emit a structured observation stamped with agent_id='extraction' for audit and telemetry.
    return tool_observation(
        'compare_spef_to_routed_nets',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='extraction',  # Ties the observation to this Extraction Agent worker.
    )


@tool(description='Read the extraction log and warnings.')  # Registers ``read_extraction_log`` as a discoverable signoff skill.
def read_extraction_log(
    candidate_ref: str = '',  # Artifact URI of the isolated layout/netlist candidate under signoff analysis.
    report_ref: str = '',  # Artifact URI of a prior report; empty means read the latest report for the candidate.
    corner: str = '',  # PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
    mode: str = '',  # Functional or analysis mode (for example functional vs scan); empty when unused.
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """Read the extraction log and warnings.

    Purpose:
        Stable operation contract for ``read_extraction_log`` in the Extraction Agent. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of parasitic extraction (SPEF) for signoff STA and power. Relates to SPEF completeness, extraction corners, OpenROAD estimate_parasitics.

    Args:
        candidate_ref: Artifact URI of the isolated layout/netlist candidate under signoff analysis.
        report_ref: Artifact URI of a prior report; empty means read the latest report for the candidate.
        corner: PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
        mode: Functional or analysis mode (for example functional vs scan); empty when unused.
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='extraction'``, and run status. Callers must not treat ``not_run``
        as a passing signoff result.

    Side effects:
        None on the layout/netlist until an adapter is bound. May append to local journal
        memory when the AgentService records the skill invocation.

    Failures:
        Does not raise for unbound frameworks; returns ``not_run``. Adapters may raise or
        return error statuses for unknown recipes, missing candidates, or tool crashes.
    """
    # Assemble the explicit signoff arguments into a flat adapter payload.
    payload = {
        'candidate_ref': candidate_ref,  # Which candidate layout/netlist this signoff operation reads.
        'report_ref': report_ref,  # Which report artifact to parse; empty selects latest for the candidate.
        'corner': corner,  # Which PVT/extraction/timing corner scopes the job.
        'mode': mode,  # Which functional/analysis mode scopes the job.
    }
    # Merge optional adapter extras (windows, deck paths, SPEF overrides) without dropping required keys.
    if params:
        # Flatten extras into the same payload dict consumed by tool_observation / the EDA adapter.
        payload.update(params)
    # Emit a structured observation stamped with agent_id='extraction' for audit and telemetry.
    return tool_observation(
        'read_extraction_log',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='extraction',  # Ties the observation to this Extraction Agent worker.
    )


@tool(description='Publish a required corner that was not extracted.')  # Registers ``flag_missing_extraction_corner`` as a discoverable signoff skill.
def flag_missing_extraction_corner(
    summary: str = '',  # One-sentence finding text published into engineering memory for downstream owners.
    evidence_refs: str = '',  # Comma-separated artifact URIs that substantiate the finding or decision.
    severity: str = '',  # Finding severity: low, medium, high, or critical for signoff triage.
    recommended_recipient: str = '',  # Agent id expected to act on the finding (for example routing_lead or eco_lead).
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """Publish a required corner that was not extracted.

    Purpose:
        Stable operation contract for ``flag_missing_extraction_corner`` in the Extraction Agent. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of parasitic extraction (SPEF) for signoff STA and power. Relates to SPEF completeness, extraction corners, OpenROAD estimate_parasitics.

    Args:
        summary: One-sentence finding text published into engineering memory for downstream owners.
        evidence_refs: Comma-separated artifact URIs that substantiate the finding or decision.
        severity: Finding severity: low, medium, high, or critical for signoff triage.
        recommended_recipient: Agent id expected to act on the finding (for example routing_lead or eco_lead).
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='extraction'``, and run status. Callers must not treat ``not_run``
        as a passing signoff result.

    Side effects:
        None on the layout/netlist until an adapter is bound. May append to local journal
        memory when the AgentService records the skill invocation.

    Failures:
        Does not raise for unbound frameworks; returns ``not_run``. Adapters may raise or
        return error statuses for unknown recipes, missing candidates, or tool crashes.
    """
    # Assemble the explicit signoff arguments into a flat adapter payload.
    payload = {
        'summary': summary,  # Finding text that downstream owners and signoff_validator will read.
        'evidence_refs': evidence_refs,  # Artifact URIs backing the finding for auditability.
        'severity': severity,  # Triage severity for the published finding.
        'recommended_recipient': recommended_recipient,  # Intended owner agent for the next repair or decision.
    }
    # Merge optional adapter extras (windows, deck paths, SPEF overrides) without dropping required keys.
    if params:
        # Flatten extras into the same payload dict consumed by tool_observation / the EDA adapter.
        payload.update(params)
    # Emit a structured observation stamped with agent_id='extraction' for audit and telemetry.
    return tool_observation(
        'flag_missing_extraction_corner',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='extraction',  # Ties the observation to this Extraction Agent worker.
    )


@tool(description='Publish missing nets or couplings.')  # Registers ``flag_incomplete_extraction`` as a discoverable signoff skill.
def flag_incomplete_extraction(
    summary: str = '',  # One-sentence finding text published into engineering memory for downstream owners.
    evidence_refs: str = '',  # Comma-separated artifact URIs that substantiate the finding or decision.
    severity: str = '',  # Finding severity: low, medium, high, or critical for signoff triage.
    recommended_recipient: str = '',  # Agent id expected to act on the finding (for example routing_lead or eco_lead).
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """Publish missing nets or couplings.

    Purpose:
        Stable operation contract for ``flag_incomplete_extraction`` in the Extraction Agent. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of parasitic extraction (SPEF) for signoff STA and power. Relates to SPEF completeness, extraction corners, OpenROAD estimate_parasitics.

    Args:
        summary: One-sentence finding text published into engineering memory for downstream owners.
        evidence_refs: Comma-separated artifact URIs that substantiate the finding or decision.
        severity: Finding severity: low, medium, high, or critical for signoff triage.
        recommended_recipient: Agent id expected to act on the finding (for example routing_lead or eco_lead).
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='extraction'``, and run status. Callers must not treat ``not_run``
        as a passing signoff result.

    Side effects:
        None on the layout/netlist until an adapter is bound. May append to local journal
        memory when the AgentService records the skill invocation.

    Failures:
        Does not raise for unbound frameworks; returns ``not_run``. Adapters may raise or
        return error statuses for unknown recipes, missing candidates, or tool crashes.
    """
    # Assemble the explicit signoff arguments into a flat adapter payload.
    payload = {
        'summary': summary,  # Finding text that downstream owners and signoff_validator will read.
        'evidence_refs': evidence_refs,  # Artifact URIs backing the finding for auditability.
        'severity': severity,  # Triage severity for the published finding.
        'recommended_recipient': recommended_recipient,  # Intended owner agent for the next repair or decision.
    }
    # Merge optional adapter extras (windows, deck paths, SPEF overrides) without dropping required keys.
    if params:
        # Flatten extras into the same payload dict consumed by tool_observation / the EDA adapter.
        payload.update(params)
    # Emit a structured observation stamped with agent_id='extraction' for audit and telemetry.
    return tool_observation(
        'flag_incomplete_extraction',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='extraction',  # Ties the observation to this Extraction Agent worker.
    )


@tool(description='Record the extractor, version, rule deck, and SPEF refs.')  # Registers ``record_extraction_provenance`` as a discoverable signoff skill.
def record_extraction_provenance(
    summary: str = '',  # One-sentence finding text published into engineering memory for downstream owners.
    evidence_refs: str = '',  # Comma-separated artifact URIs that substantiate the finding or decision.
    severity: str = '',  # Finding severity: low, medium, high, or critical for signoff triage.
    recommended_recipient: str = '',  # Agent id expected to act on the finding (for example routing_lead or eco_lead).
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """Record the extractor, version, rule deck, and SPEF refs.

    Purpose:
        Stable operation contract for ``record_extraction_provenance`` in the Extraction Agent. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of parasitic extraction (SPEF) for signoff STA and power. Relates to SPEF completeness, extraction corners, OpenROAD estimate_parasitics.

    Args:
        summary: One-sentence finding text published into engineering memory for downstream owners.
        evidence_refs: Comma-separated artifact URIs that substantiate the finding or decision.
        severity: Finding severity: low, medium, high, or critical for signoff triage.
        recommended_recipient: Agent id expected to act on the finding (for example routing_lead or eco_lead).
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='extraction'``, and run status. Callers must not treat ``not_run``
        as a passing signoff result.

    Side effects:
        None on the layout/netlist until an adapter is bound. May append to local journal
        memory when the AgentService records the skill invocation.

    Failures:
        Does not raise for unbound frameworks; returns ``not_run``. Adapters may raise or
        return error statuses for unknown recipes, missing candidates, or tool crashes.
    """
    # Assemble the explicit signoff arguments into a flat adapter payload.
    payload = {
        'summary': summary,  # Finding text that downstream owners and signoff_validator will read.
        'evidence_refs': evidence_refs,  # Artifact URIs backing the finding for auditability.
        'severity': severity,  # Triage severity for the published finding.
        'recommended_recipient': recommended_recipient,  # Intended owner agent for the next repair or decision.
    }
    # Merge optional adapter extras (windows, deck paths, SPEF overrides) without dropping required keys.
    if params:
        # Flatten extras into the same payload dict consumed by tool_observation / the EDA adapter.
        payload.update(params)
    # Emit a structured observation stamped with agent_id='extraction' for audit and telemetry.
    return tool_observation(
        'record_extraction_provenance',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='extraction',  # Ties the observation to this Extraction Agent worker.
    )
