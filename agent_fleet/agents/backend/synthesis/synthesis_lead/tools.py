"""Tools for Synthesis Lead.

Each function below is the stable operation contract for this agent. A framework
adapter (Yosys, OpenROAD, OpenSTA, or a licensed tool) is responsible for actually
performing the EDA work. Until a framework is bound through ``EDA_FRAMEWORK`` /
backend.type, every call returns a structured observation with status ``not_run``
and must not invoke a synthesizer, placer, router, equivalence engine, or simulator.

EDA focus for this tool module: RTL-to-gate synthesis orchestration: constraints, experiment hypotheses, retiming studies, logical/sequential equivalence, and netlist structural quality. PPA (power, performance, area) and equivalence acceptance decide which netlist may advance; failed equivalence always makes a candidate ineligible.

Common return shape:
    ``tool_observation(name, payload, agent_id="synthesis_lead")`` builds the dict the
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
from domains.eda.eda import tool_observation


# Register `plan_synthesis_experiments` as an invocable skill: Emit the synthesis and equivalence workflow.
@tool(description='Emit the synthesis and equivalence workflow.')
def plan_synthesis_experiments(
    objective: str = "",
    parent_task_id: str = "",
    scope_block: str = "",
    params: dict | None = None,
) -> dict:
    """Emit the synthesis and equivalence workflow.

    Purpose:
        Emit a dependency graph that sequences constraint audit, synthesis experiments, retiming, equivalence, and netlist quality for the block. Does not execute child tools.

    Args:
        objective: Natural-language outcome the child workflow or operation must achieve for this silicon task.
        parent_task_id: Identifier of the parent task that owns this child workflow in the fleet journal.
        scope_block: Hierarchical block name this work applies to; empty means the task's current block context.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `plan_synthesis_experiments` operation for agent `synthesis_lead`. When no EDA framework is
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
    # Hand the `plan_synthesis_experiments` operation to the shared observation helper for `synthesis_lead`.
    return tool_observation(
        'plan_synthesis_experiments',
        payload,
        agent_id='synthesis_lead',
    )

# Register `request_constraint_audit` as an invocable skill: Open constraint generation and audit before experiments run.
@tool(description='Open constraint generation and audit before experiments run.')
def request_constraint_audit(
    objective: str = "",
    parent_task_id: str = "",
    scope_block: str = "",
    params: dict | None = None,
) -> dict:
    """Open constraint generation and audit before experiments run.

    Purpose:
        Open constraint_generation so clocks, I/O delays, and exceptions exist and are justified before any compile burns license or CPU time on bad SDC.

    Args:
        objective: Natural-language outcome the child workflow or operation must achieve for this silicon task.
        parent_task_id: Identifier of the parent task that owns this child workflow in the fleet journal.
        scope_block: Hierarchical block name this work applies to; empty means the task's current block context.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `request_constraint_audit` operation for agent `synthesis_lead`. When no EDA framework is
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
    # Hand the `request_constraint_audit` operation to the shared observation helper for `synthesis_lead`.
    return tool_observation(
        'request_constraint_audit',
        payload,
        agent_id='synthesis_lead',
    )

# Register `request_synthesis_experiment` as an invocable skill: Open one isolated synthesis experiment with a named hypothesis.
@tool(description='Open one isolated synthesis experiment with a named hypothesis.')
def request_synthesis_experiment(
    objective: str = "",
    parent_task_id: str = "",
    scope_block: str = "",
    hypothesis: str = "",
    params: dict | None = None,
) -> dict:
    """Open one isolated synthesis experiment with a named hypothesis.

    Purpose:
        Spawn one synthesis_experiment worker with a single named hypothesis so QoR deltas are attributable to one knob (script, hierarchy, mapping effort).

    Args:
        objective: Natural-language outcome the child workflow or operation must achieve for this silicon task.
        parent_task_id: Identifier of the parent task that owns this child workflow in the fleet journal.
        scope_block: Hierarchical block name this work applies to; empty means the task's current block context.
        hypothesis: Single synthesis knob or setting this isolated experiment changes versus the baseline.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `request_synthesis_experiment` operation for agent `synthesis_lead`. When no EDA framework is
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
        'hypothesis': hypothesis,  # Single synthesis knob or setting this isolated experiment changes versus the baseline.
    }
    # Merge optional adapter/planner overrides when the caller supplied params.
    if params:
        # params keys intentionally overwrite same-named explicit fields.
        payload.update(params)
    # Hand the `request_synthesis_experiment` operation to the shared observation helper for `synthesis_lead`.
    return tool_observation(
        'request_synthesis_experiment',
        payload,
        agent_id='synthesis_lead',
    )

# Register `request_retiming_study` as an invocable skill: Open a state-preserving retiming or mapping study.
@tool(description='Open a state-preserving retiming or mapping study.')
def request_retiming_study(
    objective: str = "",
    parent_task_id: str = "",
    scope_block: str = "",
    params: dict | None = None,
) -> dict:
    """Open a state-preserving retiming or mapping study.

    Purpose:
        Open retiming_mapping to explore state-preserving register moves and remaps without changing architectural latency contracts.

    Args:
        objective: Natural-language outcome the child workflow or operation must achieve for this silicon task.
        parent_task_id: Identifier of the parent task that owns this child workflow in the fleet journal.
        scope_block: Hierarchical block name this work applies to; empty means the task's current block context.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `request_retiming_study` operation for agent `synthesis_lead`. When no EDA framework is
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
    # Hand the `request_retiming_study` operation to the shared observation helper for `synthesis_lead`.
    return tool_observation(
        'request_retiming_study',
        payload,
        agent_id='synthesis_lead',
    )

# Register `request_equivalence_check` as an invocable skill: Open equivalence between the RTL and a netlist candidate.
@tool(description='Open equivalence between the RTL and a netlist candidate.')
def request_equivalence_check(
    objective: str = "",
    parent_task_id: str = "",
    scope_block: str = "",
    params: dict | None = None,
) -> dict:
    """Open equivalence between the RTL and a netlist candidate.

    Purpose:
        Open equivalence so a netlist cannot advance on QoR alone; RTL-vs-netlist LEC/SEC must pass.

    Args:
        objective: Natural-language outcome the child workflow or operation must achieve for this silicon task.
        parent_task_id: Identifier of the parent task that owns this child workflow in the fleet journal.
        scope_block: Hierarchical block name this work applies to; empty means the task's current block context.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `request_equivalence_check` operation for agent `synthesis_lead`. When no EDA framework is
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
    # Hand the `request_equivalence_check` operation to the shared observation helper for `synthesis_lead`.
    return tool_observation(
        'request_equivalence_check',
        payload,
        agent_id='synthesis_lead',
    )

# Register `request_netlist_quality_audit` as an invocable skill: Open a structural quality audit of one netlist.
@tool(description='Open a structural quality audit of one netlist.')
def request_netlist_quality_audit(
    objective: str = "",
    parent_task_id: str = "",
    scope_block: str = "",
    params: dict | None = None,
) -> dict:
    """Open a structural quality audit of one netlist.

    Purpose:
        Open netlist_quality for structural defects (loops, fanout, DFT loss) that QoR summaries miss.

    Args:
        objective: Natural-language outcome the child workflow or operation must achieve for this silicon task.
        parent_task_id: Identifier of the parent task that owns this child workflow in the fleet journal.
        scope_block: Hierarchical block name this work applies to; empty means the task's current block context.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `request_netlist_quality_audit` operation for agent `synthesis_lead`. When no EDA framework is
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
    # Hand the `request_netlist_quality_audit` operation to the shared observation helper for `synthesis_lead`.
    return tool_observation(
        'request_netlist_quality_audit',
        payload,
        agent_id='synthesis_lead',
    )

# Register `read_synthesis_acceptance` as an invocable skill: Read the PPA and equivalence criteria for this block.
@tool(description='Read the PPA and equivalence criteria for this block.')
def read_synthesis_acceptance(
    candidate_ref: str = "",
    report_ref: str = "",
    corner: str = "",
    mode: str = "",
    params: dict | None = None,
) -> dict:
    """Read the PPA and equivalence criteria for this block.

    Purpose:
        Load PPA targets and the hard rule that failed equivalence makes a candidate ineligible.

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        report_ref: Artifact URI of a specific report; empty selects the latest report for the candidate.
        corner: Process/voltage/temperature corner filter (e.g. SS/FF); empty reads every available corner.
        mode: Operating mode filter (functional, scan, etc.); empty reads every available mode.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `read_synthesis_acceptance` operation for agent `synthesis_lead`. When no EDA framework is
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
    # Hand the `read_synthesis_acceptance` operation to the shared observation helper for `synthesis_lead`.
    return tool_observation(
        'read_synthesis_acceptance',
        payload,
        agent_id='synthesis_lead',
    )

# Register `read_experiment_qor` as an invocable skill: Read QoR for every experiment against the same baseline.
@tool(description='Read QoR for every experiment against the same baseline.')
def read_experiment_qor(
    candidate_ref: str = "",
    report_ref: str = "",
    corner: str = "",
    mode: str = "",
    params: dict | None = None,
) -> dict:
    """Read QoR for every experiment against the same baseline.

    Purpose:
        Compare timing/area/power/runtime of every experiment against the same baseline netlist.

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        report_ref: Artifact URI of a specific report; empty selects the latest report for the candidate.
        corner: Process/voltage/temperature corner filter (e.g. SS/FF); empty reads every available corner.
        mode: Operating mode filter (functional, scan, etc.); empty reads every available mode.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `read_experiment_qor` operation for agent `synthesis_lead`. When no EDA framework is
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
    # Hand the `read_experiment_qor` operation to the shared observation helper for `synthesis_lead`.
    return tool_observation(
        'read_experiment_qor',
        payload,
        agent_id='synthesis_lead',
    )

# Register `read_equivalence_status` as an invocable skill: Read whether each netlist passed equivalence.
@tool(description='Read whether each netlist passed equivalence.')
def read_equivalence_status(
    candidate_ref: str = "",
    report_ref: str = "",
    corner: str = "",
    mode: str = "",
    params: dict | None = None,
) -> dict:
    """Read whether each netlist passed equivalence.

    Purpose:
        Read pass/fail (and setup-vs-functional) status for each candidate's equivalence job.

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        report_ref: Artifact URI of a specific report; empty selects the latest report for the candidate.
        corner: Process/voltage/temperature corner filter (e.g. SS/FF); empty reads every available corner.
        mode: Operating mode filter (functional, scan, etc.); empty reads every available mode.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `read_equivalence_status` operation for agent `synthesis_lead`. When no EDA framework is
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
    # Hand the `read_equivalence_status` operation to the shared observation helper for `synthesis_lead`.
    return tool_observation(
        'read_equivalence_status',
        payload,
        agent_id='synthesis_lead',
    )

# Register `compare_synthesis_candidates` as an invocable skill: Rank candidates on timing, area, power, and runtime. A failed equivalence check stays ineligible.
@tool(description='Rank candidates on timing, area, power, and runtime. A failed equivalence check stays ineligible.')
def compare_synthesis_candidates(
    candidate_ref: str = "",
    report_ref: str = "",
    corner: str = "",
    mode: str = "",
    params: dict | None = None,
) -> dict:
    """Rank candidates on timing, area, power, and runtime. A failed equivalence check stays ineligible.

    Purpose:
        Rank only equivalence-passing candidates on timing, area, power, and runtime.

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        report_ref: Artifact URI of a specific report; empty selects the latest report for the candidate.
        corner: Process/voltage/temperature corner filter (e.g. SS/FF); empty reads every available corner.
        mode: Operating mode filter (functional, scan, etc.); empty reads every available mode.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `compare_synthesis_candidates` operation for agent `synthesis_lead`. When no EDA framework is
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
    # Hand the `compare_synthesis_candidates` operation to the shared observation helper for `synthesis_lead`.
    return tool_observation(
        'compare_synthesis_candidates',
        payload,
        agent_id='synthesis_lead',
    )

# Register `recommend_netlist_candidate` as an invocable skill: Record which experiment should advance, with its QoR and equivalence status. This does not promote it.
@tool(description='Record which experiment should advance, with its QoR and equivalence status. This does not promote it.')
def recommend_netlist_candidate(
    summary: str = "",
    evidence_refs: str = "",
    severity: str = "",
    recommended_recipient: str = "",
    params: dict | None = None,
) -> dict:
    """Record which experiment should advance, with its QoR and equivalence status. This does not promote it.

    Purpose:
        Journal which experiment should advance with QoR and equivalence evidence; does not promote.

    Args:
        summary: One-sentence finding written into engineering memory for downstream agents.
        evidence_refs: Comma-separated artifact URIs that substantiate the finding or tradeoff.
        severity: Finding severity: low, medium, high, or critical relative to hard requirements.
        recommended_recipient: Agent id that should act next on this finding.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `recommend_netlist_candidate` operation for agent `synthesis_lead`. When no EDA framework is
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
    # Hand the `recommend_netlist_candidate` operation to the shared observation helper for `synthesis_lead`.
    return tool_observation(
        'recommend_netlist_candidate',
        payload,
        agent_id='synthesis_lead',
    )

# Register `flag_ineligible_netlist` as an invocable skill: Publish a netlist that improved QoR and failed equivalence or a hard constraint.
@tool(description='Publish a netlist that improved QoR and failed equivalence or a hard constraint.')
def flag_ineligible_netlist(
    summary: str = "",
    evidence_refs: str = "",
    severity: str = "",
    recommended_recipient: str = "",
    params: dict | None = None,
) -> dict:
    """Publish a netlist that improved QoR and failed equivalence or a hard constraint.

    Purpose:
        Publish a candidate that looked better on QoR but failed equivalence or a hard constraint.

    Args:
        summary: One-sentence finding written into engineering memory for downstream agents.
        evidence_refs: Comma-separated artifact URIs that substantiate the finding or tradeoff.
        severity: Finding severity: low, medium, high, or critical relative to hard requirements.
        recommended_recipient: Agent id that should act next on this finding.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `flag_ineligible_netlist` operation for agent `synthesis_lead`. When no EDA framework is
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
    # Hand the `flag_ineligible_netlist` operation to the shared observation helper for `synthesis_lead`.
    return tool_observation(
        'flag_ineligible_netlist',
        payload,
        agent_id='synthesis_lead',
    )

# Register `record_synthesis_strategy` as an invocable skill: Record which knobs the next experiment batch will change.
@tool(description='Record which knobs the next experiment batch will change.')
def record_synthesis_strategy(
    summary: str = "",
    evidence_refs: str = "",
    severity: str = "",
    recommended_recipient: str = "",
    params: dict | None = None,
) -> dict:
    """Record which knobs the next experiment batch will change.

    Purpose:
        Record which synthesis knobs the next experiment batch will sweep.

    Args:
        summary: One-sentence finding written into engineering memory for downstream agents.
        evidence_refs: Comma-separated artifact URIs that substantiate the finding or tradeoff.
        severity: Finding severity: low, medium, high, or critical relative to hard requirements.
        recommended_recipient: Agent id that should act next on this finding.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `record_synthesis_strategy` operation for agent `synthesis_lead`. When no EDA framework is
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
    # Hand the `record_synthesis_strategy` operation to the shared observation helper for `synthesis_lead`.
    return tool_observation(
        'record_synthesis_strategy',
        payload,
        agent_id='synthesis_lead',
    )

# Register `request_netlist_decision` as an invocable skill: Ask a human to choose among feasible netlists.
@tool(description='Ask a human to choose among feasible netlists.')
def request_netlist_decision(
    decision: str = "",
    options: str = "",
    evidence_refs: str = "",
    deadline: str = "",
    params: dict | None = None,
) -> dict:
    """Ask a human to choose among feasible netlists.

    Purpose:
        Escalate to a human when two or more netlists remain feasible under acceptance criteria.

    Args:
        decision: The human choice that must be made (e.g. which feasible netlist or floorplan).
        options: Comma-separated feasible options presented to the human decision queue.
        evidence_refs: Comma-separated artifact URIs that substantiate the finding or tradeoff.
        deadline: ISO-8601 timestamp after which the undecided choice blocks the schedule.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `request_netlist_decision` operation for agent `synthesis_lead`. When no EDA framework is
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
    # Hand the `request_netlist_decision` operation to the shared observation helper for `synthesis_lead`.
    return tool_observation(
        'request_netlist_decision',
        payload,
        agent_id='synthesis_lead',
    )
