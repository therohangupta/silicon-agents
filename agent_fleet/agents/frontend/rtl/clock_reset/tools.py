"""Tools for Clock/Reset Agent (`clock_reset`).

Each function is the stable operation contract for one advertised capability in config.yaml.
A framework adapter (OpenROAD, commercial CDC/lint/UPF, simulator, etc.) performs the real
work when `EDA_FRAMEWORK` is bound. Until then, every call returns status `not_run` via
`tool_observation` and does **not** invoke OpenROAD, Yosys, OpenSTA, a licensed tool, or a
simulator.

This agent serves the **rtl** stage of frontend chip design.
Clock and reset intent defines domains, gating, and synchronizer topology before physical CTS. This agent checks RTL against declared clocking so ungated muxes and broken reset trees are caught early.

Callers (LLM runtime or orchestrator) pass string refs and optional `params`. Payloads are
assembled explicitly so telemetry and adapters see a stable schema per skill id.
"""

from __future__ import annotations  # Allow modern typing (dict | None) on older runtimes if needed.

from packages.agent_sdk import tool  # Decorator that registers the callable as an agent skill.
from domains.eda.eda import tool_observation  # Builds the stub/real observation dict for adapters.


@tool(description='Read declared clocks, generated clocks, and gating intent.')  # Registers skill `read_clock_intent` on `clock_reset`.
def read_clock_intent(
    candidate_ref: str = '',  # Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.
    report_ref: str = '',  # Artifact URI of a prior report. Empty reads the latest report for this candidate.
    corner: str = '',  # PVT corner (process/voltage/temperature). Empty when the job is not corner-specific.
    mode: str = '',  # Functional or analysis mode string. Empty when the job is not mode-specific.
    params: dict | None = None,  # Optional extra keys from an adapter or caller; merged into the payload last.
) -> dict:
    """Read declared clocks, generated clocks, and gating intent.

    Purpose:
        Read declared clocking intent (domains, frequencies, gating policy) from shared memory or artifacts. This callable is the stable operation contract; a framework adapter
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
        'read_clock_intent',  # Skill id must match capabilities/skills in config.yaml.  # Skill id must match capabilities/skills in config.yaml.
        payload,  # Argument dict forwarded to the adapter / telemetry.  # Argument dict forwarded to the adapter / telemetry.
        agent_id='clock_reset',  # Routes telemetry and ACLs to this agent (`clock_reset`).  # Routes telemetry and ACLs to this agent (`clock_reset`).
        )

@tool(description='Check clocks, generated clocks, and gating against the intent.')  # Registers skill `analyze_clock_intent` on `clock_reset`.
def analyze_clock_intent(
    candidate_ref: str = '',  # Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.
    report_ref: str = '',  # Artifact URI of a prior report. Empty reads the latest report for this candidate.
    corner: str = '',  # PVT corner (process/voltage/temperature). Empty when the job is not corner-specific.
    mode: str = '',  # Functional or analysis mode string. Empty when the job is not mode-specific.
    params: dict | None = None,  # Optional extra keys from an adapter or caller; merged into the payload last.
) -> dict:
    """Check clocks, generated clocks, and gating against the intent.

    Purpose:
        Compare RTL clocking structure against the declared intent document. This callable is the stable operation contract; a framework adapter
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
        'analyze_clock_intent',  # Skill id must match capabilities/skills in config.yaml.  # Skill id must match capabilities/skills in config.yaml.
        payload,  # Argument dict forwarded to the adapter / telemetry.  # Argument dict forwarded to the adapter / telemetry.
        agent_id='clock_reset',  # Routes telemetry and ACLs to this agent (`clock_reset`).  # Routes telemetry and ACLs to this agent (`clock_reset`).
        )

@tool(description='List clock domains and the registers in each.')  # Registers skill `list_clock_domains` on `clock_reset`.
def list_clock_domains(
    candidate_ref: str = '',  # Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.
    report_ref: str = '',  # Artifact URI of a prior report. Empty reads the latest report for this candidate.
    corner: str = '',  # PVT corner (process/voltage/temperature). Empty when the job is not corner-specific.
    mode: str = '',  # Functional or analysis mode string. Empty when the job is not mode-specific.
    params: dict | None = None,  # Optional extra keys from an adapter or caller; merged into the payload last.
) -> dict:
    """List clock domains and the registers in each.

    Purpose:
        Enumerate clock domains found in intent or inferred from the candidate. This callable is the stable operation contract; a framework adapter
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
        'list_clock_domains',  # Skill id must match capabilities/skills in config.yaml.  # Skill id must match capabilities/skills in config.yaml.
        payload,  # Argument dict forwarded to the adapter / telemetry.  # Argument dict forwarded to the adapter / telemetry.
        agent_id='clock_reset',  # Routes telemetry and ACLs to this agent (`clock_reset`).  # Routes telemetry and ACLs to this agent (`clock_reset`).
        )

@tool(description='List generated and gated clocks and their sources.')  # Registers skill `list_generated_clocks` on `clock_reset`.
def list_generated_clocks(
    candidate_ref: str = '',  # Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.
    report_ref: str = '',  # Artifact URI of a prior report. Empty reads the latest report for this candidate.
    corner: str = '',  # PVT corner (process/voltage/temperature). Empty when the job is not corner-specific.
    mode: str = '',  # Functional or analysis mode string. Empty when the job is not mode-specific.
    params: dict | None = None,  # Optional extra keys from an adapter or caller; merged into the payload last.
) -> dict:
    """List generated and gated clocks and their sources.

    Purpose:
        List derived/generated clocks that complicate STA and CDC. This callable is the stable operation contract; a framework adapter
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
        'list_generated_clocks',  # Skill id must match capabilities/skills in config.yaml.  # Skill id must match capabilities/skills in config.yaml.
        payload,  # Argument dict forwarded to the adapter / telemetry.  # Argument dict forwarded to the adapter / telemetry.
        agent_id='clock_reset',  # Routes telemetry and ACLs to this agent (`clock_reset`).  # Routes telemetry and ACLs to this agent (`clock_reset`).
        )

@tool(description='Check reset synchronizers, tree shape, and deassertion.')  # Registers skill `analyze_reset_topology` on `clock_reset`.
def analyze_reset_topology(
    candidate_ref: str = '',  # Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.
    report_ref: str = '',  # Artifact URI of a prior report. Empty reads the latest report for this candidate.
    corner: str = '',  # PVT corner (process/voltage/temperature). Empty when the job is not corner-specific.
    mode: str = '',  # Functional or analysis mode string. Empty when the job is not mode-specific.
    params: dict | None = None,  # Optional extra keys from an adapter or caller; merged into the payload last.
) -> dict:
    """Check reset synchronizers, tree shape, and deassertion.

    Purpose:
        Inspect reset assertion/deassertion topology across domains. This callable is the stable operation contract; a framework adapter
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
        'analyze_reset_topology',  # Skill id must match capabilities/skills in config.yaml.  # Skill id must match capabilities/skills in config.yaml.
        payload,  # Argument dict forwarded to the adapter / telemetry.  # Argument dict forwarded to the adapter / telemetry.
        agent_id='clock_reset',  # Routes telemetry and ACLs to this agent (`clock_reset`).  # Routes telemetry and ACLs to this agent (`clock_reset`).
        )

@tool(description='List reset domains and asynchronous-reset registers.')  # Registers skill `list_reset_domains` on `clock_reset`.
def list_reset_domains(
    candidate_ref: str = '',  # Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.
    report_ref: str = '',  # Artifact URI of a prior report. Empty reads the latest report for this candidate.
    corner: str = '',  # PVT corner (process/voltage/temperature). Empty when the job is not corner-specific.
    mode: str = '',  # Functional or analysis mode string. Empty when the job is not mode-specific.
    params: dict | None = None,  # Optional extra keys from an adapter or caller; merged into the payload last.
) -> dict:
    """List reset domains and asynchronous-reset registers.

    Purpose:
        Enumerate reset domains for RDC and reset-tree checks. This callable is the stable operation contract; a framework adapter
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
        'list_reset_domains',  # Skill id must match capabilities/skills in config.yaml.  # Skill id must match capabilities/skills in config.yaml.
        payload,  # Argument dict forwarded to the adapter / telemetry.  # Argument dict forwarded to the adapter / telemetry.
        agent_id='clock_reset',  # Routes telemetry and ACLs to this agent (`clock_reset`).  # Routes telemetry and ACLs to this agent (`clock_reset`).
        )

@tool(description='Check that asynchronous resets are synchronized once per domain.')  # Registers skill `check_reset_synchronizers` on `clock_reset`.
def check_reset_synchronizers(
    candidate_ref: str = '',  # Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.
    report_ref: str = '',  # Artifact URI of a prior report. Empty reads the latest report for this candidate.
    corner: str = '',  # PVT corner (process/voltage/temperature). Empty when the job is not corner-specific.
    mode: str = '',  # Functional or analysis mode string. Empty when the job is not mode-specific.
    params: dict | None = None,  # Optional extra keys from an adapter or caller; merged into the payload last.
) -> dict:
    """Check that asynchronous resets are synchronized once per domain.

    Purpose:
        Verify reset synchronizers exist where async resets cross domains. This callable is the stable operation contract; a framework adapter
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
        'check_reset_synchronizers',  # Skill id must match capabilities/skills in config.yaml.  # Skill id must match capabilities/skills in config.yaml.
        payload,  # Argument dict forwarded to the adapter / telemetry.  # Argument dict forwarded to the adapter / telemetry.
        agent_id='clock_reset',  # Routes telemetry and ACLs to this agent (`clock_reset`).  # Routes telemetry and ACLs to this agent (`clock_reset`).
        )

@tool(description='Edit one illegal clock gate on an isolated candidate.')  # Registers skill `write_clock_gate_fix` on `clock_reset`.
def write_clock_gate_fix(
    candidate_ref: str = '',  # Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.
    baseline_ref: str = '',  # Immutable baseline revision the candidate must descend from so lineage stays auditable.
    hypothesis: str = '',  # Single change under test for this edit so experiments stay one-hypothesis-at-a-time.
    params: dict | None = None,  # Optional extra keys from an adapter or caller; merged into the payload last.
) -> dict:
    """Edit one illegal clock gate on an isolated candidate.

    Purpose:
        Apply a bounded clock-gating fix on an isolated candidate. This callable is the stable operation contract; a framework adapter
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
        'write_clock_gate_fix',  # Skill id must match capabilities/skills in config.yaml.  # Skill id must match capabilities/skills in config.yaml.
        payload,  # Argument dict forwarded to the adapter / telemetry.  # Argument dict forwarded to the adapter / telemetry.
        agent_id='clock_reset',  # Routes telemetry and ACLs to this agent (`clock_reset`).  # Routes telemetry and ACLs to this agent (`clock_reset`).
        )

@tool(description='Add one missing reset synchronizer on an isolated candidate.')  # Registers skill `write_reset_synchronizer` on `clock_reset`.
def write_reset_synchronizer(
    candidate_ref: str = '',  # Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.
    baseline_ref: str = '',  # Immutable baseline revision the candidate must descend from so lineage stays auditable.
    hypothesis: str = '',  # Single change under test for this edit so experiments stay one-hypothesis-at-a-time.
    params: dict | None = None,  # Optional extra keys from an adapter or caller; merged into the payload last.
) -> dict:
    """Add one missing reset synchronizer on an isolated candidate.

    Purpose:
        Insert a reset synchronizer on an isolated candidate. This callable is the stable operation contract; a framework adapter
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
        'write_reset_synchronizer',  # Skill id must match capabilities/skills in config.yaml.  # Skill id must match capabilities/skills in config.yaml.
        payload,  # Argument dict forwarded to the adapter / telemetry.  # Argument dict forwarded to the adapter / telemetry.
        agent_id='clock_reset',  # Routes telemetry and ACLs to this agent (`clock_reset`).  # Routes telemetry and ACLs to this agent (`clock_reset`).
        )

@tool(description='Run the clock and reset lint rules on the candidate.')  # Registers skill `lint_clock_reset` on `clock_reset`.
def lint_clock_reset(
    candidate_ref: str = '',  # Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.
    baseline_ref: str = '',  # Immutable baseline revision the candidate must descend from so lineage stays auditable.
    recipe: str = '',  # Versioned EDA-tool recipe name; the framework adapter rejects unknown recipes.
    corner: str = '',  # PVT corner (process/voltage/temperature). Empty when the job is not corner-specific.
    mode: str = '',  # Functional or analysis mode string. Empty when the job is not mode-specific.
    params: dict | None = None,  # Optional extra keys from an adapter or caller; merged into the payload last.
) -> dict:
    """Run the clock and reset lint rules on the candidate.

    Purpose:
        Run clock/reset-specific lint rules (muxes, gating enables, reset styles). This callable is the stable operation contract; a framework adapter
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
        'lint_clock_reset',  # Skill id must match capabilities/skills in config.yaml.  # Skill id must match capabilities/skills in config.yaml.
        payload,  # Argument dict forwarded to the adapter / telemetry.  # Argument dict forwarded to the adapter / telemetry.
        agent_id='clock_reset',  # Routes telemetry and ACLs to this agent (`clock_reset`).  # Routes telemetry and ACLs to this agent (`clock_reset`).
        )

@tool(description='Publish a clock mux or gate that does not match the intent.')  # Registers skill `flag_ungated_clock_mux` on `clock_reset`.
def flag_ungated_clock_mux(
    summary: str = '',  # One-sentence finding text published into shared engineering memory.
    evidence_refs: str = '',  # Comma-separated artifact URIs that back the finding for later audit.
    severity: str = '',  # Finding severity: low, medium, high, or critical.
    recommended_recipient: str = '',  # Agent id that should act next on this finding (lead or specialist).
    params: dict | None = None,  # Optional extra keys from an adapter or caller; merged into the payload last.
) -> dict:
    """Publish a clock mux or gate that does not match the intent.

    Purpose:
        Publish a finding when a clock mux lacks required gating or glitch protection. This callable is the stable operation contract; a framework adapter
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
        'flag_ungated_clock_mux',  # Skill id must match capabilities/skills in config.yaml.  # Skill id must match capabilities/skills in config.yaml.
        payload,  # Argument dict forwarded to the adapter / telemetry.  # Argument dict forwarded to the adapter / telemetry.
        agent_id='clock_reset',  # Routes telemetry and ACLs to this agent (`clock_reset`).  # Routes telemetry and ACLs to this agent (`clock_reset`).
        )

@tool(description='Publish a reset that is asynchronous, missing, or reconvergent.')  # Registers skill `flag_reset_tree_issue` on `clock_reset`.
def flag_reset_tree_issue(
    summary: str = '',  # One-sentence finding text published into shared engineering memory.
    evidence_refs: str = '',  # Comma-separated artifact URIs that back the finding for later audit.
    severity: str = '',  # Finding severity: low, medium, high, or critical.
    recommended_recipient: str = '',  # Agent id that should act next on this finding (lead or specialist).
    params: dict | None = None,  # Optional extra keys from an adapter or caller; merged into the payload last.
) -> dict:
    """Publish a reset that is asynchronous, missing, or reconvergent.

    Purpose:
        Publish a finding for reset-tree structural problems. This callable is the stable operation contract; a framework adapter
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
        'flag_reset_tree_issue',  # Skill id must match capabilities/skills in config.yaml.  # Skill id must match capabilities/skills in config.yaml.
        payload,  # Argument dict forwarded to the adapter / telemetry.  # Argument dict forwarded to the adapter / telemetry.
        agent_id='clock_reset',  # Routes telemetry and ACLs to this agent (`clock_reset`).  # Routes telemetry and ACLs to this agent (`clock_reset`).
        )
