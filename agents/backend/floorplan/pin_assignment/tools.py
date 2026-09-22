"""Tools for Pin-Assignment.

Each function below is the stable operation contract for this agent. A framework
adapter (Yosys, OpenROAD, OpenSTA, or a licensed tool) is responsible for actually
performing the EDA work. Until a framework is bound through ``EDA_FRAMEWORK`` /
backend.type, every call returns a structured observation with status ``not_run``
and must not invoke a synthesizer, placer, router, equivalence engine, or simulator.

EDA focus for this tool module: Block pin locations, metal layers, bus ordering, and legal feedthroughs against package/bump contracts and edge track capacity. Adapter target: OpenROAD place_pins. Pin density violations create unroutable boundaries and package mismatches.

Common return shape:
    ``tool_observation(name, payload, agent_id="pin_assignment")`` builds the dict the
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


# Register `read_pin_contract` as an invocable skill: Read interface, package, and bump constraints for this block.
@tool(description='Read interface, package, and bump constraints for this block.')
def read_pin_contract(
    candidate_ref: str = "",
    report_ref: str = "",
    corner: str = "",
    mode: str = "",
    params: dict | None = None,
) -> dict:
    """Read interface, package, and bump constraints for this block.

    Purpose:
        Read interface, package, and bump constraints that legally bound pin placement.

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        report_ref: Artifact URI of a specific report; empty selects the latest report for the candidate.
        corner: Process/voltage/temperature corner filter (e.g. SS/FF); empty reads every available corner.
        mode: Operating mode filter (functional, scan, etc.); empty reads every available mode.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `read_pin_contract` operation for agent `pin_assignment`. When no EDA framework is
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
    # Hand the `read_pin_contract` operation to the shared observation helper for `pin_assignment`.
    return tool_observation(
        'read_pin_contract',
        payload,
        agent_id='pin_assignment',
    )

# Register `read_edge_capacity` as an invocable skill: Read legal layers and track capacity on each edge.
@tool(description='Read legal layers and track capacity on each edge.')
def read_edge_capacity(
    candidate_ref: str = "",
    report_ref: str = "",
    corner: str = "",
    mode: str = "",
    params: dict | None = None,
) -> dict:
    """Read legal layers and track capacity on each edge.

    Purpose:
        Read legal layers and track capacity on each die edge.

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        report_ref: Artifact URI of a specific report; empty selects the latest report for the candidate.
        corner: Process/voltage/temperature corner filter (e.g. SS/FF); empty reads every available corner.
        mode: Operating mode filter (functional, scan, etc.); empty reads every available mode.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `read_edge_capacity` operation for agent `pin_assignment`. When no EDA framework is
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
    # Hand the `read_edge_capacity` operation to the shared observation helper for `pin_assignment`.
    return tool_observation(
        'read_edge_capacity',
        payload,
        agent_id='pin_assignment',
    )

# Register `assign_pins` as an invocable skill: Assign block pin locations, layers, and order. Adapter target: OpenROAD place_pins.
@tool(description='Assign block pin locations, layers, and order. Adapter target: OpenROAD place_pins.')
def assign_pins(
    candidate_ref: str = "",
    baseline_ref: str = "",
    hypothesis: str = "",
    params: dict | None = None,
) -> dict:
    """Assign block pin locations, layers, and order. Adapter target: OpenROAD place_pins.

    Purpose:
        Assign block pin locations, layers, and order (OpenROAD place_pins).

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        baseline_ref: Artifact URI of the baseline netlist/design used for QoR or structural diffs.
        hypothesis: Single synthesis knob or setting this isolated experiment changes versus the baseline.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `assign_pins` operation for agent `pin_assignment`. When no EDA framework is
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
    # Hand the `assign_pins` operation to the shared observation helper for `pin_assignment`.
    return tool_observation(
        'assign_pins',
        payload,
        agent_id='pin_assignment',
    )

# Register `assign_pin_layer` as an invocable skill: Set the layer of one pin or bus.
@tool(description='Set the layer of one pin or bus.')
def assign_pin_layer(
    candidate_ref: str = "",
    baseline_ref: str = "",
    hypothesis: str = "",
    pin_name: str = "",
    layer: str = "",
    params: dict | None = None,
) -> dict:
    """Set the layer of one pin or bus.

    Purpose:
        Set the routing layer for one pin or bus on the boundary.

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        baseline_ref: Artifact URI of the baseline netlist/design used for QoR or structural diffs.
        hypothesis: Single synthesis knob or setting this isolated experiment changes versus the baseline.
        pin_name: Block pin or bus name being assigned.
        layer: Routing metal layer for a pin or power strap.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `assign_pin_layer` operation for agent `pin_assignment`. When no EDA framework is
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
        'pin_name': pin_name,  # Block pin or bus name being assigned.
        'layer': layer,  # Routing metal layer for a pin or power strap.
    }
    # Merge optional adapter/planner overrides when the caller supplied params.
    if params:
        # params keys intentionally overwrite same-named explicit fields.
        payload.update(params)
    # Hand the `assign_pin_layer` operation to the shared observation helper for `pin_assignment`.
    return tool_observation(
        'assign_pin_layer',
        payload,
        agent_id='pin_assignment',
    )

# Register `order_bus_pins` as an invocable skill: Set the order of one bus along an edge.
@tool(description='Set the order of one bus along an edge.')
def order_bus_pins(
    candidate_ref: str = "",
    baseline_ref: str = "",
    hypothesis: str = "",
    bus_name: str = "",
    params: dict | None = None,
) -> dict:
    """Set the order of one bus along an edge.

    Purpose:
        Set bit order of one bus along an edge to reduce twist and crosstalk.

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        baseline_ref: Artifact URI of the baseline netlist/design used for QoR or structural diffs.
        hypothesis: Single synthesis knob or setting this isolated experiment changes versus the baseline.
        bus_name: `bus name` for the `order_bus_pins` operation in this agent's EDA contract; forwarded into the observation payload for the bound framework adapter.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `order_bus_pins` operation for agent `pin_assignment`. When no EDA framework is
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
        'bus_name': bus_name,  # `bus name` for the `order_bus_pins` operation in this agent's EDA contract; forwarded into the observation payload for the bound framework adapter.
    }
    # Merge optional adapter/planner overrides when the caller supplied params.
    if params:
        # params keys intentionally overwrite same-named explicit fields.
        payload.update(params)
    # Hand the `order_bus_pins` operation to the shared observation helper for `pin_assignment`.
    return tool_observation(
        'order_bus_pins',
        payload,
        agent_id='pin_assignment',
    )

# Register `place_feedthrough` as an invocable skill: Add one feedthrough that the contract allows.
@tool(description='Add one feedthrough that the contract allows.')
def place_feedthrough(
    candidate_ref: str = "",
    baseline_ref: str = "",
    hypothesis: str = "",
    params: dict | None = None,
) -> dict:
    """Add one feedthrough that the contract allows.

    Purpose:
        Add one feedthrough net/pin the package contract explicitly allows.

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        baseline_ref: Artifact URI of the baseline netlist/design used for QoR or structural diffs.
        hypothesis: Single synthesis knob or setting this isolated experiment changes versus the baseline.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `place_feedthrough` operation for agent `pin_assignment`. When no EDA framework is
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
    # Hand the `place_feedthrough` operation to the shared observation helper for `pin_assignment`.
    return tool_observation(
        'place_feedthrough',
        payload,
        agent_id='pin_assignment',
    )

# Register `write_pin_def` as an invocable skill: Write the pin section of the DEF.
@tool(description='Write the pin section of the DEF.')
def write_pin_def(
    candidate_ref: str = "",
    baseline_ref: str = "",
    hypothesis: str = "",
    params: dict | None = None,
) -> dict:
    """Write the pin section of the DEF.

    Purpose:
        Write the pin section of the DEF for this candidate.

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        baseline_ref: Artifact URI of the baseline netlist/design used for QoR or structural diffs.
        hypothesis: Single synthesis knob or setting this isolated experiment changes versus the baseline.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `write_pin_def` operation for agent `pin_assignment`. When no EDA framework is
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
    # Hand the `write_pin_def` operation to the shared observation helper for `pin_assignment`.
    return tool_observation(
        'write_pin_def',
        payload,
        agent_id='pin_assignment',
    )

# Register `validate_pin_density` as an invocable skill: Check boundary pin density against the contract.
@tool(description='Check boundary pin density against the contract.')
def validate_pin_density(
    candidate_ref: str = "",
    baseline_ref: str = "",
    recipe: str = "",
    corner: str = "",
    mode: str = "",
    params: dict | None = None,
) -> dict:
    """Check boundary pin density against the contract.

    Purpose:
        Check boundary pin density against the contract to avoid unroutable edges.

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        baseline_ref: Artifact URI of the baseline netlist/design used for QoR or structural diffs.
        recipe: `recipe` for the `validate_pin_density` operation in this agent's EDA contract; forwarded into the observation payload for the bound framework adapter.
        corner: Process/voltage/temperature corner filter (e.g. SS/FF); empty reads every available corner.
        mode: Operating mode filter (functional, scan, etc.); empty reads every available mode.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `validate_pin_density` operation for agent `pin_assignment`. When no EDA framework is
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
        'recipe': recipe,  # `recipe` for the `validate_pin_density` operation in this agent's EDA contract; forwarded into the observation payload for the bound framework adapter.
        'corner': corner,  # Process/voltage/temperature corner filter (e.g. SS/FF); empty reads every available corner.
        'mode': mode,  # Operating mode filter (functional, scan, etc.); empty reads every available mode.
    }
    # Merge optional adapter/planner overrides when the caller supplied params.
    if params:
        # params keys intentionally overwrite same-named explicit fields.
        payload.update(params)
    # Hand the `validate_pin_density` operation to the shared observation helper for `pin_assignment`.
    return tool_observation(
        'validate_pin_density',
        payload,
        agent_id='pin_assignment',
    )

# Register `check_pin_track_alignment` as an invocable skill: Check that pins sit on legal tracks.
@tool(description='Check that pins sit on legal tracks.')
def check_pin_track_alignment(
    candidate_ref: str = "",
    baseline_ref: str = "",
    recipe: str = "",
    corner: str = "",
    mode: str = "",
    params: dict | None = None,
) -> dict:
    """Check that pins sit on legal tracks.

    Purpose:
        Check pins sit on legal manufacturing tracks for their layer.

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        baseline_ref: Artifact URI of the baseline netlist/design used for QoR or structural diffs.
        recipe: `recipe` for the `check_pin_track_alignment` operation in this agent's EDA contract; forwarded into the observation payload for the bound framework adapter.
        corner: Process/voltage/temperature corner filter (e.g. SS/FF); empty reads every available corner.
        mode: Operating mode filter (functional, scan, etc.); empty reads every available mode.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `check_pin_track_alignment` operation for agent `pin_assignment`. When no EDA framework is
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
        'recipe': recipe,  # `recipe` for the `check_pin_track_alignment` operation in this agent's EDA contract; forwarded into the observation payload for the bound framework adapter.
        'corner': corner,  # Process/voltage/temperature corner filter (e.g. SS/FF); empty reads every available corner.
        'mode': mode,  # Operating mode filter (functional, scan, etc.); empty reads every available mode.
    }
    # Merge optional adapter/planner overrides when the caller supplied params.
    if params:
        # params keys intentionally overwrite same-named explicit fields.
        payload.update(params)
    # Hand the `check_pin_track_alignment` operation to the shared observation helper for `pin_assignment`.
    return tool_observation(
        'check_pin_track_alignment',
        payload,
        agent_id='pin_assignment',
    )

# Register `check_pin_layer_rules` as an invocable skill: Check pin layers against the technology rules.
@tool(description='Check pin layers against the technology rules.')
def check_pin_layer_rules(
    candidate_ref: str = "",
    baseline_ref: str = "",
    recipe: str = "",
    corner: str = "",
    mode: str = "",
    params: dict | None = None,
) -> dict:
    """Check pin layers against the technology rules.

    Purpose:
        Check pin layers against technology stack rules (min width/spacing via).

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        baseline_ref: Artifact URI of the baseline netlist/design used for QoR or structural diffs.
        recipe: `recipe` for the `check_pin_layer_rules` operation in this agent's EDA contract; forwarded into the observation payload for the bound framework adapter.
        corner: Process/voltage/temperature corner filter (e.g. SS/FF); empty reads every available corner.
        mode: Operating mode filter (functional, scan, etc.); empty reads every available mode.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `check_pin_layer_rules` operation for agent `pin_assignment`. When no EDA framework is
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
        'recipe': recipe,  # `recipe` for the `check_pin_layer_rules` operation in this agent's EDA contract; forwarded into the observation payload for the bound framework adapter.
        'corner': corner,  # Process/voltage/temperature corner filter (e.g. SS/FF); empty reads every available corner.
        'mode': mode,  # Operating mode filter (functional, scan, etc.); empty reads every available mode.
    }
    # Merge optional adapter/planner overrides when the caller supplied params.
    if params:
        # params keys intentionally overwrite same-named explicit fields.
        payload.update(params)
    # Hand the `check_pin_layer_rules` operation to the shared observation helper for `pin_assignment`.
    return tool_observation(
        'check_pin_layer_rules',
        payload,
        agent_id='pin_assignment',
    )

# Register `estimate_pin_wirelength` as an invocable skill: Estimate wirelength from this pin assignment to the macros.
@tool(description='Estimate wirelength from this pin assignment to the macros.')
def estimate_pin_wirelength(
    candidate_ref: str = "",
    report_ref: str = "",
    corner: str = "",
    mode: str = "",
    params: dict | None = None,
) -> dict:
    """Estimate wirelength from this pin assignment to the macros.

    Purpose:
        Estimate wirelength from pins to macros as a floorplan quality proxy.

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        report_ref: Artifact URI of a specific report; empty selects the latest report for the candidate.
        corner: Process/voltage/temperature corner filter (e.g. SS/FF); empty reads every available corner.
        mode: Operating mode filter (functional, scan, etc.); empty reads every available mode.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `estimate_pin_wirelength` operation for agent `pin_assignment`. When no EDA framework is
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
    # Hand the `estimate_pin_wirelength` operation to the shared observation helper for `pin_assignment`.
    return tool_observation(
        'estimate_pin_wirelength',
        payload,
        agent_id='pin_assignment',
    )

# Register `flag_pin_density_violation` as an invocable skill: Publish an edge whose pin density exceeds the contract.
@tool(description='Publish an edge whose pin density exceeds the contract.')
def flag_pin_density_violation(
    summary: str = "",
    evidence_refs: str = "",
    severity: str = "",
    recommended_recipient: str = "",
    params: dict | None = None,
) -> dict:
    """Publish an edge whose pin density exceeds the contract.

    Purpose:
        Publish an edge whose pin density exceeds the contract.

    Args:
        summary: One-sentence finding written into engineering memory for downstream agents.
        evidence_refs: Comma-separated artifact URIs that substantiate the finding or tradeoff.
        severity: Finding severity: low, medium, high, or critical relative to hard requirements.
        recommended_recipient: Agent id that should act next on this finding.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `flag_pin_density_violation` operation for agent `pin_assignment`. When no EDA framework is
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
    # Hand the `flag_pin_density_violation` operation to the shared observation helper for `pin_assignment`.
    return tool_observation(
        'flag_pin_density_violation',
        payload,
        agent_id='pin_assignment',
    )

# Register `flag_illegal_feedthrough` as an invocable skill: Publish a feedthrough the contract does not allow.
@tool(description='Publish a feedthrough the contract does not allow.')
def flag_illegal_feedthrough(
    summary: str = "",
    evidence_refs: str = "",
    severity: str = "",
    recommended_recipient: str = "",
    params: dict | None = None,
) -> dict:
    """Publish a feedthrough the contract does not allow.

    Purpose:
        Publish a feedthrough the package/interface contract does not allow.

    Args:
        summary: One-sentence finding written into engineering memory for downstream agents.
        evidence_refs: Comma-separated artifact URIs that substantiate the finding or tradeoff.
        severity: Finding severity: low, medium, high, or critical relative to hard requirements.
        recommended_recipient: Agent id that should act next on this finding.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `flag_illegal_feedthrough` operation for agent `pin_assignment`. When no EDA framework is
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
    # Hand the `flag_illegal_feedthrough` operation to the shared observation helper for `pin_assignment`.
    return tool_observation(
        'flag_illegal_feedthrough',
        payload,
        agent_id='pin_assignment',
    )

# Register `record_pin_assignment` as an invocable skill: Record the pin DEF ref and the contract revision it was checked against.
@tool(description='Record the pin DEF ref and the contract revision it was checked against.')
def record_pin_assignment(
    summary: str = "",
    evidence_refs: str = "",
    severity: str = "",
    recommended_recipient: str = "",
    params: dict | None = None,
) -> dict:
    """Record the pin DEF ref and the contract revision it was checked against.

    Purpose:
        Record pin DEF ref and contract revision checked against.

    Args:
        summary: One-sentence finding written into engineering memory for downstream agents.
        evidence_refs: Comma-separated artifact URIs that substantiate the finding or tradeoff.
        severity: Finding severity: low, medium, high, or critical relative to hard requirements.
        recommended_recipient: Agent id that should act next on this finding.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `record_pin_assignment` operation for agent `pin_assignment`. When no EDA framework is
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
    # Hand the `record_pin_assignment` operation to the shared observation helper for `pin_assignment`.
    return tool_observation(
        'record_pin_assignment',
        payload,
        agent_id='pin_assignment',
    )
