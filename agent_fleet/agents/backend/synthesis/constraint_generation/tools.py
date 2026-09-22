"""Tools for Constraint Generation and Validation.

Each function below is the stable operation contract for this agent. A framework
adapter (Yosys, OpenROAD, OpenSTA, or a licensed tool) is responsible for actually
performing the EDA work. Until a framework is bound through ``EDA_FRAMEWORK`` /
backend.type, every call returns a structured observation with status ``not_run``
and must not invoke a synthesizer, placer, router, equivalence engine, or simulator.

EDA focus for this tool module: SDC (Synopsys Design Constraints) authorship and audit: create_clock, create_generated_clock, set_input_delay / set_output_delay, clock uncertainty, clock groups, false paths, multicycle paths, and case analysis. Bad constraints silently create optimistic timing that later fails STA or equivalence.

Common return shape:
    ``tool_observation(name, payload, agent_id="constraint_generation")`` builds the dict the
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


# Register `write_create_clock` as an invocable skill: Write create_clock constraints for the declared clocks.
@tool(description='Write create_clock constraints for the declared clocks.')
def write_create_clock(
    candidate_ref: str = "",
    baseline_ref: str = "",
    hypothesis: str = "",
    clock_name: str = "",
    params: dict | None = None,
) -> dict:
    """Write create_clock constraints for the declared clocks.

    Purpose:
        Author create_clock for a declared primary clock; missing create_clock makes STA meaningless.

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        baseline_ref: Artifact URI of the baseline netlist/design used for QoR or structural diffs.
        hypothesis: Single synthesis knob or setting this isolated experiment changes versus the baseline.
        clock_name: Name of the primary or generated clock being constrained or checked in SDC.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `write_create_clock` operation for agent `constraint_generation`. When no EDA framework is
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
        'clock_name': clock_name,  # Name of the primary or generated clock being constrained or checked in SDC.
    }
    # Merge optional adapter/planner overrides when the caller supplied params.
    if params:
        # params keys intentionally overwrite same-named explicit fields.
        payload.update(params)
    # Hand the `write_create_clock` operation to the shared observation helper for `constraint_generation`.
    return tool_observation(
        'write_create_clock',
        payload,
        agent_id='constraint_generation',
    )

# Register `write_generated_clock` as an invocable skill: Write create_generated_clock for one derived or gated clock.
@tool(description='Write create_generated_clock for one derived or gated clock.')
def write_generated_clock(
    candidate_ref: str = "",
    baseline_ref: str = "",
    hypothesis: str = "",
    clock_name: str = "",
    params: dict | None = None,
) -> dict:
    """Write create_generated_clock for one derived or gated clock.

    Purpose:
        Author create_generated_clock for derived/gated clocks so timing relations stay explicit.

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        baseline_ref: Artifact URI of the baseline netlist/design used for QoR or structural diffs.
        hypothesis: Single synthesis knob or setting this isolated experiment changes versus the baseline.
        clock_name: Name of the primary or generated clock being constrained or checked in SDC.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `write_generated_clock` operation for agent `constraint_generation`. When no EDA framework is
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
        'clock_name': clock_name,  # Name of the primary or generated clock being constrained or checked in SDC.
    }
    # Merge optional adapter/planner overrides when the caller supplied params.
    if params:
        # params keys intentionally overwrite same-named explicit fields.
        payload.update(params)
    # Hand the `write_generated_clock` operation to the shared observation helper for `constraint_generation`.
    return tool_observation(
        'write_generated_clock',
        payload,
        agent_id='constraint_generation',
    )

# Register `write_input_delay` as an invocable skill: Write set_input_delay for one port group.
@tool(description='Write set_input_delay for one port group.')
def write_input_delay(
    candidate_ref: str = "",
    baseline_ref: str = "",
    hypothesis: str = "",
    params: dict | None = None,
) -> dict:
    """Write set_input_delay for one port group.

    Purpose:
        Author set_input_delay for a port group modeling external path delay into the block.

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        baseline_ref: Artifact URI of the baseline netlist/design used for QoR or structural diffs.
        hypothesis: Single synthesis knob or setting this isolated experiment changes versus the baseline.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `write_input_delay` operation for agent `constraint_generation`. When no EDA framework is
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
    # Hand the `write_input_delay` operation to the shared observation helper for `constraint_generation`.
    return tool_observation(
        'write_input_delay',
        payload,
        agent_id='constraint_generation',
    )

# Register `write_output_delay` as an invocable skill: Write set_output_delay for one port group.
@tool(description='Write set_output_delay for one port group.')
def write_output_delay(
    candidate_ref: str = "",
    baseline_ref: str = "",
    hypothesis: str = "",
    params: dict | None = None,
) -> dict:
    """Write set_output_delay for one port group.

    Purpose:
        Author set_output_delay for a port group modeling external path delay leaving the block.

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        baseline_ref: Artifact URI of the baseline netlist/design used for QoR or structural diffs.
        hypothesis: Single synthesis knob or setting this isolated experiment changes versus the baseline.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `write_output_delay` operation for agent `constraint_generation`. When no EDA framework is
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
    # Hand the `write_output_delay` operation to the shared observation helper for `constraint_generation`.
    return tool_observation(
        'write_output_delay',
        payload,
        agent_id='constraint_generation',
    )

# Register `write_clock_uncertainty` as an invocable skill: Write setup and hold uncertainty for one clock.
@tool(description='Write setup and hold uncertainty for one clock.')
def write_clock_uncertainty(
    candidate_ref: str = "",
    baseline_ref: str = "",
    hypothesis: str = "",
    params: dict | None = None,
) -> dict:
    """Write setup and hold uncertainty for one clock.

    Purpose:
        Author setup/hold uncertainty to budget jitter, skew, and on-chip variation early.

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        baseline_ref: Artifact URI of the baseline netlist/design used for QoR or structural diffs.
        hypothesis: Single synthesis knob or setting this isolated experiment changes versus the baseline.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `write_clock_uncertainty` operation for agent `constraint_generation`. When no EDA framework is
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
    # Hand the `write_clock_uncertainty` operation to the shared observation helper for `constraint_generation`.
    return tool_observation(
        'write_clock_uncertainty',
        payload,
        agent_id='constraint_generation',
    )

# Register `write_clock_groups` as an invocable skill: Write asynchronous or logically exclusive clock groups.
@tool(description='Write asynchronous or logically exclusive clock groups.')
def write_clock_groups(
    candidate_ref: str = "",
    baseline_ref: str = "",
    hypothesis: str = "",
    params: dict | None = None,
) -> dict:
    """Write asynchronous or logically exclusive clock groups.

    Purpose:
        Author asynchronous or logically exclusive clock groups so false cross-domain paths are not timed.

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        baseline_ref: Artifact URI of the baseline netlist/design used for QoR or structural diffs.
        hypothesis: Single synthesis knob or setting this isolated experiment changes versus the baseline.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `write_clock_groups` operation for agent `constraint_generation`. When no EDA framework is
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
    # Hand the `write_clock_groups` operation to the shared observation helper for `constraint_generation`.
    return tool_observation(
        'write_clock_groups',
        payload,
        agent_id='constraint_generation',
    )

# Register `write_false_path` as an invocable skill: Write a false path only with the justification that makes it legal.
@tool(description='Write a false path only with the justification that makes it legal.')
def write_false_path(
    candidate_ref: str = "",
    baseline_ref: str = "",
    hypothesis: str = "",
    justification: str = "",
    params: dict | None = None,
) -> dict:
    """Write a false path only with the justification that makes it legal.

    Purpose:
        Author a false path only with architectural justification; unjustified false paths hide real violations.

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        baseline_ref: Artifact URI of the baseline netlist/design used for QoR or structural diffs.
        hypothesis: Single synthesis knob or setting this isolated experiment changes versus the baseline.
        justification: Architectural reason that makes a false path or mapped-away point legal.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `write_false_path` operation for agent `constraint_generation`. When no EDA framework is
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
        'justification': justification,  # Architectural reason that makes a false path or mapped-away point legal.
    }
    # Merge optional adapter/planner overrides when the caller supplied params.
    if params:
        # params keys intentionally overwrite same-named explicit fields.
        payload.update(params)
    # Hand the `write_false_path` operation to the shared observation helper for `constraint_generation`.
    return tool_observation(
        'write_false_path',
        payload,
        agent_id='constraint_generation',
    )

# Register `write_multicycle_path` as an invocable skill: Write a multicycle path with its architectural latency.
@tool(description='Write a multicycle path with its architectural latency.')
def write_multicycle_path(
    candidate_ref: str = "",
    baseline_ref: str = "",
    hypothesis: str = "",
    params: dict | None = None,
) -> dict:
    """Write a multicycle path with its architectural latency.

    Purpose:
        Author a multicycle path tied to known architectural latency (N cycles between launches).

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        baseline_ref: Artifact URI of the baseline netlist/design used for QoR or structural diffs.
        hypothesis: Single synthesis knob or setting this isolated experiment changes versus the baseline.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `write_multicycle_path` operation for agent `constraint_generation`. When no EDA framework is
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
    # Hand the `write_multicycle_path` operation to the shared observation helper for `constraint_generation`.
    return tool_observation(
        'write_multicycle_path',
        payload,
        agent_id='constraint_generation',
    )

# Register `write_case_analysis` as an invocable skill: Write set_case_analysis for one operating mode.
@tool(description='Write set_case_analysis for one operating mode.')
def write_case_analysis(
    candidate_ref: str = "",
    baseline_ref: str = "",
    hypothesis: str = "",
    mode_name: str = "",
    params: dict | None = None,
) -> dict:
    """Write set_case_analysis for one operating mode.

    Purpose:
        Author set_case_analysis pinning constants for one operating mode (e.g. scan enable).

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        baseline_ref: Artifact URI of the baseline netlist/design used for QoR or structural diffs.
        hypothesis: Single synthesis knob or setting this isolated experiment changes versus the baseline.
        mode_name: `mode name` for the `write_case_analysis` operation in this agent's EDA contract; forwarded into the observation payload for the bound framework adapter.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `write_case_analysis` operation for agent `constraint_generation`. When no EDA framework is
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
        'mode_name': mode_name,  # `mode name` for the `write_case_analysis` operation in this agent's EDA contract; forwarded into the observation payload for the bound framework adapter.
    }
    # Merge optional adapter/planner overrides when the caller supplied params.
    if params:
        # params keys intentionally overwrite same-named explicit fields.
        payload.update(params)
    # Hand the `write_case_analysis` operation to the shared observation helper for `constraint_generation`.
    return tool_observation(
        'write_case_analysis',
        payload,
        agent_id='constraint_generation',
    )

# Register `write_sdc` as an invocable skill: Write the SDC file for this candidate.
@tool(description='Write the SDC file for this candidate.')
def write_sdc(
    candidate_ref: str = "",
    baseline_ref: str = "",
    hypothesis: str = "",
    params: dict | None = None,
) -> dict:
    """Write the SDC file for this candidate.

    Purpose:
        Serialize the full SDC file artifact for this candidate so synthesizer and STA share one source.

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        baseline_ref: Artifact URI of the baseline netlist/design used for QoR or structural diffs.
        hypothesis: Single synthesis knob or setting this isolated experiment changes versus the baseline.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `write_sdc` operation for agent `constraint_generation`. When no EDA framework is
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
    # Hand the `write_sdc` operation to the shared observation helper for `constraint_generation`.
    return tool_observation(
        'write_sdc',
        payload,
        agent_id='constraint_generation',
    )

# Register `audit_constraints` as an invocable skill: Flag missing, contradictory, or unjustified exceptions.
@tool(description='Flag missing, contradictory, or unjustified exceptions.')
def audit_constraints(
    candidate_ref: str = "",
    baseline_ref: str = "",
    recipe: str = "",
    corner: str = "",
    mode: str = "",
    params: dict | None = None,
) -> dict:
    """Flag missing, contradictory, or unjustified exceptions.

    Purpose:
        Flag missing, contradictory, or unjustified exceptions before synthesis trusts the SDC.

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        baseline_ref: Artifact URI of the baseline netlist/design used for QoR or structural diffs.
        recipe: `recipe` for the `audit_constraints` operation in this agent's EDA contract; forwarded into the observation payload for the bound framework adapter.
        corner: Process/voltage/temperature corner filter (e.g. SS/FF); empty reads every available corner.
        mode: Operating mode filter (functional, scan, etc.); empty reads every available mode.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `audit_constraints` operation for agent `constraint_generation`. When no EDA framework is
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
        'recipe': recipe,  # `recipe` for the `audit_constraints` operation in this agent's EDA contract; forwarded into the observation payload for the bound framework adapter.
        'corner': corner,  # Process/voltage/temperature corner filter (e.g. SS/FF); empty reads every available corner.
        'mode': mode,  # Operating mode filter (functional, scan, etc.); empty reads every available mode.
    }
    # Merge optional adapter/planner overrides when the caller supplied params.
    if params:
        # params keys intentionally overwrite same-named explicit fields.
        payload.update(params)
    # Hand the `audit_constraints` operation to the shared observation helper for `constraint_generation`.
    return tool_observation(
        'audit_constraints',
        payload,
        agent_id='constraint_generation',
    )

# Register `check_clocks_exist_in_netlist` as an invocable skill: Check that every constrained clock exists in the candidate.
@tool(description='Check that every constrained clock exists in the candidate.')
def check_clocks_exist_in_netlist(
    candidate_ref: str = "",
    report_ref: str = "",
    corner: str = "",
    mode: str = "",
    params: dict | None = None,
) -> dict:
    """Check that every constrained clock exists in the candidate.

    Purpose:
        Verify every constrained clock pin/net still exists after compile (renames break timing).

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        report_ref: Artifact URI of a specific report; empty selects the latest report for the candidate.
        corner: Process/voltage/temperature corner filter (e.g. SS/FF); empty reads every available corner.
        mode: Operating mode filter (functional, scan, etc.); empty reads every available mode.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `check_clocks_exist_in_netlist` operation for agent `constraint_generation`. When no EDA framework is
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
    # Hand the `check_clocks_exist_in_netlist` operation to the shared observation helper for `constraint_generation`.
    return tool_observation(
        'check_clocks_exist_in_netlist',
        payload,
        agent_id='constraint_generation',
    )

# Register `read_constraint_exceptions` as an invocable skill: Read false paths, multicycle paths, and case analysis.
@tool(description='Read false paths, multicycle paths, and case analysis.')
def read_constraint_exceptions(
    candidate_ref: str = "",
    report_ref: str = "",
    corner: str = "",
    mode: str = "",
    params: dict | None = None,
) -> dict:
    """Read false paths, multicycle paths, and case analysis.

    Purpose:
        List false paths, multicycle paths, and case analysis currently active for review.

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        report_ref: Artifact URI of a specific report; empty selects the latest report for the candidate.
        corner: Process/voltage/temperature corner filter (e.g. SS/FF); empty reads every available corner.
        mode: Operating mode filter (functional, scan, etc.); empty reads every available mode.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `read_constraint_exceptions` operation for agent `constraint_generation`. When no EDA framework is
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
    # Hand the `read_constraint_exceptions` operation to the shared observation helper for `constraint_generation`.
    return tool_observation(
        'read_constraint_exceptions',
        payload,
        agent_id='constraint_generation',
    )

# Register `flag_unjustified_exception` as an invocable skill: Publish an exception that has no architectural justification.
@tool(description='Publish an exception that has no architectural justification.')
def flag_unjustified_exception(
    summary: str = "",
    evidence_refs: str = "",
    severity: str = "",
    recommended_recipient: str = "",
    params: dict | None = None,
) -> dict:
    """Publish an exception that has no architectural justification.

    Purpose:
        Publish an exception (false/MCP) that lacks architectural justification.

    Args:
        summary: One-sentence finding written into engineering memory for downstream agents.
        evidence_refs: Comma-separated artifact URIs that substantiate the finding or tradeoff.
        severity: Finding severity: low, medium, high, or critical relative to hard requirements.
        recommended_recipient: Agent id that should act next on this finding.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `flag_unjustified_exception` operation for agent `constraint_generation`. When no EDA framework is
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
    # Hand the `flag_unjustified_exception` operation to the shared observation helper for `constraint_generation`.
    return tool_observation(
        'flag_unjustified_exception',
        payload,
        agent_id='constraint_generation',
    )

# Register `flag_missing_clock` as an invocable skill: Publish a declared clock with no create_clock.
@tool(description='Publish a declared clock with no create_clock.')
def flag_missing_clock(
    summary: str = "",
    evidence_refs: str = "",
    severity: str = "",
    recommended_recipient: str = "",
    params: dict | None = None,
) -> dict:
    """Publish a declared clock with no create_clock.

    Purpose:
        Publish a declared clock that has no create_clock in the SDC.

    Args:
        summary: One-sentence finding written into engineering memory for downstream agents.
        evidence_refs: Comma-separated artifact URIs that substantiate the finding or tradeoff.
        severity: Finding severity: low, medium, high, or critical relative to hard requirements.
        recommended_recipient: Agent id that should act next on this finding.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `flag_missing_clock` operation for agent `constraint_generation`. When no EDA framework is
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
    # Hand the `flag_missing_clock` operation to the shared observation helper for `constraint_generation`.
    return tool_observation(
        'flag_missing_clock',
        payload,
        agent_id='constraint_generation',
    )

# Register `record_constraint_lineage` as an invocable skill: Record the SDC revision, mode list, and RTL revision.
@tool(description='Record the SDC revision, mode list, and RTL revision.')
def record_constraint_lineage(
    summary: str = "",
    evidence_refs: str = "",
    severity: str = "",
    recommended_recipient: str = "",
    params: dict | None = None,
) -> dict:
    """Record the SDC revision, mode list, and RTL revision.

    Purpose:
        Record SDC revision, mode list, and RTL revision for reproducibility.

    Args:
        summary: One-sentence finding written into engineering memory for downstream agents.
        evidence_refs: Comma-separated artifact URIs that substantiate the finding or tradeoff.
        severity: Finding severity: low, medium, high, or critical relative to hard requirements.
        recommended_recipient: Agent id that should act next on this finding.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `record_constraint_lineage` operation for agent `constraint_generation`. When no EDA framework is
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
    # Hand the `record_constraint_lineage` operation to the shared observation helper for `constraint_generation`.
    return tool_observation(
        'record_constraint_lineage',
        payload,
        agent_id='constraint_generation',
    )
