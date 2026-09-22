"""Tools for Macro-Placement Experiment Worker.

Each function below is the stable operation contract for this agent. A framework
adapter (Yosys, OpenROAD, OpenSTA, or a licensed tool) is responsible for actually
performing the EDA work. Until a framework is bound through ``EDA_FRAMEWORK`` /
backend.type, every call returns a structured observation with status ``not_run``
and must not invoke a synthesizer, placer, router, equivalence engine, or simulator.

EDA focus for this tool module: Hard-macro placement under halo, channel, orientation, and keepout constraints. Adapter targets OpenROAD initialize_floorplan and macro placement. Scores flyline connectivity and writes a floorplan DEF for one isolated candidate.

Common return shape:
    ``tool_observation(name, payload, agent_id="macro_placement")`` builds the dict the
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


# Register `initialize_floorplan` as an invocable skill: Create the die, core, rows, and sites for this candidate. Adapter target: OpenROAD initialize_floorplan.
@tool(description='Create the die, core, rows, and sites for this candidate. Adapter target: OpenROAD initialize_floorplan.')
def initialize_floorplan(
    candidate_ref: str = "",
    baseline_ref: str = "",
    hypothesis: str = "",
    params: dict | None = None,
) -> dict:
    """Create the die, core, rows, and sites for this candidate. Adapter target: OpenROAD initialize_floorplan.

    Purpose:
        Create die, core, rows, and sites for this candidate (OpenROAD initialize_floorplan).

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        baseline_ref: Artifact URI of the baseline netlist/design used for QoR or structural diffs.
        hypothesis: Single synthesis knob or setting this isolated experiment changes versus the baseline.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `initialize_floorplan` operation for agent `macro_placement`. When no EDA framework is
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
    # Hand the `initialize_floorplan` operation to the shared observation helper for `macro_placement`.
    return tool_observation(
        'initialize_floorplan',
        payload,
        agent_id='macro_placement',
    )

# Register `read_macro_inventory` as an invocable skill: Read macros, abstracts, and orientation limits.
@tool(description='Read macros, abstracts, and orientation limits.')
def read_macro_inventory(
    candidate_ref: str = "",
    report_ref: str = "",
    corner: str = "",
    mode: str = "",
    params: dict | None = None,
) -> dict:
    """Read macros, abstracts, and orientation limits.

    Purpose:
        Read macros, LEF abstracts, and legal orientation limits for the partition.

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        report_ref: Artifact URI of a specific report; empty selects the latest report for the candidate.
        corner: Process/voltage/temperature corner filter (e.g. SS/FF); empty reads every available corner.
        mode: Operating mode filter (functional, scan, etc.); empty reads every available mode.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `read_macro_inventory` operation for agent `macro_placement`. When no EDA framework is
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
    # Hand the `read_macro_inventory` operation to the shared observation helper for `macro_placement`.
    return tool_observation(
        'read_macro_inventory',
        payload,
        agent_id='macro_placement',
    )

# Register `read_floorplan_keepouts` as an invocable skill: Read blockages, halos, and manufacturing keepouts.
@tool(description='Read blockages, halos, and manufacturing keepouts.')
def read_floorplan_keepouts(
    candidate_ref: str = "",
    report_ref: str = "",
    corner: str = "",
    mode: str = "",
    params: dict | None = None,
) -> dict:
    """Read blockages, halos, and manufacturing keepouts.

    Purpose:
        Read blockages, manufacturing keepouts, and reserved channels.

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        report_ref: Artifact URI of a specific report; empty selects the latest report for the candidate.
        corner: Process/voltage/temperature corner filter (e.g. SS/FF); empty reads every available corner.
        mode: Operating mode filter (functional, scan, etc.); empty reads every available mode.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `read_floorplan_keepouts` operation for agent `macro_placement`. When no EDA framework is
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
    # Hand the `read_floorplan_keepouts` operation to the shared observation helper for `macro_placement`.
    return tool_observation(
        'read_floorplan_keepouts',
        payload,
        agent_id='macro_placement',
    )

# Register `place_macros` as an invocable skill: Place macros for one candidate. Adapter target: OpenROAD macro placement.
@tool(description='Place macros for one candidate. Adapter target: OpenROAD macro placement.')
def place_macros(
    candidate_ref: str = "",
    baseline_ref: str = "",
    hypothesis: str = "",
    params: dict | None = None,
) -> dict:
    """Place macros for one candidate. Adapter target: OpenROAD macro placement.

    Purpose:
        Place hard macros for one candidate (OpenROAD macro placement).

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        baseline_ref: Artifact URI of the baseline netlist/design used for QoR or structural diffs.
        hypothesis: Single synthesis knob or setting this isolated experiment changes versus the baseline.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `place_macros` operation for agent `macro_placement`. When no EDA framework is
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
    # Hand the `place_macros` operation to the shared observation helper for `macro_placement`.
    return tool_observation(
        'place_macros',
        payload,
        agent_id='macro_placement',
    )

# Register `set_macro_halo` as an invocable skill: Set the halo around one macro.
@tool(description='Set the halo around one macro.')
def set_macro_halo(
    candidate_ref: str = "",
    baseline_ref: str = "",
    hypothesis: str = "",
    macro_name: str = "",
    halo_microns: str = "",
    params: dict | None = None,
) -> dict:
    """Set the halo around one macro.

    Purpose:
        Set keep-out halo around one macro so standard cells and routes have clearance.

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        baseline_ref: Artifact URI of the baseline netlist/design used for QoR or structural diffs.
        hypothesis: Single synthesis knob or setting this isolated experiment changes versus the baseline.
        macro_name: Hard macro instance being placed or constrained.
        halo_microns: `halo microns` for the `set_macro_halo` operation in this agent's EDA contract; forwarded into the observation payload for the bound framework adapter.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `set_macro_halo` operation for agent `macro_placement`. When no EDA framework is
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
        'macro_name': macro_name,  # Hard macro instance being placed or constrained.
        'halo_microns': halo_microns,  # `halo microns` for the `set_macro_halo` operation in this agent's EDA contract; forwarded into the observation payload for the bound framework adapter.
    }
    # Merge optional adapter/planner overrides when the caller supplied params.
    if params:
        # params keys intentionally overwrite same-named explicit fields.
        payload.update(params)
    # Hand the `set_macro_halo` operation to the shared observation helper for `macro_placement`.
    return tool_observation(
        'set_macro_halo',
        payload,
        agent_id='macro_placement',
    )

# Register `set_macro_orientation` as an invocable skill: Set a legal orientation for one macro.
@tool(description='Set a legal orientation for one macro.')
def set_macro_orientation(
    candidate_ref: str = "",
    baseline_ref: str = "",
    hypothesis: str = "",
    macro_name: str = "",
    orientation: str = "",
    params: dict | None = None,
) -> dict:
    """Set a legal orientation for one macro.

    Purpose:
        Set a legal R0/R90/... orientation for one macro under abstract constraints.

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        baseline_ref: Artifact URI of the baseline netlist/design used for QoR or structural diffs.
        hypothesis: Single synthesis knob or setting this isolated experiment changes versus the baseline.
        macro_name: Hard macro instance being placed or constrained.
        orientation: Legal macro orientation (R0, R90, R180, R270, mirrors).
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `set_macro_orientation` operation for agent `macro_placement`. When no EDA framework is
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
        'macro_name': macro_name,  # Hard macro instance being placed or constrained.
        'orientation': orientation,  # Legal macro orientation (R0, R90, R180, R270, mirrors).
    }
    # Merge optional adapter/planner overrides when the caller supplied params.
    if params:
        # params keys intentionally overwrite same-named explicit fields.
        payload.update(params)
    # Hand the `set_macro_orientation` operation to the shared observation helper for `macro_placement`.
    return tool_observation(
        'set_macro_orientation',
        payload,
        agent_id='macro_placement',
    )

# Register `set_macro_channel` as an invocable skill: Set the channel width between two macros.
@tool(description='Set the channel width between two macros.')
def set_macro_channel(
    candidate_ref: str = "",
    baseline_ref: str = "",
    hypothesis: str = "",
    params: dict | None = None,
) -> dict:
    """Set the channel width between two macros.

    Purpose:
        Set channel width between two macros for routing/power straps.

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        baseline_ref: Artifact URI of the baseline netlist/design used for QoR or structural diffs.
        hypothesis: Single synthesis knob or setting this isolated experiment changes versus the baseline.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `set_macro_channel` operation for agent `macro_placement`. When no EDA framework is
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
    # Hand the `set_macro_channel` operation to the shared observation helper for `macro_placement`.
    return tool_observation(
        'set_macro_channel',
        payload,
        agent_id='macro_placement',
    )

# Register `check_macro_overlaps` as an invocable skill: Check macros for overlap.
@tool(description='Check macros for overlap.')
def check_macro_overlaps(
    candidate_ref: str = "",
    baseline_ref: str = "",
    recipe: str = "",
    corner: str = "",
    mode: str = "",
    params: dict | None = None,
) -> dict:
    """Check macros for overlap.

    Purpose:
        Hard-check that no two macros overlap in the candidate DEF.

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        baseline_ref: Artifact URI of the baseline netlist/design used for QoR or structural diffs.
        recipe: `recipe` for the `check_macro_overlaps` operation in this agent's EDA contract; forwarded into the observation payload for the bound framework adapter.
        corner: Process/voltage/temperature corner filter (e.g. SS/FF); empty reads every available corner.
        mode: Operating mode filter (functional, scan, etc.); empty reads every available mode.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `check_macro_overlaps` operation for agent `macro_placement`. When no EDA framework is
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
        'recipe': recipe,  # `recipe` for the `check_macro_overlaps` operation in this agent's EDA contract; forwarded into the observation payload for the bound framework adapter.
        'corner': corner,  # Process/voltage/temperature corner filter (e.g. SS/FF); empty reads every available corner.
        'mode': mode,  # Operating mode filter (functional, scan, etc.); empty reads every available mode.
    }
    # Merge optional adapter/planner overrides when the caller supplied params.
    if params:
        # params keys intentionally overwrite same-named explicit fields.
        payload.update(params)
    # Hand the `check_macro_overlaps` operation to the shared observation helper for `macro_placement`.
    return tool_observation(
        'check_macro_overlaps',
        payload,
        agent_id='macro_placement',
    )

# Register `check_macro_channels` as an invocable skill: Check channel widths against the routing requirement.
@tool(description='Check channel widths against the routing requirement.')
def check_macro_channels(
    candidate_ref: str = "",
    baseline_ref: str = "",
    recipe: str = "",
    corner: str = "",
    mode: str = "",
    params: dict | None = None,
) -> dict:
    """Check channel widths against the routing requirement.

    Purpose:
        Check channel widths meet routing and PDN requirements.

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        baseline_ref: Artifact URI of the baseline netlist/design used for QoR or structural diffs.
        recipe: `recipe` for the `check_macro_channels` operation in this agent's EDA contract; forwarded into the observation payload for the bound framework adapter.
        corner: Process/voltage/temperature corner filter (e.g. SS/FF); empty reads every available corner.
        mode: Operating mode filter (functional, scan, etc.); empty reads every available mode.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `check_macro_channels` operation for agent `macro_placement`. When no EDA framework is
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
        'recipe': recipe,  # `recipe` for the `check_macro_channels` operation in this agent's EDA contract; forwarded into the observation payload for the bound framework adapter.
        'corner': corner,  # Process/voltage/temperature corner filter (e.g. SS/FF); empty reads every available corner.
        'mode': mode,  # Operating mode filter (functional, scan, etc.); empty reads every available mode.
    }
    # Merge optional adapter/planner overrides when the caller supplied params.
    if params:
        # params keys intentionally overwrite same-named explicit fields.
        payload.update(params)
    # Hand the `check_macro_channels` operation to the shared observation helper for `macro_placement`.
    return tool_observation(
        'check_macro_channels',
        payload,
        agent_id='macro_placement',
    )

# Register `check_macro_keepouts` as an invocable skill: Check that no macro sits in a keepout.
@tool(description='Check that no macro sits in a keepout.')
def check_macro_keepouts(
    candidate_ref: str = "",
    baseline_ref: str = "",
    recipe: str = "",
    corner: str = "",
    mode: str = "",
    params: dict | None = None,
) -> dict:
    """Check that no macro sits in a keepout.

    Purpose:
        Check no macro intersects a keepout or blockage.

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        baseline_ref: Artifact URI of the baseline netlist/design used for QoR or structural diffs.
        recipe: `recipe` for the `check_macro_keepouts` operation in this agent's EDA contract; forwarded into the observation payload for the bound framework adapter.
        corner: Process/voltage/temperature corner filter (e.g. SS/FF); empty reads every available corner.
        mode: Operating mode filter (functional, scan, etc.); empty reads every available mode.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `check_macro_keepouts` operation for agent `macro_placement`. When no EDA framework is
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
        'recipe': recipe,  # `recipe` for the `check_macro_keepouts` operation in this agent's EDA contract; forwarded into the observation payload for the bound framework adapter.
        'corner': corner,  # Process/voltage/temperature corner filter (e.g. SS/FF); empty reads every available corner.
        'mode': mode,  # Operating mode filter (functional, scan, etc.); empty reads every available mode.
    }
    # Merge optional adapter/planner overrides when the caller supplied params.
    if params:
        # params keys intentionally overwrite same-named explicit fields.
        payload.update(params)
    # Hand the `check_macro_keepouts` operation to the shared observation helper for `macro_placement`.
    return tool_observation(
        'check_macro_keepouts',
        payload,
        agent_id='macro_placement',
    )

# Register `score_macro_connectivity` as an invocable skill: Score flyline length and macro-to-macro connectivity.
@tool(description='Score flyline length and macro-to-macro connectivity.')
def score_macro_connectivity(
    candidate_ref: str = "",
    report_ref: str = "",
    corner: str = "",
    mode: str = "",
    params: dict | None = None,
) -> dict:
    """Score flyline length and macro-to-macro connectivity.

    Purpose:
        Score flyline length and macro-to-macro connectivity as a placement quality proxy.

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        report_ref: Artifact URI of a specific report; empty selects the latest report for the candidate.
        corner: Process/voltage/temperature corner filter (e.g. SS/FF); empty reads every available corner.
        mode: Operating mode filter (functional, scan, etc.); empty reads every available mode.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `score_macro_connectivity` operation for agent `macro_placement`. When no EDA framework is
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
    # Hand the `score_macro_connectivity` operation to the shared observation helper for `macro_placement`.
    return tool_observation(
        'score_macro_connectivity',
        payload,
        agent_id='macro_placement',
    )

# Register `write_floorplan_def` as an invocable skill: Write the floorplan DEF for this candidate.
@tool(description='Write the floorplan DEF for this candidate.')
def write_floorplan_def(
    candidate_ref: str = "",
    baseline_ref: str = "",
    hypothesis: str = "",
    params: dict | None = None,
) -> dict:
    """Write the floorplan DEF for this candidate.

    Purpose:
        Write the floorplan DEF artifact for this macro candidate.

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        baseline_ref: Artifact URI of the baseline netlist/design used for QoR or structural diffs.
        hypothesis: Single synthesis knob or setting this isolated experiment changes versus the baseline.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `write_floorplan_def` operation for agent `macro_placement`. When no EDA framework is
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
    # Hand the `write_floorplan_def` operation to the shared observation helper for `macro_placement`.
    return tool_observation(
        'write_floorplan_def',
        payload,
        agent_id='macro_placement',
    )

# Register `generate_macro_placement` as an invocable skill: Place macros and write the candidate in one step when the hypothesis is a full placement.
@tool(description='Place macros and write the candidate in one step when the hypothesis is a full placement.')
def generate_macro_placement(
    candidate_ref: str = "",
    baseline_ref: str = "",
    hypothesis: str = "",
    params: dict | None = None,
) -> dict:
    """Place macros and write the candidate in one step when the hypothesis is a full placement.

    Purpose:
        Place macros and write the candidate in one step when the hypothesis is a full placement.

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        baseline_ref: Artifact URI of the baseline netlist/design used for QoR or structural diffs.
        hypothesis: Single synthesis knob or setting this isolated experiment changes versus the baseline.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `generate_macro_placement` operation for agent `macro_placement`. When no EDA framework is
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
    # Hand the `generate_macro_placement` operation to the shared observation helper for `macro_placement`.
    return tool_observation(
        'generate_macro_placement',
        payload,
        agent_id='macro_placement',
    )

# Register `score_macro_placement` as an invocable skill: Score halo, channel, orientation, and connectivity.
@tool(description='Score halo, channel, orientation, and connectivity.')
def score_macro_placement(
    candidate_ref: str = "",
    report_ref: str = "",
    corner: str = "",
    mode: str = "",
    params: dict | None = None,
) -> dict:
    """Score halo, channel, orientation, and connectivity.

    Purpose:
        Score halo, channel, orientation legality, and connectivity together.

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        report_ref: Artifact URI of a specific report; empty selects the latest report for the candidate.
        corner: Process/voltage/temperature corner filter (e.g. SS/FF); empty reads every available corner.
        mode: Operating mode filter (functional, scan, etc.); empty reads every available mode.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `score_macro_placement` operation for agent `macro_placement`. When no EDA framework is
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
    # Hand the `score_macro_placement` operation to the shared observation helper for `macro_placement`.
    return tool_observation(
        'score_macro_placement',
        payload,
        agent_id='macro_placement',
    )

# Register `flag_keepout_violation` as an invocable skill: Publish a macro that entered a keepout.
@tool(description='Publish a macro that entered a keepout.')
def flag_keepout_violation(
    summary: str = "",
    evidence_refs: str = "",
    severity: str = "",
    recommended_recipient: str = "",
    params: dict | None = None,
) -> dict:
    """Publish a macro that entered a keepout.

    Purpose:
        Publish a macro that entered a keepout region.

    Args:
        summary: One-sentence finding written into engineering memory for downstream agents.
        evidence_refs: Comma-separated artifact URIs that substantiate the finding or tradeoff.
        severity: Finding severity: low, medium, high, or critical relative to hard requirements.
        recommended_recipient: Agent id that should act next on this finding.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `flag_keepout_violation` operation for agent `macro_placement`. When no EDA framework is
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
    # Hand the `flag_keepout_violation` operation to the shared observation helper for `macro_placement`.
    return tool_observation(
        'flag_keepout_violation',
        payload,
        agent_id='macro_placement',
    )

# Register `record_macro_placement_metrics` as an invocable skill: Record utilization, flylines, and the OpenROAD recipe id.
@tool(description='Record utilization, flylines, and the OpenROAD recipe id.')
def record_macro_placement_metrics(
    summary: str = "",
    evidence_refs: str = "",
    severity: str = "",
    recommended_recipient: str = "",
    params: dict | None = None,
) -> dict:
    """Record utilization, flylines, and the OpenROAD recipe id.

    Purpose:
        Record utilization, flylines, and OpenROAD recipe id for provenance.

    Args:
        summary: One-sentence finding written into engineering memory for downstream agents.
        evidence_refs: Comma-separated artifact URIs that substantiate the finding or tradeoff.
        severity: Finding severity: low, medium, high, or critical relative to hard requirements.
        recommended_recipient: Agent id that should act next on this finding.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `record_macro_placement_metrics` operation for agent `macro_placement`. When no EDA framework is
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
    # Hand the `record_macro_placement_metrics` operation to the shared observation helper for `macro_placement`.
    return tool_observation(
        'record_macro_placement_metrics',
        payload,
        agent_id='macro_placement',
    )
