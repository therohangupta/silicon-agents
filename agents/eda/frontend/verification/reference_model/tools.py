"""Tools for the reference_model agent in the EDA chip-design agent fleet.

Operation contracts for the reference_model verification specialist.

This module is the stable operation contract for the behavioral reference-model specialist that encodes the specification for scoreboard comparison against the DUT. Each ``@tool``
function is a skill the LLM or orchestrator may invoke. Bodies do not call a
simulator, formal engine, or OpenROAD directly: they assemble a typed payload
and return ``tool_observation(...)``. Until a framework adapter is bound,
observations typically surface status ``not_run`` and never invoke OpenROAD,
Yosys, OpenSTA, a licensed EDA tool, or a UVM simulator. Skill names must stay
aligned with this agent's ``config.yaml`` capabilities and skills lists.
"""

from __future__ import annotations  # Allow dict | None annotations without runtime evaluation cost.

from packages.agent_sdk import tool  # Registers each callable as a discoverable agent skill.
from domains.eda.adapters import tool_observation  # Builds the standard observation dict (status, payload, agent_id).


@tool(description='Write a behavioral model that encodes the specification.')
def generate_reference_model(
    candidate_ref: str = "",  # Artifact URI/id of the pinned RTL candidate under verification.
    baseline_ref: str = "",  # Baseline candidate or golden revision used for comparison.
    hypothesis: str = "",  # Working hypothesis or change intent guiding this edit/analysis.
    params: dict | None = None,  # Optional adapter-specific fields merged into the observation payload.
) -> dict:
    """Write a behavioral model that encodes the specification.

    Purpose:
        For the behavioral reference-model specialist that encodes the specification for scoreboard comparison against the DUT: Write a behavioral model that encodes the specification.
        Invoking ``generate_reference_model`` records the intended verification operation for agent ``reference_model``.
        A bound framework adapter performs the real EDA work; this process only builds the observation.

    Arguments:
        candidate_ref: Artifact URI/id of the pinned RTL candidate under verification.
        baseline_ref: Baseline candidate or golden revision used for comparison.
        hypothesis: Working hypothesis or change intent guiding this edit/analysis.
        params: Optional adapter-specific fields merged into the observation payload.

    Returns:
        A ``tool_observation`` dict for skill ``generate_reference_model`` with ``agent_id='reference_model'``.

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
        'generate_reference_model',  # Skill id; must match this agent's config.yaml skills[].callable.
        payload,  # Structured arguments consumed by the bound framework adapter.
        agent_id='reference_model',  # Telemetry and journal attribution for this specialist.
    )


@tool(description="Write the model's ports from the interface contract.")
def write_model_ports(
    candidate_ref: str = "",  # Artifact URI/id of the pinned RTL candidate under verification.
    baseline_ref: str = "",  # Baseline candidate or golden revision used for comparison.
    hypothesis: str = "",  # Working hypothesis or change intent guiding this edit/analysis.
    params: dict | None = None,  # Optional adapter-specific fields merged into the observation payload.
) -> dict:
    """Write the model's ports from the interface contract.

    Purpose:
        For the behavioral reference-model specialist that encodes the specification for scoreboard comparison against the DUT: Write the model's ports from the interface contract.
        Invoking ``write_model_ports`` records the intended verification operation for agent ``reference_model``.
        A bound framework adapter performs the real EDA work; this process only builds the observation.

    Arguments:
        candidate_ref: Artifact URI/id of the pinned RTL candidate under verification.
        baseline_ref: Baseline candidate or golden revision used for comparison.
        hypothesis: Working hypothesis or change intent guiding this edit/analysis.
        params: Optional adapter-specific fields merged into the observation payload.

    Returns:
        A ``tool_observation`` dict for skill ``write_model_ports`` with ``agent_id='reference_model'``.

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
        'write_model_ports',  # Skill id; must match this agent's config.yaml skills[].callable.
        payload,  # Structured arguments consumed by the bound framework adapter.
        agent_id='reference_model',  # Telemetry and journal attribution for this specialist.
    )


@tool(description='Write legal transaction types and their fields.')
def write_model_transactions(
    candidate_ref: str = "",  # Artifact URI/id of the pinned RTL candidate under verification.
    baseline_ref: str = "",  # Baseline candidate or golden revision used for comparison.
    hypothesis: str = "",  # Working hypothesis or change intent guiding this edit/analysis.
    params: dict | None = None,  # Optional adapter-specific fields merged into the observation payload.
) -> dict:
    """Write legal transaction types and their fields.

    Purpose:
        For the behavioral reference-model specialist that encodes the specification for scoreboard comparison against the DUT: Write legal transaction types and their fields.
        Invoking ``write_model_transactions`` records the intended verification operation for agent ``reference_model``.
        A bound framework adapter performs the real EDA work; this process only builds the observation.

    Arguments:
        candidate_ref: Artifact URI/id of the pinned RTL candidate under verification.
        baseline_ref: Baseline candidate or golden revision used for comparison.
        hypothesis: Working hypothesis or change intent guiding this edit/analysis.
        params: Optional adapter-specific fields merged into the observation payload.

    Returns:
        A ``tool_observation`` dict for skill ``write_model_transactions`` with ``agent_id='reference_model'``.

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
        'write_model_transactions',  # Skill id; must match this agent's config.yaml skills[].callable.
        payload,  # Structured arguments consumed by the bound framework adapter.
        agent_id='reference_model',  # Telemetry and journal attribution for this specialist.
    )


@tool(description='Write how the model reports and recovers from illegal inputs.')
def write_model_error_behavior(
    candidate_ref: str = "",  # Artifact URI/id of the pinned RTL candidate under verification.
    baseline_ref: str = "",  # Baseline candidate or golden revision used for comparison.
    hypothesis: str = "",  # Working hypothesis or change intent guiding this edit/analysis.
    params: dict | None = None,  # Optional adapter-specific fields merged into the observation payload.
) -> dict:
    """Write how the model reports and recovers from illegal inputs.

    Purpose:
        For the behavioral reference-model specialist that encodes the specification for scoreboard comparison against the DUT: Write how the model reports and recovers from illegal inputs.
        Invoking ``write_model_error_behavior`` records the intended verification operation for agent ``reference_model``.
        A bound framework adapter performs the real EDA work; this process only builds the observation.

    Arguments:
        candidate_ref: Artifact URI/id of the pinned RTL candidate under verification.
        baseline_ref: Baseline candidate or golden revision used for comparison.
        hypothesis: Working hypothesis or change intent guiding this edit/analysis.
        params: Optional adapter-specific fields merged into the observation payload.

    Returns:
        A ``tool_observation`` dict for skill ``write_model_error_behavior`` with ``agent_id='reference_model'``.

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
        'write_model_error_behavior',  # Skill id; must match this agent's config.yaml skills[].callable.
        payload,  # Structured arguments consumed by the bound framework adapter.
        agent_id='reference_model',  # Telemetry and journal attribution for this specialist.
    )


@tool(description='Write the latency or ordering rule the model must obey.')
def write_model_latency_rule(
    candidate_ref: str = "",  # Artifact URI/id of the pinned RTL candidate under verification.
    baseline_ref: str = "",  # Baseline candidate or golden revision used for comparison.
    hypothesis: str = "",  # Working hypothesis or change intent guiding this edit/analysis.
    params: dict | None = None,  # Optional adapter-specific fields merged into the observation payload.
) -> dict:
    """Write the latency or ordering rule the model must obey.

    Purpose:
        For the behavioral reference-model specialist that encodes the specification for scoreboard comparison against the DUT: Write the latency or ordering rule the model must obey.
        Invoking ``write_model_latency_rule`` records the intended verification operation for agent ``reference_model``.
        A bound framework adapter performs the real EDA work; this process only builds the observation.

    Arguments:
        candidate_ref: Artifact URI/id of the pinned RTL candidate under verification.
        baseline_ref: Baseline candidate or golden revision used for comparison.
        hypothesis: Working hypothesis or change intent guiding this edit/analysis.
        params: Optional adapter-specific fields merged into the observation payload.

    Returns:
        A ``tool_observation`` dict for skill ``write_model_latency_rule`` with ``agent_id='reference_model'``.

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
        'write_model_latency_rule',  # Skill id; must match this agent's config.yaml skills[].callable.
        payload,  # Structured arguments consumed by the bound framework adapter.
        agent_id='reference_model',  # Telemetry and journal attribution for this specialist.
    )


@tool(description='Write directed checks that exercise the model without the DUT.')
def write_model_selfcheck(
    candidate_ref: str = "",  # Artifact URI/id of the pinned RTL candidate under verification.
    baseline_ref: str = "",  # Baseline candidate or golden revision used for comparison.
    hypothesis: str = "",  # Working hypothesis or change intent guiding this edit/analysis.
    params: dict | None = None,  # Optional adapter-specific fields merged into the observation payload.
) -> dict:
    """Write directed checks that exercise the model without the DUT.

    Purpose:
        For the behavioral reference-model specialist that encodes the specification for scoreboard comparison against the DUT: Write directed checks that exercise the model without the DUT.
        Invoking ``write_model_selfcheck`` records the intended verification operation for agent ``reference_model``.
        A bound framework adapter performs the real EDA work; this process only builds the observation.

    Arguments:
        candidate_ref: Artifact URI/id of the pinned RTL candidate under verification.
        baseline_ref: Baseline candidate or golden revision used for comparison.
        hypothesis: Working hypothesis or change intent guiding this edit/analysis.
        params: Optional adapter-specific fields merged into the observation payload.

    Returns:
        A ``tool_observation`` dict for skill ``write_model_selfcheck`` with ``agent_id='reference_model'``.

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
        'write_model_selfcheck',  # Skill id; must match this agent's config.yaml skills[].callable.
        payload,  # Structured arguments consumed by the bound framework adapter.
        agent_id='reference_model',  # Telemetry and journal attribution for this specialist.
    )


@tool(description='Read the specification clauses this model claims to encode.')
def read_model_specification(
    candidate_ref: str = "",  # Artifact URI/id of the pinned RTL candidate under verification.
    report_ref: str = "",  # Artifact URI of a report; empty means the latest for this candidate.
    corner: str = "",  # PVT corner filter; empty reads every available corner.
    mode: str = "",  # Operating-mode filter; empty reads every available mode.
    params: dict | None = None,  # Optional adapter-specific fields merged into the observation payload.
) -> dict:
    """Read the specification clauses this model claims to encode.

    Purpose:
        For the behavioral reference-model specialist that encodes the specification for scoreboard comparison against the DUT: Read the specification clauses this model claims to encode.
        Invoking ``read_model_specification`` records the intended verification operation for agent ``reference_model``.
        A bound framework adapter performs the real EDA work; this process only builds the observation.

    Arguments:
        candidate_ref: Artifact URI/id of the pinned RTL candidate under verification.
        report_ref: Artifact URI of a report; empty means the latest for this candidate.
        corner: PVT corner filter; empty reads every available corner.
        mode: Operating-mode filter; empty reads every available mode.
        params: Optional adapter-specific fields merged into the observation payload.

    Returns:
        A ``tool_observation`` dict for skill ``read_model_specification`` with ``agent_id='reference_model'``.

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
        'read_model_specification',  # Skill id; must match this agent's config.yaml skills[].callable.
        payload,  # Structured arguments consumed by the bound framework adapter.
        agent_id='reference_model',  # Telemetry and journal attribution for this specialist.
    )


@tool(description='List specification clauses the model does not yet encode.')
def diff_model_against_spec(
    candidate_ref: str = "",  # Artifact URI/id of the pinned RTL candidate under verification.
    report_ref: str = "",  # Artifact URI of a report; empty means the latest for this candidate.
    corner: str = "",  # PVT corner filter; empty reads every available corner.
    mode: str = "",  # Operating-mode filter; empty reads every available mode.
    params: dict | None = None,  # Optional adapter-specific fields merged into the observation payload.
) -> dict:
    """List specification clauses the model does not yet encode.

    Purpose:
        For the behavioral reference-model specialist that encodes the specification for scoreboard comparison against the DUT: List specification clauses the model does not yet encode.
        Invoking ``diff_model_against_spec`` records the intended verification operation for agent ``reference_model``.
        A bound framework adapter performs the real EDA work; this process only builds the observation.

    Arguments:
        candidate_ref: Artifact URI/id of the pinned RTL candidate under verification.
        report_ref: Artifact URI of a report; empty means the latest for this candidate.
        corner: PVT corner filter; empty reads every available corner.
        mode: Operating-mode filter; empty reads every available mode.
        params: Optional adapter-specific fields merged into the observation payload.

    Returns:
        A ``tool_observation`` dict for skill ``diff_model_against_spec`` with ``agent_id='reference_model'``.

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
        'diff_model_against_spec',  # Skill id; must match this agent's config.yaml skills[].callable.
        payload,  # Structured arguments consumed by the bound framework adapter.
        agent_id='reference_model',  # Telemetry and journal attribution for this specialist.
    )


@tool(description='Compile the reference model.')
def compile_reference_model(
    candidate_ref: str = "",  # Artifact URI/id of the pinned RTL candidate under verification.
    baseline_ref: str = "",  # Baseline candidate or golden revision used for comparison.
    recipe: str = "",  # Frozen compile/run recipe id (plusargs, defines, tool options).
    corner: str = "",  # PVT corner filter; empty reads every available corner.
    mode: str = "",  # Operating-mode filter; empty reads every available mode.
    params: dict | None = None,  # Optional adapter-specific fields merged into the observation payload.
) -> dict:
    """Compile the reference model.

    Purpose:
        For the behavioral reference-model specialist that encodes the specification for scoreboard comparison against the DUT: Compile the reference model.
        Invoking ``compile_reference_model`` records the intended verification operation for agent ``reference_model``.
        A bound framework adapter performs the real EDA work; this process only builds the observation.

    Arguments:
        candidate_ref: Artifact URI/id of the pinned RTL candidate under verification.
        baseline_ref: Baseline candidate or golden revision used for comparison.
        recipe: Frozen compile/run recipe id (plusargs, defines, tool options).
        corner: PVT corner filter; empty reads every available corner.
        mode: Operating-mode filter; empty reads every available mode.
        params: Optional adapter-specific fields merged into the observation payload.

    Returns:
        A ``tool_observation`` dict for skill ``compile_reference_model`` with ``agent_id='reference_model'``.

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
        'compile_reference_model',  # Skill id; must match this agent's config.yaml skills[].callable.
        payload,  # Structured arguments consumed by the bound framework adapter.
        agent_id='reference_model',  # Telemetry and journal attribution for this specialist.
    )


@tool(description="Run the model's own checks and return mismatches.")
def run_model_selfcheck(
    candidate_ref: str = "",  # Artifact URI/id of the pinned RTL candidate under verification.
    baseline_ref: str = "",  # Baseline candidate or golden revision used for comparison.
    recipe: str = "",  # Frozen compile/run recipe id (plusargs, defines, tool options).
    corner: str = "",  # PVT corner filter; empty reads every available corner.
    mode: str = "",  # Operating-mode filter; empty reads every available mode.
    params: dict | None = None,  # Optional adapter-specific fields merged into the observation payload.
) -> dict:
    """Run the model's own checks and return mismatches.

    Purpose:
        For the behavioral reference-model specialist that encodes the specification for scoreboard comparison against the DUT: Run the model's own checks and return mismatches.
        Invoking ``run_model_selfcheck`` records the intended verification operation for agent ``reference_model``.
        A bound framework adapter performs the real EDA work; this process only builds the observation.

    Arguments:
        candidate_ref: Artifact URI/id of the pinned RTL candidate under verification.
        baseline_ref: Baseline candidate or golden revision used for comparison.
        recipe: Frozen compile/run recipe id (plusargs, defines, tool options).
        corner: PVT corner filter; empty reads every available corner.
        mode: Operating-mode filter; empty reads every available mode.
        params: Optional adapter-specific fields merged into the observation payload.

    Returns:
        A ``tool_observation`` dict for skill ``run_model_selfcheck`` with ``agent_id='reference_model'``.

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
        'run_model_selfcheck',  # Skill id; must match this agent's config.yaml skills[].callable.
        payload,  # Structured arguments consumed by the bound framework adapter.
        agent_id='reference_model',  # Telemetry and journal attribution for this specialist.
    )


@tool(description='Publish a specification clause that cannot be encoded because it is ambiguous.')
def flag_spec_hole_in_model(
    summary: str = "",  # One-sentence finding or record for engineering memory.
    evidence_refs: str = "",  # Comma-separated artifact URIs that support the finding.
    severity: str = "",  # Finding severity: low, medium, high, or critical.
    recommended_recipient: str = "",  # Agent id that should act on the finding next.
    params: dict | None = None,  # Optional adapter-specific fields merged into the observation payload.
) -> dict:
    """Publish a specification clause that cannot be encoded because it is ambiguous.

    Purpose:
        For the behavioral reference-model specialist that encodes the specification for scoreboard comparison against the DUT: Publish a specification clause that cannot be encoded because it is ambiguous.
        Invoking ``flag_spec_hole_in_model`` records the intended verification operation for agent ``reference_model``.
        A bound framework adapter performs the real EDA work; this process only builds the observation.

    Arguments:
        summary: One-sentence finding or record for engineering memory.
        evidence_refs: Comma-separated artifact URIs that support the finding.
        severity: Finding severity: low, medium, high, or critical.
        recommended_recipient: Agent id that should act on the finding next.
        params: Optional adapter-specific fields merged into the observation payload.

    Returns:
        A ``tool_observation`` dict for skill ``flag_spec_hole_in_model`` with ``agent_id='reference_model'``.

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
        'flag_spec_hole_in_model',  # Skill id; must match this agent's config.yaml skills[].callable.
        payload,  # Structured arguments consumed by the bound framework adapter.
        agent_id='reference_model',  # Telemetry and journal attribution for this specialist.
    )


@tool(description='Record the model source, spec revision, and language.')
def record_reference_model_version(
    summary: str = "",  # One-sentence finding or record for engineering memory.
    evidence_refs: str = "",  # Comma-separated artifact URIs that support the finding.
    severity: str = "",  # Finding severity: low, medium, high, or critical.
    recommended_recipient: str = "",  # Agent id that should act on the finding next.
    params: dict | None = None,  # Optional adapter-specific fields merged into the observation payload.
) -> dict:
    """Record the model source, spec revision, and language.

    Purpose:
        For the behavioral reference-model specialist that encodes the specification for scoreboard comparison against the DUT: Record the model source, spec revision, and language.
        Invoking ``record_reference_model_version`` records the intended verification operation for agent ``reference_model``.
        A bound framework adapter performs the real EDA work; this process only builds the observation.

    Arguments:
        summary: One-sentence finding or record for engineering memory.
        evidence_refs: Comma-separated artifact URIs that support the finding.
        severity: Finding severity: low, medium, high, or critical.
        recommended_recipient: Agent id that should act on the finding next.
        params: Optional adapter-specific fields merged into the observation payload.

    Returns:
        A ``tool_observation`` dict for skill ``record_reference_model_version`` with ``agent_id='reference_model'``.

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
        'record_reference_model_version',  # Skill id; must match this agent's config.yaml skills[].callable.
        payload,  # Structured arguments consumed by the bound framework adapter.
        agent_id='reference_model',  # Telemetry and journal attribution for this specialist.
    )

