"""Tools for RTL Lead (`rtl_lead`).

Each function is the stable operation contract for one advertised capability in config.yaml.
A framework adapter (OpenROAD, commercial CDC/lint/UPF, simulator, etc.) performs the real
work when `EDA_FRAMEWORK` is bound. Until then, every call returns status `not_run` via
`tool_observation` and does **not** invoke OpenROAD, Yosys, OpenSTA, a licensed tool, or a
simulator.

This agent serves the **rtl** stage of frontend chip design.
The RTL lead plans block implementation, opens qualification and edit tasks, and hands candidates to verification. It coordinates workers without promoting baselines itself.

Callers (LLM runtime or orchestrator) pass string refs and optional `params`. Payloads are
assembled explicitly so telemetry and adapters see a stable schema per skill id.
"""

from __future__ import annotations  # Allow modern typing (dict | None) on older runtimes if needed.

from packages.agent_sdk import tool  # Decorator that registers the callable as an agent skill.
from domains.eda.eda import tool_observation  # Builds the stub/real observation dict for adapters.


@tool(description='Emit the block workflow from spec through qualification.')  # Registers skill `plan_block_implementation` on `rtl_lead`.
def plan_block_implementation(
    objective: str = '',  # Argument `objective` for skill `plan_block_implementation` on agent `rtl_lead`; forwarded in the tool payload.
    parent_task_id: str = '',  # Argument `parent_task_id` for skill `plan_block_implementation` on agent `rtl_lead`; forwarded in the tool payload.
    scope_block: str = '',  # Argument `scope_block` for skill `plan_block_implementation` on agent `rtl_lead`; forwarded in the tool payload.
    params: dict | None = None,  # Optional extra keys from an adapter or caller; merged into the payload last.
) -> dict:
    """Emit the block workflow from spec through qualification.

    Purpose:
        Emit the block workflow from spec through qualification for workers. This callable is the stable operation contract; a framework adapter
        performs the real EDA work when bound.

    Arguments:
        objective: Argument `objective` for skill `plan_block_implementation` on agent `rtl_lead`; forwarded in the tool payload.
        parent_task_id: Argument `parent_task_id` for skill `plan_block_implementation` on agent `rtl_lead`; forwarded in the tool payload.
        scope_block: Argument `scope_block` for skill `plan_block_implementation` on agent `rtl_lead`; forwarded in the tool payload.
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
        'objective': objective,  # Argument `objective` for skill `plan_block_implementation` on agent `rtl_lead`; forwarded in the tool payload.  # Argument `objective` for skill `plan_block_implementation` on agent `rtl_lead`; forwarded in the tool payload.
        'parent_task_id': parent_task_id,  # Argument `parent_task_id` for skill `plan_block_implementation` on agent `rtl_lead`; forwarded in the tool payload.  # Argument `parent_task_id` for skill `plan_block_implementation` on agent `rtl_lead`; forwarded in the tool payload.
        'scope_block': scope_block  # Argument `scope_block` for skill `plan_block_implementation` on agent `rtl_lead`; forwarded in the tool payload.  # Argument `scope_block` for skill `plan_block_implementation` on agent `rtl_lead`; forwarded in the tool payload.
        }
    if params:  # Merge optional adapter/caller extras without dropping known keys.
        payload.update(params)  # Last-write wins for colliding keys from params.
    # Emit a structured observation; unbound adapters yield status not_run.
    return tool_observation(
        'plan_block_implementation',  # Skill id must match capabilities/skills in config.yaml.  # Skill id must match capabilities/skills in config.yaml.
        payload,  # Argument dict forwarded to the adapter / telemetry.  # Argument dict forwarded to the adapter / telemetry.
        agent_id='rtl_lead',  # Routes telemetry and ACLs to this agent (`rtl_lead`).  # Routes telemetry and ACLs to this agent (`rtl_lead`).
        )

@tool(description='Ask lint, clock, CDC, low-power, and integration checks to grade the current candidate.')  # Registers skill `request_block_qualification` on `rtl_lead`.
def request_block_qualification(
    objective: str = '',  # Argument `objective` for skill `request_block_qualification` on agent `rtl_lead`; forwarded in the tool payload.
    parent_task_id: str = '',  # Argument `parent_task_id` for skill `request_block_qualification` on agent `rtl_lead`; forwarded in the tool payload.
    scope_block: str = '',  # Argument `scope_block` for skill `request_block_qualification` on agent `rtl_lead`; forwarded in the tool payload.
    params: dict | None = None,  # Optional extra keys from an adapter or caller; merged into the payload last.
) -> dict:
    """Ask lint, clock, CDC, low-power, and integration checks to grade the current candidate.

    Purpose:
        Ask lint, clock, CDC, low-power, and integration to grade the candidate. This callable is the stable operation contract; a framework adapter
        performs the real EDA work when bound.

    Arguments:
        objective: Argument `objective` for skill `request_block_qualification` on agent `rtl_lead`; forwarded in the tool payload.
        parent_task_id: Argument `parent_task_id` for skill `request_block_qualification` on agent `rtl_lead`; forwarded in the tool payload.
        scope_block: Argument `scope_block` for skill `request_block_qualification` on agent `rtl_lead`; forwarded in the tool payload.
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
        'objective': objective,  # Argument `objective` for skill `request_block_qualification` on agent `rtl_lead`; forwarded in the tool payload.  # Argument `objective` for skill `request_block_qualification` on agent `rtl_lead`; forwarded in the tool payload.
        'parent_task_id': parent_task_id,  # Argument `parent_task_id` for skill `request_block_qualification` on agent `rtl_lead`; forwarded in the tool payload.  # Argument `parent_task_id` for skill `request_block_qualification` on agent `rtl_lead`; forwarded in the tool payload.
        'scope_block': scope_block  # Argument `scope_block` for skill `request_block_qualification` on agent `rtl_lead`; forwarded in the tool payload.  # Argument `scope_block` for skill `request_block_qualification` on agent `rtl_lead`; forwarded in the tool payload.
        }
    if params:  # Merge optional adapter/caller extras without dropping known keys.
        payload.update(params)  # Last-write wins for colliding keys from params.
    # Emit a structured observation; unbound adapters yield status not_run.
    return tool_observation(
        'request_block_qualification',  # Skill id must match capabilities/skills in config.yaml.  # Skill id must match capabilities/skills in config.yaml.
        payload,  # Argument dict forwarded to the adapter / telemetry.  # Argument dict forwarded to the adapter / telemetry.
        agent_id='rtl_lead',  # Routes telemetry and ACLs to this agent (`rtl_lead`).  # Routes telemetry and ACLs to this agent (`rtl_lead`).
        )

@tool(description='Open one bounded RTL-edit task with a single hypothesis.')  # Registers skill `request_rtl_edit` on `rtl_lead`.
def request_rtl_edit(
    objective: str = '',  # Argument `objective` for skill `request_rtl_edit` on agent `rtl_lead`; forwarded in the tool payload.
    parent_task_id: str = '',  # Argument `parent_task_id` for skill `request_rtl_edit` on agent `rtl_lead`; forwarded in the tool payload.
    scope_block: str = '',  # Argument `scope_block` for skill `request_rtl_edit` on agent `rtl_lead`; forwarded in the tool payload.
    hypothesis: str = '',  # Single change under test for this edit so experiments stay one-hypothesis-at-a-time.
    params: dict | None = None,  # Optional extra keys from an adapter or caller; merged into the payload last.
) -> dict:
    """Open one bounded RTL-edit task with a single hypothesis.

    Purpose:
        Open one bounded RTL-edit task with a single hypothesis. This callable is the stable operation contract; a framework adapter
        performs the real EDA work when bound.

    Arguments:
        objective: Argument `objective` for skill `request_rtl_edit` on agent `rtl_lead`; forwarded in the tool payload.
        parent_task_id: Argument `parent_task_id` for skill `request_rtl_edit` on agent `rtl_lead`; forwarded in the tool payload.
        scope_block: Argument `scope_block` for skill `request_rtl_edit` on agent `rtl_lead`; forwarded in the tool payload.
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
        'objective': objective,  # Argument `objective` for skill `request_rtl_edit` on agent `rtl_lead`; forwarded in the tool payload.  # Argument `objective` for skill `request_rtl_edit` on agent `rtl_lead`; forwarded in the tool payload.
        'parent_task_id': parent_task_id,  # Argument `parent_task_id` for skill `request_rtl_edit` on agent `rtl_lead`; forwarded in the tool payload.  # Argument `parent_task_id` for skill `request_rtl_edit` on agent `rtl_lead`; forwarded in the tool payload.
        'scope_block': scope_block,  # Argument `scope_block` for skill `request_rtl_edit` on agent `rtl_lead`; forwarded in the tool payload.  # Argument `scope_block` for skill `request_rtl_edit` on agent `rtl_lead`; forwarded in the tool payload.
        'hypothesis': hypothesis  # Single change under test for this edit so experiments stay one-hypothesis-at-a-time.  # Single change under test for this edit so experiments stay one-hypothesis-at-a-time.
        }
    if params:  # Merge optional adapter/caller extras without dropping known keys.
        payload.update(params)  # Last-write wins for colliding keys from params.
    # Emit a structured observation; unbound adapters yield status not_run.
    return tool_observation(
        'request_rtl_edit',  # Skill id must match capabilities/skills in config.yaml.  # Skill id must match capabilities/skills in config.yaml.
        payload,  # Argument dict forwarded to the adapter / telemetry.  # Argument dict forwarded to the adapter / telemetry.
        agent_id='rtl_lead',  # Routes telemetry and ACLs to this agent (`rtl_lead`).  # Routes telemetry and ACLs to this agent (`rtl_lead`).
        )

@tool(description='Open a merge of block candidates that have passed their local checks.')  # Registers skill `request_integration` on `rtl_lead`.
def request_integration(
    objective: str = '',  # Argument `objective` for skill `request_integration` on agent `rtl_lead`; forwarded in the tool payload.
    parent_task_id: str = '',  # Argument `parent_task_id` for skill `request_integration` on agent `rtl_lead`; forwarded in the tool payload.
    scope_block: str = '',  # Argument `scope_block` for skill `request_integration` on agent `rtl_lead`; forwarded in the tool payload.
    params: dict | None = None,  # Optional extra keys from an adapter or caller; merged into the payload last.
) -> dict:
    """Open a merge of block candidates that have passed their local checks.

    Purpose:
        Open a merge of block candidates that passed local checks. This callable is the stable operation contract; a framework adapter
        performs the real EDA work when bound.

    Arguments:
        objective: Argument `objective` for skill `request_integration` on agent `rtl_lead`; forwarded in the tool payload.
        parent_task_id: Argument `parent_task_id` for skill `request_integration` on agent `rtl_lead`; forwarded in the tool payload.
        scope_block: Argument `scope_block` for skill `request_integration` on agent `rtl_lead`; forwarded in the tool payload.
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
        'objective': objective,  # Argument `objective` for skill `request_integration` on agent `rtl_lead`; forwarded in the tool payload.  # Argument `objective` for skill `request_integration` on agent `rtl_lead`; forwarded in the tool payload.
        'parent_task_id': parent_task_id,  # Argument `parent_task_id` for skill `request_integration` on agent `rtl_lead`; forwarded in the tool payload.  # Argument `parent_task_id` for skill `request_integration` on agent `rtl_lead`; forwarded in the tool payload.
        'scope_block': scope_block  # Argument `scope_block` for skill `request_integration` on agent `rtl_lead`; forwarded in the tool payload.  # Argument `scope_block` for skill `request_integration` on agent `rtl_lead`; forwarded in the tool payload.
        }
    if params:  # Merge optional adapter/caller extras without dropping known keys.
        payload.update(params)  # Last-write wins for colliding keys from params.
    # Emit a structured observation; unbound adapters yield status not_run.
    return tool_observation(
        'request_integration',  # Skill id must match capabilities/skills in config.yaml.  # Skill id must match capabilities/skills in config.yaml.
        payload,  # Argument dict forwarded to the adapter / telemetry.  # Argument dict forwarded to the adapter / telemetry.
        agent_id='rtl_lead',  # Routes telemetry and ACLs to this agent (`rtl_lead`).  # Routes telemetry and ACLs to this agent (`rtl_lead`).
        )

@tool(description='Read the qualified specification and interface contracts for this block.')  # Registers skill `read_block_spec` on `rtl_lead`.
def read_block_spec(
    candidate_ref: str = '',  # Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.
    report_ref: str = '',  # Artifact URI of a prior report. Empty reads the latest report for this candidate.
    corner: str = '',  # PVT corner (process/voltage/temperature). Empty when the job is not corner-specific.
    mode: str = '',  # Functional or analysis mode string. Empty when the job is not mode-specific.
    params: dict | None = None,  # Optional extra keys from an adapter or caller; merged into the payload last.
) -> dict:
    """Read the qualified specification and interface contracts for this block.

    Purpose:
        Read the qualified specification and interface contracts for this block. This callable is the stable operation contract; a framework adapter
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
        'read_block_spec',  # Skill id must match capabilities/skills in config.yaml.  # Skill id must match capabilities/skills in config.yaml.
        payload,  # Argument dict forwarded to the adapter / telemetry.  # Argument dict forwarded to the adapter / telemetry.
        agent_id='rtl_lead',  # Routes telemetry and ACLs to this agent (`rtl_lead`).  # Routes telemetry and ACLs to this agent (`rtl_lead`).
        )

@tool(description='Read lint, CDC, clock, and low-power status for the active candidate.')  # Registers skill `read_candidate_status` on `rtl_lead`.
def read_candidate_status(
    candidate_ref: str = '',  # Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.
    report_ref: str = '',  # Artifact URI of a prior report. Empty reads the latest report for this candidate.
    corner: str = '',  # PVT corner (process/voltage/temperature). Empty when the job is not corner-specific.
    mode: str = '',  # Functional or analysis mode string. Empty when the job is not mode-specific.
    params: dict | None = None,  # Optional extra keys from an adapter or caller; merged into the payload last.
) -> dict:
    """Read lint, CDC, clock, and low-power status for the active candidate.

    Purpose:
        Read lint, CDC, clock, and low-power status for the active candidate. This callable is the stable operation contract; a framework adapter
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
        'read_candidate_status',  # Skill id must match capabilities/skills in config.yaml.  # Skill id must match capabilities/skills in config.yaml.
        payload,  # Argument dict forwarded to the adapter / telemetry.  # Argument dict forwarded to the adapter / telemetry.
        agent_id='rtl_lead',  # Routes telemetry and ACLs to this agent (`rtl_lead`).  # Routes telemetry and ACLs to this agent (`rtl_lead`).
        )

@tool(description='Read findings still open against this block.')  # Registers skill `read_open_rtl_findings` on `rtl_lead`.
def read_open_rtl_findings(
    candidate_ref: str = '',  # Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.
    report_ref: str = '',  # Artifact URI of a prior report. Empty reads the latest report for this candidate.
    corner: str = '',  # PVT corner (process/voltage/temperature). Empty when the job is not corner-specific.
    mode: str = '',  # Functional or analysis mode string. Empty when the job is not mode-specific.
    params: dict | None = None,  # Optional extra keys from an adapter or caller; merged into the payload last.
) -> dict:
    """Read findings still open against this block.

    Purpose:
        Read findings still open against this block. This callable is the stable operation contract; a framework adapter
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
        'read_open_rtl_findings',  # Skill id must match capabilities/skills in config.yaml.  # Skill id must match capabilities/skills in config.yaml.
        payload,  # Argument dict forwarded to the adapter / telemetry.  # Argument dict forwarded to the adapter / telemetry.
        agent_id='rtl_lead',  # Routes telemetry and ACLs to this agent (`rtl_lead`).  # Routes telemetry and ACLs to this agent (`rtl_lead`).
        )

@tool(description='Record which isolated candidate should be handed to verification. This does not promote it.')  # Registers skill `recommend_rtl_candidate` on `rtl_lead`.
def recommend_rtl_candidate(
    summary: str = '',  # One-sentence finding text published into shared engineering memory.
    evidence_refs: str = '',  # Comma-separated artifact URIs that back the finding for later audit.
    severity: str = '',  # Finding severity: low, medium, high, or critical.
    recommended_recipient: str = '',  # Agent id that should act next on this finding (lead or specialist).
    params: dict | None = None,  # Optional extra keys from an adapter or caller; merged into the payload last.
) -> dict:
    """Record which isolated candidate should be handed to verification. This does not promote it.

    Purpose:
        Record which isolated candidate should go to verification (not a promote). This callable is the stable operation contract; a framework adapter
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
        'recommend_rtl_candidate',  # Skill id must match capabilities/skills in config.yaml.  # Skill id must match capabilities/skills in config.yaml.
        payload,  # Argument dict forwarded to the adapter / telemetry.  # Argument dict forwarded to the adapter / telemetry.
        agent_id='rtl_lead',  # Routes telemetry and ACLs to this agent (`rtl_lead`).  # Routes telemetry and ACLs to this agent (`rtl_lead`).
        )

@tool(description='Publish a finding when the specification cannot be implemented as written.')  # Registers skill `return_spec_gap` on `rtl_lead`.
def return_spec_gap(
    summary: str = '',  # One-sentence finding text published into shared engineering memory.
    evidence_refs: str = '',  # Comma-separated artifact URIs that back the finding for later audit.
    severity: str = '',  # Finding severity: low, medium, high, or critical.
    recommended_recipient: str = '',  # Agent id that should act next on this finding (lead or specialist).
    params: dict | None = None,  # Optional extra keys from an adapter or caller; merged into the payload last.
) -> dict:
    """Publish a finding when the specification cannot be implemented as written.

    Purpose:
        Publish a finding when the specification cannot be implemented as written. This callable is the stable operation contract; a framework adapter
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
        'return_spec_gap',  # Skill id must match capabilities/skills in config.yaml.  # Skill id must match capabilities/skills in config.yaml.
        payload,  # Argument dict forwarded to the adapter / telemetry.  # Argument dict forwarded to the adapter / telemetry.
        agent_id='rtl_lead',  # Routes telemetry and ACLs to this agent (`rtl_lead`).  # Routes telemetry and ACLs to this agent (`rtl_lead`).
        )

@tool(description='Publish a required lint, CDC, clock, or low-power check that has not run.')  # Registers skill `flag_missing_block_check` on `rtl_lead`.
def flag_missing_block_check(
    summary: str = '',  # One-sentence finding text published into shared engineering memory.
    evidence_refs: str = '',  # Comma-separated artifact URIs that back the finding for later audit.
    severity: str = '',  # Finding severity: low, medium, high, or critical.
    recommended_recipient: str = '',  # Agent id that should act next on this finding (lead or specialist).
    params: dict | None = None,  # Optional extra keys from an adapter or caller; merged into the payload last.
) -> dict:
    """Publish a required lint, CDC, clock, or low-power check that has not run.

    Purpose:
        Publish a required check that has not yet run. This callable is the stable operation contract; a framework adapter
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
        'flag_missing_block_check',  # Skill id must match capabilities/skills in config.yaml.  # Skill id must match capabilities/skills in config.yaml.
        payload,  # Argument dict forwarded to the adapter / telemetry.  # Argument dict forwarded to the adapter / telemetry.
        agent_id='rtl_lead',  # Routes telemetry and ACLs to this agent (`rtl_lead`).  # Routes telemetry and ACLs to this agent (`rtl_lead`).
        )

@tool(description='Record the candidate ref, checks, and open findings included in a handoff.')  # Registers skill `record_block_handoff` on `rtl_lead`.
def record_block_handoff(
    summary: str = '',  # One-sentence finding text published into shared engineering memory.
    evidence_refs: str = '',  # Comma-separated artifact URIs that back the finding for later audit.
    severity: str = '',  # Finding severity: low, medium, high, or critical.
    recommended_recipient: str = '',  # Agent id that should act next on this finding (lead or specialist).
    params: dict | None = None,  # Optional extra keys from an adapter or caller; merged into the payload last.
) -> dict:
    """Record the candidate ref, checks, and open findings included in a handoff.

    Purpose:
        Record candidate ref, checks, and open findings in a handoff package. This callable is the stable operation contract; a framework adapter
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
        'record_block_handoff',  # Skill id must match capabilities/skills in config.yaml.  # Skill id must match capabilities/skills in config.yaml.
        payload,  # Argument dict forwarded to the adapter / telemetry.  # Argument dict forwarded to the adapter / telemetry.
        agent_id='rtl_lead',  # Routes telemetry and ACLs to this agent (`rtl_lead`).  # Routes telemetry and ACLs to this agent (`rtl_lead`).
        )

@tool(description='Open the verification workflow for a candidate that has passed basic compile and lint readiness.')  # Registers skill `request_verification_handoff` on `rtl_lead`.
def request_verification_handoff(
    objective: str = '',  # Argument `objective` for skill `request_verification_handoff` on agent `rtl_lead`; forwarded in the tool payload.
    parent_task_id: str = '',  # Argument `parent_task_id` for skill `request_verification_handoff` on agent `rtl_lead`; forwarded in the tool payload.
    scope_block: str = '',  # Argument `scope_block` for skill `request_verification_handoff` on agent `rtl_lead`; forwarded in the tool payload.
    params: dict | None = None,  # Optional extra keys from an adapter or caller; merged into the payload last.
) -> dict:
    """Open the verification workflow for a candidate that has passed basic compile and lint readiness.

    Purpose:
        Open verification workflow once compile/lint readiness is met. This callable is the stable operation contract; a framework adapter
        performs the real EDA work when bound.

    Arguments:
        objective: Argument `objective` for skill `request_verification_handoff` on agent `rtl_lead`; forwarded in the tool payload.
        parent_task_id: Argument `parent_task_id` for skill `request_verification_handoff` on agent `rtl_lead`; forwarded in the tool payload.
        scope_block: Argument `scope_block` for skill `request_verification_handoff` on agent `rtl_lead`; forwarded in the tool payload.
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
        'objective': objective,  # Argument `objective` for skill `request_verification_handoff` on agent `rtl_lead`; forwarded in the tool payload.  # Argument `objective` for skill `request_verification_handoff` on agent `rtl_lead`; forwarded in the tool payload.
        'parent_task_id': parent_task_id,  # Argument `parent_task_id` for skill `request_verification_handoff` on agent `rtl_lead`; forwarded in the tool payload.  # Argument `parent_task_id` for skill `request_verification_handoff` on agent `rtl_lead`; forwarded in the tool payload.
        'scope_block': scope_block  # Argument `scope_block` for skill `request_verification_handoff` on agent `rtl_lead`; forwarded in the tool payload.  # Argument `scope_block` for skill `request_verification_handoff` on agent `rtl_lead`; forwarded in the tool payload.
        }
    if params:  # Merge optional adapter/caller extras without dropping known keys.
        payload.update(params)  # Last-write wins for colliding keys from params.
    # Emit a structured observation; unbound adapters yield status not_run.
    return tool_observation(
        'request_verification_handoff',  # Skill id must match capabilities/skills in config.yaml.  # Skill id must match capabilities/skills in config.yaml.
        payload,  # Argument dict forwarded to the adapter / telemetry.  # Argument dict forwarded to the adapter / telemetry.
        agent_id='rtl_lead',  # Routes telemetry and ACLs to this agent (`rtl_lead`).  # Routes telemetry and ACLs to this agent (`rtl_lead`).
        )
