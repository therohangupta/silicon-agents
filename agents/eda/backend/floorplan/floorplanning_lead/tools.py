"""Tools for Floorplanning Lead.

Each function below is the stable operation contract for this agent. A framework
adapter (Yosys, OpenROAD, OpenSTA, or a licensed tool) is responsible for actually
performing the EDA work. Until a framework is bound through ``EDA_FRAMEWORK`` /
backend.type, every call returns a structured observation with status ``not_run``
and must not invoke a synthesizer, placer, router, equivalence engine, or simulator.

EDA focus for this tool module: Partition floorplanning: macros, pin assignment, power distribution network (PDN), blockages/utilization, and early routability/timing estimates. Recommends a candidate for placement without promoting it onto the baseline.

Common return shape:
    ``tool_observation(name, payload, agent_id="floorplanning_lead")`` builds the dict the
    fleet journals and the planner consumes. Side effects are limited to that
    observation record unless an adapter is bound.

Failures:
    Adapters may raise or return failed statuses when required scripts, libraries,
    constraints, or DEFs are missing; the unbound path should not raise merely
    because no engine exists.
"""

# Postpone evaluation of annotations so ``dict | None`` works on older typing runtimes.
from __future__ import annotations

# Decorator that registers a function as a fleet-invocable skill/tool.
from packages.agent_sdk import tool
# Helper that wraps a named operation + payload into the standard observation dict.
from domains.eda.adapters import tool_observation


# Register `plan_floorplan_exploration` as an invocable skill: Emit the floorplan workflow for this partition.
@tool(description='Emit the floorplan workflow for this partition.')
def plan_floorplan_exploration(
    objective: str = "",
    parent_task_id: str = "",
    scope_block: str = "",
    params: dict | None = None,
) -> dict:
    """Emit the floorplan workflow for this partition.

    Purpose:
        Emit the floorplan workflow sequencing macros, pins, PDN, and early physical estimates.

    Args:
        objective: Natural-language outcome the child workflow or operation must achieve for this silicon task.
        parent_task_id: Identifier of the parent task that owns this child workflow in the fleet journal.
        scope_block: Hierarchical block name this work applies to; empty means the task's current block context.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `plan_floorplan_exploration` operation for agent `floorplanning_lead`. When no EDA framework is
        bound, status is ``not_run`` and no netlist/DEF/SDC file is mutated.

    Side effects:
        Journals an observation through the shared helper. A bound adapter may
        additionally write scripts, netlists, SDC, DEF, or report artifacts.

    Failures:
        Bound adapters fail when required RTL, libraries, constraints, or physical
        inputs are missing or inconsistent; the unbound path returns ``not_run``.
    """
    # Assemble the observation payload from the explicit skill arguments.
    payload = {
        'objective': objective,  # Natural-language outcome the child workflow or operation must achieve for this silicon task.
        'parent_task_id': parent_task_id,  # Identifier of the parent task that owns this child workflow in the fleet journal.
        'scope_block': scope_block,  # Hierarchical block name this work applies to; empty means the task's current block context.
    }
    # Merge optional adapter/planner overrides when the caller supplied params.
    if params:
        # params keys intentionally overwrite same-named explicit fields.
        payload.update(params)
    # Hand the `plan_floorplan_exploration` operation to the shared observation helper for `floorplanning_lead`.
    return tool_observation(
        'plan_floorplan_exploration',
        payload,
        agent_id='floorplanning_lead',
    )

# Register `request_macro_alternatives` as an invocable skill: Open another macro-placement batch with one changed constraint.
@tool(description='Open another macro-placement batch with one changed constraint.')
def request_macro_alternatives(
    objective: str = "",
    parent_task_id: str = "",
    scope_block: str = "",
    params: dict | None = None,
) -> dict:
    """Open another macro-placement batch with one changed constraint.

    Purpose:
        Open another macro_placement batch with one changed constraint (halo/channel/orient).

    Args:
        objective: Natural-language outcome the child workflow or operation must achieve for this silicon task.
        parent_task_id: Identifier of the parent task that owns this child workflow in the fleet journal.
        scope_block: Hierarchical block name this work applies to; empty means the task's current block context.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `request_macro_alternatives` operation for agent `floorplanning_lead`. When no EDA framework is
        bound, status is ``not_run`` and no netlist/DEF/SDC file is mutated.

    Side effects:
        Journals an observation through the shared helper. A bound adapter may
        additionally write scripts, netlists, SDC, DEF, or report artifacts.

    Failures:
        Bound adapters fail when required RTL, libraries, constraints, or physical
        inputs are missing or inconsistent; the unbound path returns ``not_run``.
    """
    # Assemble the observation payload from the explicit skill arguments.
    payload = {
        'objective': objective,  # Natural-language outcome the child workflow or operation must achieve for this silicon task.
        'parent_task_id': parent_task_id,  # Identifier of the parent task that owns this child workflow in the fleet journal.
        'scope_block': scope_block,  # Hierarchical block name this work applies to; empty means the task's current block context.
    }
    # Merge optional adapter/planner overrides when the caller supplied params.
    if params:
        # params keys intentionally overwrite same-named explicit fields.
        payload.update(params)
    # Hand the `request_macro_alternatives` operation to the shared observation helper for `floorplanning_lead`.
    return tool_observation(
        'request_macro_alternatives',
        payload,
        agent_id='floorplanning_lead',
    )

# Register `request_pin_assignment` as an invocable skill: Open pin assignment for the current macro candidate.
@tool(description='Open pin assignment for the current macro candidate.')
def request_pin_assignment(
    objective: str = "",
    parent_task_id: str = "",
    scope_block: str = "",
    params: dict | None = None,
) -> dict:
    """Open pin assignment for the current macro candidate.

    Purpose:
        Open pin_assignment for the current macro candidate against the package contract.

    Args:
        objective: Natural-language outcome the child workflow or operation must achieve for this silicon task.
        parent_task_id: Identifier of the parent task that owns this child workflow in the fleet journal.
        scope_block: Hierarchical block name this work applies to; empty means the task's current block context.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `request_pin_assignment` operation for agent `floorplanning_lead`. When no EDA framework is
        bound, status is ``not_run`` and no netlist/DEF/SDC file is mutated.

    Side effects:
        Journals an observation through the shared helper. A bound adapter may
        additionally write scripts, netlists, SDC, DEF, or report artifacts.

    Failures:
        Bound adapters fail when required RTL, libraries, constraints, or physical
        inputs are missing or inconsistent; the unbound path returns ``not_run``.
    """
    # Assemble the observation payload from the explicit skill arguments.
    payload = {
        'objective': objective,  # Natural-language outcome the child workflow or operation must achieve for this silicon task.
        'parent_task_id': parent_task_id,  # Identifier of the parent task that owns this child workflow in the fleet journal.
        'scope_block': scope_block,  # Hierarchical block name this work applies to; empty means the task's current block context.
    }
    # Merge optional adapter/planner overrides when the caller supplied params.
    if params:
        # params keys intentionally overwrite same-named explicit fields.
        payload.update(params)
    # Hand the `request_pin_assignment` operation to the shared observation helper for `floorplanning_lead`.
    return tool_observation(
        'request_pin_assignment',
        payload,
        agent_id='floorplanning_lead',
    )

# Register `request_power_grid` as an invocable skill: Open an early power-grid candidate.
@tool(description='Open an early power-grid candidate.')
def request_power_grid(
    objective: str = "",
    parent_task_id: str = "",
    scope_block: str = "",
    params: dict | None = None,
) -> dict:
    """Open an early power-grid candidate.

    Purpose:
        Open power_grid to build an early PDN candidate for IR/resource feedback.

    Args:
        objective: Natural-language outcome the child workflow or operation must achieve for this silicon task.
        parent_task_id: Identifier of the parent task that owns this child workflow in the fleet journal.
        scope_block: Hierarchical block name this work applies to; empty means the task's current block context.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `request_power_grid` operation for agent `floorplanning_lead`. When no EDA framework is
        bound, status is ``not_run`` and no netlist/DEF/SDC file is mutated.

    Side effects:
        Journals an observation through the shared helper. A bound adapter may
        additionally write scripts, netlists, SDC, DEF, or report artifacts.

    Failures:
        Bound adapters fail when required RTL, libraries, constraints, or physical
        inputs are missing or inconsistent; the unbound path returns ``not_run``.
    """
    # Assemble the observation payload from the explicit skill arguments.
    payload = {
        'objective': objective,  # Natural-language outcome the child workflow or operation must achieve for this silicon task.
        'parent_task_id': parent_task_id,  # Identifier of the parent task that owns this child workflow in the fleet journal.
        'scope_block': scope_block,  # Hierarchical block name this work applies to; empty means the task's current block context.
    }
    # Merge optional adapter/planner overrides when the caller supplied params.
    if params:
        # params keys intentionally overwrite same-named explicit fields.
        payload.update(params)
    # Hand the `request_power_grid` operation to the shared observation helper for `floorplanning_lead`.
    return tool_observation(
        'request_power_grid',
        payload,
        agent_id='floorplanning_lead',
    )

# Register `request_early_physical_estimate` as an invocable skill: Open trial placement, global route, and early timing.
@tool(description='Open trial placement, global route, and early timing.')
def request_early_physical_estimate(
    objective: str = "",
    parent_task_id: str = "",
    scope_block: str = "",
    params: dict | None = None,
) -> dict:
    """Open trial placement, global route, and early timing.

    Purpose:
        Open early_congestion_timing for trial place/route and early timing proxies.

    Args:
        objective: Natural-language outcome the child workflow or operation must achieve for this silicon task.
        parent_task_id: Identifier of the parent task that owns this child workflow in the fleet journal.
        scope_block: Hierarchical block name this work applies to; empty means the task's current block context.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `request_early_physical_estimate` operation for agent `floorplanning_lead`. When no EDA framework is
        bound, status is ``not_run`` and no netlist/DEF/SDC file is mutated.

    Side effects:
        Journals an observation through the shared helper. A bound adapter may
        additionally write scripts, netlists, SDC, DEF, or report artifacts.

    Failures:
        Bound adapters fail when required RTL, libraries, constraints, or physical
        inputs are missing or inconsistent; the unbound path returns ``not_run``.
    """
    # Assemble the observation payload from the explicit skill arguments.
    payload = {
        'objective': objective,  # Natural-language outcome the child workflow or operation must achieve for this silicon task.
        'parent_task_id': parent_task_id,  # Identifier of the parent task that owns this child workflow in the fleet journal.
        'scope_block': scope_block,  # Hierarchical block name this work applies to; empty means the task's current block context.
    }
    # Merge optional adapter/planner overrides when the caller supplied params.
    if params:
        # params keys intentionally overwrite same-named explicit fields.
        payload.update(params)
    # Hand the `request_early_physical_estimate` operation to the shared observation helper for `floorplanning_lead`.
    return tool_observation(
        'request_early_physical_estimate',
        payload,
        agent_id='floorplanning_lead',
    )

# Register `read_floorplan_inputs` as an invocable skill: Read die, utilization, macros, constraints, and package contract.
@tool(description='Read die, utilization, macros, constraints, and package contract.')
def read_floorplan_inputs(
    candidate_ref: str = "",
    report_ref: str = "",
    corner: str = "",
    mode: str = "",
    params: dict | None = None,
) -> dict:
    """Read die, utilization, macros, constraints, and package contract.

    Purpose:
        Read die size, utilization targets, macro inventory, constraints, and package contract.

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        report_ref: Artifact URI of a specific report; empty selects the latest report for the candidate.
        corner: Process/voltage/temperature corner filter (e.g. SS/FF); empty reads every available corner.
        mode: Operating mode filter (functional, scan, etc.); empty reads every available mode.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `read_floorplan_inputs` operation for agent `floorplanning_lead`. When no EDA framework is
        bound, status is ``not_run`` and no netlist/DEF/SDC file is mutated.

    Side effects:
        Journals an observation through the shared helper. A bound adapter may
        additionally write scripts, netlists, SDC, DEF, or report artifacts.

    Failures:
        Bound adapters fail when required RTL, libraries, constraints, or physical
        inputs are missing or inconsistent; the unbound path returns ``not_run``.
    """
    # Assemble the observation payload from the explicit skill arguments.
    payload = {
        'candidate_ref': candidate_ref,  # Artifact URI or memory id of the design candidate whose reports are read.
        'report_ref': report_ref,  # Artifact URI of a specific report; empty selects the latest report for the candidate.
        'corner': corner,  # Process/voltage/temperature corner filter (e.g. SS/FF); empty reads every available corner.
        'mode': mode,  # Operating mode filter (functional, scan, etc.); empty reads every available mode.
    }
    # Merge optional adapter/planner overrides when the caller supplied params.
    if params:
        # params keys intentionally overwrite same-named explicit fields.
        payload.update(params)
    # Hand the `read_floorplan_inputs` operation to the shared observation helper for `floorplanning_lead`.
    return tool_observation(
        'read_floorplan_inputs',
        payload,
        agent_id='floorplanning_lead',
    )

# Register `read_floorplan_metrics` as an invocable skill: Read congestion, early timing, pin density, and IR proxy for each candidate.
@tool(description='Read congestion, early timing, pin density, and IR proxy for each candidate.')
def read_floorplan_metrics(
    candidate_ref: str = "",
    report_ref: str = "",
    corner: str = "",
    mode: str = "",
    params: dict | None = None,
) -> dict:
    """Read congestion, early timing, pin density, and IR proxy for each candidate.

    Purpose:
        Read congestion, early timing, pin density, and IR proxy for each floorplan candidate.

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        report_ref: Artifact URI of a specific report; empty selects the latest report for the candidate.
        corner: Process/voltage/temperature corner filter (e.g. SS/FF); empty reads every available corner.
        mode: Operating mode filter (functional, scan, etc.); empty reads every available mode.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `read_floorplan_metrics` operation for agent `floorplanning_lead`. When no EDA framework is
        bound, status is ``not_run`` and no netlist/DEF/SDC file is mutated.

    Side effects:
        Journals an observation through the shared helper. A bound adapter may
        additionally write scripts, netlists, SDC, DEF, or report artifacts.

    Failures:
        Bound adapters fail when required RTL, libraries, constraints, or physical
        inputs are missing or inconsistent; the unbound path returns ``not_run``.
    """
    # Assemble the observation payload from the explicit skill arguments.
    payload = {
        'candidate_ref': candidate_ref,  # Artifact URI or memory id of the design candidate whose reports are read.
        'report_ref': report_ref,  # Artifact URI of a specific report; empty selects the latest report for the candidate.
        'corner': corner,  # Process/voltage/temperature corner filter (e.g. SS/FF); empty reads every available corner.
        'mode': mode,  # Operating mode filter (functional, scan, etc.); empty reads every available mode.
    }
    # Merge optional adapter/planner overrides when the caller supplied params.
    if params:
        # params keys intentionally overwrite same-named explicit fields.
        payload.update(params)
    # Hand the `read_floorplan_metrics` operation to the shared observation helper for `floorplanning_lead`.
    return tool_observation(
        'read_floorplan_metrics',
        payload,
        agent_id='floorplanning_lead',
    )

# Register `compare_floorplan_candidates` as an invocable skill: Rank candidates that satisfy hard physical limits.
@tool(description='Rank candidates that satisfy hard physical limits.')
def compare_floorplan_candidates(
    candidate_ref: str = "",
    report_ref: str = "",
    corner: str = "",
    mode: str = "",
    params: dict | None = None,
) -> dict:
    """Rank candidates that satisfy hard physical limits.

    Purpose:
        Rank only candidates that satisfy hard physical limits (keepout, density, IR).

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        report_ref: Artifact URI of a specific report; empty selects the latest report for the candidate.
        corner: Process/voltage/temperature corner filter (e.g. SS/FF); empty reads every available corner.
        mode: Operating mode filter (functional, scan, etc.); empty reads every available mode.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `compare_floorplan_candidates` operation for agent `floorplanning_lead`. When no EDA framework is
        bound, status is ``not_run`` and no netlist/DEF/SDC file is mutated.

    Side effects:
        Journals an observation through the shared helper. A bound adapter may
        additionally write scripts, netlists, SDC, DEF, or report artifacts.

    Failures:
        Bound adapters fail when required RTL, libraries, constraints, or physical
        inputs are missing or inconsistent; the unbound path returns ``not_run``.
    """
    # Assemble the observation payload from the explicit skill arguments.
    payload = {
        'candidate_ref': candidate_ref,  # Artifact URI or memory id of the design candidate whose reports are read.
        'report_ref': report_ref,  # Artifact URI of a specific report; empty selects the latest report for the candidate.
        'corner': corner,  # Process/voltage/temperature corner filter (e.g. SS/FF); empty reads every available corner.
        'mode': mode,  # Operating mode filter (functional, scan, etc.); empty reads every available mode.
    }
    # Merge optional adapter/planner overrides when the caller supplied params.
    if params:
        # params keys intentionally overwrite same-named explicit fields.
        payload.update(params)
    # Hand the `compare_floorplan_candidates` operation to the shared observation helper for `floorplanning_lead`.
    return tool_observation(
        'compare_floorplan_candidates',
        payload,
        agent_id='floorplanning_lead',
    )

# Register `recommend_floorplan_candidate` as an invocable skill: Record which floorplan should advance to placement. This does not promote it.
@tool(description='Record which floorplan should advance to placement. This does not promote it.')
def recommend_floorplan_candidate(
    summary: str = "",
    evidence_refs: str = "",
    severity: str = "",
    recommended_recipient: str = "",
    params: dict | None = None,
) -> dict:
    """Record which floorplan should advance to placement. This does not promote it.

    Purpose:
        Journal which floorplan should advance to placement; does not promote the baseline.

    Args:
        summary: One-sentence finding written into engineering memory for downstream agents.
        evidence_refs: Comma-separated artifact URIs that substantiate the finding or tradeoff.
        severity: Finding severity: low, medium, high, or critical relative to hard requirements.
        recommended_recipient: Agent id that should act next on this finding.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `recommend_floorplan_candidate` operation for agent `floorplanning_lead`. When no EDA framework is
        bound, status is ``not_run`` and no netlist/DEF/SDC file is mutated.

    Side effects:
        Journals an observation through the shared helper. A bound adapter may
        additionally write scripts, netlists, SDC, DEF, or report artifacts.

    Failures:
        Bound adapters fail when required RTL, libraries, constraints, or physical
        inputs are missing or inconsistent; the unbound path returns ``not_run``.
    """
    # Assemble the observation payload from the explicit skill arguments.
    payload = {
        'summary': summary,  # One-sentence finding written into engineering memory for downstream agents.
        'evidence_refs': evidence_refs,  # Comma-separated artifact URIs that substantiate the finding or tradeoff.
        'severity': severity,  # Finding severity: low, medium, high, or critical relative to hard requirements.
        'recommended_recipient': recommended_recipient,  # Agent id that should act next on this finding.
    }
    # Merge optional adapter/planner overrides when the caller supplied params.
    if params:
        # params keys intentionally overwrite same-named explicit fields.
        payload.update(params)
    # Hand the `recommend_floorplan_candidate` operation to the shared observation helper for `floorplanning_lead`.
    return tool_observation(
        'recommend_floorplan_candidate',
        payload,
        agent_id='floorplanning_lead',
    )

# Register `request_floorplan_upstream_change` as an invocable skill: Publish evidence when pin density or hierarchy makes the floorplan infeasible.
@tool(description='Publish evidence when pin density or hierarchy makes the floorplan infeasible.')
def request_floorplan_upstream_change(
    summary: str = "",
    evidence_refs: str = "",
    severity: str = "",
    recommended_recipient: str = "",
    params: dict | None = None,
) -> dict:
    """Publish evidence when pin density or hierarchy makes the floorplan infeasible.

    Purpose:
        Publish evidence when pin density or hierarchy makes any legal floorplan infeasible.

    Args:
        summary: One-sentence finding written into engineering memory for downstream agents.
        evidence_refs: Comma-separated artifact URIs that substantiate the finding or tradeoff.
        severity: Finding severity: low, medium, high, or critical relative to hard requirements.
        recommended_recipient: Agent id that should act next on this finding.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `request_floorplan_upstream_change` operation for agent `floorplanning_lead`. When no EDA framework is
        bound, status is ``not_run`` and no netlist/DEF/SDC file is mutated.

    Side effects:
        Journals an observation through the shared helper. A bound adapter may
        additionally write scripts, netlists, SDC, DEF, or report artifacts.

    Failures:
        Bound adapters fail when required RTL, libraries, constraints, or physical
        inputs are missing or inconsistent; the unbound path returns ``not_run``.
    """
    # Assemble the observation payload from the explicit skill arguments.
    payload = {
        'summary': summary,  # One-sentence finding written into engineering memory for downstream agents.
        'evidence_refs': evidence_refs,  # Comma-separated artifact URIs that substantiate the finding or tradeoff.
        'severity': severity,  # Finding severity: low, medium, high, or critical relative to hard requirements.
        'recommended_recipient': recommended_recipient,  # Agent id that should act next on this finding.
    }
    # Merge optional adapter/planner overrides when the caller supplied params.
    if params:
        # params keys intentionally overwrite same-named explicit fields.
        payload.update(params)
    # Hand the `request_floorplan_upstream_change` operation to the shared observation helper for `floorplanning_lead`.
    return tool_observation(
        'request_floorplan_upstream_change',
        payload,
        agent_id='floorplanning_lead',
    )

# Register `flag_hard_physical_limit` as an invocable skill: Publish a candidate that breaks a keepout, pin-density, or IR limit.
@tool(description='Publish a candidate that breaks a keepout, pin-density, or IR limit.')
def flag_hard_physical_limit(
    summary: str = "",
    evidence_refs: str = "",
    severity: str = "",
    recommended_recipient: str = "",
    params: dict | None = None,
) -> dict:
    """Publish a candidate that breaks a keepout, pin-density, or IR limit.

    Purpose:
        Publish a candidate that breaks keepout, pin-density, or IR hard limits.

    Args:
        summary: One-sentence finding written into engineering memory for downstream agents.
        evidence_refs: Comma-separated artifact URIs that substantiate the finding or tradeoff.
        severity: Finding severity: low, medium, high, or critical relative to hard requirements.
        recommended_recipient: Agent id that should act next on this finding.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `flag_hard_physical_limit` operation for agent `floorplanning_lead`. When no EDA framework is
        bound, status is ``not_run`` and no netlist/DEF/SDC file is mutated.

    Side effects:
        Journals an observation through the shared helper. A bound adapter may
        additionally write scripts, netlists, SDC, DEF, or report artifacts.

    Failures:
        Bound adapters fail when required RTL, libraries, constraints, or physical
        inputs are missing or inconsistent; the unbound path returns ``not_run``.
    """
    # Assemble the observation payload from the explicit skill arguments.
    payload = {
        'summary': summary,  # One-sentence finding written into engineering memory for downstream agents.
        'evidence_refs': evidence_refs,  # Comma-separated artifact URIs that substantiate the finding or tradeoff.
        'severity': severity,  # Finding severity: low, medium, high, or critical relative to hard requirements.
        'recommended_recipient': recommended_recipient,  # Agent id that should act next on this finding.
    }
    # Merge optional adapter/planner overrides when the caller supplied params.
    if params:
        # params keys intentionally overwrite same-named explicit fields.
        payload.update(params)
    # Hand the `flag_hard_physical_limit` operation to the shared observation helper for `floorplanning_lead`.
    return tool_observation(
        'flag_hard_physical_limit',
        payload,
        agent_id='floorplanning_lead',
    )

# Register `record_floorplan_strategy` as an invocable skill: Record which physical variable the next batch will change.
@tool(description='Record which physical variable the next batch will change.')
def record_floorplan_strategy(
    summary: str = "",
    evidence_refs: str = "",
    severity: str = "",
    recommended_recipient: str = "",
    params: dict | None = None,
) -> dict:
    """Record which physical variable the next batch will change.

    Purpose:
        Record which physical variable (macro pitch, pin edge, strap pitch) the next batch changes.

    Args:
        summary: One-sentence finding written into engineering memory for downstream agents.
        evidence_refs: Comma-separated artifact URIs that substantiate the finding or tradeoff.
        severity: Finding severity: low, medium, high, or critical relative to hard requirements.
        recommended_recipient: Agent id that should act next on this finding.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `record_floorplan_strategy` operation for agent `floorplanning_lead`. When no EDA framework is
        bound, status is ``not_run`` and no netlist/DEF/SDC file is mutated.

    Side effects:
        Journals an observation through the shared helper. A bound adapter may
        additionally write scripts, netlists, SDC, DEF, or report artifacts.

    Failures:
        Bound adapters fail when required RTL, libraries, constraints, or physical
        inputs are missing or inconsistent; the unbound path returns ``not_run``.
    """
    # Assemble the observation payload from the explicit skill arguments.
    payload = {
        'summary': summary,  # One-sentence finding written into engineering memory for downstream agents.
        'evidence_refs': evidence_refs,  # Comma-separated artifact URIs that substantiate the finding or tradeoff.
        'severity': severity,  # Finding severity: low, medium, high, or critical relative to hard requirements.
        'recommended_recipient': recommended_recipient,  # Agent id that should act next on this finding.
    }
    # Merge optional adapter/planner overrides when the caller supplied params.
    if params:
        # params keys intentionally overwrite same-named explicit fields.
        payload.update(params)
    # Hand the `record_floorplan_strategy` operation to the shared observation helper for `floorplanning_lead`.
    return tool_observation(
        'record_floorplan_strategy',
        payload,
        agent_id='floorplanning_lead',
    )

# Register `request_floorplan_decision` as an invocable skill: Ask a human to choose among feasible floorplans or to change an upstream contract.
@tool(description='Ask a human to choose among feasible floorplans or to change an upstream contract.')
def request_floorplan_decision(
    decision: str = "",
    options: str = "",
    evidence_refs: str = "",
    deadline: str = "",
    params: dict | None = None,
) -> dict:
    """Ask a human to choose among feasible floorplans or to change an upstream contract.

    Purpose:
        Ask a human to pick among feasible floorplans or to change an upstream contract.

    Args:
        decision: The human choice that must be made (e.g. which feasible netlist or floorplan).
        options: Comma-separated feasible options presented to the human decision queue.
        evidence_refs: Comma-separated artifact URIs that substantiate the finding or tradeoff.
        deadline: ISO-8601 timestamp after which the undecided choice blocks the schedule.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `request_floorplan_decision` operation for agent `floorplanning_lead`. When no EDA framework is
        bound, status is ``not_run`` and no netlist/DEF/SDC file is mutated.

    Side effects:
        Journals an observation through the shared helper. A bound adapter may
        additionally write scripts, netlists, SDC, DEF, or report artifacts.

    Failures:
        Bound adapters fail when required RTL, libraries, constraints, or physical
        inputs are missing or inconsistent; the unbound path returns ``not_run``.
    """
    # Assemble the observation payload from the explicit skill arguments.
    payload = {
        'decision': decision,  # The human choice that must be made (e.g. which feasible netlist or floorplan).
        'options': options,  # Comma-separated feasible options presented to the human decision queue.
        'evidence_refs': evidence_refs,  # Comma-separated artifact URIs that substantiate the finding or tradeoff.
        'deadline': deadline,  # ISO-8601 timestamp after which the undecided choice blocks the schedule.
    }
    # Merge optional adapter/planner overrides when the caller supplied params.
    if params:
        # params keys intentionally overwrite same-named explicit fields.
        payload.update(params)
    # Hand the `request_floorplan_decision` operation to the shared observation helper for `floorplanning_lead`.
    return tool_observation(
        'request_floorplan_decision',
        payload,
        agent_id='floorplanning_lead',
    )
