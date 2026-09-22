"""Tools for the reproduction agent in the EDA chip-design agent fleet.

Operation contracts for the reproduction verification specialist.

This module is the stable operation contract for the reproduction specialist that minimizes failing seeds/waveforms for a triage cluster. Each ``@tool``
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


@tool(description='Read the waveform for the seed that represents this cluster.')
def read_failing_waveform(
    candidate_ref: str = "",  # Artifact URI/id of the pinned RTL candidate under verification.
    report_ref: str = "",  # Artifact URI of a report; empty means the latest for this candidate.
    corner: str = "",  # PVT corner filter; empty reads every available corner.
    mode: str = "",  # Operating-mode filter; empty reads every available mode.
    params: dict | None = None,  # Optional adapter-specific fields merged into the observation payload.
) -> dict:
    """Read the waveform for the seed that represents this cluster.

    Purpose:
        For the reproduction specialist that minimizes failing seeds/waveforms for a triage cluster: Read the waveform for the seed that represents this cluster.
        Invoking ``read_failing_waveform`` records the intended verification operation for agent ``reproduction``.
        A bound framework adapter performs the real EDA work; this process only builds the observation.

    Arguments:
        candidate_ref: Artifact URI/id of the pinned RTL candidate under verification.
        report_ref: Artifact URI of a report; empty means the latest for this candidate.
        corner: PVT corner filter; empty reads every available corner.
        mode: Operating-mode filter; empty reads every available mode.
        params: Optional adapter-specific fields merged into the observation payload.

    Returns:
        A ``tool_observation`` dict for skill ``read_failing_waveform`` with ``agent_id='reproduction'``.

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
        'read_failing_waveform',  # Skill id; must match this agent's config.yaml skills[].callable.
        payload,  # Structured arguments consumed by the bound framework adapter.
        agent_id='reproduction',  # Telemetry and journal attribution for this specialist.
    )


@tool(description='Reduce a failing test to a stable reproduction.')
def minimize_failure(
    candidate_ref: str = "",  # Artifact URI/id of the pinned RTL candidate under verification.
    baseline_ref: str = "",  # Baseline candidate or golden revision used for comparison.
    hypothesis: str = "",  # Working hypothesis or change intent guiding this edit/analysis.
    cluster_id: str = "",  # Failure-cluster identifier produced by failure triage.
    params: dict | None = None,  # Optional adapter-specific fields merged into the observation payload.
) -> dict:
    """Reduce a failing test to a stable reproduction.

    Purpose:
        For the reproduction specialist that minimizes failing seeds/waveforms for a triage cluster: Reduce a failing test to a stable reproduction.
        Invoking ``minimize_failure`` records the intended verification operation for agent ``reproduction``.
        A bound framework adapter performs the real EDA work; this process only builds the observation.

    Arguments:
        candidate_ref: Artifact URI/id of the pinned RTL candidate under verification.
        baseline_ref: Baseline candidate or golden revision used for comparison.
        hypothesis: Working hypothesis or change intent guiding this edit/analysis.
        cluster_id: Failure-cluster identifier produced by failure triage.
        params: Optional adapter-specific fields merged into the observation payload.

    Returns:
        A ``tool_observation`` dict for skill ``minimize_failure`` with ``agent_id='reproduction'``.

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
        'cluster_id': cluster_id,  # Failure-cluster identifier produced by failure triage.
    }
    if params:
        # Optional extras override base keys so framework adapters can extend the contract.
        payload.update(params)
    return tool_observation(
        'minimize_failure',  # Skill id; must match this agent's config.yaml skills[].callable.
        payload,  # Structured arguments consumed by the bound framework adapter.
        agent_id='reproduction',  # Telemetry and journal attribution for this specialist.
    )


@tool(description='Extract the signals and time window that show the failure.')
def slice_waveform(
    candidate_ref: str = "",  # Artifact URI/id of the pinned RTL candidate under verification.
    report_ref: str = "",  # Artifact URI of a report; empty means the latest for this candidate.
    corner: str = "",  # PVT corner filter; empty reads every available corner.
    mode: str = "",  # Operating-mode filter; empty reads every available mode.
    params: dict | None = None,  # Optional adapter-specific fields merged into the observation payload.
) -> dict:
    """Extract the signals and time window that show the failure.

    Purpose:
        For the reproduction specialist that minimizes failing seeds/waveforms for a triage cluster: Extract the signals and time window that show the failure.
        Invoking ``slice_waveform`` records the intended verification operation for agent ``reproduction``.
        A bound framework adapter performs the real EDA work; this process only builds the observation.

    Arguments:
        candidate_ref: Artifact URI/id of the pinned RTL candidate under verification.
        report_ref: Artifact URI of a report; empty means the latest for this candidate.
        corner: PVT corner filter; empty reads every available corner.
        mode: Operating-mode filter; empty reads every available mode.
        params: Optional adapter-specific fields merged into the observation payload.

    Returns:
        A ``tool_observation`` dict for skill ``slice_waveform`` with ``agent_id='reproduction'``.

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
        'slice_waveform',  # Skill id; must match this agent's config.yaml skills[].callable.
        payload,  # Structured arguments consumed by the bound framework adapter.
        agent_id='reproduction',  # Telemetry and journal attribution for this specialist.
    )


@tool(description='Write the minimized test on an isolated branch.')
def write_reproduction_test(
    candidate_ref: str = "",  # Artifact URI/id of the pinned RTL candidate under verification.
    baseline_ref: str = "",  # Baseline candidate or golden revision used for comparison.
    hypothesis: str = "",  # Working hypothesis or change intent guiding this edit/analysis.
    params: dict | None = None,  # Optional adapter-specific fields merged into the observation payload.
) -> dict:
    """Write the minimized test on an isolated branch.

    Purpose:
        For the reproduction specialist that minimizes failing seeds/waveforms for a triage cluster: Write the minimized test on an isolated branch.
        Invoking ``write_reproduction_test`` records the intended verification operation for agent ``reproduction``.
        A bound framework adapter performs the real EDA work; this process only builds the observation.

    Arguments:
        candidate_ref: Artifact URI/id of the pinned RTL candidate under verification.
        baseline_ref: Baseline candidate or golden revision used for comparison.
        hypothesis: Working hypothesis or change intent guiding this edit/analysis.
        params: Optional adapter-specific fields merged into the observation payload.

    Returns:
        A ``tool_observation`` dict for skill ``write_reproduction_test`` with ``agent_id='reproduction'``.

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
        'write_reproduction_test',  # Skill id; must match this agent's config.yaml skills[].callable.
        payload,  # Structured arguments consumed by the bound framework adapter.
        agent_id='reproduction',  # Telemetry and journal attribution for this specialist.
    )


@tool(description='Rerun the minimized test and confirm it still fails.')
def confirm_reproduction_fails(
    candidate_ref: str = "",  # Artifact URI/id of the pinned RTL candidate under verification.
    baseline_ref: str = "",  # Baseline candidate or golden revision used for comparison.
    recipe: str = "",  # Frozen compile/run recipe id (plusargs, defines, tool options).
    corner: str = "",  # PVT corner filter; empty reads every available corner.
    mode: str = "",  # Operating-mode filter; empty reads every available mode.
    params: dict | None = None,  # Optional adapter-specific fields merged into the observation payload.
) -> dict:
    """Rerun the minimized test and confirm it still fails.

    Purpose:
        For the reproduction specialist that minimizes failing seeds/waveforms for a triage cluster: Rerun the minimized test and confirm it still fails.
        Invoking ``confirm_reproduction_fails`` records the intended verification operation for agent ``reproduction``.
        A bound framework adapter performs the real EDA work; this process only builds the observation.

    Arguments:
        candidate_ref: Artifact URI/id of the pinned RTL candidate under verification.
        baseline_ref: Baseline candidate or golden revision used for comparison.
        recipe: Frozen compile/run recipe id (plusargs, defines, tool options).
        corner: PVT corner filter; empty reads every available corner.
        mode: Operating-mode filter; empty reads every available mode.
        params: Optional adapter-specific fields merged into the observation payload.

    Returns:
        A ``tool_observation`` dict for skill ``confirm_reproduction_fails`` with ``agent_id='reproduction'``.

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
        'confirm_reproduction_fails',  # Skill id; must match this agent's config.yaml skills[].callable.
        payload,  # Structured arguments consumed by the bound framework adapter.
        agent_id='reproduction',  # Telemetry and journal attribution for this specialist.
    )


@tool(description='Rerun the minimized test across the requested seeds and report which still fail.')
def confirm_reproduction_stable(
    candidate_ref: str = "",  # Artifact URI/id of the pinned RTL candidate under verification.
    baseline_ref: str = "",  # Baseline candidate or golden revision used for comparison.
    recipe: str = "",  # Frozen compile/run recipe id (plusargs, defines, tool options).
    corner: str = "",  # PVT corner filter; empty reads every available corner.
    mode: str = "",  # Operating-mode filter; empty reads every available mode.
    params: dict | None = None,  # Optional adapter-specific fields merged into the observation payload.
) -> dict:
    """Rerun the minimized test across the requested seeds and report which still fail.

    Purpose:
        For the reproduction specialist that minimizes failing seeds/waveforms for a triage cluster: Rerun the minimized test across the requested seeds and report which still fail.
        Invoking ``confirm_reproduction_stable`` records the intended verification operation for agent ``reproduction``.
        A bound framework adapter performs the real EDA work; this process only builds the observation.

    Arguments:
        candidate_ref: Artifact URI/id of the pinned RTL candidate under verification.
        baseline_ref: Baseline candidate or golden revision used for comparison.
        recipe: Frozen compile/run recipe id (plusargs, defines, tool options).
        corner: PVT corner filter; empty reads every available corner.
        mode: Operating-mode filter; empty reads every available mode.
        params: Optional adapter-specific fields merged into the observation payload.

    Returns:
        A ``tool_observation`` dict for skill ``confirm_reproduction_stable`` with ``agent_id='reproduction'``.

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
        'confirm_reproduction_stable',  # Skill id; must match this agent's config.yaml skills[].callable.
        payload,  # Structured arguments consumed by the bound framework adapter.
        agent_id='reproduction',  # Telemetry and journal attribution for this specialist.
    )


@tool(description='List the signals required to see the failure.')
def list_reproduction_signals(
    candidate_ref: str = "",  # Artifact URI/id of the pinned RTL candidate under verification.
    report_ref: str = "",  # Artifact URI of a report; empty means the latest for this candidate.
    corner: str = "",  # PVT corner filter; empty reads every available corner.
    mode: str = "",  # Operating-mode filter; empty reads every available mode.
    params: dict | None = None,  # Optional adapter-specific fields merged into the observation payload.
) -> dict:
    """List the signals required to see the failure.

    Purpose:
        For the reproduction specialist that minimizes failing seeds/waveforms for a triage cluster: List the signals required to see the failure.
        Invoking ``list_reproduction_signals`` records the intended verification operation for agent ``reproduction``.
        A bound framework adapter performs the real EDA work; this process only builds the observation.

    Arguments:
        candidate_ref: Artifact URI/id of the pinned RTL candidate under verification.
        report_ref: Artifact URI of a report; empty means the latest for this candidate.
        corner: PVT corner filter; empty reads every available corner.
        mode: Operating-mode filter; empty reads every available mode.
        params: Optional adapter-specific fields merged into the observation payload.

    Returns:
        A ``tool_observation`` dict for skill ``list_reproduction_signals`` with ``agent_id='reproduction'``.

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
        'list_reproduction_signals',  # Skill id; must match this agent's config.yaml skills[].callable.
        payload,  # Structured arguments consumed by the bound framework adapter.
        agent_id='reproduction',  # Telemetry and journal attribution for this specialist.
    )


@tool(description='Show what the minimization removed.')
def diff_reproduction_against_original(
    candidate_ref: str = "",  # Artifact URI/id of the pinned RTL candidate under verification.
    report_ref: str = "",  # Artifact URI of a report; empty means the latest for this candidate.
    corner: str = "",  # PVT corner filter; empty reads every available corner.
    mode: str = "",  # Operating-mode filter; empty reads every available mode.
    params: dict | None = None,  # Optional adapter-specific fields merged into the observation payload.
) -> dict:
    """Show what the minimization removed.

    Purpose:
        For the reproduction specialist that minimizes failing seeds/waveforms for a triage cluster: Show what the minimization removed.
        Invoking ``diff_reproduction_against_original`` records the intended verification operation for agent ``reproduction``.
        A bound framework adapter performs the real EDA work; this process only builds the observation.

    Arguments:
        candidate_ref: Artifact URI/id of the pinned RTL candidate under verification.
        report_ref: Artifact URI of a report; empty means the latest for this candidate.
        corner: PVT corner filter; empty reads every available corner.
        mode: Operating-mode filter; empty reads every available mode.
        params: Optional adapter-specific fields merged into the observation payload.

    Returns:
        A ``tool_observation`` dict for skill ``diff_reproduction_against_original`` with ``agent_id='reproduction'``.

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
        'diff_reproduction_against_original',  # Skill id; must match this agent's config.yaml skills[].callable.
        payload,  # Structured arguments consumed by the bound framework adapter.
        agent_id='reproduction',  # Telemetry and journal attribution for this specialist.
    )


@tool(description='Publish a minimized test that does not fail reliably.')
def flag_unstable_reproduction(
    summary: str = "",  # One-sentence finding or record for engineering memory.
    evidence_refs: str = "",  # Comma-separated artifact URIs that support the finding.
    severity: str = "",  # Finding severity: low, medium, high, or critical.
    recommended_recipient: str = "",  # Agent id that should act on the finding next.
    params: dict | None = None,  # Optional adapter-specific fields merged into the observation payload.
) -> dict:
    """Publish a minimized test that does not fail reliably.

    Purpose:
        For the reproduction specialist that minimizes failing seeds/waveforms for a triage cluster: Publish a minimized test that does not fail reliably.
        Invoking ``flag_unstable_reproduction`` records the intended verification operation for agent ``reproduction``.
        A bound framework adapter performs the real EDA work; this process only builds the observation.

    Arguments:
        summary: One-sentence finding or record for engineering memory.
        evidence_refs: Comma-separated artifact URIs that support the finding.
        severity: Finding severity: low, medium, high, or critical.
        recommended_recipient: Agent id that should act on the finding next.
        params: Optional adapter-specific fields merged into the observation payload.

    Returns:
        A ``tool_observation`` dict for skill ``flag_unstable_reproduction`` with ``agent_id='reproduction'``.

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
        'flag_unstable_reproduction',  # Skill id; must match this agent's config.yaml skills[].callable.
        payload,  # Structured arguments consumed by the bound framework adapter.
        agent_id='reproduction',  # Telemetry and journal attribution for this specialist.
    )


@tool(description='Publish a minimized test whose first error differs from the original.')
def flag_reproduction_changed_symptom(
    summary: str = "",  # One-sentence finding or record for engineering memory.
    evidence_refs: str = "",  # Comma-separated artifact URIs that support the finding.
    severity: str = "",  # Finding severity: low, medium, high, or critical.
    recommended_recipient: str = "",  # Agent id that should act on the finding next.
    params: dict | None = None,  # Optional adapter-specific fields merged into the observation payload.
) -> dict:
    """Publish a minimized test whose first error differs from the original.

    Purpose:
        For the reproduction specialist that minimizes failing seeds/waveforms for a triage cluster: Publish a minimized test whose first error differs from the original.
        Invoking ``flag_reproduction_changed_symptom`` records the intended verification operation for agent ``reproduction``.
        A bound framework adapter performs the real EDA work; this process only builds the observation.

    Arguments:
        summary: One-sentence finding or record for engineering memory.
        evidence_refs: Comma-separated artifact URIs that support the finding.
        severity: Finding severity: low, medium, high, or critical.
        recommended_recipient: Agent id that should act on the finding next.
        params: Optional adapter-specific fields merged into the observation payload.

    Returns:
        A ``tool_observation`` dict for skill ``flag_reproduction_changed_symptom`` with ``agent_id='reproduction'``.

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
        'flag_reproduction_changed_symptom',  # Skill id; must match this agent's config.yaml skills[].callable.
        payload,  # Structured arguments consumed by the bound framework adapter.
        agent_id='reproduction',  # Telemetry and journal attribution for this specialist.
    )


@tool(description='Record the test, seed, waveform slice, and original cluster.')
def record_reproduction_artifact(
    summary: str = "",  # One-sentence finding or record for engineering memory.
    evidence_refs: str = "",  # Comma-separated artifact URIs that support the finding.
    severity: str = "",  # Finding severity: low, medium, high, or critical.
    recommended_recipient: str = "",  # Agent id that should act on the finding next.
    params: dict | None = None,  # Optional adapter-specific fields merged into the observation payload.
) -> dict:
    """Record the test, seed, waveform slice, and original cluster.

    Purpose:
        For the reproduction specialist that minimizes failing seeds/waveforms for a triage cluster: Record the test, seed, waveform slice, and original cluster.
        Invoking ``record_reproduction_artifact`` records the intended verification operation for agent ``reproduction``.
        A bound framework adapter performs the real EDA work; this process only builds the observation.

    Arguments:
        summary: One-sentence finding or record for engineering memory.
        evidence_refs: Comma-separated artifact URIs that support the finding.
        severity: Finding severity: low, medium, high, or critical.
        recommended_recipient: Agent id that should act on the finding next.
        params: Optional adapter-specific fields merged into the observation payload.

    Returns:
        A ``tool_observation`` dict for skill ``record_reproduction_artifact`` with ``agent_id='reproduction'``.

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
        'record_reproduction_artifact',  # Skill id; must match this agent's config.yaml skills[].callable.
        payload,  # Structured arguments consumed by the bound framework adapter.
        agent_id='reproduction',  # Telemetry and journal attribution for this specialist.
    )


@tool(description='Publish the minimized test ref and the waveform slice.')
def publish_reproduction(
    summary: str = "",  # One-sentence finding or record for engineering memory.
    evidence_refs: str = "",  # Comma-separated artifact URIs that support the finding.
    severity: str = "",  # Finding severity: low, medium, high, or critical.
    recommended_recipient: str = "",  # Agent id that should act on the finding next.
    params: dict | None = None,  # Optional adapter-specific fields merged into the observation payload.
) -> dict:
    """Publish the minimized test ref and the waveform slice.

    Purpose:
        For the reproduction specialist that minimizes failing seeds/waveforms for a triage cluster: Publish the minimized test ref and the waveform slice.
        Invoking ``publish_reproduction`` records the intended verification operation for agent ``reproduction``.
        A bound framework adapter performs the real EDA work; this process only builds the observation.

    Arguments:
        summary: One-sentence finding or record for engineering memory.
        evidence_refs: Comma-separated artifact URIs that support the finding.
        severity: Finding severity: low, medium, high, or critical.
        recommended_recipient: Agent id that should act on the finding next.
        params: Optional adapter-specific fields merged into the observation payload.

    Returns:
        A ``tool_observation`` dict for skill ``publish_reproduction`` with ``agent_id='reproduction'``.

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
        'publish_reproduction',  # Skill id; must match this agent's config.yaml skills[].callable.
        payload,  # Structured arguments consumed by the bound framework adapter.
        agent_id='reproduction',  # Telemetry and journal attribution for this specialist.
    )

