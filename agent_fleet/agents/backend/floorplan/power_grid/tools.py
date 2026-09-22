"""Tools for Power-Grid.

Each function below is the stable operation contract for this agent. A framework
adapter (Yosys, OpenROAD, OpenSTA, or a licensed tool) is responsible for actually
performing the EDA work. Until a framework is bound through ``EDA_FRAMEWORK`` /
backend.type, every call returns a structured observation with status ``not_run``
and must not invoke a synthesizer, placer, router, equivalence engine, or simulator.

EDA focus for this tool module: PDN design: rings, straps, standard-cell rails, vias, and macro power connections against IR-drop, electromigration (EM), and routing-resource budgets. Adapter target: OpenROAD pdngen. Early IR/EM proxies guide strap pitch before signoff analysis.

Common return shape:
    ``tool_observation(name, payload, agent_id="power_grid")`` builds the dict the
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


# Register `read_power_domains` as an invocable skill: Read domains, supplies, and macro power pins.
@tool(description='Read domains, supplies, and macro power pins.')
def read_power_domains(
    candidate_ref: str = "",
    report_ref: str = "",
    corner: str = "",
    mode: str = "",
    params: dict | None = None,
) -> dict:
    """Read domains, supplies, and macro power pins.

    Purpose:
        Read power domains, supplies, and macro power pin names for PDN construction.

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        report_ref: Artifact URI of a specific report; empty selects the latest report for the candidate.
        corner: Process/voltage/temperature corner filter (e.g. SS/FF); empty reads every available corner.
        mode: Operating mode filter (functional, scan, etc.); empty reads every available mode.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `read_power_domains` operation for agent `power_grid`. When no EDA framework is
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
    # Hand the `read_power_domains` operation to the shared observation helper for `power_grid`.
    return tool_observation(
        'read_power_domains',
        payload,
        agent_id='power_grid',
    )

# Register `read_current_budget` as an invocable skill: Read the activity assumption and current budget.
@tool(description='Read the activity assumption and current budget.')
def read_current_budget(
    candidate_ref: str = "",
    report_ref: str = "",
    corner: str = "",
    mode: str = "",
    params: dict | None = None,
) -> dict:
    """Read the activity assumption and current budget.

    Purpose:
        Read activity assumption and current budget used for IR/EM proxies.

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        report_ref: Artifact URI of a specific report; empty selects the latest report for the candidate.
        corner: Process/voltage/temperature corner filter (e.g. SS/FF); empty reads every available corner.
        mode: Operating mode filter (functional, scan, etc.); empty reads every available mode.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `read_current_budget` operation for agent `power_grid`. When no EDA framework is
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
    # Hand the `read_current_budget` operation to the shared observation helper for `power_grid`.
    return tool_observation(
        'read_current_budget',
        payload,
        agent_id='power_grid',
    )

# Register `write_pdn_spec` as an invocable skill: Write the power-grid specification for rings, straps, rails, and vias.
@tool(description='Write the power-grid specification for rings, straps, rails, and vias.')
def write_pdn_spec(
    candidate_ref: str = "",
    baseline_ref: str = "",
    hypothesis: str = "",
    params: dict | None = None,
) -> dict:
    """Write the power-grid specification for rings, straps, rails, and vias.

    Purpose:
        Write the PDN specification for rings, straps, rails, and via stacks.

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        baseline_ref: Artifact URI of the baseline netlist/design used for QoR or structural diffs.
        hypothesis: Single synthesis knob or setting this isolated experiment changes versus the baseline.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `write_pdn_spec` operation for agent `power_grid`. When no EDA framework is
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
        'baseline_ref': baseline_ref,  # Artifact URI of the baseline netlist/design used for QoR or structural diffs.
        'hypothesis': hypothesis,  # Single synthesis knob or setting this isolated experiment changes versus the baseline.
    }
    # Merge optional adapter/planner overrides when the caller supplied params.
    if params:
        # params keys intentionally overwrite same-named explicit fields.
        payload.update(params)
    # Hand the `write_pdn_spec` operation to the shared observation helper for `power_grid`.
    return tool_observation(
        'write_pdn_spec',
        payload,
        agent_id='power_grid',
    )

# Register `propose_power_grid` as an invocable skill: Build rings, straps, rails, and macro connections. Adapter target: OpenROAD pdngen.
@tool(description='Build rings, straps, rails, and macro connections. Adapter target: OpenROAD pdngen.')
def propose_power_grid(
    candidate_ref: str = "",
    baseline_ref: str = "",
    hypothesis: str = "",
    params: dict | None = None,
) -> dict:
    """Build rings, straps, rails, and macro connections. Adapter target: OpenROAD pdngen.

    Purpose:
        Build rings, straps, rails, and macro connections (OpenROAD pdngen).

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        baseline_ref: Artifact URI of the baseline netlist/design used for QoR or structural diffs.
        hypothesis: Single synthesis knob or setting this isolated experiment changes versus the baseline.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `propose_power_grid` operation for agent `power_grid`. When no EDA framework is
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
        'baseline_ref': baseline_ref,  # Artifact URI of the baseline netlist/design used for QoR or structural diffs.
        'hypothesis': hypothesis,  # Single synthesis knob or setting this isolated experiment changes versus the baseline.
    }
    # Merge optional adapter/planner overrides when the caller supplied params.
    if params:
        # params keys intentionally overwrite same-named explicit fields.
        payload.update(params)
    # Hand the `propose_power_grid` operation to the shared observation helper for `power_grid`.
    return tool_observation(
        'propose_power_grid',
        payload,
        agent_id='power_grid',
    )

# Register `add_power_ring` as an invocable skill: Add a core or domain ring.
@tool(description='Add a core or domain ring.')
def add_power_ring(
    candidate_ref: str = "",
    baseline_ref: str = "",
    hypothesis: str = "",
    params: dict | None = None,
) -> dict:
    """Add a core or domain ring.

    Purpose:
        Add a core or domain power/ground ring on specified layers.

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        baseline_ref: Artifact URI of the baseline netlist/design used for QoR or structural diffs.
        hypothesis: Single synthesis knob or setting this isolated experiment changes versus the baseline.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `add_power_ring` operation for agent `power_grid`. When no EDA framework is
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
        'baseline_ref': baseline_ref,  # Artifact URI of the baseline netlist/design used for QoR or structural diffs.
        'hypothesis': hypothesis,  # Single synthesis knob or setting this isolated experiment changes versus the baseline.
    }
    # Merge optional adapter/planner overrides when the caller supplied params.
    if params:
        # params keys intentionally overwrite same-named explicit fields.
        payload.update(params)
    # Hand the `add_power_ring` operation to the shared observation helper for `power_grid`.
    return tool_observation(
        'add_power_ring',
        payload,
        agent_id='power_grid',
    )

# Register `add_power_straps` as an invocable skill: Add straps on a named layer and pitch.
@tool(description='Add straps on a named layer and pitch.')
def add_power_straps(
    candidate_ref: str = "",
    baseline_ref: str = "",
    hypothesis: str = "",
    layer: str = "",
    pitch_microns: str = "",
    params: dict | None = None,
) -> dict:
    """Add straps on a named layer and pitch.

    Purpose:
        Add power straps on a named layer at a given pitch.

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        baseline_ref: Artifact URI of the baseline netlist/design used for QoR or structural diffs.
        hypothesis: Single synthesis knob or setting this isolated experiment changes versus the baseline.
        layer: Routing metal layer for a pin or power strap.
        pitch_microns: `pitch microns` for the `add_power_straps` operation in this agent's EDA contract; forwarded into the observation payload for the bound framework adapter.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `add_power_straps` operation for agent `power_grid`. When no EDA framework is
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
        'baseline_ref': baseline_ref,  # Artifact URI of the baseline netlist/design used for QoR or structural diffs.
        'hypothesis': hypothesis,  # Single synthesis knob or setting this isolated experiment changes versus the baseline.
        'layer': layer,  # Routing metal layer for a pin or power strap.
        'pitch_microns': pitch_microns,  # `pitch microns` for the `add_power_straps` operation in this agent's EDA contract; forwarded into the observation payload for the bound framework adapter.
    }
    # Merge optional adapter/planner overrides when the caller supplied params.
    if params:
        # params keys intentionally overwrite same-named explicit fields.
        payload.update(params)
    # Hand the `add_power_straps` operation to the shared observation helper for `power_grid`.
    return tool_observation(
        'add_power_straps',
        payload,
        agent_id='power_grid',
    )

# Register `add_rails` as an invocable skill: Add standard-cell rails.
@tool(description='Add standard-cell rails.')
def add_rails(
    candidate_ref: str = "",
    baseline_ref: str = "",
    hypothesis: str = "",
    params: dict | None = None,
) -> dict:
    """Add standard-cell rails.

    Purpose:
        Add standard-cell power/ground rails tied to the strap grid.

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        baseline_ref: Artifact URI of the baseline netlist/design used for QoR or structural diffs.
        hypothesis: Single synthesis knob or setting this isolated experiment changes versus the baseline.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `add_rails` operation for agent `power_grid`. When no EDA framework is
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
        'baseline_ref': baseline_ref,  # Artifact URI of the baseline netlist/design used for QoR or structural diffs.
        'hypothesis': hypothesis,  # Single synthesis knob or setting this isolated experiment changes versus the baseline.
    }
    # Merge optional adapter/planner overrides when the caller supplied params.
    if params:
        # params keys intentionally overwrite same-named explicit fields.
        payload.update(params)
    # Hand the `add_rails` operation to the shared observation helper for `power_grid`.
    return tool_observation(
        'add_rails',
        payload,
        agent_id='power_grid',
    )

# Register `connect_macro_power` as an invocable skill: Connect macro power pins to the grid.
@tool(description='Connect macro power pins to the grid.')
def connect_macro_power(
    candidate_ref: str = "",
    baseline_ref: str = "",
    hypothesis: str = "",
    params: dict | None = None,
) -> dict:
    """Connect macro power pins to the grid.

    Purpose:
        Connect macro power pins into the PDN so macros are not floating supplies.

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        baseline_ref: Artifact URI of the baseline netlist/design used for QoR or structural diffs.
        hypothesis: Single synthesis knob or setting this isolated experiment changes versus the baseline.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `connect_macro_power` operation for agent `power_grid`. When no EDA framework is
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
        'baseline_ref': baseline_ref,  # Artifact URI of the baseline netlist/design used for QoR or structural diffs.
        'hypothesis': hypothesis,  # Single synthesis knob or setting this isolated experiment changes versus the baseline.
    }
    # Merge optional adapter/planner overrides when the caller supplied params.
    if params:
        # params keys intentionally overwrite same-named explicit fields.
        payload.update(params)
    # Hand the `connect_macro_power` operation to the shared observation helper for `power_grid`.
    return tool_observation(
        'connect_macro_power',
        payload,
        agent_id='power_grid',
    )

# Register `write_pdn_def` as an invocable skill: Write the power-grid geometry into the candidate.
@tool(description='Write the power-grid geometry into the candidate.')
def write_pdn_def(
    candidate_ref: str = "",
    baseline_ref: str = "",
    hypothesis: str = "",
    params: dict | None = None,
) -> dict:
    """Write the power-grid geometry into the candidate.

    Purpose:
        Write power-grid geometry into the candidate DEF/LEF views.

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        baseline_ref: Artifact URI of the baseline netlist/design used for QoR or structural diffs.
        hypothesis: Single synthesis knob or setting this isolated experiment changes versus the baseline.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `write_pdn_def` operation for agent `power_grid`. When no EDA framework is
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
        'baseline_ref': baseline_ref,  # Artifact URI of the baseline netlist/design used for QoR or structural diffs.
        'hypothesis': hypothesis,  # Single synthesis knob or setting this isolated experiment changes versus the baseline.
    }
    # Merge optional adapter/planner overrides when the caller supplied params.
    if params:
        # params keys intentionally overwrite same-named explicit fields.
        payload.update(params)
    # Hand the `write_pdn_def` operation to the shared observation helper for `power_grid`.
    return tool_observation(
        'write_pdn_def',
        payload,
        agent_id='power_grid',
    )

# Register `evaluate_ir_em_proxy` as an invocable skill: Estimate IR drop and electromigration against the activity assumption.
@tool(description='Estimate IR drop and electromigration against the activity assumption.')
def evaluate_ir_em_proxy(
    candidate_ref: str = "",
    baseline_ref: str = "",
    recipe: str = "",
    corner: str = "",
    mode: str = "",
    params: dict | None = None,
) -> dict:
    """Estimate IR drop and electromigration against the activity assumption.

    Purpose:
        Estimate IR drop and electromigration risk under the activity assumption (not signoff).

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        baseline_ref: Artifact URI of the baseline netlist/design used for QoR or structural diffs.
        recipe: `recipe` for the `evaluate_ir_em_proxy` operation in this agent's EDA contract; forwarded into the observation payload for the bound framework adapter.
        corner: Process/voltage/temperature corner filter (e.g. SS/FF); empty reads every available corner.
        mode: Operating mode filter (functional, scan, etc.); empty reads every available mode.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `evaluate_ir_em_proxy` operation for agent `power_grid`. When no EDA framework is
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
        'baseline_ref': baseline_ref,  # Artifact URI of the baseline netlist/design used for QoR or structural diffs.
        'recipe': recipe,  # `recipe` for the `evaluate_ir_em_proxy` operation in this agent's EDA contract; forwarded into the observation payload for the bound framework adapter.
        'corner': corner,  # Process/voltage/temperature corner filter (e.g. SS/FF); empty reads every available corner.
        'mode': mode,  # Operating mode filter (functional, scan, etc.); empty reads every available mode.
    }
    # Merge optional adapter/planner overrides when the caller supplied params.
    if params:
        # params keys intentionally overwrite same-named explicit fields.
        payload.update(params)
    # Hand the `evaluate_ir_em_proxy` operation to the shared observation helper for `power_grid`.
    return tool_observation(
        'evaluate_ir_em_proxy',
        payload,
        agent_id='power_grid',
    )

# Register `estimate_grid_routing_resource` as an invocable skill: Estimate the tracks the grid consumes.
@tool(description='Estimate the tracks the grid consumes.')
def estimate_grid_routing_resource(
    candidate_ref: str = "",
    report_ref: str = "",
    corner: str = "",
    mode: str = "",
    params: dict | None = None,
) -> dict:
    """Estimate the tracks the grid consumes.

    Purpose:
        Estimate routing tracks consumed by straps/rings that placement/route must avoid.

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        report_ref: Artifact URI of a specific report; empty selects the latest report for the candidate.
        corner: Process/voltage/temperature corner filter (e.g. SS/FF); empty reads every available corner.
        mode: Operating mode filter (functional, scan, etc.); empty reads every available mode.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `estimate_grid_routing_resource` operation for agent `power_grid`. When no EDA framework is
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
    # Hand the `estimate_grid_routing_resource` operation to the shared observation helper for `power_grid`.
    return tool_observation(
        'estimate_grid_routing_resource',
        payload,
        agent_id='power_grid',
    )

# Register `flag_ir_over_budget` as an invocable skill: Publish a region whose IR proxy exceeds the budget.
@tool(description='Publish a region whose IR proxy exceeds the budget.')
def flag_ir_over_budget(
    summary: str = "",
    evidence_refs: str = "",
    severity: str = "",
    recommended_recipient: str = "",
    params: dict | None = None,
) -> dict:
    """Publish a region whose IR proxy exceeds the budget.

    Purpose:
        Publish a region whose IR proxy exceeds the current budget.

    Args:
        summary: One-sentence finding written into engineering memory for downstream agents.
        evidence_refs: Comma-separated artifact URIs that substantiate the finding or tradeoff.
        severity: Finding severity: low, medium, high, or critical relative to hard requirements.
        recommended_recipient: Agent id that should act next on this finding.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `flag_ir_over_budget` operation for agent `power_grid`. When no EDA framework is
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
    # Hand the `flag_ir_over_budget` operation to the shared observation helper for `power_grid`.
    return tool_observation(
        'flag_ir_over_budget',
        payload,
        agent_id='power_grid',
    )

# Register `flag_strap_congestion_tradeoff` as an invocable skill: Publish a strap removal and the IR impact that must be accepted with it.
@tool(description='Publish a strap removal and the IR impact that must be accepted with it.')
def flag_strap_congestion_tradeoff(
    summary: str = "",
    evidence_refs: str = "",
    severity: str = "",
    recommended_recipient: str = "",
    params: dict | None = None,
) -> dict:
    """Publish a strap removal and the IR impact that must be accepted with it.

    Purpose:
        Publish a proposed strap removal and the IR impact that must be accepted with it.

    Args:
        summary: One-sentence finding written into engineering memory for downstream agents.
        evidence_refs: Comma-separated artifact URIs that substantiate the finding or tradeoff.
        severity: Finding severity: low, medium, high, or critical relative to hard requirements.
        recommended_recipient: Agent id that should act next on this finding.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `flag_strap_congestion_tradeoff` operation for agent `power_grid`. When no EDA framework is
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
    # Hand the `flag_strap_congestion_tradeoff` operation to the shared observation helper for `power_grid`.
    return tool_observation(
        'flag_strap_congestion_tradeoff',
        payload,
        agent_id='power_grid',
    )

# Register `record_pdn_recipe` as an invocable skill: Record the PDN spec, pitch, and activity file.
@tool(description='Record the PDN spec, pitch, and activity file.')
def record_pdn_recipe(
    summary: str = "",
    evidence_refs: str = "",
    severity: str = "",
    recommended_recipient: str = "",
    params: dict | None = None,
) -> dict:
    """Record the PDN spec, pitch, and activity file.

    Purpose:
        Record PDN spec, strap pitch, and activity file for reproducibility.

    Args:
        summary: One-sentence finding written into engineering memory for downstream agents.
        evidence_refs: Comma-separated artifact URIs that substantiate the finding or tradeoff.
        severity: Finding severity: low, medium, high, or critical relative to hard requirements.
        recommended_recipient: Agent id that should act next on this finding.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `record_pdn_recipe` operation for agent `power_grid`. When no EDA framework is
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
    # Hand the `record_pdn_recipe` operation to the shared observation helper for `power_grid`.
    return tool_observation(
        'record_pdn_recipe',
        payload,
        agent_id='power_grid',
    )
