"""Tools for Low-Power Agent (`low_power`).

Each function is the stable operation contract for one advertised capability in config.yaml.
A framework adapter (OpenROAD, commercial CDC/lint/UPF, simulator, etc.) performs the real
work when `EDA_FRAMEWORK` is bound. Until then, every call returns status `not_run` via
`tool_observation` and does **not** invoke OpenROAD, Yosys, OpenSTA, a licensed tool, or a
simulator.

This agent serves the **rtl** stage of frontend chip design.
Unified Power Format (UPF) describes power domains, isolation, retention, and level shifters. This agent keeps UPF and RTL consistent so low-power intent survives into backend power analysis.

Callers (LLM runtime or orchestrator) pass string refs and optional `params`. Payloads are
assembled explicitly so telemetry and adapters see a stable schema per skill id.
"""

from __future__ import annotations  # Allow modern typing (dict | None) on older runtimes if needed.

from packages.agent_sdk import tool  # Decorator that registers the callable as an agent skill.
from domains.eda.eda import tool_observation  # Builds the stub/real observation dict for adapters.


@tool(description='Read power domains, supply nets, and isolation strategies.')  # Registers skill `read_upf` on `low_power`.
def read_upf(
    candidate_ref: str = '',  # Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.
    report_ref: str = '',  # Artifact URI of a prior report. Empty reads the latest report for this candidate.
    corner: str = '',  # PVT corner (process/voltage/temperature). Empty when the job is not corner-specific.
    mode: str = '',  # Functional or analysis mode string. Empty when the job is not mode-specific.
    params: dict | None = None,  # Optional extra keys from an adapter or caller; merged into the payload last.
) -> dict:
    """Read power domains, supply nets, and isolation strategies.

    Purpose:
        Read Unified Power Format power-intent for the candidate or block. This callable is the stable operation contract; a framework adapter
        performs the real EDA work when bound.

    Arguments:
        candidate_ref: Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.
        report_ref: Artifact URI of a prior report. Empty reads the latest report for this candidate.
        corner: PVT corner (process/voltage/temperature). Empty when the job is not corner-specific.
        mode: Functional or analysis mode string. Empty when the job is not mode-specific.
        params: Optional extra keys from an adapter or caller; merged into the payload last.

    Returns:
        dict observation from `tool_observation`, typically including status `not_run`
        until an EDA framework adapter is configured.

    Side effects:
        None on the filesystem while unbound. When bound, may submit tool jobs, read
        reports, edit isolated candidates, or publish findings per the skill's action.

    Failure behavior:
        Adapter/validation errors surface as observation error fields or raised exceptions
        handled by AgentService; this stub does not raise on the happy not_run path.
        """
    # Build the skill payload from explicit kwargs (stable schema for adapters).
    payload = {
        'candidate_ref': candidate_ref,  # Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.  # Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.
        'report_ref': report_ref,  # Artifact URI of a prior report. Empty reads the latest report for this candidate.  # Artifact URI of a prior report. Empty reads the latest report for this candidate.
        'corner': corner,  # PVT corner (process/voltage/temperature). Empty when the job is not corner-specific.  # PVT corner (process/voltage/temperature). Empty when the job is not corner-specific.
        'mode': mode  # Functional or analysis mode string. Empty when the job is not mode-specific.  # Functional or analysis mode string. Empty when the job is not mode-specific.
        }
    if params:  # Merge optional adapter/caller extras without dropping known keys.
        payload.update(params)  # Last-write wins for colliding keys from params.
    # Emit a structured observation; unbound adapters yield status not_run.
    return tool_observation(
        'read_upf',  # Skill id must match capabilities/skills in config.yaml.  # Skill id must match capabilities/skills in config.yaml.
        payload,  # Argument dict forwarded to the adapter / telemetry.  # Argument dict forwarded to the adapter / telemetry.
        agent_id='low_power',  # Routes telemetry and ACLs to this agent (`low_power`).  # Routes telemetry and ACLs to this agent (`low_power`).
        )

@tool(description='Compare UPF domains and RTL hierarchy.')  # Registers skill `check_upf_consistency` on `low_power`.
def check_upf_consistency(
    candidate_ref: str = '',  # Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.
    report_ref: str = '',  # Artifact URI of a prior report. Empty reads the latest report for this candidate.
    corner: str = '',  # PVT corner (process/voltage/temperature). Empty when the job is not corner-specific.
    mode: str = '',  # Functional or analysis mode string. Empty when the job is not mode-specific.
    params: dict | None = None,  # Optional extra keys from an adapter or caller; merged into the payload last.
) -> dict:
    """Compare UPF domains and RTL hierarchy.

    Purpose:
        Check UPF internal consistency (domains, supply sets, strategies). This callable is the stable operation contract; a framework adapter
        performs the real EDA work when bound.

    Arguments:
        candidate_ref: Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.
        report_ref: Artifact URI of a prior report. Empty reads the latest report for this candidate.
        corner: PVT corner (process/voltage/temperature). Empty when the job is not corner-specific.
        mode: Functional or analysis mode string. Empty when the job is not mode-specific.
        params: Optional extra keys from an adapter or caller; merged into the payload last.

    Returns:
        dict observation from `tool_observation`, typically including status `not_run`
        until an EDA framework adapter is configured.

    Side effects:
        None on the filesystem while unbound. When bound, may submit tool jobs, read
        reports, edit isolated candidates, or publish findings per the skill's action.

    Failure behavior:
        Adapter/validation errors surface as observation error fields or raised exceptions
        handled by AgentService; this stub does not raise on the happy not_run path.
        """
    # Build the skill payload from explicit kwargs (stable schema for adapters).
    payload = {
        'candidate_ref': candidate_ref,  # Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.  # Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.
        'report_ref': report_ref,  # Artifact URI of a prior report. Empty reads the latest report for this candidate.  # Artifact URI of a prior report. Empty reads the latest report for this candidate.
        'corner': corner,  # PVT corner (process/voltage/temperature). Empty when the job is not corner-specific.  # PVT corner (process/voltage/temperature). Empty when the job is not corner-specific.
        'mode': mode  # Functional or analysis mode string. Empty when the job is not mode-specific.  # Functional or analysis mode string. Empty when the job is not mode-specific.
        }
    if params:  # Merge optional adapter/caller extras without dropping known keys.
        payload.update(params)  # Last-write wins for colliding keys from params.
    # Emit a structured observation; unbound adapters yield status not_run.
    return tool_observation(
        'check_upf_consistency',  # Skill id must match capabilities/skills in config.yaml.  # Skill id must match capabilities/skills in config.yaml.
        payload,  # Argument dict forwarded to the adapter / telemetry.  # Argument dict forwarded to the adapter / telemetry.
        agent_id='low_power',  # Routes telemetry and ACLs to this agent (`low_power`).  # Routes telemetry and ACLs to this agent (`low_power`).
        )

@tool(description='Check isolation, retention, and level-shifter strategy.')  # Registers skill `check_isolation_retention` on `low_power`.
def check_isolation_retention(
    candidate_ref: str = '',  # Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.
    report_ref: str = '',  # Artifact URI of a prior report. Empty reads the latest report for this candidate.
    corner: str = '',  # PVT corner (process/voltage/temperature). Empty when the job is not corner-specific.
    mode: str = '',  # Functional or analysis mode string. Empty when the job is not mode-specific.
    params: dict | None = None,  # Optional extra keys from an adapter or caller; merged into the payload last.
) -> dict:
    """Check isolation, retention, and level-shifter strategy.

    Purpose:
        Verify isolation and retention strategies cover required crossings. This callable is the stable operation contract; a framework adapter
        performs the real EDA work when bound.

    Arguments:
        candidate_ref: Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.
        report_ref: Artifact URI of a prior report. Empty reads the latest report for this candidate.
        corner: PVT corner (process/voltage/temperature). Empty when the job is not corner-specific.
        mode: Functional or analysis mode string. Empty when the job is not mode-specific.
        params: Optional extra keys from an adapter or caller; merged into the payload last.

    Returns:
        dict observation from `tool_observation`, typically including status `not_run`
        until an EDA framework adapter is configured.

    Side effects:
        None on the filesystem while unbound. When bound, may submit tool jobs, read
        reports, edit isolated candidates, or publish findings per the skill's action.

    Failure behavior:
        Adapter/validation errors surface as observation error fields or raised exceptions
        handled by AgentService; this stub does not raise on the happy not_run path.
        """
    # Build the skill payload from explicit kwargs (stable schema for adapters).
    payload = {
        'candidate_ref': candidate_ref,  # Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.  # Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.
        'report_ref': report_ref,  # Artifact URI of a prior report. Empty reads the latest report for this candidate.  # Artifact URI of a prior report. Empty reads the latest report for this candidate.
        'corner': corner,  # PVT corner (process/voltage/temperature). Empty when the job is not corner-specific.  # PVT corner (process/voltage/temperature). Empty when the job is not corner-specific.
        'mode': mode  # Functional or analysis mode string. Empty when the job is not mode-specific.  # Functional or analysis mode string. Empty when the job is not mode-specific.
        }
    if params:  # Merge optional adapter/caller extras without dropping known keys.
        payload.update(params)  # Last-write wins for colliding keys from params.
    # Emit a structured observation; unbound adapters yield status not_run.
    return tool_observation(
        'check_isolation_retention',  # Skill id must match capabilities/skills in config.yaml.  # Skill id must match capabilities/skills in config.yaml.
        payload,  # Argument dict forwarded to the adapter / telemetry.  # Argument dict forwarded to the adapter / telemetry.
        agent_id='low_power',  # Routes telemetry and ACLs to this agent (`low_power`).  # Routes telemetry and ACLs to this agent (`low_power`).
        )

@tool(description='List domains, their supplies, and the modules inside them.')  # Registers skill `list_power_domains` on `low_power`.
def list_power_domains(
    candidate_ref: str = '',  # Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.
    report_ref: str = '',  # Artifact URI of a prior report. Empty reads the latest report for this candidate.
    corner: str = '',  # PVT corner (process/voltage/temperature). Empty when the job is not corner-specific.
    mode: str = '',  # Functional or analysis mode string. Empty when the job is not mode-specific.
    params: dict | None = None,  # Optional extra keys from an adapter or caller; merged into the payload last.
) -> dict:
    """List domains, their supplies, and the modules inside them.

    Purpose:
        List power domains declared in UPF. This callable is the stable operation contract; a framework adapter
        performs the real EDA work when bound.

    Arguments:
        candidate_ref: Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.
        report_ref: Artifact URI of a prior report. Empty reads the latest report for this candidate.
        corner: PVT corner (process/voltage/temperature). Empty when the job is not corner-specific.
        mode: Functional or analysis mode string. Empty when the job is not mode-specific.
        params: Optional extra keys from an adapter or caller; merged into the payload last.

    Returns:
        dict observation from `tool_observation`, typically including status `not_run`
        until an EDA framework adapter is configured.

    Side effects:
        None on the filesystem while unbound. When bound, may submit tool jobs, read
        reports, edit isolated candidates, or publish findings per the skill's action.

    Failure behavior:
        Adapter/validation errors surface as observation error fields or raised exceptions
        handled by AgentService; this stub does not raise on the happy not_run path.
        """
    # Build the skill payload from explicit kwargs (stable schema for adapters).
    payload = {
        'candidate_ref': candidate_ref,  # Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.  # Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.
        'report_ref': report_ref,  # Artifact URI of a prior report. Empty reads the latest report for this candidate.  # Artifact URI of a prior report. Empty reads the latest report for this candidate.
        'corner': corner,  # PVT corner (process/voltage/temperature). Empty when the job is not corner-specific.  # PVT corner (process/voltage/temperature). Empty when the job is not corner-specific.
        'mode': mode  # Functional or analysis mode string. Empty when the job is not mode-specific.  # Functional or analysis mode string. Empty when the job is not mode-specific.
        }
    if params:  # Merge optional adapter/caller extras without dropping known keys.
        payload.update(params)  # Last-write wins for colliding keys from params.
    # Emit a structured observation; unbound adapters yield status not_run.
    return tool_observation(
        'list_power_domains',  # Skill id must match capabilities/skills in config.yaml.  # Skill id must match capabilities/skills in config.yaml.
        payload,  # Argument dict forwarded to the adapter / telemetry.  # Argument dict forwarded to the adapter / telemetry.
        agent_id='low_power',  # Routes telemetry and ACLs to this agent (`low_power`).  # Routes telemetry and ACLs to this agent (`low_power`).
        )

@tool(description='List signals that cross power domains.')  # Registers skill `list_domain_crossings` on `low_power`.
def list_domain_crossings(
    candidate_ref: str = '',  # Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.
    report_ref: str = '',  # Artifact URI of a prior report. Empty reads the latest report for this candidate.
    corner: str = '',  # PVT corner (process/voltage/temperature). Empty when the job is not corner-specific.
    mode: str = '',  # Functional or analysis mode string. Empty when the job is not mode-specific.
    params: dict | None = None,  # Optional extra keys from an adapter or caller; merged into the payload last.
) -> dict:
    """List signals that cross power domains.

    Purpose:
        List signal crossings between power domains that need isolation/level shifters. This callable is the stable operation contract; a framework adapter
        performs the real EDA work when bound.

    Arguments:
        candidate_ref: Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.
        report_ref: Artifact URI of a prior report. Empty reads the latest report for this candidate.
        corner: PVT corner (process/voltage/temperature). Empty when the job is not corner-specific.
        mode: Functional or analysis mode string. Empty when the job is not mode-specific.
        params: Optional extra keys from an adapter or caller; merged into the payload last.

    Returns:
        dict observation from `tool_observation`, typically including status `not_run`
        until an EDA framework adapter is configured.

    Side effects:
        None on the filesystem while unbound. When bound, may submit tool jobs, read
        reports, edit isolated candidates, or publish findings per the skill's action.

    Failure behavior:
        Adapter/validation errors surface as observation error fields or raised exceptions
        handled by AgentService; this stub does not raise on the happy not_run path.
        """
    # Build the skill payload from explicit kwargs (stable schema for adapters).
    payload = {
        'candidate_ref': candidate_ref,  # Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.  # Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.
        'report_ref': report_ref,  # Artifact URI of a prior report. Empty reads the latest report for this candidate.  # Artifact URI of a prior report. Empty reads the latest report for this candidate.
        'corner': corner,  # PVT corner (process/voltage/temperature). Empty when the job is not corner-specific.  # PVT corner (process/voltage/temperature). Empty when the job is not corner-specific.
        'mode': mode  # Functional or analysis mode string. Empty when the job is not mode-specific.  # Functional or analysis mode string. Empty when the job is not mode-specific.
        }
    if params:  # Merge optional adapter/caller extras without dropping known keys.
        payload.update(params)  # Last-write wins for colliding keys from params.
    # Emit a structured observation; unbound adapters yield status not_run.
    return tool_observation(
        'list_domain_crossings',  # Skill id must match capabilities/skills in config.yaml.  # Skill id must match capabilities/skills in config.yaml.
        payload,  # Argument dict forwarded to the adapter / telemetry.  # Argument dict forwarded to the adapter / telemetry.
        agent_id='low_power',  # Routes telemetry and ACLs to this agent (`low_power`).  # Routes telemetry and ACLs to this agent (`low_power`).
        )

@tool(description='Check which registers require retention and which cells implement it.')  # Registers skill `check_retention_registers` on `low_power`.
def check_retention_registers(
    candidate_ref: str = '',  # Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.
    report_ref: str = '',  # Artifact URI of a prior report. Empty reads the latest report for this candidate.
    corner: str = '',  # PVT corner (process/voltage/temperature). Empty when the job is not corner-specific.
    mode: str = '',  # Functional or analysis mode string. Empty when the job is not mode-specific.
    params: dict | None = None,  # Optional extra keys from an adapter or caller; merged into the payload last.
) -> dict:
    """Check which registers require retention and which cells implement it.

    Purpose:
        Verify retention register coverage for powered-down domains. This callable is the stable operation contract; a framework adapter
        performs the real EDA work when bound.

    Arguments:
        candidate_ref: Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.
        report_ref: Artifact URI of a prior report. Empty reads the latest report for this candidate.
        corner: PVT corner (process/voltage/temperature). Empty when the job is not corner-specific.
        mode: Functional or analysis mode string. Empty when the job is not mode-specific.
        params: Optional extra keys from an adapter or caller; merged into the payload last.

    Returns:
        dict observation from `tool_observation`, typically including status `not_run`
        until an EDA framework adapter is configured.

    Side effects:
        None on the filesystem while unbound. When bound, may submit tool jobs, read
        reports, edit isolated candidates, or publish findings per the skill's action.

    Failure behavior:
        Adapter/validation errors surface as observation error fields or raised exceptions
        handled by AgentService; this stub does not raise on the happy not_run path.
        """
    # Build the skill payload from explicit kwargs (stable schema for adapters).
    payload = {
        'candidate_ref': candidate_ref,  # Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.  # Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.
        'report_ref': report_ref,  # Artifact URI of a prior report. Empty reads the latest report for this candidate.  # Artifact URI of a prior report. Empty reads the latest report for this candidate.
        'corner': corner,  # PVT corner (process/voltage/temperature). Empty when the job is not corner-specific.  # PVT corner (process/voltage/temperature). Empty when the job is not corner-specific.
        'mode': mode  # Functional or analysis mode string. Empty when the job is not mode-specific.  # Functional or analysis mode string. Empty when the job is not mode-specific.
        }
    if params:  # Merge optional adapter/caller extras without dropping known keys.
        payload.update(params)  # Last-write wins for colliding keys from params.
    # Emit a structured observation; unbound adapters yield status not_run.
    return tool_observation(
        'check_retention_registers',  # Skill id must match capabilities/skills in config.yaml.  # Skill id must match capabilities/skills in config.yaml.
        payload,  # Argument dict forwarded to the adapter / telemetry.  # Argument dict forwarded to the adapter / telemetry.
        agent_id='low_power',  # Routes telemetry and ACLs to this agent (`low_power`).  # Routes telemetry and ACLs to this agent (`low_power`).
        )

@tool(description='Add a missing isolation strategy on an isolated UPF candidate.')  # Registers skill `write_isolation_strategy` on `low_power`.
def write_isolation_strategy(
    candidate_ref: str = '',  # Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.
    baseline_ref: str = '',  # Immutable baseline revision the candidate must descend from so lineage stays auditable.
    hypothesis: str = '',  # Single change under test for this edit so experiments stay one-hypothesis-at-a-time.
    params: dict | None = None,  # Optional extra keys from an adapter or caller; merged into the payload last.
) -> dict:
    """Add a missing isolation strategy on an isolated UPF candidate.

    Purpose:
        Write or update an isolation strategy on an isolated candidate. This callable is the stable operation contract; a framework adapter
        performs the real EDA work when bound.

    Arguments:
        candidate_ref: Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.
        baseline_ref: Immutable baseline revision the candidate must descend from so lineage stays auditable.
        hypothesis: Single change under test for this edit so experiments stay one-hypothesis-at-a-time.
        params: Optional extra keys from an adapter or caller; merged into the payload last.

    Returns:
        dict observation from `tool_observation`, typically including status `not_run`
        until an EDA framework adapter is configured.

    Side effects:
        None on the filesystem while unbound. When bound, may submit tool jobs, read
        reports, edit isolated candidates, or publish findings per the skill's action.

    Failure behavior:
        Adapter/validation errors surface as observation error fields or raised exceptions
        handled by AgentService; this stub does not raise on the happy not_run path.
        """
    # Build the skill payload from explicit kwargs (stable schema for adapters).
    payload = {
        'candidate_ref': candidate_ref,  # Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.  # Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.
        'baseline_ref': baseline_ref,  # Immutable baseline revision the candidate must descend from so lineage stays auditable.  # Immutable baseline revision the candidate must descend from so lineage stays auditable.
        'hypothesis': hypothesis  # Single change under test for this edit so experiments stay one-hypothesis-at-a-time.  # Single change under test for this edit so experiments stay one-hypothesis-at-a-time.
        }
    if params:  # Merge optional adapter/caller extras without dropping known keys.
        payload.update(params)  # Last-write wins for colliding keys from params.
    # Emit a structured observation; unbound adapters yield status not_run.
    return tool_observation(
        'write_isolation_strategy',  # Skill id must match capabilities/skills in config.yaml.  # Skill id must match capabilities/skills in config.yaml.
        payload,  # Argument dict forwarded to the adapter / telemetry.  # Argument dict forwarded to the adapter / telemetry.
        agent_id='low_power',  # Routes telemetry and ACLs to this agent (`low_power`).  # Routes telemetry and ACLs to this agent (`low_power`).
        )

@tool(description='Add a missing retention strategy on an isolated UPF candidate.')  # Registers skill `write_retention_strategy` on `low_power`.
def write_retention_strategy(
    candidate_ref: str = '',  # Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.
    baseline_ref: str = '',  # Immutable baseline revision the candidate must descend from so lineage stays auditable.
    hypothesis: str = '',  # Single change under test for this edit so experiments stay one-hypothesis-at-a-time.
    params: dict | None = None,  # Optional extra keys from an adapter or caller; merged into the payload last.
) -> dict:
    """Add a missing retention strategy on an isolated UPF candidate.

    Purpose:
        Write or update a retention strategy on an isolated candidate. This callable is the stable operation contract; a framework adapter
        performs the real EDA work when bound.

    Arguments:
        candidate_ref: Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.
        baseline_ref: Immutable baseline revision the candidate must descend from so lineage stays auditable.
        hypothesis: Single change under test for this edit so experiments stay one-hypothesis-at-a-time.
        params: Optional extra keys from an adapter or caller; merged into the payload last.

    Returns:
        dict observation from `tool_observation`, typically including status `not_run`
        until an EDA framework adapter is configured.

    Side effects:
        None on the filesystem while unbound. When bound, may submit tool jobs, read
        reports, edit isolated candidates, or publish findings per the skill's action.

    Failure behavior:
        Adapter/validation errors surface as observation error fields or raised exceptions
        handled by AgentService; this stub does not raise on the happy not_run path.
        """
    # Build the skill payload from explicit kwargs (stable schema for adapters).
    payload = {
        'candidate_ref': candidate_ref,  # Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.  # Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.
        'baseline_ref': baseline_ref,  # Immutable baseline revision the candidate must descend from so lineage stays auditable.  # Immutable baseline revision the candidate must descend from so lineage stays auditable.
        'hypothesis': hypothesis  # Single change under test for this edit so experiments stay one-hypothesis-at-a-time.  # Single change under test for this edit so experiments stay one-hypothesis-at-a-time.
        }
    if params:  # Merge optional adapter/caller extras without dropping known keys.
        payload.update(params)  # Last-write wins for colliding keys from params.
    # Emit a structured observation; unbound adapters yield status not_run.
    return tool_observation(
        'write_retention_strategy',  # Skill id must match capabilities/skills in config.yaml.  # Skill id must match capabilities/skills in config.yaml.
        payload,  # Argument dict forwarded to the adapter / telemetry.  # Argument dict forwarded to the adapter / telemetry.
        agent_id='low_power',  # Routes telemetry and ACLs to this agent (`low_power`).  # Routes telemetry and ACLs to this agent (`low_power`).
        )

@tool(description='Add a level shifter on one domain crossing in the candidate.')  # Registers skill `write_level_shifter` on `low_power`.
def write_level_shifter(
    candidate_ref: str = '',  # Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.
    baseline_ref: str = '',  # Immutable baseline revision the candidate must descend from so lineage stays auditable.
    hypothesis: str = '',  # Single change under test for this edit so experiments stay one-hypothesis-at-a-time.
    params: dict | None = None,  # Optional extra keys from an adapter or caller; merged into the payload last.
) -> dict:
    """Add a level shifter on one domain crossing in the candidate.

    Purpose:
        Insert or declare a level-shifter strategy for a voltage crossing. This callable is the stable operation contract; a framework adapter
        performs the real EDA work when bound.

    Arguments:
        candidate_ref: Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.
        baseline_ref: Immutable baseline revision the candidate must descend from so lineage stays auditable.
        hypothesis: Single change under test for this edit so experiments stay one-hypothesis-at-a-time.
        params: Optional extra keys from an adapter or caller; merged into the payload last.

    Returns:
        dict observation from `tool_observation`, typically including status `not_run`
        until an EDA framework adapter is configured.

    Side effects:
        None on the filesystem while unbound. When bound, may submit tool jobs, read
        reports, edit isolated candidates, or publish findings per the skill's action.

    Failure behavior:
        Adapter/validation errors surface as observation error fields or raised exceptions
        handled by AgentService; this stub does not raise on the happy not_run path.
        """
    # Build the skill payload from explicit kwargs (stable schema for adapters).
    payload = {
        'candidate_ref': candidate_ref,  # Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.  # Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.
        'baseline_ref': baseline_ref,  # Immutable baseline revision the candidate must descend from so lineage stays auditable.  # Immutable baseline revision the candidate must descend from so lineage stays auditable.
        'hypothesis': hypothesis  # Single change under test for this edit so experiments stay one-hypothesis-at-a-time.  # Single change under test for this edit so experiments stay one-hypothesis-at-a-time.
        }
    if params:  # Merge optional adapter/caller extras without dropping known keys.
        payload.update(params)  # Last-write wins for colliding keys from params.
    # Emit a structured observation; unbound adapters yield status not_run.
    return tool_observation(
        'write_level_shifter',  # Skill id must match capabilities/skills in config.yaml.  # Skill id must match capabilities/skills in config.yaml.
        payload,  # Argument dict forwarded to the adapter / telemetry.  # Argument dict forwarded to the adapter / telemetry.
        agent_id='low_power',  # Routes telemetry and ACLs to this agent (`low_power`).  # Routes telemetry and ACLs to this agent (`low_power`).
        )

@tool(description='Run UPF consistency checks.')  # Registers skill `run_upf_lint` on `low_power`.
def run_upf_lint(
    candidate_ref: str = '',  # Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.
    baseline_ref: str = '',  # Immutable baseline revision the candidate must descend from so lineage stays auditable.
    recipe: str = '',  # Versioned EDA-tool recipe name; the framework adapter rejects unknown recipes.
    corner: str = '',  # PVT corner (process/voltage/temperature). Empty when the job is not corner-specific.
    mode: str = '',  # Functional or analysis mode string. Empty when the job is not mode-specific.
    params: dict | None = None,  # Optional extra keys from an adapter or caller; merged into the payload last.
) -> dict:
    """Run UPF consistency checks.

    Purpose:
        Lint UPF against RTL structural expectations. This callable is the stable operation contract; a framework adapter
        performs the real EDA work when bound.

    Arguments:
        candidate_ref: Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.
        baseline_ref: Immutable baseline revision the candidate must descend from so lineage stays auditable.
        recipe: Versioned EDA-tool recipe name; the framework adapter rejects unknown recipes.
        corner: PVT corner (process/voltage/temperature). Empty when the job is not corner-specific.
        mode: Functional or analysis mode string. Empty when the job is not mode-specific.
        params: Optional extra keys from an adapter or caller; merged into the payload last.

    Returns:
        dict observation from `tool_observation`, typically including status `not_run`
        until an EDA framework adapter is configured.

    Side effects:
        None on the filesystem while unbound. When bound, may submit tool jobs, read
        reports, edit isolated candidates, or publish findings per the skill's action.

    Failure behavior:
        Adapter/validation errors surface as observation error fields or raised exceptions
        handled by AgentService; this stub does not raise on the happy not_run path.
        """
    # Build the skill payload from explicit kwargs (stable schema for adapters).
    payload = {
        'candidate_ref': candidate_ref,  # Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.  # Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.
        'baseline_ref': baseline_ref,  # Immutable baseline revision the candidate must descend from so lineage stays auditable.  # Immutable baseline revision the candidate must descend from so lineage stays auditable.
        'recipe': recipe,  # Versioned EDA-tool recipe name; the framework adapter rejects unknown recipes.  # Versioned EDA-tool recipe name; the framework adapter rejects unknown recipes.
        'corner': corner,  # PVT corner (process/voltage/temperature). Empty when the job is not corner-specific.  # PVT corner (process/voltage/temperature). Empty when the job is not corner-specific.
        'mode': mode  # Functional or analysis mode string. Empty when the job is not mode-specific.  # Functional or analysis mode string. Empty when the job is not mode-specific.
        }
    if params:  # Merge optional adapter/caller extras without dropping known keys.
        payload.update(params)  # Last-write wins for colliding keys from params.
    # Emit a structured observation; unbound adapters yield status not_run.
    return tool_observation(
        'run_upf_lint',  # Skill id must match capabilities/skills in config.yaml.  # Skill id must match capabilities/skills in config.yaml.
        payload,  # Argument dict forwarded to the adapter / telemetry.  # Argument dict forwarded to the adapter / telemetry.
        agent_id='low_power',  # Routes telemetry and ACLs to this agent (`low_power`).  # Routes telemetry and ACLs to this agent (`low_power`).
        )

@tool(description='Publish a domain crossing with no isolation.')  # Registers skill `flag_missing_power_isolation` on `low_power`.
def flag_missing_power_isolation(
    summary: str = '',  # One-sentence finding text published into shared engineering memory.
    evidence_refs: str = '',  # Comma-separated artifact URIs that back the finding for later audit.
    severity: str = '',  # Finding severity: low, medium, high, or critical.
    recommended_recipient: str = '',  # Agent id that should act next on this finding (lead or specialist).
    params: dict | None = None,  # Optional extra keys from an adapter or caller; merged into the payload last.
) -> dict:
    """Publish a domain crossing with no isolation.

    Purpose:
        Publish a finding when a domain crossing lacks isolation. This callable is the stable operation contract; a framework adapter
        performs the real EDA work when bound.

    Arguments:
        summary: One-sentence finding text published into shared engineering memory.
        evidence_refs: Comma-separated artifact URIs that back the finding for later audit.
        severity: Finding severity: low, medium, high, or critical.
        recommended_recipient: Agent id that should act next on this finding (lead or specialist).
        params: Optional extra keys from an adapter or caller; merged into the payload last.

    Returns:
        dict observation from `tool_observation`, typically including status `not_run`
        until an EDA framework adapter is configured.

    Side effects:
        None on the filesystem while unbound. When bound, may submit tool jobs, read
        reports, edit isolated candidates, or publish findings per the skill's action.

    Failure behavior:
        Adapter/validation errors surface as observation error fields or raised exceptions
        handled by AgentService; this stub does not raise on the happy not_run path.
        """
    # Build the skill payload from explicit kwargs (stable schema for adapters).
    payload = {
        'summary': summary,  # One-sentence finding text published into shared engineering memory.  # One-sentence finding text published into shared engineering memory.
        'evidence_refs': evidence_refs,  # Comma-separated artifact URIs that back the finding for later audit.  # Comma-separated artifact URIs that back the finding for later audit.
        'severity': severity,  # Finding severity: low, medium, high, or critical.  # Finding severity: low, medium, high, or critical.
        'recommended_recipient': recommended_recipient  # Agent id that should act next on this finding (lead or specialist).  # Agent id that should act next on this finding (lead or specialist).
        }
    if params:  # Merge optional adapter/caller extras without dropping known keys.
        payload.update(params)  # Last-write wins for colliding keys from params.
    # Emit a structured observation; unbound adapters yield status not_run.
    return tool_observation(
        'flag_missing_power_isolation',  # Skill id must match capabilities/skills in config.yaml.  # Skill id must match capabilities/skills in config.yaml.
        payload,  # Argument dict forwarded to the adapter / telemetry.  # Argument dict forwarded to the adapter / telemetry.
        agent_id='low_power',  # Routes telemetry and ACLs to this agent (`low_power`).  # Routes telemetry and ACLs to this agent (`low_power`).
        )

@tool(description='Publish a module whose UPF domain and RTL hierarchy disagree.')  # Registers skill `flag_upf_rtl_mismatch` on `low_power`.
def flag_upf_rtl_mismatch(
    summary: str = '',  # One-sentence finding text published into shared engineering memory.
    evidence_refs: str = '',  # Comma-separated artifact URIs that back the finding for later audit.
    severity: str = '',  # Finding severity: low, medium, high, or critical.
    recommended_recipient: str = '',  # Agent id that should act next on this finding (lead or specialist).
    params: dict | None = None,  # Optional extra keys from an adapter or caller; merged into the payload last.
) -> dict:
    """Publish a module whose UPF domain and RTL hierarchy disagree.

    Purpose:
        Publish a finding when UPF and RTL power intent disagree. This callable is the stable operation contract; a framework adapter
        performs the real EDA work when bound.

    Arguments:
        summary: One-sentence finding text published into shared engineering memory.
        evidence_refs: Comma-separated artifact URIs that back the finding for later audit.
        severity: Finding severity: low, medium, high, or critical.
        recommended_recipient: Agent id that should act next on this finding (lead or specialist).
        params: Optional extra keys from an adapter or caller; merged into the payload last.

    Returns:
        dict observation from `tool_observation`, typically including status `not_run`
        until an EDA framework adapter is configured.

    Side effects:
        None on the filesystem while unbound. When bound, may submit tool jobs, read
        reports, edit isolated candidates, or publish findings per the skill's action.

    Failure behavior:
        Adapter/validation errors surface as observation error fields or raised exceptions
        handled by AgentService; this stub does not raise on the happy not_run path.
        """
    # Build the skill payload from explicit kwargs (stable schema for adapters).
    payload = {
        'summary': summary,  # One-sentence finding text published into shared engineering memory.  # One-sentence finding text published into shared engineering memory.
        'evidence_refs': evidence_refs,  # Comma-separated artifact URIs that back the finding for later audit.  # Comma-separated artifact URIs that back the finding for later audit.
        'severity': severity,  # Finding severity: low, medium, high, or critical.  # Finding severity: low, medium, high, or critical.
        'recommended_recipient': recommended_recipient  # Agent id that should act next on this finding (lead or specialist).  # Agent id that should act next on this finding (lead or specialist).
        }
    if params:  # Merge optional adapter/caller extras without dropping known keys.
        payload.update(params)  # Last-write wins for colliding keys from params.
    # Emit a structured observation; unbound adapters yield status not_run.
    return tool_observation(
        'flag_upf_rtl_mismatch',  # Skill id must match capabilities/skills in config.yaml.  # Skill id must match capabilities/skills in config.yaml.
        payload,  # Argument dict forwarded to the adapter / telemetry.  # Argument dict forwarded to the adapter / telemetry.
        agent_id='low_power',  # Routes telemetry and ACLs to this agent (`low_power`).  # Routes telemetry and ACLs to this agent (`low_power`).
        )
