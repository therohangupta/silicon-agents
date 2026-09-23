"""Tools for the failure_triage agent in the EDA chip-design agent fleet.

Operation contracts for the failure_triage verification specialist.

This module is the stable operation contract for the failure-triage specialist that clusters failing sims and assigns likely owners with evidence. Each ``@tool``
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


@tool(description='Read failing simulation logs for this campaign.')
def read_failure_logs(
    candidate_ref: str = "",  # Artifact URI/id of the pinned RTL candidate under verification.
    report_ref: str = "",  # Artifact URI of a report; empty means the latest for this candidate.
    corner: str = "",  # PVT corner filter; empty reads every available corner.
    mode: str = "",  # Operating-mode filter; empty reads every available mode.
    params: dict | None = None,  # Optional adapter-specific fields merged into the observation payload.
) -> dict:
    """Read failing simulation logs for this campaign.

    Purpose:
        For the failure-triage specialist that clusters failing sims and assigns likely owners with evidence: Read failing simulation logs for this campaign.
        Invoking ``read_failure_logs`` records the intended verification operation for agent ``failure_triage``.
        A bound framework adapter performs the real EDA work; this process only builds the observation.

    Arguments:
        candidate_ref: Artifact URI/id of the pinned RTL candidate under verification.
        report_ref: Artifact URI of a report; empty means the latest for this candidate.
        corner: PVT corner filter; empty reads every available corner.
        mode: Operating-mode filter; empty reads every available mode.
        params: Optional adapter-specific fields merged into the observation payload.

    Returns:
        A ``tool_observation`` dict for skill ``read_failure_logs`` with ``agent_id='failure_triage'``.

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
        'read_failure_logs',  # Skill id; must match this agent's config.yaml skills[].callable.
        payload,  # Structured arguments consumed by the bound framework adapter.
        agent_id='failure_triage',  # Telemetry and journal attribution for this specialist.
    )


@tool(description='Read the waveform index for failing tests.')
def read_waveform_index(
    candidate_ref: str = "",  # Artifact URI/id of the pinned RTL candidate under verification.
    report_ref: str = "",  # Artifact URI of a report; empty means the latest for this candidate.
    corner: str = "",  # PVT corner filter; empty reads every available corner.
    mode: str = "",  # Operating-mode filter; empty reads every available mode.
    params: dict | None = None,  # Optional adapter-specific fields merged into the observation payload.
) -> dict:
    """Read the waveform index for failing tests.

    Purpose:
        For the failure-triage specialist that clusters failing sims and assigns likely owners with evidence: Read the waveform index for failing tests.
        Invoking ``read_waveform_index`` records the intended verification operation for agent ``failure_triage``.
        A bound framework adapter performs the real EDA work; this process only builds the observation.

    Arguments:
        candidate_ref: Artifact URI/id of the pinned RTL candidate under verification.
        report_ref: Artifact URI of a report; empty means the latest for this candidate.
        corner: PVT corner filter; empty reads every available corner.
        mode: Operating-mode filter; empty reads every available mode.
        params: Optional adapter-specific fields merged into the observation payload.

    Returns:
        A ``tool_observation`` dict for skill ``read_waveform_index`` with ``agent_id='failure_triage'``.

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
        'read_waveform_index',  # Skill id; must match this agent's config.yaml skills[].callable.
        payload,  # Structured arguments consumed by the bound framework adapter.
        agent_id='failure_triage',  # Telemetry and journal attribution for this specialist.
    )


@tool(description='Group failures that share a signature.')
def cluster_failures(
    candidate_ref: str = "",  # Artifact URI/id of the pinned RTL candidate under verification.
    report_ref: str = "",  # Artifact URI of a report; empty means the latest for this candidate.
    corner: str = "",  # PVT corner filter; empty reads every available corner.
    mode: str = "",  # Operating-mode filter; empty reads every available mode.
    params: dict | None = None,  # Optional adapter-specific fields merged into the observation payload.
) -> dict:
    """Group failures that share a signature.

    Purpose:
        For the failure-triage specialist that clusters failing sims and assigns likely owners with evidence: Group failures that share a signature.
        Invoking ``cluster_failures`` records the intended verification operation for agent ``failure_triage``.
        A bound framework adapter performs the real EDA work; this process only builds the observation.

    Arguments:
        candidate_ref: Artifact URI/id of the pinned RTL candidate under verification.
        report_ref: Artifact URI of a report; empty means the latest for this candidate.
        corner: PVT corner filter; empty reads every available corner.
        mode: Operating-mode filter; empty reads every available mode.
        params: Optional adapter-specific fields merged into the observation payload.

    Returns:
        A ``tool_observation`` dict for skill ``cluster_failures`` with ``agent_id='failure_triage'``.

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
        'cluster_failures',  # Skill id; must match this agent's config.yaml skills[].callable.
        payload,  # Structured arguments consumed by the bound framework adapter.
        agent_id='failure_triage',  # Telemetry and journal attribution for this specialist.
    )


@tool(description='Extract the first error, time, and hierarchy for one failure.')
def extract_failure_signature(
    candidate_ref: str = "",  # Artifact URI/id of the pinned RTL candidate under verification.
    report_ref: str = "",  # Artifact URI of a report; empty means the latest for this candidate.
    corner: str = "",  # PVT corner filter; empty reads every available corner.
    mode: str = "",  # Operating-mode filter; empty reads every available mode.
    test_id: str = "",  # Argument ``test_id`` forwarded into the observation payload for this EDA skill.
    params: dict | None = None,  # Optional adapter-specific fields merged into the observation payload.
) -> dict:
    """Extract the first error, time, and hierarchy for one failure.

    Purpose:
        For the failure-triage specialist that clusters failing sims and assigns likely owners with evidence: Extract the first error, time, and hierarchy for one failure.
        Invoking ``extract_failure_signature`` records the intended verification operation for agent ``failure_triage``.
        A bound framework adapter performs the real EDA work; this process only builds the observation.

    Arguments:
        candidate_ref: Artifact URI/id of the pinned RTL candidate under verification.
        report_ref: Artifact URI of a report; empty means the latest for this candidate.
        corner: PVT corner filter; empty reads every available corner.
        mode: Operating-mode filter; empty reads every available mode.
        test_id: Payload field ``test_id``.
        params: Optional adapter-specific fields merged into the observation payload.

    Returns:
        A ``tool_observation`` dict for skill ``extract_failure_signature`` with ``agent_id='failure_triage'``.

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
        'test_id': test_id,  # Field ``test_id`` required by this verification operation.
    }
    if params:
        # Optional extras override base keys so framework adapters can extend the contract.
        payload.update(params)
    return tool_observation(
        'extract_failure_signature',  # Skill id; must match this agent's config.yaml skills[].callable.
        payload,  # Structured arguments consumed by the bound framework adapter.
        agent_id='failure_triage',  # Telemetry and journal attribution for this specialist.
    )


@tool(description='Separate license, timeout, and compile failures from functional failures.')
def separate_infrastructure_failures(
    candidate_ref: str = "",  # Artifact URI/id of the pinned RTL candidate under verification.
    report_ref: str = "",  # Artifact URI of a report; empty means the latest for this candidate.
    corner: str = "",  # PVT corner filter; empty reads every available corner.
    mode: str = "",  # Operating-mode filter; empty reads every available mode.
    params: dict | None = None,  # Optional adapter-specific fields merged into the observation payload.
) -> dict:
    """Separate license, timeout, and compile failures from functional failures.

    Purpose:
        For the failure-triage specialist that clusters failing sims and assigns likely owners with evidence: Separate license, timeout, and compile failures from functional failures.
        Invoking ``separate_infrastructure_failures`` records the intended verification operation for agent ``failure_triage``.
        A bound framework adapter performs the real EDA work; this process only builds the observation.

    Arguments:
        candidate_ref: Artifact URI/id of the pinned RTL candidate under verification.
        report_ref: Artifact URI of a report; empty means the latest for this candidate.
        corner: PVT corner filter; empty reads every available corner.
        mode: Operating-mode filter; empty reads every available mode.
        params: Optional adapter-specific fields merged into the observation payload.

    Returns:
        A ``tool_observation`` dict for skill ``separate_infrastructure_failures`` with ``agent_id='failure_triage'``.

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
        'separate_infrastructure_failures',  # Skill id; must match this agent's config.yaml skills[].callable.
        payload,  # Structured arguments consumed by the bound framework adapter.
        agent_id='failure_triage',  # Telemetry and journal attribution for this specialist.
    )


@tool(description='Name the likely owner, confidence, and evidence for a cluster.')
def assign_likely_owner(
    summary: str = "",  # One-sentence finding or record for engineering memory.
    evidence_refs: str = "",  # Comma-separated artifact URIs that support the finding.
    severity: str = "",  # Finding severity: low, medium, high, or critical.
    recommended_recipient: str = "",  # Agent id that should act on the finding next.
    cluster_id: str = "",  # Failure-cluster identifier produced by failure triage.
    params: dict | None = None,  # Optional adapter-specific fields merged into the observation payload.
) -> dict:
    """Name the likely owner, confidence, and evidence for a cluster.

    Purpose:
        For the failure-triage specialist that clusters failing sims and assigns likely owners with evidence: Name the likely owner, confidence, and evidence for a cluster.
        Invoking ``assign_likely_owner`` records the intended verification operation for agent ``failure_triage``.
        A bound framework adapter performs the real EDA work; this process only builds the observation.

    Arguments:
        summary: One-sentence finding or record for engineering memory.
        evidence_refs: Comma-separated artifact URIs that support the finding.
        severity: Finding severity: low, medium, high, or critical.
        recommended_recipient: Agent id that should act on the finding next.
        cluster_id: Failure-cluster identifier produced by failure triage.
        params: Optional adapter-specific fields merged into the observation payload.

    Returns:
        A ``tool_observation`` dict for skill ``assign_likely_owner`` with ``agent_id='failure_triage'``.

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
        'cluster_id': cluster_id,  # Failure-cluster identifier produced by failure triage.
    }
    if params:
        # Optional extras override base keys so framework adapters can extend the contract.
        payload.update(params)
    return tool_observation(
        'assign_likely_owner',  # Skill id; must match this agent's config.yaml skills[].callable.
        payload,  # Structured arguments consumed by the bound framework adapter.
        agent_id='failure_triage',  # Telemetry and journal attribution for this specialist.
    )


@tool(description='Rank clusters by how many seeds they cover.')
def rank_clusters_by_frequency(
    candidate_ref: str = "",  # Artifact URI/id of the pinned RTL candidate under verification.
    report_ref: str = "",  # Artifact URI of a report; empty means the latest for this candidate.
    corner: str = "",  # PVT corner filter; empty reads every available corner.
    mode: str = "",  # Operating-mode filter; empty reads every available mode.
    params: dict | None = None,  # Optional adapter-specific fields merged into the observation payload.
) -> dict:
    """Rank clusters by how many seeds they cover.

    Purpose:
        For the failure-triage specialist that clusters failing sims and assigns likely owners with evidence: Rank clusters by how many seeds they cover.
        Invoking ``rank_clusters_by_frequency`` records the intended verification operation for agent ``failure_triage``.
        A bound framework adapter performs the real EDA work; this process only builds the observation.

    Arguments:
        candidate_ref: Artifact URI/id of the pinned RTL candidate under verification.
        report_ref: Artifact URI of a report; empty means the latest for this candidate.
        corner: PVT corner filter; empty reads every available corner.
        mode: Operating-mode filter; empty reads every available mode.
        params: Optional adapter-specific fields merged into the observation payload.

    Returns:
        A ``tool_observation`` dict for skill ``rank_clusters_by_frequency`` with ``agent_id='failure_triage'``.

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
        'rank_clusters_by_frequency',  # Skill id; must match this agent's config.yaml skills[].callable.
        payload,  # Structured arguments consumed by the bound framework adapter.
        agent_id='failure_triage',  # Telemetry and journal attribution for this specialist.
    )


@tool(description='Read the logs and waves attached to one cluster.')
def read_cluster_evidence(
    candidate_ref: str = "",  # Artifact URI/id of the pinned RTL candidate under verification.
    report_ref: str = "",  # Artifact URI of a report; empty means the latest for this candidate.
    corner: str = "",  # PVT corner filter; empty reads every available corner.
    mode: str = "",  # Operating-mode filter; empty reads every available mode.
    cluster_id: str = "",  # Failure-cluster identifier produced by failure triage.
    params: dict | None = None,  # Optional adapter-specific fields merged into the observation payload.
) -> dict:
    """Read the logs and waves attached to one cluster.

    Purpose:
        For the failure-triage specialist that clusters failing sims and assigns likely owners with evidence: Read the logs and waves attached to one cluster.
        Invoking ``read_cluster_evidence`` records the intended verification operation for agent ``failure_triage``.
        A bound framework adapter performs the real EDA work; this process only builds the observation.

    Arguments:
        candidate_ref: Artifact URI/id of the pinned RTL candidate under verification.
        report_ref: Artifact URI of a report; empty means the latest for this candidate.
        corner: PVT corner filter; empty reads every available corner.
        mode: Operating-mode filter; empty reads every available mode.
        cluster_id: Failure-cluster identifier produced by failure triage.
        params: Optional adapter-specific fields merged into the observation payload.

    Returns:
        A ``tool_observation`` dict for skill ``read_cluster_evidence`` with ``agent_id='failure_triage'``.

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
        'cluster_id': cluster_id,  # Failure-cluster identifier produced by failure triage.
    }
    if params:
        # Optional extras override base keys so framework adapters can extend the contract.
        payload.update(params)
    return tool_observation(
        'read_cluster_evidence',  # Skill id; must match this agent's config.yaml skills[].callable.
        payload,  # Structured arguments consumed by the bound framework adapter.
        agent_id='failure_triage',  # Telemetry and journal attribution for this specialist.
    )


@tool(description='Publish a cluster that has evidence but no likely owner.')
def flag_unowned_cluster(
    summary: str = "",  # One-sentence finding or record for engineering memory.
    evidence_refs: str = "",  # Comma-separated artifact URIs that support the finding.
    severity: str = "",  # Finding severity: low, medium, high, or critical.
    recommended_recipient: str = "",  # Agent id that should act on the finding next.
    params: dict | None = None,  # Optional adapter-specific fields merged into the observation payload.
) -> dict:
    """Publish a cluster that has evidence but no likely owner.

    Purpose:
        For the failure-triage specialist that clusters failing sims and assigns likely owners with evidence: Publish a cluster that has evidence but no likely owner.
        Invoking ``flag_unowned_cluster`` records the intended verification operation for agent ``failure_triage``.
        A bound framework adapter performs the real EDA work; this process only builds the observation.

    Arguments:
        summary: One-sentence finding or record for engineering memory.
        evidence_refs: Comma-separated artifact URIs that support the finding.
        severity: Finding severity: low, medium, high, or critical.
        recommended_recipient: Agent id that should act on the finding next.
        params: Optional adapter-specific fields merged into the observation payload.

    Returns:
        A ``tool_observation`` dict for skill ``flag_unowned_cluster`` with ``agent_id='failure_triage'``.

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
        'flag_unowned_cluster',  # Skill id; must match this agent's config.yaml skills[].callable.
        payload,  # Structured arguments consumed by the bound framework adapter.
        agent_id='failure_triage',  # Telemetry and journal attribution for this specialist.
    )


@tool(description='Publish a cluster whose members do not share a signature.')
def flag_mixed_signature_cluster(
    summary: str = "",  # One-sentence finding or record for engineering memory.
    evidence_refs: str = "",  # Comma-separated artifact URIs that support the finding.
    severity: str = "",  # Finding severity: low, medium, high, or critical.
    recommended_recipient: str = "",  # Agent id that should act on the finding next.
    params: dict | None = None,  # Optional adapter-specific fields merged into the observation payload.
) -> dict:
    """Publish a cluster whose members do not share a signature.

    Purpose:
        For the failure-triage specialist that clusters failing sims and assigns likely owners with evidence: Publish a cluster whose members do not share a signature.
        Invoking ``flag_mixed_signature_cluster`` records the intended verification operation for agent ``failure_triage``.
        A bound framework adapter performs the real EDA work; this process only builds the observation.

    Arguments:
        summary: One-sentence finding or record for engineering memory.
        evidence_refs: Comma-separated artifact URIs that support the finding.
        severity: Finding severity: low, medium, high, or critical.
        recommended_recipient: Agent id that should act on the finding next.
        params: Optional adapter-specific fields merged into the observation payload.

    Returns:
        A ``tool_observation`` dict for skill ``flag_mixed_signature_cluster`` with ``agent_id='failure_triage'``.

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
        'flag_mixed_signature_cluster',  # Skill id; must match this agent's config.yaml skills[].callable.
        payload,  # Structured arguments consumed by the bound framework adapter.
        agent_id='failure_triage',  # Telemetry and journal attribution for this specialist.
    )


@tool(description='Record the confidence and the evidence refs for a cluster assignment.')
def record_triage_confidence(
    summary: str = "",  # One-sentence finding or record for engineering memory.
    evidence_refs: str = "",  # Comma-separated artifact URIs that support the finding.
    severity: str = "",  # Finding severity: low, medium, high, or critical.
    recommended_recipient: str = "",  # Agent id that should act on the finding next.
    params: dict | None = None,  # Optional adapter-specific fields merged into the observation payload.
) -> dict:
    """Record the confidence and the evidence refs for a cluster assignment.

    Purpose:
        For the failure-triage specialist that clusters failing sims and assigns likely owners with evidence: Record the confidence and the evidence refs for a cluster assignment.
        Invoking ``record_triage_confidence`` records the intended verification operation for agent ``failure_triage``.
        A bound framework adapter performs the real EDA work; this process only builds the observation.

    Arguments:
        summary: One-sentence finding or record for engineering memory.
        evidence_refs: Comma-separated artifact URIs that support the finding.
        severity: Finding severity: low, medium, high, or critical.
        recommended_recipient: Agent id that should act on the finding next.
        params: Optional adapter-specific fields merged into the observation payload.

    Returns:
        A ``tool_observation`` dict for skill ``record_triage_confidence`` with ``agent_id='failure_triage'``.

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
        'record_triage_confidence',  # Skill id; must match this agent's config.yaml skills[].callable.
        payload,  # Structured arguments consumed by the bound framework adapter.
        agent_id='failure_triage',  # Telemetry and journal attribution for this specialist.
    )


@tool(description='Publish the cluster id, signature, seeds, and likely owner.')
def publish_failure_cluster(
    summary: str = "",  # One-sentence finding or record for engineering memory.
    evidence_refs: str = "",  # Comma-separated artifact URIs that support the finding.
    severity: str = "",  # Finding severity: low, medium, high, or critical.
    recommended_recipient: str = "",  # Agent id that should act on the finding next.
    params: dict | None = None,  # Optional adapter-specific fields merged into the observation payload.
) -> dict:
    """Publish the cluster id, signature, seeds, and likely owner.

    Purpose:
        For the failure-triage specialist that clusters failing sims and assigns likely owners with evidence: Publish the cluster id, signature, seeds, and likely owner.
        Invoking ``publish_failure_cluster`` records the intended verification operation for agent ``failure_triage``.
        A bound framework adapter performs the real EDA work; this process only builds the observation.

    Arguments:
        summary: One-sentence finding or record for engineering memory.
        evidence_refs: Comma-separated artifact URIs that support the finding.
        severity: Finding severity: low, medium, high, or critical.
        recommended_recipient: Agent id that should act on the finding next.
        params: Optional adapter-specific fields merged into the observation payload.

    Returns:
        A ``tool_observation`` dict for skill ``publish_failure_cluster`` with ``agent_id='failure_triage'``.

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
        'publish_failure_cluster',  # Skill id; must match this agent's config.yaml skills[].callable.
        payload,  # Structured arguments consumed by the bound framework adapter.
        agent_id='failure_triage',  # Telemetry and journal attribution for this specialist.
    )

