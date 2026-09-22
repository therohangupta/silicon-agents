"""Tools for the assertion_formal agent in the EDA chip-design agent fleet.

Operation contracts for the assertion_formal verification specialist.

This module is the stable operation contract for the assertion and formal-proof specialist that writes SVA properties, assumptions, covers, and submits formal jobs. Each ``@tool``
function is a skill the LLM or orchestrator may invoke. Bodies do not call a
simulator, formal engine, or OpenROAD directly: they assemble a typed payload
and return ``tool_observation(...)``. Until a framework adapter is bound,
observations typically surface status ``not_run`` and never invoke OpenROAD,
Yosys, OpenSTA, a licensed EDA tool, or a UVM simulator. Skill names must stay
aligned with this agent's ``config.yaml`` capabilities and skills lists.
"""

from __future__ import annotations  # Allow dict | None annotations without runtime evaluation cost.

from packages.agent_sdk import tool  # Registers each callable as a discoverable agent skill.
from domains.eda.eda import tool_observation  # Builds the standard observation dict (status, payload, agent_id).


@tool(description='Write properties for the named requirements.')
def generate_assertions(
    candidate_ref: str = "",  # Artifact URI/id of the pinned RTL candidate under verification.
    baseline_ref: str = "",  # Baseline candidate or golden revision used for comparison.
    hypothesis: str = "",  # Working hypothesis or change intent guiding this edit/analysis.
    requirement_ids: str = "",  # Comma-separated requirement ids this proof or model covers.
    params: dict | None = None,  # Optional adapter-specific fields merged into the observation payload.
) -> dict:
    """Write properties for the named requirements.

    Purpose:
        For the assertion and formal-proof specialist that writes SVA properties, assumptions, covers, and submits formal jobs: Write properties for the named requirements.
        Invoking ``generate_assertions`` records the intended verification operation for agent ``assertion_formal``.
        A bound framework adapter performs the real EDA work; this process only builds the observation.

    Arguments:
        candidate_ref: Artifact URI/id of the pinned RTL candidate under verification.
        baseline_ref: Baseline candidate or golden revision used for comparison.
        hypothesis: Working hypothesis or change intent guiding this edit/analysis.
        requirement_ids: Comma-separated requirement ids this proof or model covers.
        params: Optional adapter-specific fields merged into the observation payload.

    Returns:
        A ``tool_observation`` dict for skill ``generate_assertions`` with ``agent_id='assertion_formal'``.

    Side effects:
        None in-process. A bound adapter may read/write silicon-store artifacts, submit farm jobs,
        or publish findings into engineering memory.

    Failure behavior:
        Until an adapter is bound, the observation typically reports ``not_run`` and does not
        invoke simulators, formal engines, OpenROAD, Yosys, or OpenSTA. Empty fields are still
        forwarded so the adapter can reject them explicitly.
    """
    # Payload keys mirror config.yaml skill params so AgentService can validate and dispatch.
    payload = {
        'candidate_ref': candidate_ref,  # Artifact URI/id of the pinned RTL candidate under verification.
        'baseline_ref': baseline_ref,  # Baseline candidate or golden revision used for comparison.
        'hypothesis': hypothesis,  # Working hypothesis or change intent guiding this edit/analysis.
        'requirement_ids': requirement_ids,  # Comma-separated requirement ids this proof or model covers.
    }
    if params:
        # Optional extras override base keys so framework adapters can extend the contract.
        payload.update(params)
    return tool_observation(
        'generate_assertions',  # Skill id; must match this agent's config.yaml skills[].callable.
        payload,  # Structured arguments consumed by the bound framework adapter.
        agent_id='assertion_formal',  # Telemetry and journal attribution for this specialist.
    )


@tool(description='Write environment assumptions. Each assumption cites the contract clause that justifies it.')
def write_formal_assumptions(
    candidate_ref: str = "",  # Artifact URI/id of the pinned RTL candidate under verification.
    baseline_ref: str = "",  # Baseline candidate or golden revision used for comparison.
    hypothesis: str = "",  # Working hypothesis or change intent guiding this edit/analysis.
    params: dict | None = None,  # Optional adapter-specific fields merged into the observation payload.
) -> dict:
    """Write environment assumptions. Each assumption cites the contract clause that justifies it.

    Purpose:
        For the assertion and formal-proof specialist that writes SVA properties, assumptions, covers, and submits formal jobs: Write environment assumptions. Each assumption cites the contract clause that justifies it.
        Invoking ``write_formal_assumptions`` records the intended verification operation for agent ``assertion_formal``.
        A bound framework adapter performs the real EDA work; this process only builds the observation.

    Arguments:
        candidate_ref: Artifact URI/id of the pinned RTL candidate under verification.
        baseline_ref: Baseline candidate or golden revision used for comparison.
        hypothesis: Working hypothesis or change intent guiding this edit/analysis.
        params: Optional adapter-specific fields merged into the observation payload.

    Returns:
        A ``tool_observation`` dict for skill ``write_formal_assumptions`` with ``agent_id='assertion_formal'``.

    Side effects:
        None in-process. A bound adapter may read/write silicon-store artifacts, submit farm jobs,
        or publish findings into engineering memory.

    Failure behavior:
        Until an adapter is bound, the observation typically reports ``not_run`` and does not
        invoke simulators, formal engines, OpenROAD, Yosys, or OpenSTA. Empty fields are still
        forwarded so the adapter can reject them explicitly.
    """
    # Payload keys mirror config.yaml skill params so AgentService can validate and dispatch.
    payload = {
        'candidate_ref': candidate_ref,  # Artifact URI/id of the pinned RTL candidate under verification.
        'baseline_ref': baseline_ref,  # Baseline candidate or golden revision used for comparison.
        'hypothesis': hypothesis,  # Working hypothesis or change intent guiding this edit/analysis.
    }
    if params:
        # Optional extras override base keys so framework adapters can extend the contract.
        payload.update(params)
    return tool_observation(
        'write_formal_assumptions',  # Skill id; must match this agent's config.yaml skills[].callable.
        payload,  # Structured arguments consumed by the bound framework adapter.
        agent_id='assertion_formal',  # Telemetry and journal attribution for this specialist.
    )


@tool(description='Write cover properties for the legal scenarios the proof must reach.')
def write_cover_properties(
    candidate_ref: str = "",  # Artifact URI/id of the pinned RTL candidate under verification.
    baseline_ref: str = "",  # Baseline candidate or golden revision used for comparison.
    hypothesis: str = "",  # Working hypothesis or change intent guiding this edit/analysis.
    params: dict | None = None,  # Optional adapter-specific fields merged into the observation payload.
) -> dict:
    """Write cover properties for the legal scenarios the proof must reach.

    Purpose:
        For the assertion and formal-proof specialist that writes SVA properties, assumptions, covers, and submits formal jobs: Write cover properties for the legal scenarios the proof must reach.
        Invoking ``write_cover_properties`` records the intended verification operation for agent ``assertion_formal``.
        A bound framework adapter performs the real EDA work; this process only builds the observation.

    Arguments:
        candidate_ref: Artifact URI/id of the pinned RTL candidate under verification.
        baseline_ref: Baseline candidate or golden revision used for comparison.
        hypothesis: Working hypothesis or change intent guiding this edit/analysis.
        params: Optional adapter-specific fields merged into the observation payload.

    Returns:
        A ``tool_observation`` dict for skill ``write_cover_properties`` with ``agent_id='assertion_formal'``.

    Side effects:
        None in-process. A bound adapter may read/write silicon-store artifacts, submit farm jobs,
        or publish findings into engineering memory.

    Failure behavior:
        Until an adapter is bound, the observation typically reports ``not_run`` and does not
        invoke simulators, formal engines, OpenROAD, Yosys, or OpenSTA. Empty fields are still
        forwarded so the adapter can reject them explicitly.
    """
    # Payload keys mirror config.yaml skill params so AgentService can validate and dispatch.
    payload = {
        'candidate_ref': candidate_ref,  # Artifact URI/id of the pinned RTL candidate under verification.
        'baseline_ref': baseline_ref,  # Baseline candidate or golden revision used for comparison.
        'hypothesis': hypothesis,  # Working hypothesis or change intent guiding this edit/analysis.
    }
    if params:
        # Optional extras override base keys so framework adapters can extend the contract.
        payload.update(params)
    return tool_observation(
        'write_cover_properties',  # Skill id; must match this agent's config.yaml skills[].callable.
        payload,  # Structured arguments consumed by the bound framework adapter.
        agent_id='assertion_formal',  # Telemetry and journal attribution for this specialist.
    )


@tool(description='Write the bind file that attaches properties to the candidate.')
def write_assertion_bind(
    candidate_ref: str = "",  # Artifact URI/id of the pinned RTL candidate under verification.
    baseline_ref: str = "",  # Baseline candidate or golden revision used for comparison.
    hypothesis: str = "",  # Working hypothesis or change intent guiding this edit/analysis.
    params: dict | None = None,  # Optional adapter-specific fields merged into the observation payload.
) -> dict:
    """Write the bind file that attaches properties to the candidate.

    Purpose:
        For the assertion and formal-proof specialist that writes SVA properties, assumptions, covers, and submits formal jobs: Write the bind file that attaches properties to the candidate.
        Invoking ``write_assertion_bind`` records the intended verification operation for agent ``assertion_formal``.
        A bound framework adapter performs the real EDA work; this process only builds the observation.

    Arguments:
        candidate_ref: Artifact URI/id of the pinned RTL candidate under verification.
        baseline_ref: Baseline candidate or golden revision used for comparison.
        hypothesis: Working hypothesis or change intent guiding this edit/analysis.
        params: Optional adapter-specific fields merged into the observation payload.

    Returns:
        A ``tool_observation`` dict for skill ``write_assertion_bind`` with ``agent_id='assertion_formal'``.

    Side effects:
        None in-process. A bound adapter may read/write silicon-store artifacts, submit farm jobs,
        or publish findings into engineering memory.

    Failure behavior:
        Until an adapter is bound, the observation typically reports ``not_run`` and does not
        invoke simulators, formal engines, OpenROAD, Yosys, or OpenSTA. Empty fields are still
        forwarded so the adapter can reject them explicitly.
    """
    # Payload keys mirror config.yaml skill params so AgentService can validate and dispatch.
    payload = {
        'candidate_ref': candidate_ref,  # Artifact URI/id of the pinned RTL candidate under verification.
        'baseline_ref': baseline_ref,  # Baseline candidate or golden revision used for comparison.
        'hypothesis': hypothesis,  # Working hypothesis or change intent guiding this edit/analysis.
    }
    if params:
        # Optional extras override base keys so framework adapters can extend the contract.
        payload.update(params)
    return tool_observation(
        'write_assertion_bind',  # Skill id; must match this agent's config.yaml skills[].callable.
        payload,  # Structured arguments consumed by the bound framework adapter.
        agent_id='assertion_formal',  # Telemetry and journal attribution for this specialist.
    )


@tool(description='Read the requirements this proof is responsible for.')
def read_formal_requirements(
    candidate_ref: str = "",  # Artifact URI/id of the pinned RTL candidate under verification.
    report_ref: str = "",  # Artifact URI of a report; empty means the latest for this candidate.
    corner: str = "",  # PVT corner filter; empty reads every available corner.
    mode: str = "",  # Operating-mode filter; empty reads every available mode.
    params: dict | None = None,  # Optional adapter-specific fields merged into the observation payload.
) -> dict:
    """Read the requirements this proof is responsible for.

    Purpose:
        For the assertion and formal-proof specialist that writes SVA properties, assumptions, covers, and submits formal jobs: Read the requirements this proof is responsible for.
        Invoking ``read_formal_requirements`` records the intended verification operation for agent ``assertion_formal``.
        A bound framework adapter performs the real EDA work; this process only builds the observation.

    Arguments:
        candidate_ref: Artifact URI/id of the pinned RTL candidate under verification.
        report_ref: Artifact URI of a report; empty means the latest for this candidate.
        corner: PVT corner filter; empty reads every available corner.
        mode: Operating-mode filter; empty reads every available mode.
        params: Optional adapter-specific fields merged into the observation payload.

    Returns:
        A ``tool_observation`` dict for skill ``read_formal_requirements`` with ``agent_id='assertion_formal'``.

    Side effects:
        None in-process. A bound adapter may read/write silicon-store artifacts, submit farm jobs,
        or publish findings into engineering memory.

    Failure behavior:
        Until an adapter is bound, the observation typically reports ``not_run`` and does not
        invoke simulators, formal engines, OpenROAD, Yosys, or OpenSTA. Empty fields are still
        forwarded so the adapter can reject them explicitly.
    """
    # Payload keys mirror config.yaml skill params so AgentService can validate and dispatch.
    payload = {
        'candidate_ref': candidate_ref,  # Artifact URI/id of the pinned RTL candidate under verification.
        'report_ref': report_ref,  # Artifact URI of a report; empty means the latest for this candidate.
        'corner': corner,  # PVT corner filter; empty reads every available corner.
        'mode': mode,  # Operating-mode filter; empty reads every available mode.
    }
    if params:
        # Optional extras override base keys so framework adapters can extend the contract.
        payload.update(params)
    return tool_observation(
        'read_formal_requirements',  # Skill id; must match this agent's config.yaml skills[].callable.
        payload,  # Structured arguments consumed by the bound framework adapter.
        agent_id='assertion_formal',  # Telemetry and journal attribution for this specialist.
    )


@tool(description='Submit the property manifest to the bound formal engine.')
def submit_formal(
    candidate_ref: str = "",  # Artifact URI/id of the pinned RTL candidate under verification.
    baseline_ref: str = "",  # Baseline candidate or golden revision used for comparison.
    recipe: str = "",  # Frozen compile/run recipe id (plusargs, defines, tool options).
    corner: str = "",  # PVT corner filter; empty reads every available corner.
    mode: str = "",  # Operating-mode filter; empty reads every available mode.
    params: dict | None = None,  # Optional adapter-specific fields merged into the observation payload.
) -> dict:
    """Submit the property manifest to the bound formal engine.

    Purpose:
        For the assertion and formal-proof specialist that writes SVA properties, assumptions, covers, and submits formal jobs: Submit the property manifest to the bound formal engine.
        Invoking ``submit_formal`` records the intended verification operation for agent ``assertion_formal``.
        A bound framework adapter performs the real EDA work; this process only builds the observation.

    Arguments:
        candidate_ref: Artifact URI/id of the pinned RTL candidate under verification.
        baseline_ref: Baseline candidate or golden revision used for comparison.
        recipe: Frozen compile/run recipe id (plusargs, defines, tool options).
        corner: PVT corner filter; empty reads every available corner.
        mode: Operating-mode filter; empty reads every available mode.
        params: Optional adapter-specific fields merged into the observation payload.

    Returns:
        A ``tool_observation`` dict for skill ``submit_formal`` with ``agent_id='assertion_formal'``.

    Side effects:
        None in-process. A bound adapter may read/write silicon-store artifacts, submit farm jobs,
        or publish findings into engineering memory.

    Failure behavior:
        Until an adapter is bound, the observation typically reports ``not_run`` and does not
        invoke simulators, formal engines, OpenROAD, Yosys, or OpenSTA. Empty fields are still
        forwarded so the adapter can reject them explicitly.
    """
    # Payload keys mirror config.yaml skill params so AgentService can validate and dispatch.
    payload = {
        'candidate_ref': candidate_ref,  # Artifact URI/id of the pinned RTL candidate under verification.
        'baseline_ref': baseline_ref,  # Baseline candidate or golden revision used for comparison.
        'recipe': recipe,  # Frozen compile/run recipe id (plusargs, defines, tool options).
        'corner': corner,  # PVT corner filter; empty reads every available corner.
        'mode': mode,  # Operating-mode filter; empty reads every available mode.
    }
    if params:
        # Optional extras override base keys so framework adapters can extend the contract.
        payload.update(params)
    return tool_observation(
        'submit_formal',  # Skill id; must match this agent's config.yaml skills[].callable.
        payload,  # Structured arguments consumed by the bound framework adapter.
        agent_id='assertion_formal',  # Telemetry and journal attribution for this specialist.
    )


@tool(description='Read proven, cex, vacuous, and undetermined properties.')
def read_formal_results(
    candidate_ref: str = "",  # Artifact URI/id of the pinned RTL candidate under verification.
    report_ref: str = "",  # Artifact URI of a report; empty means the latest for this candidate.
    corner: str = "",  # PVT corner filter; empty reads every available corner.
    mode: str = "",  # Operating-mode filter; empty reads every available mode.
    params: dict | None = None,  # Optional adapter-specific fields merged into the observation payload.
) -> dict:
    """Read proven, cex, vacuous, and undetermined properties.

    Purpose:
        For the assertion and formal-proof specialist that writes SVA properties, assumptions, covers, and submits formal jobs: Read proven, cex, vacuous, and undetermined properties.
        Invoking ``read_formal_results`` records the intended verification operation for agent ``assertion_formal``.
        A bound framework adapter performs the real EDA work; this process only builds the observation.

    Arguments:
        candidate_ref: Artifact URI/id of the pinned RTL candidate under verification.
        report_ref: Artifact URI of a report; empty means the latest for this candidate.
        corner: PVT corner filter; empty reads every available corner.
        mode: Operating-mode filter; empty reads every available mode.
        params: Optional adapter-specific fields merged into the observation payload.

    Returns:
        A ``tool_observation`` dict for skill ``read_formal_results`` with ``agent_id='assertion_formal'``.

    Side effects:
        None in-process. A bound adapter may read/write silicon-store artifacts, submit farm jobs,
        or publish findings into engineering memory.

    Failure behavior:
        Until an adapter is bound, the observation typically reports ``not_run`` and does not
        invoke simulators, formal engines, OpenROAD, Yosys, or OpenSTA. Empty fields are still
        forwarded so the adapter can reject them explicitly.
    """
    # Payload keys mirror config.yaml skill params so AgentService can validate and dispatch.
    payload = {
        'candidate_ref': candidate_ref,  # Artifact URI/id of the pinned RTL candidate under verification.
        'report_ref': report_ref,  # Artifact URI of a report; empty means the latest for this candidate.
        'corner': corner,  # PVT corner filter; empty reads every available corner.
        'mode': mode,  # Operating-mode filter; empty reads every available mode.
    }
    if params:
        # Optional extras override base keys so framework adapters can extend the contract.
        payload.update(params)
    return tool_observation(
        'read_formal_results',  # Skill id; must match this agent's config.yaml skills[].callable.
        payload,  # Structured arguments consumed by the bound framework adapter.
        agent_id='assertion_formal',  # Telemetry and journal attribution for this specialist.
    )


@tool(description='Classify one counterexample as a design bug, a missing constraint, or an overconstraint.')
def classify_counterexample(
    candidate_ref: str = "",  # Artifact URI/id of the pinned RTL candidate under verification.
    report_ref: str = "",  # Artifact URI of a report; empty means the latest for this candidate.
    corner: str = "",  # PVT corner filter; empty reads every available corner.
    mode: str = "",  # Operating-mode filter; empty reads every available mode.
    property_id: str = "",  # Formal property identifier being classified or minimized.
    params: dict | None = None,  # Optional adapter-specific fields merged into the observation payload.
) -> dict:
    """Classify one counterexample as a design bug, a missing constraint, or an overconstraint.

    Purpose:
        For the assertion and formal-proof specialist that writes SVA properties, assumptions, covers, and submits formal jobs: Classify one counterexample as a design bug, a missing constraint, or an overconstraint.
        Invoking ``classify_counterexample`` records the intended verification operation for agent ``assertion_formal``.
        A bound framework adapter performs the real EDA work; this process only builds the observation.

    Arguments:
        candidate_ref: Artifact URI/id of the pinned RTL candidate under verification.
        report_ref: Artifact URI of a report; empty means the latest for this candidate.
        corner: PVT corner filter; empty reads every available corner.
        mode: Operating-mode filter; empty reads every available mode.
        property_id: Formal property identifier being classified or minimized.
        params: Optional adapter-specific fields merged into the observation payload.

    Returns:
        A ``tool_observation`` dict for skill ``classify_counterexample`` with ``agent_id='assertion_formal'``.

    Side effects:
        None in-process. A bound adapter may read/write silicon-store artifacts, submit farm jobs,
        or publish findings into engineering memory.

    Failure behavior:
        Until an adapter is bound, the observation typically reports ``not_run`` and does not
        invoke simulators, formal engines, OpenROAD, Yosys, or OpenSTA. Empty fields are still
        forwarded so the adapter can reject them explicitly.
    """
    # Payload keys mirror config.yaml skill params so AgentService can validate and dispatch.
    payload = {
        'candidate_ref': candidate_ref,  # Artifact URI/id of the pinned RTL candidate under verification.
        'report_ref': report_ref,  # Artifact URI of a report; empty means the latest for this candidate.
        'corner': corner,  # PVT corner filter; empty reads every available corner.
        'mode': mode,  # Operating-mode filter; empty reads every available mode.
        'property_id': property_id,  # Formal property identifier being classified or minimized.
    }
    if params:
        # Optional extras override base keys so framework adapters can extend the contract.
        payload.update(params)
    return tool_observation(
        'classify_counterexample',  # Skill id; must match this agent's config.yaml skills[].callable.
        payload,  # Structured arguments consumed by the bound framework adapter.
        agent_id='assertion_formal',  # Telemetry and journal attribution for this specialist.
    )


@tool(description='Ask the formal engine for a shorter counterexample.')
def minimize_counterexample(
    candidate_ref: str = "",  # Artifact URI/id of the pinned RTL candidate under verification.
    baseline_ref: str = "",  # Baseline candidate or golden revision used for comparison.
    recipe: str = "",  # Frozen compile/run recipe id (plusargs, defines, tool options).
    corner: str = "",  # PVT corner filter; empty reads every available corner.
    mode: str = "",  # Operating-mode filter; empty reads every available mode.
    property_id: str = "",  # Formal property identifier being classified or minimized.
    params: dict | None = None,  # Optional adapter-specific fields merged into the observation payload.
) -> dict:
    """Ask the formal engine for a shorter counterexample.

    Purpose:
        For the assertion and formal-proof specialist that writes SVA properties, assumptions, covers, and submits formal jobs: Ask the formal engine for a shorter counterexample.
        Invoking ``minimize_counterexample`` records the intended verification operation for agent ``assertion_formal``.
        A bound framework adapter performs the real EDA work; this process only builds the observation.

    Arguments:
        candidate_ref: Artifact URI/id of the pinned RTL candidate under verification.
        baseline_ref: Baseline candidate or golden revision used for comparison.
        recipe: Frozen compile/run recipe id (plusargs, defines, tool options).
        corner: PVT corner filter; empty reads every available corner.
        mode: Operating-mode filter; empty reads every available mode.
        property_id: Formal property identifier being classified or minimized.
        params: Optional adapter-specific fields merged into the observation payload.

    Returns:
        A ``tool_observation`` dict for skill ``minimize_counterexample`` with ``agent_id='assertion_formal'``.

    Side effects:
        None in-process. A bound adapter may read/write silicon-store artifacts, submit farm jobs,
        or publish findings into engineering memory.

    Failure behavior:
        Until an adapter is bound, the observation typically reports ``not_run`` and does not
        invoke simulators, formal engines, OpenROAD, Yosys, or OpenSTA. Empty fields are still
        forwarded so the adapter can reject them explicitly.
    """
    # Payload keys mirror config.yaml skill params so AgentService can validate and dispatch.
    payload = {
        'candidate_ref': candidate_ref,  # Artifact URI/id of the pinned RTL candidate under verification.
        'baseline_ref': baseline_ref,  # Baseline candidate or golden revision used for comparison.
        'recipe': recipe,  # Frozen compile/run recipe id (plusargs, defines, tool options).
        'corner': corner,  # PVT corner filter; empty reads every available corner.
        'mode': mode,  # Operating-mode filter; empty reads every available mode.
        'property_id': property_id,  # Formal property identifier being classified or minimized.
    }
    if params:
        # Optional extras override base keys so framework adapters can extend the contract.
        payload.update(params)
    return tool_observation(
        'minimize_counterexample',  # Skill id; must match this agent's config.yaml skills[].callable.
        payload,  # Structured arguments consumed by the bound framework adapter.
        agent_id='assertion_formal',  # Telemetry and journal attribution for this specialist.
    )


@tool(description='Publish a property that passes only because its antecedent is unreachable.')
def flag_vacuous_property(
    summary: str = "",  # One-sentence finding or record for engineering memory.
    evidence_refs: str = "",  # Comma-separated artifact URIs that support the finding.
    severity: str = "",  # Finding severity: low, medium, high, or critical.
    recommended_recipient: str = "",  # Agent id that should act on the finding next.
    params: dict | None = None,  # Optional adapter-specific fields merged into the observation payload.
) -> dict:
    """Publish a property that passes only because its antecedent is unreachable.

    Purpose:
        For the assertion and formal-proof specialist that writes SVA properties, assumptions, covers, and submits formal jobs: Publish a property that passes only because its antecedent is unreachable.
        Invoking ``flag_vacuous_property`` records the intended verification operation for agent ``assertion_formal``.
        A bound framework adapter performs the real EDA work; this process only builds the observation.

    Arguments:
        summary: One-sentence finding or record for engineering memory.
        evidence_refs: Comma-separated artifact URIs that support the finding.
        severity: Finding severity: low, medium, high, or critical.
        recommended_recipient: Agent id that should act on the finding next.
        params: Optional adapter-specific fields merged into the observation payload.

    Returns:
        A ``tool_observation`` dict for skill ``flag_vacuous_property`` with ``agent_id='assertion_formal'``.

    Side effects:
        None in-process. A bound adapter may read/write silicon-store artifacts, submit farm jobs,
        or publish findings into engineering memory.

    Failure behavior:
        Until an adapter is bound, the observation typically reports ``not_run`` and does not
        invoke simulators, formal engines, OpenROAD, Yosys, or OpenSTA. Empty fields are still
        forwarded so the adapter can reject them explicitly.
    """
    # Payload keys mirror config.yaml skill params so AgentService can validate and dispatch.
    payload = {
        'summary': summary,  # One-sentence finding or record for engineering memory.
        'evidence_refs': evidence_refs,  # Comma-separated artifact URIs that support the finding.
        'severity': severity,  # Finding severity: low, medium, high, or critical.
        'recommended_recipient': recommended_recipient,  # Agent id that should act on the finding next.
    }
    if params:
        # Optional extras override base keys so framework adapters can extend the contract.
        payload.update(params)
    return tool_observation(
        'flag_vacuous_property',  # Skill id; must match this agent's config.yaml skills[].callable.
        payload,  # Structured arguments consumed by the bound framework adapter.
        agent_id='assertion_formal',  # Telemetry and journal attribution for this specialist.
    )


@tool(description='Publish an assumption that removes legal stimulus.')
def flag_overconstraint(
    summary: str = "",  # One-sentence finding or record for engineering memory.
    evidence_refs: str = "",  # Comma-separated artifact URIs that support the finding.
    severity: str = "",  # Finding severity: low, medium, high, or critical.
    recommended_recipient: str = "",  # Agent id that should act on the finding next.
    params: dict | None = None,  # Optional adapter-specific fields merged into the observation payload.
) -> dict:
    """Publish an assumption that removes legal stimulus.

    Purpose:
        For the assertion and formal-proof specialist that writes SVA properties, assumptions, covers, and submits formal jobs: Publish an assumption that removes legal stimulus.
        Invoking ``flag_overconstraint`` records the intended verification operation for agent ``assertion_formal``.
        A bound framework adapter performs the real EDA work; this process only builds the observation.

    Arguments:
        summary: One-sentence finding or record for engineering memory.
        evidence_refs: Comma-separated artifact URIs that support the finding.
        severity: Finding severity: low, medium, high, or critical.
        recommended_recipient: Agent id that should act on the finding next.
        params: Optional adapter-specific fields merged into the observation payload.

    Returns:
        A ``tool_observation`` dict for skill ``flag_overconstraint`` with ``agent_id='assertion_formal'``.

    Side effects:
        None in-process. A bound adapter may read/write silicon-store artifacts, submit farm jobs,
        or publish findings into engineering memory.

    Failure behavior:
        Until an adapter is bound, the observation typically reports ``not_run`` and does not
        invoke simulators, formal engines, OpenROAD, Yosys, or OpenSTA. Empty fields are still
        forwarded so the adapter can reject them explicitly.
    """
    # Payload keys mirror config.yaml skill params so AgentService can validate and dispatch.
    payload = {
        'summary': summary,  # One-sentence finding or record for engineering memory.
        'evidence_refs': evidence_refs,  # Comma-separated artifact URIs that support the finding.
        'severity': severity,  # Finding severity: low, medium, high, or critical.
        'recommended_recipient': recommended_recipient,  # Agent id that should act on the finding next.
    }
    if params:
        # Optional extras override base keys so framework adapters can extend the contract.
        payload.update(params)
    return tool_observation(
        'flag_overconstraint',  # Skill id; must match this agent's config.yaml skills[].callable.
        payload,  # Structured arguments consumed by the bound framework adapter.
        agent_id='assertion_formal',  # Telemetry and journal attribution for this specialist.
    )


@tool(description='Record the formal engine, version, and proof settings.')
def record_formal_engine_version(
    summary: str = "",  # One-sentence finding or record for engineering memory.
    evidence_refs: str = "",  # Comma-separated artifact URIs that support the finding.
    severity: str = "",  # Finding severity: low, medium, high, or critical.
    recommended_recipient: str = "",  # Agent id that should act on the finding next.
    params: dict | None = None,  # Optional adapter-specific fields merged into the observation payload.
) -> dict:
    """Record the formal engine, version, and proof settings.

    Purpose:
        For the assertion and formal-proof specialist that writes SVA properties, assumptions, covers, and submits formal jobs: Record the formal engine, version, and proof settings.
        Invoking ``record_formal_engine_version`` records the intended verification operation for agent ``assertion_formal``.
        A bound framework adapter performs the real EDA work; this process only builds the observation.

    Arguments:
        summary: One-sentence finding or record for engineering memory.
        evidence_refs: Comma-separated artifact URIs that support the finding.
        severity: Finding severity: low, medium, high, or critical.
        recommended_recipient: Agent id that should act on the finding next.
        params: Optional adapter-specific fields merged into the observation payload.

    Returns:
        A ``tool_observation`` dict for skill ``record_formal_engine_version`` with ``agent_id='assertion_formal'``.

    Side effects:
        None in-process. A bound adapter may read/write silicon-store artifacts, submit farm jobs,
        or publish findings into engineering memory.

    Failure behavior:
        Until an adapter is bound, the observation typically reports ``not_run`` and does not
        invoke simulators, formal engines, OpenROAD, Yosys, or OpenSTA. Empty fields are still
        forwarded so the adapter can reject them explicitly.
    """
    # Payload keys mirror config.yaml skill params so AgentService can validate and dispatch.
    payload = {
        'summary': summary,  # One-sentence finding or record for engineering memory.
        'evidence_refs': evidence_refs,  # Comma-separated artifact URIs that support the finding.
        'severity': severity,  # Finding severity: low, medium, high, or critical.
        'recommended_recipient': recommended_recipient,  # Agent id that should act on the finding next.
    }
    if params:
        # Optional extras override base keys so framework adapters can extend the contract.
        payload.update(params)
    return tool_observation(
        'record_formal_engine_version',  # Skill id; must match this agent's config.yaml skills[].callable.
        payload,  # Structured arguments consumed by the bound framework adapter.
        agent_id='assertion_formal',  # Telemetry and journal attribution for this specialist.
    )

