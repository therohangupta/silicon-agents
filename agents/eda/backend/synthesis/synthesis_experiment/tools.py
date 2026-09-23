"""Tools for Synthesis Experiment Worker.

Each function below is the stable operation contract for this agent. A framework
adapter (Yosys, OpenROAD, OpenSTA, or a licensed tool) is responsible for actually
performing the EDA work. Until a framework is bound through ``EDA_FRAMEWORK`` /
backend.type, every call returns a structured observation with status ``not_run``
and must not invoke a synthesizer, placer, router, equivalence engine, or simulator.

EDA focus for this tool module: One isolated RTL-to-netlist compile with a named hypothesis (script, flatten vs preserve hierarchy, library set). Adapter targets Yosys synth first; a licensed synthesizer later binds the same operations. Emits QoR proxies (area, cell counts, timing estimate), warnings (blackboxes, latches, loops), and a gate-level netlist.

Common return shape:
    ``tool_observation(name, payload, agent_id="synthesis_experiment")`` builds the dict the
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


# Register `write_synthesis_script` as an invocable skill: Write the versioned synthesis script for this experiment.
@tool(description='Write the versioned synthesis script for this experiment.')
def write_synthesis_script(
    candidate_ref: str = "",
    baseline_ref: str = "",
    hypothesis: str = "",
    params: dict | None = None,
) -> dict:
    """Write the versioned synthesis script for this experiment.

    Purpose:
        Write the versioned Yosys/synth script (or licensed-tool script) for this hypothesis.

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        baseline_ref: Artifact URI of the baseline netlist/design used for QoR or structural diffs.
        hypothesis: Single synthesis knob or setting this isolated experiment changes versus the baseline.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `write_synthesis_script` operation for agent `synthesis_experiment`. When no EDA framework is
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
    # Hand the `write_synthesis_script` operation to the shared observation helper for `synthesis_experiment`.
    return tool_observation(
        'write_synthesis_script',
        payload,
        agent_id='synthesis_experiment',
    )

# Register `write_compile_directives` as an invocable skill: Write compile, boundary, and optimization directives.
@tool(description='Write compile, boundary, and optimization directives.')
def write_compile_directives(
    candidate_ref: str = "",
    baseline_ref: str = "",
    hypothesis: str = "",
    params: dict | None = None,
) -> dict:
    """Write compile, boundary, and optimization directives.

    Purpose:
        Write compile, boundary optimization, and effort directives that define the experiment.

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        baseline_ref: Artifact URI of the baseline netlist/design used for QoR or structural diffs.
        hypothesis: Single synthesis knob or setting this isolated experiment changes versus the baseline.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `write_compile_directives` operation for agent `synthesis_experiment`. When no EDA framework is
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
    # Hand the `write_compile_directives` operation to the shared observation helper for `synthesis_experiment`.
    return tool_observation(
        'write_compile_directives',
        payload,
        agent_id='synthesis_experiment',
    )

# Register `preserve_hierarchy` as an invocable skill: Mark modules that must stay hierarchical.
@tool(description='Mark modules that must stay hierarchical.')
def preserve_hierarchy(
    candidate_ref: str = "",
    baseline_ref: str = "",
    hypothesis: str = "",
    modules: str = "",
    params: dict | None = None,
) -> dict:
    """Mark modules that must stay hierarchical.

    Purpose:
        Mark modules that must remain hierarchical for DFT, floorplan, or debug boundaries.

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        baseline_ref: Artifact URI of the baseline netlist/design used for QoR or structural diffs.
        hypothesis: Single synthesis knob or setting this isolated experiment changes versus the baseline.
        modules: `modules` for the `preserve_hierarchy` operation in this agent's EDA contract; forwarded into the observation payload for the bound framework adapter.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `preserve_hierarchy` operation for agent `synthesis_experiment`. When no EDA framework is
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
        'modules': modules,  # `modules` for the `preserve_hierarchy` operation in this agent's EDA contract; forwarded into the observation payload for the bound framework adapter.
    }
    # Merge optional adapter/planner overrides when the caller supplied params.
    if params:
        # params keys intentionally overwrite same-named explicit fields.
        payload.update(params)
    # Hand the `preserve_hierarchy` operation to the shared observation helper for `synthesis_experiment`.
    return tool_observation(
        'preserve_hierarchy',
        payload,
        agent_id='synthesis_experiment',
    )

# Register `flatten_hierarchy` as an invocable skill: Mark modules that this experiment may flatten.
@tool(description='Mark modules that this experiment may flatten.')
def flatten_hierarchy(
    candidate_ref: str = "",
    baseline_ref: str = "",
    hypothesis: str = "",
    modules: str = "",
    params: dict | None = None,
) -> dict:
    """Mark modules that this experiment may flatten.

    Purpose:
        Mark modules this experiment may flatten for better cross-boundary optimization.

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        baseline_ref: Artifact URI of the baseline netlist/design used for QoR or structural diffs.
        hypothesis: Single synthesis knob or setting this isolated experiment changes versus the baseline.
        modules: `modules` for the `flatten_hierarchy` operation in this agent's EDA contract; forwarded into the observation payload for the bound framework adapter.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `flatten_hierarchy` operation for agent `synthesis_experiment`. When no EDA framework is
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
        'modules': modules,  # `modules` for the `flatten_hierarchy` operation in this agent's EDA contract; forwarded into the observation payload for the bound framework adapter.
    }
    # Merge optional adapter/planner overrides when the caller supplied params.
    if params:
        # params keys intentionally overwrite same-named explicit fields.
        payload.update(params)
    # Hand the `flatten_hierarchy` operation to the shared observation helper for `synthesis_experiment`.
    return tool_observation(
        'flatten_hierarchy',
        payload,
        agent_id='synthesis_experiment',
    )

# Register `read_synthesis_libraries` as an invocable skill: Read the liberty libraries this experiment will link.
@tool(description='Read the liberty libraries this experiment will link.')
def read_synthesis_libraries(
    candidate_ref: str = "",
    report_ref: str = "",
    corner: str = "",
    mode: str = "",
    params: dict | None = None,
) -> dict:
    """Read the liberty libraries this experiment will link.

    Purpose:
        Read liberty (.lib) libraries this compile will link for mapping and timing proxies.

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        report_ref: Artifact URI of a specific report; empty selects the latest report for the candidate.
        corner: Process/voltage/temperature corner filter (e.g. SS/FF); empty reads every available corner.
        mode: Operating mode filter (functional, scan, etc.); empty reads every available mode.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `read_synthesis_libraries` operation for agent `synthesis_experiment`. When no EDA framework is
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
    # Hand the `read_synthesis_libraries` operation to the shared observation helper for `synthesis_experiment`.
    return tool_observation(
        'read_synthesis_libraries',
        payload,
        agent_id='synthesis_experiment',
    )

# Register `submit_synthesis` as an invocable skill: Run synthesis for one candidate and tool setting. Adapter target: yosys synth or the bound synthesizer.
@tool(description='Run synthesis for one candidate and tool setting. Adapter target: yosys synth or the bound synthesizer.')
def submit_synthesis(
    candidate_ref: str = "",
    baseline_ref: str = "",
    recipe: str = "",
    corner: str = "",
    mode: str = "",
    params: dict | None = None,
) -> dict:
    """Run synthesis for one candidate and tool setting. Adapter target: yosys synth or the bound synthesizer.

    Purpose:
        Run one synthesis job for this candidate; adapter target yosys synth or bound synthesizer.

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        baseline_ref: Artifact URI of the baseline netlist/design used for QoR or structural diffs.
        recipe: `recipe` for the `submit_synthesis` operation in this agent's EDA contract; forwarded into the observation payload for the bound framework adapter.
        corner: Process/voltage/temperature corner filter (e.g. SS/FF); empty reads every available corner.
        mode: Operating mode filter (functional, scan, etc.); empty reads every available mode.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `submit_synthesis` operation for agent `synthesis_experiment`. When no EDA framework is
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
        'recipe': recipe,  # `recipe` for the `submit_synthesis` operation in this agent's EDA contract; forwarded into the observation payload for the bound framework adapter.
        'corner': corner,  # Process/voltage/temperature corner filter (e.g. SS/FF); empty reads every available corner.
        'mode': mode,  # Operating mode filter (functional, scan, etc.); empty reads every available mode.
    }
    # Merge optional adapter/planner overrides when the caller supplied params.
    if params:
        # params keys intentionally overwrite same-named explicit fields.
        payload.update(params)
    # Hand the `submit_synthesis` operation to the shared observation helper for `synthesis_experiment`.
    return tool_observation(
        'submit_synthesis',
        payload,
        agent_id='synthesis_experiment',
    )

# Register `read_synthesis_log` as an invocable skill: Read the synthesis log.
@tool(description='Read the synthesis log.')
def read_synthesis_log(
    candidate_ref: str = "",
    report_ref: str = "",
    corner: str = "",
    mode: str = "",
    params: dict | None = None,
) -> dict:
    """Read the synthesis log.

    Purpose:
        Read the raw synthesis log for warnings, errors, and mapping messages.

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        report_ref: Artifact URI of a specific report; empty selects the latest report for the candidate.
        corner: Process/voltage/temperature corner filter (e.g. SS/FF); empty reads every available corner.
        mode: Operating mode filter (functional, scan, etc.); empty reads every available mode.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `read_synthesis_log` operation for agent `synthesis_experiment`. When no EDA framework is
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
    # Hand the `read_synthesis_log` operation to the shared observation helper for `synthesis_experiment`.
    return tool_observation(
        'read_synthesis_log',
        payload,
        agent_id='synthesis_experiment',
    )

# Register `summarize_qor` as an invocable skill: Return area, timing proxy, runtime, and warnings.
@tool(description='Return area, timing proxy, runtime, and warnings.')
def summarize_qor(
    candidate_ref: str = "",
    report_ref: str = "",
    corner: str = "",
    mode: str = "",
    params: dict | None = None,
) -> dict:
    """Return area, timing proxy, runtime, and warnings.

    Purpose:
        Return area, timing proxy, runtime, and warning counts for the lead's comparison table.

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        report_ref: Artifact URI of a specific report; empty selects the latest report for the candidate.
        corner: Process/voltage/temperature corner filter (e.g. SS/FF); empty reads every available corner.
        mode: Operating mode filter (functional, scan, etc.); empty reads every available mode.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `summarize_qor` operation for agent `synthesis_experiment`. When no EDA framework is
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
    # Hand the `summarize_qor` operation to the shared observation helper for `synthesis_experiment`.
    return tool_observation(
        'summarize_qor',
        payload,
        agent_id='synthesis_experiment',
    )

# Register `report_area` as an invocable skill: Report cell area and utilization.
@tool(description='Report cell area and utilization.')
def report_area(
    candidate_ref: str = "",
    report_ref: str = "",
    corner: str = "",
    mode: str = "",
    params: dict | None = None,
) -> dict:
    """Report cell area and utilization.

    Purpose:
        Report cell area and estimated utilization from the mapped netlist.

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        report_ref: Artifact URI of a specific report; empty selects the latest report for the candidate.
        corner: Process/voltage/temperature corner filter (e.g. SS/FF); empty reads every available corner.
        mode: Operating mode filter (functional, scan, etc.); empty reads every available mode.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `report_area` operation for agent `synthesis_experiment`. When no EDA framework is
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
    # Hand the `report_area` operation to the shared observation helper for `synthesis_experiment`.
    return tool_observation(
        'report_area',
        payload,
        agent_id='synthesis_experiment',
    )

# Register `report_cell_counts` as an invocable skill: Report cell counts by class.
@tool(description='Report cell counts by class.')
def report_cell_counts(
    candidate_ref: str = "",
    report_ref: str = "",
    corner: str = "",
    mode: str = "",
    params: dict | None = None,
) -> dict:
    """Report cell counts by class.

    Purpose:
        Report cell counts by class (combo, seq, clock, buffer) for structural insight.

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        report_ref: Artifact URI of a specific report; empty selects the latest report for the candidate.
        corner: Process/voltage/temperature corner filter (e.g. SS/FF); empty reads every available corner.
        mode: Operating mode filter (functional, scan, etc.); empty reads every available mode.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `report_cell_counts` operation for agent `synthesis_experiment`. When no EDA framework is
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
    # Hand the `report_cell_counts` operation to the shared observation helper for `synthesis_experiment`.
    return tool_observation(
        'report_cell_counts',
        payload,
        agent_id='synthesis_experiment',
    )

# Register `report_timing_proxy` as an invocable skill: Report the synthesis timing estimate. This is not signoff STA.
@tool(description='Report the synthesis timing estimate. This is not signoff STA.')
def report_timing_proxy(
    candidate_ref: str = "",
    report_ref: str = "",
    corner: str = "",
    mode: str = "",
    params: dict | None = None,
) -> dict:
    """Report the synthesis timing estimate. This is not signoff STA.

    Purpose:
        Report the synthesizer's timing estimate; this is not signoff static timing analysis.

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        report_ref: Artifact URI of a specific report; empty selects the latest report for the candidate.
        corner: Process/voltage/temperature corner filter (e.g. SS/FF); empty reads every available corner.
        mode: Operating mode filter (functional, scan, etc.); empty reads every available mode.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `report_timing_proxy` operation for agent `synthesis_experiment`. When no EDA framework is
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
    # Hand the `report_timing_proxy` operation to the shared observation helper for `synthesis_experiment`.
    return tool_observation(
        'report_timing_proxy',
        payload,
        agent_id='synthesis_experiment',
    )

# Register `report_synthesis_runtime` as an invocable skill: Report wall time and peak memory.
@tool(description='Report wall time and peak memory.')
def report_synthesis_runtime(
    candidate_ref: str = "",
    report_ref: str = "",
    corner: str = "",
    mode: str = "",
    params: dict | None = None,
) -> dict:
    """Report wall time and peak memory.

    Purpose:
        Report wall time and peak memory so expensive knobs can be weighed against QoR.

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        report_ref: Artifact URI of a specific report; empty selects the latest report for the candidate.
        corner: Process/voltage/temperature corner filter (e.g. SS/FF); empty reads every available corner.
        mode: Operating mode filter (functional, scan, etc.); empty reads every available mode.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `report_synthesis_runtime` operation for agent `synthesis_experiment`. When no EDA framework is
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
    # Hand the `report_synthesis_runtime` operation to the shared observation helper for `synthesis_experiment`.
    return tool_observation(
        'report_synthesis_runtime',
        payload,
        agent_id='synthesis_experiment',
    )

# Register `report_synthesis_warnings` as an invocable skill: List black boxes, latches, and unmapped cells from the log.
@tool(description='List black boxes, latches, and unmapped cells from the log.')
def report_synthesis_warnings(
    candidate_ref: str = "",
    report_ref: str = "",
    corner: str = "",
    mode: str = "",
    params: dict | None = None,
) -> dict:
    """List black boxes, latches, and unmapped cells from the log.

    Purpose:
        List black boxes, inferred latches, and unmapped cells called out in the log.

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        report_ref: Artifact URI of a specific report; empty selects the latest report for the candidate.
        corner: Process/voltage/temperature corner filter (e.g. SS/FF); empty reads every available corner.
        mode: Operating mode filter (functional, scan, etc.); empty reads every available mode.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `report_synthesis_warnings` operation for agent `synthesis_experiment`. When no EDA framework is
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
    # Hand the `report_synthesis_warnings` operation to the shared observation helper for `synthesis_experiment`.
    return tool_observation(
        'report_synthesis_warnings',
        payload,
        agent_id='synthesis_experiment',
    )

# Register `diff_qor_against_baseline` as an invocable skill: Compare area, cell counts, and timing proxy with the baseline netlist.
@tool(description='Compare area, cell counts, and timing proxy with the baseline netlist.')
def diff_qor_against_baseline(
    candidate_ref: str = "",
    report_ref: str = "",
    corner: str = "",
    mode: str = "",
    params: dict | None = None,
) -> dict:
    """Compare area, cell counts, and timing proxy with the baseline netlist.

    Purpose:
        Compare area, cell counts, and timing proxy versus the recorded baseline netlist.

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        report_ref: Artifact URI of a specific report; empty selects the latest report for the candidate.
        corner: Process/voltage/temperature corner filter (e.g. SS/FF); empty reads every available corner.
        mode: Operating mode filter (functional, scan, etc.); empty reads every available mode.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `diff_qor_against_baseline` operation for agent `synthesis_experiment`. When no EDA framework is
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
    # Hand the `diff_qor_against_baseline` operation to the shared observation helper for `synthesis_experiment`.
    return tool_observation(
        'diff_qor_against_baseline',
        payload,
        agent_id='synthesis_experiment',
    )

# Register `emit_netlist` as an invocable skill: Write the gate-level netlist artifact for this candidate.
@tool(description='Write the gate-level netlist artifact for this candidate.')
def emit_netlist(
    candidate_ref: str = "",
    baseline_ref: str = "",
    recipe: str = "",
    corner: str = "",
    mode: str = "",
    params: dict | None = None,
) -> dict:
    """Write the gate-level netlist artifact for this candidate.

    Purpose:
        Write the gate-level Verilog/netlist artifact for downstream equivalence and floorplan.

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        baseline_ref: Artifact URI of the baseline netlist/design used for QoR or structural diffs.
        recipe: `recipe` for the `emit_netlist` operation in this agent's EDA contract; forwarded into the observation payload for the bound framework adapter.
        corner: Process/voltage/temperature corner filter (e.g. SS/FF); empty reads every available corner.
        mode: Operating mode filter (functional, scan, etc.); empty reads every available mode.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `emit_netlist` operation for agent `synthesis_experiment`. When no EDA framework is
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
        'recipe': recipe,  # `recipe` for the `emit_netlist` operation in this agent's EDA contract; forwarded into the observation payload for the bound framework adapter.
        'corner': corner,  # Process/voltage/temperature corner filter (e.g. SS/FF); empty reads every available corner.
        'mode': mode,  # Operating mode filter (functional, scan, etc.); empty reads every available mode.
    }
    # Merge optional adapter/planner overrides when the caller supplied params.
    if params:
        # params keys intentionally overwrite same-named explicit fields.
        payload.update(params)
    # Hand the `emit_netlist` operation to the shared observation helper for `synthesis_experiment`.
    return tool_observation(
        'emit_netlist',
        payload,
        agent_id='synthesis_experiment',
    )

# Register `check_blackboxes` as an invocable skill: List modules left as black boxes.
@tool(description='List modules left as black boxes.')
def check_blackboxes(
    candidate_ref: str = "",
    report_ref: str = "",
    corner: str = "",
    mode: str = "",
    params: dict | None = None,
) -> dict:
    """List modules left as black boxes.

    Purpose:
        List modules left as black boxes (missing RTL or intentionally empty).

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        report_ref: Artifact URI of a specific report; empty selects the latest report for the candidate.
        corner: Process/voltage/temperature corner filter (e.g. SS/FF); empty reads every available corner.
        mode: Operating mode filter (functional, scan, etc.); empty reads every available mode.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `check_blackboxes` operation for agent `synthesis_experiment`. When no EDA framework is
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
    # Hand the `check_blackboxes` operation to the shared observation helper for `synthesis_experiment`.
    return tool_observation(
        'check_blackboxes',
        payload,
        agent_id='synthesis_experiment',
    )

# Register `check_inferred_latches` as an invocable skill: List inferred latches.
@tool(description='List inferred latches.')
def check_inferred_latches(
    candidate_ref: str = "",
    report_ref: str = "",
    corner: str = "",
    mode: str = "",
    params: dict | None = None,
) -> dict:
    """List inferred latches.

    Purpose:
        List inferred latches, often a sign of incomplete RTL assignments.

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        report_ref: Artifact URI of a specific report; empty selects the latest report for the candidate.
        corner: Process/voltage/temperature corner filter (e.g. SS/FF); empty reads every available corner.
        mode: Operating mode filter (functional, scan, etc.); empty reads every available mode.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `check_inferred_latches` operation for agent `synthesis_experiment`. When no EDA framework is
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
    # Hand the `check_inferred_latches` operation to the shared observation helper for `synthesis_experiment`.
    return tool_observation(
        'check_inferred_latches',
        payload,
        agent_id='synthesis_experiment',
    )

# Register `check_combinational_loops` as an invocable skill: List combinational loops in the netlist.
@tool(description='List combinational loops in the netlist.')
def check_combinational_loops(
    candidate_ref: str = "",
    report_ref: str = "",
    corner: str = "",
    mode: str = "",
    params: dict | None = None,
) -> dict:
    """List combinational loops in the netlist.

    Purpose:
        List combinational loops in the netlist that break timing and DFT assumptions.

    Args:
        candidate_ref: Artifact URI or memory id of the design candidate whose reports are read.
        report_ref: Artifact URI of a specific report; empty selects the latest report for the candidate.
        corner: Process/voltage/temperature corner filter (e.g. SS/FF); empty reads every available corner.
        mode: Operating mode filter (functional, scan, etc.); empty reads every available mode.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `check_combinational_loops` operation for agent `synthesis_experiment`. When no EDA framework is
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
    # Hand the `check_combinational_loops` operation to the shared observation helper for `synthesis_experiment`.
    return tool_observation(
        'check_combinational_loops',
        payload,
        agent_id='synthesis_experiment',
    )

# Register `record_synthesis_tool_version` as an invocable skill: Record the synthesizer, version, script, and library set.
@tool(description='Record the synthesizer, version, script, and library set.')
def record_synthesis_tool_version(
    summary: str = "",
    evidence_refs: str = "",
    severity: str = "",
    recommended_recipient: str = "",
    params: dict | None = None,
) -> dict:
    """Record the synthesizer, version, script, and library set.

    Purpose:
        Record synthesizer binary, version, script hash, and library set for provenance.

    Args:
        summary: One-sentence finding written into engineering memory for downstream agents.
        evidence_refs: Comma-separated artifact URIs that substantiate the finding or tradeoff.
        severity: Finding severity: low, medium, high, or critical relative to hard requirements.
        recommended_recipient: Agent id that should act next on this finding.
        params: Optional dict of extra adapter knobs merged into the observation payload.

    Returns:
        dict observation from ``tool_observation`` describing the requested
        `record_synthesis_tool_version` operation for agent `synthesis_experiment`. When no EDA framework is
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
    # Hand the `record_synthesis_tool_version` operation to the shared observation helper for `synthesis_experiment`.
    return tool_observation(
        'record_synthesis_tool_version',
        payload,
        agent_id='synthesis_experiment',
    )
