"""Tools for DRC/LVS/ERC/DFM Agent.

Each function below is the stable operation contract for physical verification (DRC, LVS, ERC, density, DFM). A framework
adapter performs the real work (OpenROAD, OpenSTA, licensed DRC/LVS/IR/thermal/power
tools, or simulators) when ``EDA_FRAMEWORK`` is bound.

Until a framework is bound, every call returns status ``not_run`` and does **not** invoke
OpenROAD, Yosys, OpenSTA, a licensed tool, or a simulator. That keep-safe behavior lets
the fleet exercise planning, journaling, and telemetry without mutating silicon artifacts.

EDA focus for this module: DRC/LVS markers, rule decks, shorts/opens, manufacturability.
Observations always stamp ``agent_id='drc_lvs'`` so signoff_validator and leads can audit
which worker claimed a check.
"""

from __future__ import annotations  # Allow modern ``dict | None`` annotations without runtime eval.

from packages.agent_sdk import tool  # Decorator registering the callable as an Agent Fleet skill.
from domains.eda.eda import tool_observation  # Builds the not_run/adapted observation dict for silicon memory.


@tool(description='Run design-rule checks.')  # Registers ``run_drc`` as a discoverable signoff skill.
def run_drc(
    candidate_ref: str = '',  # Artifact URI of the isolated layout/netlist candidate under signoff analysis.
    baseline_ref: str = '',  # Artifact URI of the canonical baseline used for comparison or ECO descent.
    recipe: str = '',  # Versioned EDA tool recipe (deck/flow/version); adapters reject unknown recipes.
    corner: str = '',  # PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
    mode: str = '',  # Functional or analysis mode (for example functional vs scan); empty when unused.
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """Run design-rule checks.

    Purpose:
        Stable operation contract for ``run_drc`` in the DRC/LVS/ERC/DFM Agent. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of physical verification (DRC, LVS, ERC, density, DFM). Relates to DRC/LVS markers, rule decks, shorts/opens, manufacturability.

    Args:
        candidate_ref: Artifact URI of the isolated layout/netlist candidate under signoff analysis.
        baseline_ref: Artifact URI of the canonical baseline used for comparison or ECO descent.
        recipe: Versioned EDA tool recipe (deck/flow/version); adapters reject unknown recipes.
        corner: PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
        mode: Functional or analysis mode (for example functional vs scan); empty when unused.
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='drc_lvs'``, and run status. Callers must not treat ``not_run``
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
    # Emit a structured observation stamped with agent_id='drc_lvs' for audit and telemetry.
    return tool_observation(
        'run_drc',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='drc_lvs',  # Ties the observation to this DRC/LVS/ERC/DFM Agent worker.
    )


@tool(description='Run layout-versus-schematic.')  # Registers ``run_lvs`` as a discoverable signoff skill.
def run_lvs(
    candidate_ref: str = '',  # Artifact URI of the isolated layout/netlist candidate under signoff analysis.
    baseline_ref: str = '',  # Artifact URI of the canonical baseline used for comparison or ECO descent.
    recipe: str = '',  # Versioned EDA tool recipe (deck/flow/version); adapters reject unknown recipes.
    corner: str = '',  # PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
    mode: str = '',  # Functional or analysis mode (for example functional vs scan); empty when unused.
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """Run layout-versus-schematic.

    Purpose:
        Stable operation contract for ``run_lvs`` in the DRC/LVS/ERC/DFM Agent. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of physical verification (DRC, LVS, ERC, density, DFM). Relates to DRC/LVS markers, rule decks, shorts/opens, manufacturability.

    Args:
        candidate_ref: Artifact URI of the isolated layout/netlist candidate under signoff analysis.
        baseline_ref: Artifact URI of the canonical baseline used for comparison or ECO descent.
        recipe: Versioned EDA tool recipe (deck/flow/version); adapters reject unknown recipes.
        corner: PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
        mode: Functional or analysis mode (for example functional vs scan); empty when unused.
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='drc_lvs'``, and run status. Callers must not treat ``not_run``
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
    # Emit a structured observation stamped with agent_id='drc_lvs' for audit and telemetry.
    return tool_observation(
        'run_lvs',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='drc_lvs',  # Ties the observation to this DRC/LVS/ERC/DFM Agent worker.
    )


@tool(description='Run electrical-rule checks.')  # Registers ``run_erc`` as a discoverable signoff skill.
def run_erc(
    candidate_ref: str = '',  # Artifact URI of the isolated layout/netlist candidate under signoff analysis.
    baseline_ref: str = '',  # Artifact URI of the canonical baseline used for comparison or ECO descent.
    recipe: str = '',  # Versioned EDA tool recipe (deck/flow/version); adapters reject unknown recipes.
    corner: str = '',  # PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
    mode: str = '',  # Functional or analysis mode (for example functional vs scan); empty when unused.
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """Run electrical-rule checks.

    Purpose:
        Stable operation contract for ``run_erc`` in the DRC/LVS/ERC/DFM Agent. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of physical verification (DRC, LVS, ERC, density, DFM). Relates to DRC/LVS markers, rule decks, shorts/opens, manufacturability.

    Args:
        candidate_ref: Artifact URI of the isolated layout/netlist candidate under signoff analysis.
        baseline_ref: Artifact URI of the canonical baseline used for comparison or ECO descent.
        recipe: Versioned EDA tool recipe (deck/flow/version); adapters reject unknown recipes.
        corner: PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
        mode: Functional or analysis mode (for example functional vs scan); empty when unused.
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='drc_lvs'``, and run status. Callers must not treat ``not_run``
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
    # Emit a structured observation stamped with agent_id='drc_lvs' for audit and telemetry.
    return tool_observation(
        'run_erc',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='drc_lvs',  # Ties the observation to this DRC/LVS/ERC/DFM Agent worker.
    )


@tool(description='Run density checks.')  # Registers ``run_density`` as a discoverable signoff skill.
def run_density(
    candidate_ref: str = '',  # Artifact URI of the isolated layout/netlist candidate under signoff analysis.
    baseline_ref: str = '',  # Artifact URI of the canonical baseline used for comparison or ECO descent.
    recipe: str = '',  # Versioned EDA tool recipe (deck/flow/version); adapters reject unknown recipes.
    corner: str = '',  # PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
    mode: str = '',  # Functional or analysis mode (for example functional vs scan); empty when unused.
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """Run density checks.

    Purpose:
        Stable operation contract for ``run_density`` in the DRC/LVS/ERC/DFM Agent. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of physical verification (DRC, LVS, ERC, density, DFM). Relates to DRC/LVS markers, rule decks, shorts/opens, manufacturability.

    Args:
        candidate_ref: Artifact URI of the isolated layout/netlist candidate under signoff analysis.
        baseline_ref: Artifact URI of the canonical baseline used for comparison or ECO descent.
        recipe: Versioned EDA tool recipe (deck/flow/version); adapters reject unknown recipes.
        corner: PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
        mode: Functional or analysis mode (for example functional vs scan); empty when unused.
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='drc_lvs'``, and run status. Callers must not treat ``not_run``
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
    # Emit a structured observation stamped with agent_id='drc_lvs' for audit and telemetry.
    return tool_observation(
        'run_density',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='drc_lvs',  # Ties the observation to this DRC/LVS/ERC/DFM Agent worker.
    )


@tool(description='Run manufacturability checks.')  # Registers ``run_dfm`` as a discoverable signoff skill.
def run_dfm(
    candidate_ref: str = '',  # Artifact URI of the isolated layout/netlist candidate under signoff analysis.
    baseline_ref: str = '',  # Artifact URI of the canonical baseline used for comparison or ECO descent.
    recipe: str = '',  # Versioned EDA tool recipe (deck/flow/version); adapters reject unknown recipes.
    corner: str = '',  # PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
    mode: str = '',  # Functional or analysis mode (for example functional vs scan); empty when unused.
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """Run manufacturability checks.

    Purpose:
        Stable operation contract for ``run_dfm`` in the DRC/LVS/ERC/DFM Agent. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of physical verification (DRC, LVS, ERC, density, DFM). Relates to DRC/LVS markers, rule decks, shorts/opens, manufacturability.

    Args:
        candidate_ref: Artifact URI of the isolated layout/netlist candidate under signoff analysis.
        baseline_ref: Artifact URI of the canonical baseline used for comparison or ECO descent.
        recipe: Versioned EDA tool recipe (deck/flow/version); adapters reject unknown recipes.
        corner: PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
        mode: Functional or analysis mode (for example functional vs scan); empty when unused.
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='drc_lvs'``, and run status. Callers must not treat ``not_run``
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
    # Emit a structured observation stamped with agent_id='drc_lvs' for audit and telemetry.
    return tool_observation(
        'run_dfm',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='drc_lvs',  # Ties the observation to this DRC/LVS/ERC/DFM Agent worker.
    )


@tool(description='Read DRC markers.')  # Registers ``read_drc_markers`` as a discoverable signoff skill.
def read_drc_markers(
    candidate_ref: str = '',  # Artifact URI of the isolated layout/netlist candidate under signoff analysis.
    report_ref: str = '',  # Artifact URI of a prior report; empty means read the latest report for the candidate.
    corner: str = '',  # PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
    mode: str = '',  # Functional or analysis mode (for example functional vs scan); empty when unused.
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """Read DRC markers.

    Purpose:
        Stable operation contract for ``read_drc_markers`` in the DRC/LVS/ERC/DFM Agent. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of physical verification (DRC, LVS, ERC, density, DFM). Relates to DRC/LVS markers, rule decks, shorts/opens, manufacturability.

    Args:
        candidate_ref: Artifact URI of the isolated layout/netlist candidate under signoff analysis.
        report_ref: Artifact URI of a prior report; empty means read the latest report for the candidate.
        corner: PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
        mode: Functional or analysis mode (for example functional vs scan); empty when unused.
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='drc_lvs'``, and run status. Callers must not treat ``not_run``
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
    # Emit a structured observation stamped with agent_id='drc_lvs' for audit and telemetry.
    return tool_observation(
        'read_drc_markers',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='drc_lvs',  # Ties the observation to this DRC/LVS/ERC/DFM Agent worker.
    )


@tool(description='Read shorts, opens, and device mismatches.')  # Registers ``read_lvs_discrepancies`` as a discoverable signoff skill.
def read_lvs_discrepancies(
    candidate_ref: str = '',  # Artifact URI of the isolated layout/netlist candidate under signoff analysis.
    report_ref: str = '',  # Artifact URI of a prior report; empty means read the latest report for the candidate.
    corner: str = '',  # PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
    mode: str = '',  # Functional or analysis mode (for example functional vs scan); empty when unused.
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """Read shorts, opens, and device mismatches.

    Purpose:
        Stable operation contract for ``read_lvs_discrepancies`` in the DRC/LVS/ERC/DFM Agent. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of physical verification (DRC, LVS, ERC, density, DFM). Relates to DRC/LVS markers, rule decks, shorts/opens, manufacturability.

    Args:
        candidate_ref: Artifact URI of the isolated layout/netlist candidate under signoff analysis.
        report_ref: Artifact URI of a prior report; empty means read the latest report for the candidate.
        corner: PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
        mode: Functional or analysis mode (for example functional vs scan); empty when unused.
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='drc_lvs'``, and run status. Callers must not treat ``not_run``
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
    # Emit a structured observation stamped with agent_id='drc_lvs' for audit and telemetry.
    return tool_observation(
        'read_lvs_discrepancies',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='drc_lvs',  # Ties the observation to this DRC/LVS/ERC/DFM Agent worker.
    )


@tool(description='Read electrical-rule markers.')  # Registers ``read_erc_markers`` as a discoverable signoff skill.
def read_erc_markers(
    candidate_ref: str = '',  # Artifact URI of the isolated layout/netlist candidate under signoff analysis.
    report_ref: str = '',  # Artifact URI of a prior report; empty means read the latest report for the candidate.
    corner: str = '',  # PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
    mode: str = '',  # Functional or analysis mode (for example functional vs scan); empty when unused.
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """Read electrical-rule markers.

    Purpose:
        Stable operation contract for ``read_erc_markers`` in the DRC/LVS/ERC/DFM Agent. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of physical verification (DRC, LVS, ERC, density, DFM). Relates to DRC/LVS markers, rule decks, shorts/opens, manufacturability.

    Args:
        candidate_ref: Artifact URI of the isolated layout/netlist candidate under signoff analysis.
        report_ref: Artifact URI of a prior report; empty means read the latest report for the candidate.
        corner: PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
        mode: Functional or analysis mode (for example functional vs scan); empty when unused.
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='drc_lvs'``, and run status. Callers must not treat ``not_run``
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
    # Emit a structured observation stamped with agent_id='drc_lvs' for audit and telemetry.
    return tool_observation(
        'read_erc_markers',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='drc_lvs',  # Ties the observation to this DRC/LVS/ERC/DFM Agent worker.
    )


@tool(description='Cluster violations and separate real defects from setup errors.')  # Registers ``cluster_physical_violations`` as a discoverable signoff skill.
def cluster_physical_violations(
    summary: str = '',  # One-sentence finding text published into engineering memory for downstream owners.
    evidence_refs: str = '',  # Comma-separated artifact URIs that substantiate the finding or decision.
    severity: str = '',  # Finding severity: low, medium, high, or critical for signoff triage.
    recommended_recipient: str = '',  # Agent id expected to act on the finding (for example routing_lead or eco_lead).
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """Cluster violations and separate real defects from setup errors.

    Purpose:
        Stable operation contract for ``cluster_physical_violations`` in the DRC/LVS/ERC/DFM Agent. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of physical verification (DRC, LVS, ERC, density, DFM). Relates to DRC/LVS markers, rule decks, shorts/opens, manufacturability.

    Args:
        summary: One-sentence finding text published into engineering memory for downstream owners.
        evidence_refs: Comma-separated artifact URIs that substantiate the finding or decision.
        severity: Finding severity: low, medium, high, or critical for signoff triage.
        recommended_recipient: Agent id expected to act on the finding (for example routing_lead or eco_lead).
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='drc_lvs'``, and run status. Callers must not treat ``not_run``
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
    # Emit a structured observation stamped with agent_id='drc_lvs' for audit and telemetry.
    return tool_observation(
        'cluster_physical_violations',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='drc_lvs',  # Ties the observation to this DRC/LVS/ERC/DFM Agent worker.
    )


@tool(description='List markers caused by a wrong rule deck, cell view, or window.')  # Registers ``separate_setup_errors`` as a discoverable signoff skill.
def separate_setup_errors(
    candidate_ref: str = '',  # Artifact URI of the isolated layout/netlist candidate under signoff analysis.
    report_ref: str = '',  # Artifact URI of a prior report; empty means read the latest report for the candidate.
    corner: str = '',  # PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
    mode: str = '',  # Functional or analysis mode (for example functional vs scan); empty when unused.
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """List markers caused by a wrong rule deck, cell view, or window.

    Purpose:
        Stable operation contract for ``separate_setup_errors`` in the DRC/LVS/ERC/DFM Agent. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of physical verification (DRC, LVS, ERC, density, DFM). Relates to DRC/LVS markers, rule decks, shorts/opens, manufacturability.

    Args:
        candidate_ref: Artifact URI of the isolated layout/netlist candidate under signoff analysis.
        report_ref: Artifact URI of a prior report; empty means read the latest report for the candidate.
        corner: PVT / extraction / timing corner name; empty when the operation is corner-agnostic.
        mode: Functional or analysis mode (for example functional vs scan); empty when unused.
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='drc_lvs'``, and run status. Callers must not treat ``not_run``
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
    # Emit a structured observation stamped with agent_id='drc_lvs' for audit and telemetry.
    return tool_observation(
        'separate_setup_errors',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='drc_lvs',  # Ties the observation to this DRC/LVS/ERC/DFM Agent worker.
    )


@tool(description='Publish a marker that is not a setup error and is not waived.')  # Registers ``flag_real_physical_defect`` as a discoverable signoff skill.
def flag_real_physical_defect(
    summary: str = '',  # One-sentence finding text published into engineering memory for downstream owners.
    evidence_refs: str = '',  # Comma-separated artifact URIs that substantiate the finding or decision.
    severity: str = '',  # Finding severity: low, medium, high, or critical for signoff triage.
    recommended_recipient: str = '',  # Agent id expected to act on the finding (for example routing_lead or eco_lead).
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """Publish a marker that is not a setup error and is not waived.

    Purpose:
        Stable operation contract for ``flag_real_physical_defect`` in the DRC/LVS/ERC/DFM Agent. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of physical verification (DRC, LVS, ERC, density, DFM). Relates to DRC/LVS markers, rule decks, shorts/opens, manufacturability.

    Args:
        summary: One-sentence finding text published into engineering memory for downstream owners.
        evidence_refs: Comma-separated artifact URIs that substantiate the finding or decision.
        severity: Finding severity: low, medium, high, or critical for signoff triage.
        recommended_recipient: Agent id expected to act on the finding (for example routing_lead or eco_lead).
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='drc_lvs'``, and run status. Callers must not treat ``not_run``
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
    # Emit a structured observation stamped with agent_id='drc_lvs' for audit and telemetry.
    return tool_observation(
        'flag_real_physical_defect',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='drc_lvs',  # Ties the observation to this DRC/LVS/ERC/DFM Agent worker.
    )


@tool(description='Record the rule deck, layout ref, and tool version.')  # Registers ``record_physical_verification_deck`` as a discoverable signoff skill.
def record_physical_verification_deck(
    summary: str = '',  # One-sentence finding text published into engineering memory for downstream owners.
    evidence_refs: str = '',  # Comma-separated artifact URIs that substantiate the finding or decision.
    severity: str = '',  # Finding severity: low, medium, high, or critical for signoff triage.
    recommended_recipient: str = '',  # Agent id expected to act on the finding (for example routing_lead or eco_lead).
    params: dict | None = None,  # Optional extra adapter kwargs merged into the observation payload for framework binding.
) -> dict:
    """Record the rule deck, layout ref, and tool version.

    Purpose:
        Stable operation contract for ``record_physical_verification_deck`` in the DRC/LVS/ERC/DFM Agent. A framework adapter
        (when bound via ``EDA_FRAMEWORK``) performs the real EDA work; until then this
        function records a structured observation and returns status ``not_run``.

    Domain context:
        Part of physical verification (DRC, LVS, ERC, density, DFM). Relates to DRC/LVS markers, rule decks, shorts/opens, manufacturability.

    Args:
        summary: One-sentence finding text published into engineering memory for downstream owners.
        evidence_refs: Comma-separated artifact URIs that substantiate the finding or decision.
        severity: Finding severity: low, medium, high, or critical for signoff triage.
        recommended_recipient: Agent id expected to act on the finding (for example routing_lead or eco_lead).
        params: Optional extra adapter kwargs merged into the observation payload for framework binding.

    Returns:
        dict: Observation payload from ``tool_observation``, including operation name,
        inputs, ``agent_id='drc_lvs'``, and run status. Callers must not treat ``not_run``
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
    # Emit a structured observation stamped with agent_id='drc_lvs' for audit and telemetry.
    return tool_observation(
        'record_physical_verification_deck',  # Skill/operation id recorded in the silicon journal.
        payload,  # Argument map consumed by the future EDA framework adapter.
        agent_id='drc_lvs',  # Ties the observation to this DRC/LVS/ERC/DFM Agent worker.
    )
