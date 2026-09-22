"""Tools for Power/Area Estimation Agent (`power_area_estimation`).

Each function is the stable operation contract for one advertised capability in config.yaml.
A framework adapter (OpenROAD, commercial CDC/lint/UPF, simulator, etc.) performs the real
work when `EDA_FRAMEWORK` is bound. Until then, every call returns status `not_run` via
`tool_observation` and does **not** invoke OpenROAD, Yosys, OpenSTA, a licensed tool, or a
simulator.

This agent serves the **architecture** stage of frontend chip design.
Pre-RTL power and area estimates set block budgets with explicit uncertainty. Stale estimates are flagged when inputs change so physical design does not inherit outdated PPA numbers.

Callers (LLM runtime or orchestrator) pass string refs and optional `params`. Payloads are
assembled explicitly so telemetry and adapters see a stable schema per skill id.
"""

from __future__ import annotations  # Allow modern typing (dict | None) on older runtimes if needed.

from packages.agent_sdk import tool  # Decorator that registers the callable as an agent skill.
from domains.eda.eda import tool_observation  # Builds the stub/real observation dict for adapters.


@tool(description='Read area models, activity, library, and utilization assumptions.')  # Registers skill `collect_estimation_inputs` on `power_area_estimation`.
def collect_estimation_inputs(
    candidate_ref: str = '',  # Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.
    report_ref: str = '',  # Artifact URI of a prior report. Empty reads the latest report for this candidate.
    corner: str = '',  # PVT corner (process/voltage/temperature). Empty when the job is not corner-specific.
    mode: str = '',  # Functional or analysis mode string. Empty when the job is not mode-specific.
    params: dict | None = None,  # Optional extra keys from an adapter or caller; merged into the payload last.
) -> dict:
    """Read area models, activity, library, and utilization assumptions.

    Purpose:
        Collect process, library, and architectural inputs for PPA estimation. This callable is the stable operation contract; a framework adapter
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
        'collect_estimation_inputs',  # Skill id must match capabilities/skills in config.yaml.
        payload,  # Argument dict forwarded to the adapter / telemetry.
        agent_id='power_area_estimation',  # Routes telemetry and ACLs to this agent (`power_area_estimation`).
        )

@tool(description='Write the activity, library, and utilization assumptions for one estimate.')  # Registers skill `write_estimation_assumptions` on `power_area_estimation`.
def write_estimation_assumptions(
    candidate_ref: str = '',  # Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.
    baseline_ref: str = '',  # Immutable baseline revision the candidate must descend from so lineage stays auditable.
    hypothesis: str = '',  # Single change under test for this edit so experiments stay one-hypothesis-at-a-time.
    params: dict | None = None,  # Optional extra keys from an adapter or caller; merged into the payload last.
) -> dict:
    """Write the activity, library, and utilization assumptions for one estimate.

    Purpose:
        Write explicit estimation assumptions for audit. This callable is the stable operation contract; a framework adapter
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
        'candidate_ref': candidate_ref,  # Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.
        'baseline_ref': baseline_ref,  # Immutable baseline revision the candidate must descend from so lineage stays auditable.
        'hypothesis': hypothesis  # Single change under test for this edit so experiments stay one-hypothesis-at-a-time.
        }
    if params:  # Merge optional adapter/caller extras without dropping known keys.
        payload.update(params)  # Last-write wins for colliding keys from params.
    # Emit a structured observation; unbound adapters yield status not_run.
    return tool_observation(
        'write_estimation_assumptions',  # Skill id must match capabilities/skills in config.yaml.
        payload,  # Argument dict forwarded to the adapter / telemetry.
        agent_id='power_area_estimation',  # Routes telemetry and ACLs to this agent (`power_area_estimation`).
        )

@tool(description='Produce an early area estimate and its uncertainty.')  # Registers skill `estimate_area` on `power_area_estimation`.
def estimate_area(
    candidate_ref: str = '',  # Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.
    baseline_ref: str = '',  # Immutable baseline revision the candidate must descend from so lineage stays auditable.
    recipe: str = '',  # Versioned EDA-tool recipe name; the framework adapter rejects unknown recipes.
    corner: str = '',  # PVT corner (process/voltage/temperature). Empty when the job is not corner-specific.
    mode: str = '',  # Functional or analysis mode string. Empty when the job is not mode-specific.
    params: dict | None = None,  # Optional extra keys from an adapter or caller; merged into the payload last.
) -> dict:
    """Produce an early area estimate and its uncertainty.

    Purpose:
        Produce an early area estimate with uncertainty. This callable is the stable operation contract; a framework adapter
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
        'candidate_ref': candidate_ref,  # Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.
        'baseline_ref': baseline_ref,  # Immutable baseline revision the candidate must descend from so lineage stays auditable.
        'recipe': recipe,  # Versioned EDA-tool recipe name; the framework adapter rejects unknown recipes.
        'corner': corner,  # PVT corner (process/voltage/temperature). Empty when the job is not corner-specific.
        'mode': mode  # Functional or analysis mode string. Empty when the job is not mode-specific.
        }
    if params:  # Merge optional adapter/caller extras without dropping known keys.
        payload.update(params)  # Last-write wins for colliding keys from params.
    # Emit a structured observation; unbound adapters yield status not_run.
    return tool_observation(
        'estimate_area',  # Skill id must match capabilities/skills in config.yaml.
        payload,  # Argument dict forwarded to the adapter / telemetry.
        agent_id='power_area_estimation',  # Routes telemetry and ACLs to this agent (`power_area_estimation`).
        )

@tool(description='Produce an early dynamic and leakage estimate and its uncertainty.')  # Registers skill `estimate_power` on `power_area_estimation`.
def estimate_power(
    candidate_ref: str = '',  # Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.
    baseline_ref: str = '',  # Immutable baseline revision the candidate must descend from so lineage stays auditable.
    recipe: str = '',  # Versioned EDA-tool recipe name; the framework adapter rejects unknown recipes.
    corner: str = '',  # PVT corner (process/voltage/temperature). Empty when the job is not corner-specific.
    mode: str = '',  # Functional or analysis mode string. Empty when the job is not mode-specific.
    params: dict | None = None,  # Optional extra keys from an adapter or caller; merged into the payload last.
) -> dict:
    """Produce an early dynamic and leakage estimate and its uncertainty.

    Purpose:
        Produce an early power estimate with uncertainty. This callable is the stable operation contract; a framework adapter
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
        'candidate_ref': candidate_ref,  # Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.
        'baseline_ref': baseline_ref,  # Immutable baseline revision the candidate must descend from so lineage stays auditable.
        'recipe': recipe,  # Versioned EDA-tool recipe name; the framework adapter rejects unknown recipes.
        'corner': corner,  # PVT corner (process/voltage/temperature). Empty when the job is not corner-specific.
        'mode': mode  # Functional or analysis mode string. Empty when the job is not mode-specific.
        }
    if params:  # Merge optional adapter/caller extras without dropping known keys.
        payload.update(params)  # Last-write wins for colliding keys from params.
    # Emit a structured observation; unbound adapters yield status not_run.
    return tool_observation(
        'estimate_power',  # Skill id must match capabilities/skills in config.yaml.
        payload,  # Argument dict forwarded to the adapter / telemetry.
        agent_id='power_area_estimation',  # Routes telemetry and ACLs to this agent (`power_area_estimation`).
        )

@tool(description='Produce a combined power, performance, and area estimate.')  # Registers skill `estimate_ppa` on `power_area_estimation`.
def estimate_ppa(
    candidate_ref: str = '',  # Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.
    baseline_ref: str = '',  # Immutable baseline revision the candidate must descend from so lineage stays auditable.
    recipe: str = '',  # Versioned EDA-tool recipe name; the framework adapter rejects unknown recipes.
    corner: str = '',  # PVT corner (process/voltage/temperature). Empty when the job is not corner-specific.
    mode: str = '',  # Functional or analysis mode string. Empty when the job is not mode-specific.
    params: dict | None = None,  # Optional extra keys from an adapter or caller; merged into the payload last.
) -> dict:
    """Produce a combined power, performance, and area estimate.

    Purpose:
        Produce a combined power/performance/area estimate package. This callable is the stable operation contract; a framework adapter
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
        'candidate_ref': candidate_ref,  # Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.
        'baseline_ref': baseline_ref,  # Immutable baseline revision the candidate must descend from so lineage stays auditable.
        'recipe': recipe,  # Versioned EDA-tool recipe name; the framework adapter rejects unknown recipes.
        'corner': corner,  # PVT corner (process/voltage/temperature). Empty when the job is not corner-specific.
        'mode': mode  # Functional or analysis mode string. Empty when the job is not mode-specific.
        }
    if params:  # Merge optional adapter/caller extras without dropping known keys.
        payload.update(params)  # Last-write wins for colliding keys from params.
    # Emit a structured observation; unbound adapters yield status not_run.
    return tool_observation(
        'estimate_ppa',  # Skill id must match capabilities/skills in config.yaml.
        payload,  # Argument dict forwarded to the adapter / telemetry.
        agent_id='power_area_estimation',  # Routes telemetry and ACLs to this agent (`power_area_estimation`).
        )

@tool(description='Rerun the estimate across a utilization range.')  # Registers skill `sweep_utilization` on `power_area_estimation`.
def sweep_utilization(
    candidate_ref: str = '',  # Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.
    baseline_ref: str = '',  # Immutable baseline revision the candidate must descend from so lineage stays auditable.
    recipe: str = '',  # Versioned EDA-tool recipe name; the framework adapter rejects unknown recipes.
    corner: str = '',  # PVT corner (process/voltage/temperature). Empty when the job is not corner-specific.
    mode: str = '',  # Functional or analysis mode string. Empty when the job is not mode-specific.
    params: dict | None = None,  # Optional extra keys from an adapter or caller; merged into the payload last.
) -> dict:
    """Rerun the estimate across a utilization range.

    Purpose:
        Sweep target utilization to see area sensitivity. This callable is the stable operation contract; a framework adapter
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
        'candidate_ref': candidate_ref,  # Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.
        'baseline_ref': baseline_ref,  # Immutable baseline revision the candidate must descend from so lineage stays auditable.
        'recipe': recipe,  # Versioned EDA-tool recipe name; the framework adapter rejects unknown recipes.
        'corner': corner,  # PVT corner (process/voltage/temperature). Empty when the job is not corner-specific.
        'mode': mode  # Functional or analysis mode string. Empty when the job is not mode-specific.
        }
    if params:  # Merge optional adapter/caller extras without dropping known keys.
        payload.update(params)  # Last-write wins for colliding keys from params.
    # Emit a structured observation; unbound adapters yield status not_run.
    return tool_observation(
        'sweep_utilization',  # Skill id must match capabilities/skills in config.yaml.
        payload,  # Argument dict forwarded to the adapter / telemetry.
        agent_id='power_area_estimation',  # Routes telemetry and ACLs to this agent (`power_area_estimation`).
        )

@tool(description='Read one stored early estimate and its assumptions.')  # Registers skill `read_estimate` on `power_area_estimation`.
def read_estimate(
    candidate_ref: str = '',  # Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.
    report_ref: str = '',  # Artifact URI of a prior report. Empty reads the latest report for this candidate.
    corner: str = '',  # PVT corner (process/voltage/temperature). Empty when the job is not corner-specific.
    mode: str = '',  # Functional or analysis mode string. Empty when the job is not mode-specific.
    params: dict | None = None,  # Optional extra keys from an adapter or caller; merged into the payload last.
) -> dict:
    """Read one stored early estimate and its assumptions.

    Purpose:
        Read a prior estimate artifact. This callable is the stable operation contract; a framework adapter
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
        'read_estimate',  # Skill id must match capabilities/skills in config.yaml.
        payload,  # Argument dict forwarded to the adapter / telemetry.
        agent_id='power_area_estimation',  # Routes telemetry and ACLs to this agent (`power_area_estimation`).
        )

@tool(description='Compare an estimate with the block power and area budgets.')  # Registers skill `compare_estimate_to_budget` on `power_area_estimation`.
def compare_estimate_to_budget(
    candidate_ref: str = '',  # Artifact URI of the isolated design candidate this skill reads or edits; empty often means create-from-baseline.
    report_ref: str = '',  # Artifact URI of a prior report. Empty reads the latest report for this candidate.
    corner: str = '',  # PVT corner (process/voltage/temperature). Empty when the job is not corner-specific.
    mode: str = '',  # Functional or analysis mode string. Empty when the job is not mode-specific.
    params: dict | None = None,  # Optional extra keys from an adapter or caller; merged into the payload last.
) -> dict:
    """Compare an estimate with the block power and area budgets.

    Purpose:
        Compare estimates against published block budgets. This callable is the stable operation contract; a framework adapter
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
        'compare_estimate_to_budget',  # Skill id must match capabilities/skills in config.yaml.
        payload,  # Argument dict forwarded to the adapter / telemetry.
        agent_id='power_area_estimation',  # Routes telemetry and ACLs to this agent (`power_area_estimation`).
        )

@tool(description='Publish the assumptions behind an estimate so a later stage can reject a stale one.')  # Registers skill `record_assumptions` on `power_area_estimation`.
def record_assumptions(
    summary: str = '',  # One-sentence finding text published into shared engineering memory.
    evidence_refs: str = '',  # Comma-separated artifact URIs that back the finding for later audit.
    severity: str = '',  # Finding severity: low, medium, high, or critical.
    recommended_recipient: str = '',  # Agent id that should act next on this finding (lead or specialist).
    params: dict | None = None,  # Optional extra keys from an adapter or caller; merged into the payload last.
) -> dict:
    """Publish the assumptions behind an estimate so a later stage can reject a stale one.

    Purpose:
        Record assumptions attached to the active estimate. This callable is the stable operation contract; a framework adapter
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
        'record_assumptions',  # Skill id must match capabilities/skills in config.yaml.
        payload,  # Argument dict forwarded to the adapter / telemetry.
        agent_id='power_area_estimation',  # Routes telemetry and ACLs to this agent (`power_area_estimation`).
        )

@tool(description='Publish an estimate that crosses a budget inside its uncertainty band.')  # Registers skill `flag_budget_risk` on `power_area_estimation`.
def flag_budget_risk(
    summary: str = '',  # One-sentence finding text published into shared engineering memory.
    evidence_refs: str = '',  # Comma-separated artifact URIs that back the finding for later audit.
    severity: str = '',  # Finding severity: low, medium, high, or critical.
    recommended_recipient: str = '',  # Agent id that should act next on this finding (lead or specialist).
    params: dict | None = None,  # Optional extra keys from an adapter or caller; merged into the payload last.
) -> dict:
    """Publish an estimate that crosses a budget inside its uncertainty band.

    Purpose:
        Publish a finding when estimates threaten a budget. This callable is the stable operation contract; a framework adapter
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
        'flag_budget_risk',  # Skill id must match capabilities/skills in config.yaml.
        payload,  # Argument dict forwarded to the adapter / telemetry.
        agent_id='power_area_estimation',  # Routes telemetry and ACLs to this agent (`power_area_estimation`).
        )

@tool(description='Publish an estimate whose architecture revision is no longer current.')  # Registers skill `flag_stale_estimate` on `power_area_estimation`.
def flag_stale_estimate(
    summary: str = '',  # One-sentence finding text published into shared engineering memory.
    evidence_refs: str = '',  # Comma-separated artifact URIs that back the finding for later audit.
    severity: str = '',  # Finding severity: low, medium, high, or critical.
    recommended_recipient: str = '',  # Agent id that should act next on this finding (lead or specialist).
    params: dict | None = None,  # Optional extra keys from an adapter or caller; merged into the payload last.
) -> dict:
    """Publish an estimate whose architecture revision is no longer current.

    Purpose:
        Publish a finding when inputs changed under an old estimate. This callable is the stable operation contract; a framework adapter
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
        'flag_stale_estimate',  # Skill id must match capabilities/skills in config.yaml.
        payload,  # Argument dict forwarded to the adapter / telemetry.
        agent_id='power_area_estimation',  # Routes telemetry and ACLs to this agent (`power_area_estimation`).
        )

@tool(description='Record the model, activity file, and library used for an estimate.')  # Registers skill `record_estimate_lineage` on `power_area_estimation`.
def record_estimate_lineage(
    summary: str = '',  # One-sentence finding text published into shared engineering memory.
    evidence_refs: str = '',  # Comma-separated artifact URIs that back the finding for later audit.
    severity: str = '',  # Finding severity: low, medium, high, or critical.
    recommended_recipient: str = '',  # Agent id that should act next on this finding (lead or specialist).
    params: dict | None = None,  # Optional extra keys from an adapter or caller; merged into the payload last.
) -> dict:
    """Record the model, activity file, and library used for an estimate.

    Purpose:
        Record lineage from inputs and assumptions to the estimate. This callable is the stable operation contract; a framework adapter
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
        'record_estimate_lineage',  # Skill id must match capabilities/skills in config.yaml.
        payload,  # Argument dict forwarded to the adapter / telemetry.
        agent_id='power_area_estimation',  # Routes telemetry and ACLs to this agent (`power_area_estimation`).
        )
