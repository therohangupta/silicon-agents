"""Tools for Architecture Lead (`architecture_lead`).

Each function is the stable operation contract for one advertised capability in config.yaml.
A framework adapter (OpenROAD, commercial CDC/lint/UPF, simulator, etc.) performs the real
work when `EDA_FRAMEWORK` is bound. Until then, every call returns status `not_run` via
`tool_observation` and does **not** invoke OpenROAD, Yosys, OpenSTA, a licensed tool, or a
simulator.

This agent serves the **architecture** stage of frontend chip design.
The architecture lead owns decomposition, budgets, and tradeoff selection. It asks workers for performance, interface, power/area, requirements, and security studies, then recommends a revision.

Callers (LLM runtime or orchestrator) pass string refs and optional `params`. Payloads are
assembled explicitly so telemetry and adapters see a stable schema per skill id.
"""

from __future__ import annotations  # Allow modern typing (dict | None) on older runtimes if needed.

from packages.agent_sdk import tool  # Decorator that registers the callable as an agent skill.
from domains.eda.eda import tool_observation  # Builds the stub/real observation dict for adapters.


@tool(description='Emit the workflow that produces one architecture revision.')  # Registers skill `publish_architecture_plan` on `architecture_lead`.
def publish_architecture_plan(
    objective: str = '',  # Argument `objective` for skill `publish_architecture_plan` on agent `architecture_lead`; forwarded in the tool payload.
    parent_task_id: str = '',  # Argument `parent_task_id` for skill `publish_architecture_plan` on agent `architecture_lead`; forwarded in the tool payload.
    scope_block: str = '',  # Argument `scope_block` for skill `publish_architecture_plan` on agent `architecture_lead`; forwarded in the tool payload.
    params: dict | None = None,  # Optional extra keys from an adapter or caller; merged into the payload last.
) -> dict:
    """Emit the workflow that produces one architecture revision.

    Purpose:
        Publish the architecture plan with decomposition and study requests. This callable is the stable operation contract; a framework adapter
        performs the real EDA work when bound.

    Arguments:
        objective: Argument `objective` for skill `publish_architecture_plan` on agent `architecture_lead`; forwarded in the tool payload.
        parent_task_id: Argument `parent_task_id` for skill `publish_architecture_plan` on agent `architecture_lead`; forwarded in the tool payload.
        scope_block: Argument `scope_block` for skill `publish_architecture_plan` on agent `architecture_lead`; forwarded in the tool payload.
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
        'objective': objective,  # Argument `objective` for skill `publish_architecture_plan` on agent `architecture_lead`; forwarded in the tool payload.
        'parent_task_id': parent_task_id,  # Argument `parent_task_id` for skill `publish_architecture_plan` on agent `architecture_lead`; forwarded in the tool payload.
        'scope_block': scope_block  # Argument `scope_block` for skill `publish_architecture_plan` on agent `architecture_lead`; forwarded in the tool payload.
        }
    if params:  # Merge optional adapter/caller extras without dropping known keys.
        payload.update(params)  # Last-write wins for colliding keys from params.
    # Emit a structured observation; unbound adapters yield status not_run.
    return tool_observation(
        'publish_architecture_plan',  # Skill id must match capabilities/skills in config.yaml.
        payload,  # Argument dict forwarded to the adapter / telemetry.
        agent_id='architecture_lead',  # Routes telemetry and ACLs to this agent (`architecture_lead`).
        )

@tool(description='Ask the decomposition work to divide the chip into blocks and interfaces.')  # Registers skill `request_block_decomposition` on `architecture_lead`.
def request_block_decomposition(
    objective: str = '',  # Argument `objective` for skill `request_block_decomposition` on agent `architecture_lead`; forwarded in the tool payload.
    parent_task_id: str = '',  # Argument `parent_task_id` for skill `request_block_decomposition` on agent `architecture_lead`; forwarded in the tool payload.
    scope_block: str = '',  # Argument `scope_block` for skill `request_block_decomposition` on agent `architecture_lead`; forwarded in the tool payload.
    params: dict | None = None,  # Optional extra keys from an adapter or caller; merged into the payload last.
) -> dict:
    """Ask the decomposition work to divide the chip into blocks and interfaces.

    Purpose:
        Ask for a block partition proposal under area/perf constraints. This callable is the stable operation contract; a framework adapter
        performs the real EDA work when bound.

    Arguments:
        objective: Argument `objective` for skill `request_block_decomposition` on agent `architecture_lead`; forwarded in the tool payload.
        parent_task_id: Argument `parent_task_id` for skill `request_block_decomposition` on agent `architecture_lead`; forwarded in the tool payload.
        scope_block: Argument `scope_block` for skill `request_block_decomposition` on agent `architecture_lead`; forwarded in the tool payload.
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
        'objective': objective,  # Argument `objective` for skill `request_block_decomposition` on agent `architecture_lead`; forwarded in the tool payload.
        'parent_task_id': parent_task_id,  # Argument `parent_task_id` for skill `request_block_decomposition` on agent `architecture_lead`; forwarded in the tool payload.
        'scope_block': scope_block  # Argument `scope_block` for skill `request_block_decomposition` on agent `architecture_lead`; forwarded in the tool payload.
        }
    if params:  # Merge optional adapter/caller extras without dropping known keys.
        payload.update(params)  # Last-write wins for colliding keys from params.
    # Emit a structured observation; unbound adapters yield status not_run.
    return tool_observation(
        'request_block_decomposition',  # Skill id must match capabilities/skills in config.yaml.
        payload,  # Argument dict forwarded to the adapter / telemetry.
        agent_id='architecture_lead',  # Routes telemetry and ACLs to this agent (`architecture_lead`).
        )

@tool(description='Open a performance-modeling task for one workload.')  # Registers skill `request_performance_study` on `architecture_lead`.
def request_performance_study(
    objective: str = '',  # Argument `objective` for skill `request_performance_study` on agent `architecture_lead`; forwarded in the tool payload.
    parent_task_id: str = '',  # Argument `parent_task_id` for skill `request_performance_study` on agent `architecture_lead`; forwarded in the tool payload.
    scope_block: str = '',  # Argument `scope_block` for skill `request_performance_study` on agent `architecture_lead`; forwarded in the tool payload.
    params: dict | None = None,  # Optional extra keys from an adapter or caller; merged into the payload last.
) -> dict:
    """Open a performance-modeling task for one workload.

    Purpose:
        Open a performance-modeling study for a workload and partition. This callable is the stable operation contract; a framework adapter
        performs the real EDA work when bound.

    Arguments:
        objective: Argument `objective` for skill `request_performance_study` on agent `architecture_lead`; forwarded in the tool payload.
        parent_task_id: Argument `parent_task_id` for skill `request_performance_study` on agent `architecture_lead`; forwarded in the tool payload.
        scope_block: Argument `scope_block` for skill `request_performance_study` on agent `architecture_lead`; forwarded in the tool payload.
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
        'objective': objective,  # Argument `objective` for skill `request_performance_study` on agent `architecture_lead`; forwarded in the tool payload.
        'parent_task_id': parent_task_id,  # Argument `parent_task_id` for skill `request_performance_study` on agent `architecture_lead`; forwarded in the tool payload.
        'scope_block': scope_block  # Argument `scope_block` for skill `request_performance_study` on agent `architecture_lead`; forwarded in the tool payload.
        }
    if params:  # Merge optional adapter/caller extras without dropping known keys.
        payload.update(params)  # Last-write wins for colliding keys from params.
    # Emit a structured observation; unbound adapters yield status not_run.
    return tool_observation(
        'request_performance_study',  # Skill id must match capabilities/skills in config.yaml.
        payload,  # Argument dict forwarded to the adapter / telemetry.
        agent_id='architecture_lead',  # Routes telemetry and ACLs to this agent (`architecture_lead`).
        )

@tool(description='Open an interface-contract task between two blocks.')  # Registers skill `request_interface_definition` on `architecture_lead`.
def request_interface_definition(
    objective: str = '',  # Argument `objective` for skill `request_interface_definition` on agent `architecture_lead`; forwarded in the tool payload.
    parent_task_id: str = '',  # Argument `parent_task_id` for skill `request_interface_definition` on agent `architecture_lead`; forwarded in the tool payload.
    scope_block: str = '',  # Argument `scope_block` for skill `request_interface_definition` on agent `architecture_lead`; forwarded in the tool payload.
    params: dict | None = None,  # Optional extra keys from an adapter or caller; merged into the payload last.
) -> dict:
    """Open an interface-contract task between two blocks.

    Purpose:
        Open an interface-contract definition task between blocks. This callable is the stable operation contract; a framework adapter
        performs the real EDA work when bound.

    Arguments:
        objective: Argument `objective` for skill `request_interface_definition` on agent `architecture_lead`; forwarded in the tool payload.
        parent_task_id: Argument `parent_task_id` for skill `request_interface_definition` on agent `architecture_lead`; forwarded in the tool payload.
        scope_block: Argument `scope_block` for skill `request_interface_definition` on agent `architecture_lead`; forwarded in the tool payload.
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
        'objective': objective,  # Argument `objective` for skill `request_interface_definition` on agent `architecture_lead`; forwarded in the tool payload.
        'parent_task_id': parent_task_id,  # Argument `parent_task_id` for skill `request_interface_definition` on agent `architecture_lead`; forwarded in the tool payload.
        'scope_block': scope_block  # Argument `scope_block` for skill `request_interface_definition` on agent `architecture_lead`; forwarded in the tool payload.
        }
    if params:  # Merge optional adapter/caller extras without dropping known keys.
        payload.update(params)  # Last-write wins for colliding keys from params.
    # Emit a structured observation; unbound adapters yield status not_run.
    return tool_observation(
        'request_interface_definition',  # Skill id must match capabilities/skills in config.yaml.
        payload,  # Argument dict forwarded to the adapter / telemetry.
        agent_id='architecture_lead',  # Routes telemetry and ACLs to this agent (`architecture_lead`).
        )

@tool(description='Rank architecture candidates against requirements and budgets.')  # Registers skill `compare_architectures` on `architecture_lead`.
def compare_architectures(
    candidate_ref: str = '',  # Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.
    report_ref: str = '',  # Artifact URI of a prior report. Empty reads the latest report for this candidate.
    corner: str = '',  # PVT corner (process/voltage/temperature). Empty when the job is not corner-specific.
    mode: str = '',  # Functional or analysis mode string. Empty when the job is not mode-specific.
    params: dict | None = None,  # Optional extra keys from an adapter or caller; merged into the payload last.
) -> dict:
    """Rank architecture candidates against requirements and budgets.

    Purpose:
        Compare architecture revisions on budgets, coverage, and open tradeoffs. This callable is the stable operation contract; a framework adapter
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
        'candidate_ref': candidate_ref,  # Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.
        'report_ref': report_ref,  # Artifact URI of a prior report. Empty reads the latest report for this candidate.
        'corner': corner,  # PVT corner (process/voltage/temperature). Empty when the job is not corner-specific.
        'mode': mode  # Functional or analysis mode string. Empty when the job is not mode-specific.
        }
    if params:  # Merge optional adapter/caller extras without dropping known keys.
        payload.update(params)  # Last-write wins for colliding keys from params.
    # Emit a structured observation; unbound adapters yield status not_run.
    return tool_observation(
        'compare_architectures',  # Skill id must match capabilities/skills in config.yaml.
        payload,  # Argument dict forwarded to the adapter / telemetry.
        agent_id='architecture_lead',  # Routes telemetry and ACLs to this agent (`architecture_lead`).
        )

@tool(description='Read latency, bandwidth, power, and area budgets per block.')  # Registers skill `read_block_budgets` on `architecture_lead`.
def read_block_budgets(
    candidate_ref: str = '',  # Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.
    report_ref: str = '',  # Artifact URI of a prior report. Empty reads the latest report for this candidate.
    corner: str = '',  # PVT corner (process/voltage/temperature). Empty when the job is not corner-specific.
    mode: str = '',  # Functional or analysis mode string. Empty when the job is not mode-specific.
    params: dict | None = None,  # Optional extra keys from an adapter or caller; merged into the payload last.
) -> dict:
    """Read latency, bandwidth, power, and area budgets per block.

    Purpose:
        Read power/area/performance budgets assigned to blocks. This callable is the stable operation contract; a framework adapter
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
        'candidate_ref': candidate_ref,  # Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.
        'report_ref': report_ref,  # Artifact URI of a prior report. Empty reads the latest report for this candidate.
        'corner': corner,  # PVT corner (process/voltage/temperature). Empty when the job is not corner-specific.
        'mode': mode  # Functional or analysis mode string. Empty when the job is not mode-specific.
        }
    if params:  # Merge optional adapter/caller extras without dropping known keys.
        payload.update(params)  # Last-write wins for colliding keys from params.
    # Emit a structured observation; unbound adapters yield status not_run.
    return tool_observation(
        'read_block_budgets',  # Skill id must match capabilities/skills in config.yaml.
        payload,  # Argument dict forwarded to the adapter / telemetry.
        agent_id='architecture_lead',  # Routes telemetry and ACLs to this agent (`architecture_lead`).
        )

@tool(description='Read which requirements each architecture candidate claims to meet.')  # Registers skill `read_requirement_coverage` on `architecture_lead`.
def read_requirement_coverage(
    candidate_ref: str = '',  # Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.
    report_ref: str = '',  # Artifact URI of a prior report. Empty reads the latest report for this candidate.
    corner: str = '',  # PVT corner (process/voltage/temperature). Empty when the job is not corner-specific.
    mode: str = '',  # Functional or analysis mode string. Empty when the job is not mode-specific.
    params: dict | None = None,  # Optional extra keys from an adapter or caller; merged into the payload last.
) -> dict:
    """Read which requirements each architecture candidate claims to meet.

    Purpose:
        Read how requirements map onto architecture and checks. This callable is the stable operation contract; a framework adapter
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
        'candidate_ref': candidate_ref,  # Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.
        'report_ref': report_ref,  # Artifact URI of a prior report. Empty reads the latest report for this candidate.
        'corner': corner,  # PVT corner (process/voltage/temperature). Empty when the job is not corner-specific.
        'mode': mode  # Functional or analysis mode string. Empty when the job is not mode-specific.
        }
    if params:  # Merge optional adapter/caller extras without dropping known keys.
        payload.update(params)  # Last-write wins for colliding keys from params.
    # Emit a structured observation; unbound adapters yield status not_run.
    return tool_observation(
        'read_requirement_coverage',  # Skill id must match capabilities/skills in config.yaml.
        payload,  # Argument dict forwarded to the adapter / telemetry.
        agent_id='architecture_lead',  # Routes telemetry and ACLs to this agent (`architecture_lead`).
        )

@tool(description='List architecture choices that are still unresolved.')  # Registers skill `list_open_tradeoffs` on `architecture_lead`.
def list_open_tradeoffs(
    candidate_ref: str = '',  # Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.
    report_ref: str = '',  # Artifact URI of a prior report. Empty reads the latest report for this candidate.
    corner: str = '',  # PVT corner (process/voltage/temperature). Empty when the job is not corner-specific.
    mode: str = '',  # Functional or analysis mode string. Empty when the job is not mode-specific.
    params: dict | None = None,  # Optional extra keys from an adapter or caller; merged into the payload last.
) -> dict:
    """List architecture choices that are still unresolved.

    Purpose:
        List unresolved architecture tradeoffs awaiting decision. This callable is the stable operation contract; a framework adapter
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
        'candidate_ref': candidate_ref,  # Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.
        'report_ref': report_ref,  # Artifact URI of a prior report. Empty reads the latest report for this candidate.
        'corner': corner,  # PVT corner (process/voltage/temperature). Empty when the job is not corner-specific.
        'mode': mode  # Functional or analysis mode string. Empty when the job is not mode-specific.
        }
    if params:  # Merge optional adapter/caller extras without dropping known keys.
        payload.update(params)  # Last-write wins for colliding keys from params.
    # Emit a structured observation; unbound adapters yield status not_run.
    return tool_observation(
        'list_open_tradeoffs',  # Skill id must match capabilities/skills in config.yaml.
        payload,  # Argument dict forwarded to the adapter / telemetry.
        agent_id='architecture_lead',  # Routes telemetry and ACLs to this agent (`architecture_lead`).
        )

@tool(description='Record which candidate should become the qualified architecture revision.')  # Registers skill `recommend_architecture_revision` on `architecture_lead`.
def recommend_architecture_revision(
    summary: str = '',  # One-sentence finding text published into shared engineering memory.
    evidence_refs: str = '',  # Comma-separated artifact URIs that back the finding for later audit.
    severity: str = '',  # Finding severity: low, medium, high, or critical.
    recommended_recipient: str = '',  # Agent id that should act next on this finding (lead or specialist).
    params: dict | None = None,  # Optional extra keys from an adapter or caller; merged into the payload last.
) -> dict:
    """Record which candidate should become the qualified architecture revision.

    Purpose:
        Recommend a qualified architecture revision for human/decision gates. This callable is the stable operation contract; a framework adapter
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
        'summary': summary,  # One-sentence finding text published into shared engineering memory.
        'evidence_refs': evidence_refs,  # Comma-separated artifact URIs that back the finding for later audit.
        'severity': severity,  # Finding severity: low, medium, high, or critical.
        'recommended_recipient': recommended_recipient  # Agent id that should act next on this finding (lead or specialist).
        }
    if params:  # Merge optional adapter/caller extras without dropping known keys.
        payload.update(params)  # Last-write wins for colliding keys from params.
    # Emit a structured observation; unbound adapters yield status not_run.
    return tool_observation(
        'recommend_architecture_revision',  # Skill id must match capabilities/skills in config.yaml.
        payload,  # Argument dict forwarded to the adapter / telemetry.
        agent_id='architecture_lead',  # Routes telemetry and ACLs to this agent (`architecture_lead`).
        )

@tool(description='Publish a proposed budget for one block. A human still owns the requirement.')  # Registers skill `publish_block_budget` on `architecture_lead`.
def publish_block_budget(
    summary: str = '',  # One-sentence finding text published into shared engineering memory.
    evidence_refs: str = '',  # Comma-separated artifact URIs that back the finding for later audit.
    severity: str = '',  # Finding severity: low, medium, high, or critical.
    recommended_recipient: str = '',  # Agent id that should act next on this finding (lead or specialist).
    params: dict | None = None,  # Optional extra keys from an adapter or caller; merged into the payload last.
) -> dict:
    """Publish a proposed budget for one block. A human still owns the requirement.

    Purpose:
        Publish a block budget artifact for downstream RTL and physical stages. This callable is the stable operation contract; a framework adapter
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
        'summary': summary,  # One-sentence finding text published into shared engineering memory.
        'evidence_refs': evidence_refs,  # Comma-separated artifact URIs that back the finding for later audit.
        'severity': severity,  # Finding severity: low, medium, high, or critical.
        'recommended_recipient': recommended_recipient  # Agent id that should act next on this finding (lead or specialist).
        }
    if params:  # Merge optional adapter/caller extras without dropping known keys.
        payload.update(params)  # Last-write wins for colliding keys from params.
    # Emit a structured observation; unbound adapters yield status not_run.
    return tool_observation(
        'publish_block_budget',  # Skill id must match capabilities/skills in config.yaml.
        payload,  # Argument dict forwarded to the adapter / telemetry.
        agent_id='architecture_lead',  # Routes telemetry and ACLs to this agent (`architecture_lead`).
        )

@tool(description='Publish evidence that a proposed hierarchy cannot meet a hard budget.')  # Registers skill `flag_infeasible_partition` on `architecture_lead`.
def flag_infeasible_partition(
    summary: str = '',  # One-sentence finding text published into shared engineering memory.
    evidence_refs: str = '',  # Comma-separated artifact URIs that back the finding for later audit.
    severity: str = '',  # Finding severity: low, medium, high, or critical.
    recommended_recipient: str = '',  # Agent id that should act next on this finding (lead or specialist).
    params: dict | None = None,  # Optional extra keys from an adapter or caller; merged into the payload last.
) -> dict:
    """Publish evidence that a proposed hierarchy cannot meet a hard budget.

    Purpose:
        Publish a finding when a partition cannot meet budgets. This callable is the stable operation contract; a framework adapter
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
        'summary': summary,  # One-sentence finding text published into shared engineering memory.
        'evidence_refs': evidence_refs,  # Comma-separated artifact URIs that back the finding for later audit.
        'severity': severity,  # Finding severity: low, medium, high, or critical.
        'recommended_recipient': recommended_recipient  # Agent id that should act next on this finding (lead or specialist).
        }
    if params:  # Merge optional adapter/caller extras without dropping known keys.
        payload.update(params)  # Last-write wins for colliding keys from params.
    # Emit a structured observation; unbound adapters yield status not_run.
    return tool_observation(
        'flag_infeasible_partition',  # Skill id must match capabilities/skills in config.yaml.
        payload,  # Argument dict forwarded to the adapter / telemetry.
        agent_id='architecture_lead',  # Routes telemetry and ACLs to this agent (`architecture_lead`).
        )

@tool(description='Escalate an unresolved architecture tradeoff.')  # Registers skill `request_architecture_decision` on `architecture_lead`.
def request_architecture_decision(
    decision: str = '',  # Argument `decision` for skill `request_architecture_decision` on agent `architecture_lead`; forwarded in the tool payload.
    options: str = '',  # Argument `options` for skill `request_architecture_decision` on agent `architecture_lead`; forwarded in the tool payload.
    evidence_refs: str = '',  # Comma-separated artifact URIs that back the finding for later audit.
    deadline: str = '',  # Argument `deadline` for skill `request_architecture_decision` on agent `architecture_lead`; forwarded in the tool payload.
    params: dict | None = None,  # Optional extra keys from an adapter or caller; merged into the payload last.
) -> dict:
    """Escalate an unresolved architecture tradeoff.

    Purpose:
        Request a recorded architecture decision on an open tradeoff. This callable is the stable operation contract; a framework adapter
        performs the real EDA work when bound.

    Arguments:
        decision: Argument `decision` for skill `request_architecture_decision` on agent `architecture_lead`; forwarded in the tool payload.
        options: Argument `options` for skill `request_architecture_decision` on agent `architecture_lead`; forwarded in the tool payload.
        evidence_refs: Comma-separated artifact URIs that back the finding for later audit.
        deadline: Argument `deadline` for skill `request_architecture_decision` on agent `architecture_lead`; forwarded in the tool payload.
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
        'decision': decision,  # Argument `decision` for skill `request_architecture_decision` on agent `architecture_lead`; forwarded in the tool payload.
        'options': options,  # Argument `options` for skill `request_architecture_decision` on agent `architecture_lead`; forwarded in the tool payload.
        'evidence_refs': evidence_refs,  # Comma-separated artifact URIs that back the finding for later audit.
        'deadline': deadline  # Argument `deadline` for skill `request_architecture_decision` on agent `architecture_lead`; forwarded in the tool payload.
        }
    if params:  # Merge optional adapter/caller extras without dropping known keys.
        payload.update(params)  # Last-write wins for colliding keys from params.
    # Emit a structured observation; unbound adapters yield status not_run.
    return tool_observation(
        'request_architecture_decision',  # Skill id must match capabilities/skills in config.yaml.
        payload,  # Argument dict forwarded to the adapter / telemetry.
        agent_id='architecture_lead',  # Routes telemetry and ACLs to this agent (`architecture_lead`).
        )
