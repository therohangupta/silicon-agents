"""Tools for the uvm_environment agent in the EDA chip-design agent fleet.

Operation contracts for the uvm_environment verification specialist.

This module is the stable operation contract for the UVM environment specialist that authors drivers, monitors, scoreboards, agents, and sequences for one RTL block. Each ``@tool``
function is a skill the LLM or orchestrator may invoke. Bodies do not call a
simulator, formal engine, or OpenROAD directly: they assemble a typed payload
and return ``tool_observation(...)``. Until a framework adapter is bound,
observations typically surface status ``not_run`` and never invoke OpenROAD,
Yosys, OpenSTA, a licensed EDA tool, or a UVM simulator. Skill names must stay
aligned with this agent's ``config.yaml`` capabilities and skills lists.
"""

from __future__ import annotations  # Allow dict | None annotations without runtime evaluation cost.

from packages.agent_sdk import tool  # Registers each callable as a discoverable agent skill.
from domains.eda.adapters import tool_observation  # Builds the standard observation dict (status, payload, agent_id).


@tool(description='Create the UVM environment package from the interface contract.')
def generate_uvm_environment(
    candidate_ref: str = "",  # Artifact URI/id of the pinned RTL candidate under verification.
    baseline_ref: str = "",  # Baseline candidate or golden revision used for comparison.
    hypothesis: str = "",  # Working hypothesis or change intent guiding this edit/analysis.
    params: dict | None = None,  # Optional adapter-specific fields merged into the observation payload.
) -> dict:
    """Create the UVM environment package from the interface contract.

    Purpose:
        For the UVM environment specialist that authors drivers, monitors, scoreboards, agents, and sequences for one RTL block: Create the UVM environment package from the interface contract.
        Invoking ``generate_uvm_environment`` records the intended verification operation for agent ``uvm_environment``.
        A bound framework adapter performs the real EDA work; this process only builds the observation.

    Arguments:
        candidate_ref: Artifact URI/id of the pinned RTL candidate under verification.
        baseline_ref: Baseline candidate or golden revision used for comparison.
        hypothesis: Working hypothesis or change intent guiding this edit/analysis.
        params: Optional adapter-specific fields merged into the observation payload.

    Returns:
        A ``tool_observation`` dict for skill ``generate_uvm_environment`` with ``agent_id='uvm_environment'``.

    Side effects:
        None in-process. A bound adapter may read/write silicon-store artifacts, submit farm jobs,
        or publish findings into engineering memory.

    Failure behavior:
        Until an adapter is bound, the observation typically reports ``not_run`` and does not
        invoke simulators, formal engines, OpenROAD, Yosys, or OpenSTA. Empty fields are still
        forwarded so the adapter can reject them explicitly.
    """
    # Payload keys mirror config.yaml skill params so AgentService can validate and dispatch.
    payload = {
        'candidate_ref': candidate_ref,  # Artifact URI/id of the pinned RTL candidate under verification.
        'baseline_ref': baseline_ref,  # Baseline candidate or golden revision used for comparison.
        'hypothesis': hypothesis,  # Working hypothesis or change intent guiding this edit/analysis.
    }
    if params:
        # Optional extras override base keys so framework adapters can extend the contract.
        payload.update(params)
    return tool_observation(
        'generate_uvm_environment',  # Skill id; must match this agent's config.yaml skills[].callable.
        payload,  # Structured arguments consumed by the bound framework adapter.
        agent_id='uvm_environment',  # Telemetry and journal attribution for this specialist.
    )


@tool(description='Write the driver for one interface.')
def write_uvm_driver(
    candidate_ref: str = "",  # Artifact URI/id of the pinned RTL candidate under verification.
    baseline_ref: str = "",  # Baseline candidate or golden revision used for comparison.
    hypothesis: str = "",  # Working hypothesis or change intent guiding this edit/analysis.
    interface_id: str = "",  # UVM/DUT interface identifier this driver/monitor/agent targets.
    params: dict | None = None,  # Optional adapter-specific fields merged into the observation payload.
) -> dict:
    """Write the driver for one interface.

    Purpose:
        For the UVM environment specialist that authors drivers, monitors, scoreboards, agents, and sequences for one RTL block: Write the driver for one interface.
        Invoking ``write_uvm_driver`` records the intended verification operation for agent ``uvm_environment``.
        A bound framework adapter performs the real EDA work; this process only builds the observation.

    Arguments:
        candidate_ref: Artifact URI/id of the pinned RTL candidate under verification.
        baseline_ref: Baseline candidate or golden revision used for comparison.
        hypothesis: Working hypothesis or change intent guiding this edit/analysis.
        interface_id: UVM/DUT interface identifier this driver/monitor/agent targets.
        params: Optional adapter-specific fields merged into the observation payload.

    Returns:
        A ``tool_observation`` dict for skill ``write_uvm_driver`` with ``agent_id='uvm_environment'``.

    Side effects:
        None in-process. A bound adapter may read/write silicon-store artifacts, submit farm jobs,
        or publish findings into engineering memory.

    Failure behavior:
        Until an adapter is bound, the observation typically reports ``not_run`` and does not
        invoke simulators, formal engines, OpenROAD, Yosys, or OpenSTA. Empty fields are still
        forwarded so the adapter can reject them explicitly.
    """
    # Payload keys mirror config.yaml skill params so AgentService can validate and dispatch.
    payload = {
        'candidate_ref': candidate_ref,  # Artifact URI/id of the pinned RTL candidate under verification.
        'baseline_ref': baseline_ref,  # Baseline candidate or golden revision used for comparison.
        'hypothesis': hypothesis,  # Working hypothesis or change intent guiding this edit/analysis.
        'interface_id': interface_id,  # UVM/DUT interface identifier this driver/monitor/agent targets.
    }
    if params:
        # Optional extras override base keys so framework adapters can extend the contract.
        payload.update(params)
    return tool_observation(
        'write_uvm_driver',  # Skill id; must match this agent's config.yaml skills[].callable.
        payload,  # Structured arguments consumed by the bound framework adapter.
        agent_id='uvm_environment',  # Telemetry and journal attribution for this specialist.
    )


@tool(description='Write the monitor for one interface.')
def write_uvm_monitor(
    candidate_ref: str = "",  # Artifact URI/id of the pinned RTL candidate under verification.
    baseline_ref: str = "",  # Baseline candidate or golden revision used for comparison.
    hypothesis: str = "",  # Working hypothesis or change intent guiding this edit/analysis.
    interface_id: str = "",  # UVM/DUT interface identifier this driver/monitor/agent targets.
    params: dict | None = None,  # Optional adapter-specific fields merged into the observation payload.
) -> dict:
    """Write the monitor for one interface.

    Purpose:
        For the UVM environment specialist that authors drivers, monitors, scoreboards, agents, and sequences for one RTL block: Write the monitor for one interface.
        Invoking ``write_uvm_monitor`` records the intended verification operation for agent ``uvm_environment``.
        A bound framework adapter performs the real EDA work; this process only builds the observation.

    Arguments:
        candidate_ref: Artifact URI/id of the pinned RTL candidate under verification.
        baseline_ref: Baseline candidate or golden revision used for comparison.
        hypothesis: Working hypothesis or change intent guiding this edit/analysis.
        interface_id: UVM/DUT interface identifier this driver/monitor/agent targets.
        params: Optional adapter-specific fields merged into the observation payload.

    Returns:
        A ``tool_observation`` dict for skill ``write_uvm_monitor`` with ``agent_id='uvm_environment'``.

    Side effects:
        None in-process. A bound adapter may read/write silicon-store artifacts, submit farm jobs,
        or publish findings into engineering memory.

    Failure behavior:
        Until an adapter is bound, the observation typically reports ``not_run`` and does not
        invoke simulators, formal engines, OpenROAD, Yosys, or OpenSTA. Empty fields are still
        forwarded so the adapter can reject them explicitly.
    """
    # Payload keys mirror config.yaml skill params so AgentService can validate and dispatch.
    payload = {
        'candidate_ref': candidate_ref,  # Artifact URI/id of the pinned RTL candidate under verification.
        'baseline_ref': baseline_ref,  # Baseline candidate or golden revision used for comparison.
        'hypothesis': hypothesis,  # Working hypothesis or change intent guiding this edit/analysis.
        'interface_id': interface_id,  # UVM/DUT interface identifier this driver/monitor/agent targets.
    }
    if params:
        # Optional extras override base keys so framework adapters can extend the contract.
        payload.update(params)
    return tool_observation(
        'write_uvm_monitor',  # Skill id; must match this agent's config.yaml skills[].callable.
        payload,  # Structured arguments consumed by the bound framework adapter.
        agent_id='uvm_environment',  # Telemetry and journal attribution for this specialist.
    )


@tool(description='Write the scoreboard that compares DUT outputs with the reference model.')
def write_uvm_scoreboard(
    candidate_ref: str = "",  # Artifact URI/id of the pinned RTL candidate under verification.
    baseline_ref: str = "",  # Baseline candidate or golden revision used for comparison.
    hypothesis: str = "",  # Working hypothesis or change intent guiding this edit/analysis.
    params: dict | None = None,  # Optional adapter-specific fields merged into the observation payload.
) -> dict:
    """Write the scoreboard that compares DUT outputs with the reference model.

    Purpose:
        For the UVM environment specialist that authors drivers, monitors, scoreboards, agents, and sequences for one RTL block: Write the scoreboard that compares DUT outputs with the reference model.
        Invoking ``write_uvm_scoreboard`` records the intended verification operation for agent ``uvm_environment``.
        A bound framework adapter performs the real EDA work; this process only builds the observation.

    Arguments:
        candidate_ref: Artifact URI/id of the pinned RTL candidate under verification.
        baseline_ref: Baseline candidate or golden revision used for comparison.
        hypothesis: Working hypothesis or change intent guiding this edit/analysis.
        params: Optional adapter-specific fields merged into the observation payload.

    Returns:
        A ``tool_observation`` dict for skill ``write_uvm_scoreboard`` with ``agent_id='uvm_environment'``.

    Side effects:
        None in-process. A bound adapter may read/write silicon-store artifacts, submit farm jobs,
        or publish findings into engineering memory.

    Failure behavior:
        Until an adapter is bound, the observation typically reports ``not_run`` and does not
        invoke simulators, formal engines, OpenROAD, Yosys, or OpenSTA. Empty fields are still
        forwarded so the adapter can reject them explicitly.
    """
    # Payload keys mirror config.yaml skill params so AgentService can validate and dispatch.
    payload = {
        'candidate_ref': candidate_ref,  # Artifact URI/id of the pinned RTL candidate under verification.
        'baseline_ref': baseline_ref,  # Baseline candidate or golden revision used for comparison.
        'hypothesis': hypothesis,  # Working hypothesis or change intent guiding this edit/analysis.
    }
    if params:
        # Optional extras override base keys so framework adapters can extend the contract.
        payload.update(params)
    return tool_observation(
        'write_uvm_scoreboard',  # Skill id; must match this agent's config.yaml skills[].callable.
        payload,  # Structured arguments consumed by the bound framework adapter.
        agent_id='uvm_environment',  # Telemetry and journal attribution for this specialist.
    )


@tool(description='Write the agent that binds driver, monitor, and sequencer.')
def write_uvm_agent(
    candidate_ref: str = "",  # Artifact URI/id of the pinned RTL candidate under verification.
    baseline_ref: str = "",  # Baseline candidate or golden revision used for comparison.
    hypothesis: str = "",  # Working hypothesis or change intent guiding this edit/analysis.
    params: dict | None = None,  # Optional adapter-specific fields merged into the observation payload.
) -> dict:
    """Write the agent that binds driver, monitor, and sequencer.

    Purpose:
        For the UVM environment specialist that authors drivers, monitors, scoreboards, agents, and sequences for one RTL block: Write the agent that binds driver, monitor, and sequencer.
        Invoking ``write_uvm_agent`` records the intended verification operation for agent ``uvm_environment``.
        A bound framework adapter performs the real EDA work; this process only builds the observation.

    Arguments:
        candidate_ref: Artifact URI/id of the pinned RTL candidate under verification.
        baseline_ref: Baseline candidate or golden revision used for comparison.
        hypothesis: Working hypothesis or change intent guiding this edit/analysis.
        params: Optional adapter-specific fields merged into the observation payload.

    Returns:
        A ``tool_observation`` dict for skill ``write_uvm_agent`` with ``agent_id='uvm_environment'``.

    Side effects:
        None in-process. A bound adapter may read/write silicon-store artifacts, submit farm jobs,
        or publish findings into engineering memory.

    Failure behavior:
        Until an adapter is bound, the observation typically reports ``not_run`` and does not
        invoke simulators, formal engines, OpenROAD, Yosys, or OpenSTA. Empty fields are still
        forwarded so the adapter can reject them explicitly.
    """
    # Payload keys mirror config.yaml skill params so AgentService can validate and dispatch.
    payload = {
        'candidate_ref': candidate_ref,  # Artifact URI/id of the pinned RTL candidate under verification.
        'baseline_ref': baseline_ref,  # Baseline candidate or golden revision used for comparison.
        'hypothesis': hypothesis,  # Working hypothesis or change intent guiding this edit/analysis.
    }
    if params:
        # Optional extras override base keys so framework adapters can extend the contract.
        payload.update(params)
    return tool_observation(
        'write_uvm_agent',  # Skill id; must match this agent's config.yaml skills[].callable.
        payload,  # Structured arguments consumed by the bound framework adapter.
        agent_id='uvm_environment',  # Telemetry and journal attribution for this specialist.
    )


@tool(description='Write the base sequence library for this block.')
def write_uvm_sequence_library(
    candidate_ref: str = "",  # Artifact URI/id of the pinned RTL candidate under verification.
    baseline_ref: str = "",  # Baseline candidate or golden revision used for comparison.
    hypothesis: str = "",  # Working hypothesis or change intent guiding this edit/analysis.
    params: dict | None = None,  # Optional adapter-specific fields merged into the observation payload.
) -> dict:
    """Write the base sequence library for this block.

    Purpose:
        For the UVM environment specialist that authors drivers, monitors, scoreboards, agents, and sequences for one RTL block: Write the base sequence library for this block.
        Invoking ``write_uvm_sequence_library`` records the intended verification operation for agent ``uvm_environment``.
        A bound framework adapter performs the real EDA work; this process only builds the observation.

    Arguments:
        candidate_ref: Artifact URI/id of the pinned RTL candidate under verification.
        baseline_ref: Baseline candidate or golden revision used for comparison.
        hypothesis: Working hypothesis or change intent guiding this edit/analysis.
        params: Optional adapter-specific fields merged into the observation payload.

    Returns:
        A ``tool_observation`` dict for skill ``write_uvm_sequence_library`` with ``agent_id='uvm_environment'``.

    Side effects:
        None in-process. A bound adapter may read/write silicon-store artifacts, submit farm jobs,
        or publish findings into engineering memory.

    Failure behavior:
        Until an adapter is bound, the observation typically reports ``not_run`` and does not
        invoke simulators, formal engines, OpenROAD, Yosys, or OpenSTA. Empty fields are still
        forwarded so the adapter can reject them explicitly.
    """
    # Payload keys mirror config.yaml skill params so AgentService can validate and dispatch.
    payload = {
        'candidate_ref': candidate_ref,  # Artifact URI/id of the pinned RTL candidate under verification.
        'baseline_ref': baseline_ref,  # Baseline candidate or golden revision used for comparison.
        'hypothesis': hypothesis,  # Working hypothesis or change intent guiding this edit/analysis.
    }
    if params:
        # Optional extras override base keys so framework adapters can extend the contract.
        payload.update(params)
    return tool_observation(
        'write_uvm_sequence_library',  # Skill id; must match this agent's config.yaml skills[].callable.
        payload,  # Structured arguments consumed by the bound framework adapter.
        agent_id='uvm_environment',  # Telemetry and journal attribution for this specialist.
    )


@tool(description='Write the configuration object and factory overrides.')
def write_uvm_config(
    candidate_ref: str = "",  # Artifact URI/id of the pinned RTL candidate under verification.
    baseline_ref: str = "",  # Baseline candidate or golden revision used for comparison.
    hypothesis: str = "",  # Working hypothesis or change intent guiding this edit/analysis.
    params: dict | None = None,  # Optional adapter-specific fields merged into the observation payload.
) -> dict:
    """Write the configuration object and factory overrides.

    Purpose:
        For the UVM environment specialist that authors drivers, monitors, scoreboards, agents, and sequences for one RTL block: Write the configuration object and factory overrides.
        Invoking ``write_uvm_config`` records the intended verification operation for agent ``uvm_environment``.
        A bound framework adapter performs the real EDA work; this process only builds the observation.

    Arguments:
        candidate_ref: Artifact URI/id of the pinned RTL candidate under verification.
        baseline_ref: Baseline candidate or golden revision used for comparison.
        hypothesis: Working hypothesis or change intent guiding this edit/analysis.
        params: Optional adapter-specific fields merged into the observation payload.

    Returns:
        A ``tool_observation`` dict for skill ``write_uvm_config`` with ``agent_id='uvm_environment'``.

    Side effects:
        None in-process. A bound adapter may read/write silicon-store artifacts, submit farm jobs,
        or publish findings into engineering memory.

    Failure behavior:
        Until an adapter is bound, the observation typically reports ``not_run`` and does not
        invoke simulators, formal engines, OpenROAD, Yosys, or OpenSTA. Empty fields are still
        forwarded so the adapter can reject them explicitly.
    """
    # Payload keys mirror config.yaml skill params so AgentService can validate and dispatch.
    payload = {
        'candidate_ref': candidate_ref,  # Artifact URI/id of the pinned RTL candidate under verification.
        'baseline_ref': baseline_ref,  # Baseline candidate or golden revision used for comparison.
        'hypothesis': hypothesis,  # Working hypothesis or change intent guiding this edit/analysis.
    }
    if params:
        # Optional extras override base keys so framework adapters can extend the contract.
        payload.update(params)
    return tool_observation(
        'write_uvm_config',  # Skill id; must match this agent's config.yaml skills[].callable.
        payload,  # Structured arguments consumed by the bound framework adapter.
        agent_id='uvm_environment',  # Telemetry and journal attribution for this specialist.
    )


@tool(description='Bind virtual interfaces to the DUT ports in the isolated branch.')
def bind_uvm_interfaces(
    candidate_ref: str = "",  # Artifact URI/id of the pinned RTL candidate under verification.
    baseline_ref: str = "",  # Baseline candidate or golden revision used for comparison.
    hypothesis: str = "",  # Working hypothesis or change intent guiding this edit/analysis.
    params: dict | None = None,  # Optional adapter-specific fields merged into the observation payload.
) -> dict:
    """Bind virtual interfaces to the DUT ports in the isolated branch.

    Purpose:
        For the UVM environment specialist that authors drivers, monitors, scoreboards, agents, and sequences for one RTL block: Bind virtual interfaces to the DUT ports in the isolated branch.
        Invoking ``bind_uvm_interfaces`` records the intended verification operation for agent ``uvm_environment``.
        A bound framework adapter performs the real EDA work; this process only builds the observation.

    Arguments:
        candidate_ref: Artifact URI/id of the pinned RTL candidate under verification.
        baseline_ref: Baseline candidate or golden revision used for comparison.
        hypothesis: Working hypothesis or change intent guiding this edit/analysis.
        params: Optional adapter-specific fields merged into the observation payload.

    Returns:
        A ``tool_observation`` dict for skill ``bind_uvm_interfaces`` with ``agent_id='uvm_environment'``.

    Side effects:
        None in-process. A bound adapter may read/write silicon-store artifacts, submit farm jobs,
        or publish findings into engineering memory.

    Failure behavior:
        Until an adapter is bound, the observation typically reports ``not_run`` and does not
        invoke simulators, formal engines, OpenROAD, Yosys, or OpenSTA. Empty fields are still
        forwarded so the adapter can reject them explicitly.
    """
    # Payload keys mirror config.yaml skill params so AgentService can validate and dispatch.
    payload = {
        'candidate_ref': candidate_ref,  # Artifact URI/id of the pinned RTL candidate under verification.
        'baseline_ref': baseline_ref,  # Baseline candidate or golden revision used for comparison.
        'hypothesis': hypothesis,  # Working hypothesis or change intent guiding this edit/analysis.
    }
    if params:
        # Optional extras override base keys so framework adapters can extend the contract.
        payload.update(params)
    return tool_observation(
        'bind_uvm_interfaces',  # Skill id; must match this agent's config.yaml skills[].callable.
        payload,  # Structured arguments consumed by the bound framework adapter.
        agent_id='uvm_environment',  # Telemetry and journal attribution for this specialist.
    )


@tool(description='Adjust the scoreboard for one clarified requirement.')
def update_scoreboard(
    candidate_ref: str = "",  # Artifact URI/id of the pinned RTL candidate under verification.
    baseline_ref: str = "",  # Baseline candidate or golden revision used for comparison.
    hypothesis: str = "",  # Working hypothesis or change intent guiding this edit/analysis.
    requirement_id: str = "",  # Argument ``requirement_id`` forwarded into the observation payload for this EDA skill.
    params: dict | None = None,  # Optional adapter-specific fields merged into the observation payload.
) -> dict:
    """Adjust the scoreboard for one clarified requirement.

    Purpose:
        For the UVM environment specialist that authors drivers, monitors, scoreboards, agents, and sequences for one RTL block: Adjust the scoreboard for one clarified requirement.
        Invoking ``update_scoreboard`` records the intended verification operation for agent ``uvm_environment``.
        A bound framework adapter performs the real EDA work; this process only builds the observation.

    Arguments:
        candidate_ref: Artifact URI/id of the pinned RTL candidate under verification.
        baseline_ref: Baseline candidate or golden revision used for comparison.
        hypothesis: Working hypothesis or change intent guiding this edit/analysis.
        requirement_id: Payload field ``requirement_id``.
        params: Optional adapter-specific fields merged into the observation payload.

    Returns:
        A ``tool_observation`` dict for skill ``update_scoreboard`` with ``agent_id='uvm_environment'``.

    Side effects:
        None in-process. A bound adapter may read/write silicon-store artifacts, submit farm jobs,
        or publish findings into engineering memory.

    Failure behavior:
        Until an adapter is bound, the observation typically reports ``not_run`` and does not
        invoke simulators, formal engines, OpenROAD, Yosys, or OpenSTA. Empty fields are still
        forwarded so the adapter can reject them explicitly.
    """
    # Payload keys mirror config.yaml skill params so AgentService can validate and dispatch.
    payload = {
        'candidate_ref': candidate_ref,  # Artifact URI/id of the pinned RTL candidate under verification.
        'baseline_ref': baseline_ref,  # Baseline candidate or golden revision used for comparison.
        'hypothesis': hypothesis,  # Working hypothesis or change intent guiding this edit/analysis.
        'requirement_id': requirement_id,  # Field ``requirement_id`` required by this verification operation.
    }
    if params:
        # Optional extras override base keys so framework adapters can extend the contract.
        payload.update(params)
    return tool_observation(
        'update_scoreboard',  # Skill id; must match this agent's config.yaml skills[].callable.
        payload,  # Structured arguments consumed by the bound framework adapter.
        agent_id='uvm_environment',  # Telemetry and journal attribution for this specialist.
    )


@tool(description='Read the interface contract this environment implements.')
def read_uvm_interface_contract(
    candidate_ref: str = "",  # Artifact URI/id of the pinned RTL candidate under verification.
    report_ref: str = "",  # Artifact URI of a report; empty means the latest for this candidate.
    corner: str = "",  # PVT corner filter; empty reads every available corner.
    mode: str = "",  # Operating-mode filter; empty reads every available mode.
    params: dict | None = None,  # Optional adapter-specific fields merged into the observation payload.
) -> dict:
    """Read the interface contract this environment implements.

    Purpose:
        For the UVM environment specialist that authors drivers, monitors, scoreboards, agents, and sequences for one RTL block: Read the interface contract this environment implements.
        Invoking ``read_uvm_interface_contract`` records the intended verification operation for agent ``uvm_environment``.
        A bound framework adapter performs the real EDA work; this process only builds the observation.

    Arguments:
        candidate_ref: Artifact URI/id of the pinned RTL candidate under verification.
        report_ref: Artifact URI of a report; empty means the latest for this candidate.
        corner: PVT corner filter; empty reads every available corner.
        mode: Operating-mode filter; empty reads every available mode.
        params: Optional adapter-specific fields merged into the observation payload.

    Returns:
        A ``tool_observation`` dict for skill ``read_uvm_interface_contract`` with ``agent_id='uvm_environment'``.

    Side effects:
        None in-process. A bound adapter may read/write silicon-store artifacts, submit farm jobs,
        or publish findings into engineering memory.

    Failure behavior:
        Until an adapter is bound, the observation typically reports ``not_run`` and does not
        invoke simulators, formal engines, OpenROAD, Yosys, or OpenSTA. Empty fields are still
        forwarded so the adapter can reject them explicitly.
    """
    # Payload keys mirror config.yaml skill params so AgentService can validate and dispatch.
    payload = {
        'candidate_ref': candidate_ref,  # Artifact URI/id of the pinned RTL candidate under verification.
        'report_ref': report_ref,  # Artifact URI of a report; empty means the latest for this candidate.
        'corner': corner,  # PVT corner filter; empty reads every available corner.
        'mode': mode,  # Operating-mode filter; empty reads every available mode.
    }
    if params:
        # Optional extras override base keys so framework adapters can extend the contract.
        payload.update(params)
    return tool_observation(
        'read_uvm_interface_contract',  # Skill id; must match this agent's config.yaml skills[].callable.
        payload,  # Structured arguments consumed by the bound framework adapter.
        agent_id='uvm_environment',  # Telemetry and journal attribution for this specialist.
    )


@tool(description='Compile the environment and the DUT in the isolated branch.')
def compile_uvm_environment(
    candidate_ref: str = "",  # Artifact URI/id of the pinned RTL candidate under verification.
    baseline_ref: str = "",  # Baseline candidate or golden revision used for comparison.
    recipe: str = "",  # Frozen compile/run recipe id (plusargs, defines, tool options).
    corner: str = "",  # PVT corner filter; empty reads every available corner.
    mode: str = "",  # Operating-mode filter; empty reads every available mode.
    params: dict | None = None,  # Optional adapter-specific fields merged into the observation payload.
) -> dict:
    """Compile the environment and the DUT in the isolated branch.

    Purpose:
        For the UVM environment specialist that authors drivers, monitors, scoreboards, agents, and sequences for one RTL block: Compile the environment and the DUT in the isolated branch.
        Invoking ``compile_uvm_environment`` records the intended verification operation for agent ``uvm_environment``.
        A bound framework adapter performs the real EDA work; this process only builds the observation.

    Arguments:
        candidate_ref: Artifact URI/id of the pinned RTL candidate under verification.
        baseline_ref: Baseline candidate or golden revision used for comparison.
        recipe: Frozen compile/run recipe id (plusargs, defines, tool options).
        corner: PVT corner filter; empty reads every available corner.
        mode: Operating-mode filter; empty reads every available mode.
        params: Optional adapter-specific fields merged into the observation payload.

    Returns:
        A ``tool_observation`` dict for skill ``compile_uvm_environment`` with ``agent_id='uvm_environment'``.

    Side effects:
        None in-process. A bound adapter may read/write silicon-store artifacts, submit farm jobs,
        or publish findings into engineering memory.

    Failure behavior:
        Until an adapter is bound, the observation typically reports ``not_run`` and does not
        invoke simulators, formal engines, OpenROAD, Yosys, or OpenSTA. Empty fields are still
        forwarded so the adapter can reject them explicitly.
    """
    # Payload keys mirror config.yaml skill params so AgentService can validate and dispatch.
    payload = {
        'candidate_ref': candidate_ref,  # Artifact URI/id of the pinned RTL candidate under verification.
        'baseline_ref': baseline_ref,  # Baseline candidate or golden revision used for comparison.
        'recipe': recipe,  # Frozen compile/run recipe id (plusargs, defines, tool options).
        'corner': corner,  # PVT corner filter; empty reads every available corner.
        'mode': mode,  # Operating-mode filter; empty reads every available mode.
    }
    if params:
        # Optional extras override base keys so framework adapters can extend the contract.
        payload.update(params)
    return tool_observation(
        'compile_uvm_environment',  # Skill id; must match this agent's config.yaml skills[].callable.
        payload,  # Structured arguments consumed by the bound framework adapter.
        agent_id='uvm_environment',  # Telemetry and journal attribution for this specialist.
    )


@tool(description='Run one smoke test and return the log.')
def run_uvm_smoke(
    candidate_ref: str = "",  # Artifact URI/id of the pinned RTL candidate under verification.
    baseline_ref: str = "",  # Baseline candidate or golden revision used for comparison.
    recipe: str = "",  # Frozen compile/run recipe id (plusargs, defines, tool options).
    corner: str = "",  # PVT corner filter; empty reads every available corner.
    mode: str = "",  # Operating-mode filter; empty reads every available mode.
    params: dict | None = None,  # Optional adapter-specific fields merged into the observation payload.
) -> dict:
    """Run one smoke test and return the log.

    Purpose:
        For the UVM environment specialist that authors drivers, monitors, scoreboards, agents, and sequences for one RTL block: Run one smoke test and return the log.
        Invoking ``run_uvm_smoke`` records the intended verification operation for agent ``uvm_environment``.
        A bound framework adapter performs the real EDA work; this process only builds the observation.

    Arguments:
        candidate_ref: Artifact URI/id of the pinned RTL candidate under verification.
        baseline_ref: Baseline candidate or golden revision used for comparison.
        recipe: Frozen compile/run recipe id (plusargs, defines, tool options).
        corner: PVT corner filter; empty reads every available corner.
        mode: Operating-mode filter; empty reads every available mode.
        params: Optional adapter-specific fields merged into the observation payload.

    Returns:
        A ``tool_observation`` dict for skill ``run_uvm_smoke`` with ``agent_id='uvm_environment'``.

    Side effects:
        None in-process. A bound adapter may read/write silicon-store artifacts, submit farm jobs,
        or publish findings into engineering memory.

    Failure behavior:
        Until an adapter is bound, the observation typically reports ``not_run`` and does not
        invoke simulators, formal engines, OpenROAD, Yosys, or OpenSTA. Empty fields are still
        forwarded so the adapter can reject them explicitly.
    """
    # Payload keys mirror config.yaml skill params so AgentService can validate and dispatch.
    payload = {
        'candidate_ref': candidate_ref,  # Artifact URI/id of the pinned RTL candidate under verification.
        'baseline_ref': baseline_ref,  # Baseline candidate or golden revision used for comparison.
        'recipe': recipe,  # Frozen compile/run recipe id (plusargs, defines, tool options).
        'corner': corner,  # PVT corner filter; empty reads every available corner.
        'mode': mode,  # Operating-mode filter; empty reads every available mode.
    }
    if params:
        # Optional extras override base keys so framework adapters can extend the contract.
        payload.update(params)
    return tool_observation(
        'run_uvm_smoke',  # Skill id; must match this agent's config.yaml skills[].callable.
        payload,  # Structured arguments consumed by the bound framework adapter.
        agent_id='uvm_environment',  # Telemetry and journal attribution for this specialist.
    )


@tool(description='Publish a requirement the scoreboard does not check.')
def flag_scoreboard_gap(
    summary: str = "",  # One-sentence finding or record for engineering memory.
    evidence_refs: str = "",  # Comma-separated artifact URIs that support the finding.
    severity: str = "",  # Finding severity: low, medium, high, or critical.
    recommended_recipient: str = "",  # Agent id that should act on the finding next.
    params: dict | None = None,  # Optional adapter-specific fields merged into the observation payload.
) -> dict:
    """Publish a requirement the scoreboard does not check.

    Purpose:
        For the UVM environment specialist that authors drivers, monitors, scoreboards, agents, and sequences for one RTL block: Publish a requirement the scoreboard does not check.
        Invoking ``flag_scoreboard_gap`` records the intended verification operation for agent ``uvm_environment``.
        A bound framework adapter performs the real EDA work; this process only builds the observation.

    Arguments:
        summary: One-sentence finding or record for engineering memory.
        evidence_refs: Comma-separated artifact URIs that support the finding.
        severity: Finding severity: low, medium, high, or critical.
        recommended_recipient: Agent id that should act on the finding next.
        params: Optional adapter-specific fields merged into the observation payload.

    Returns:
        A ``tool_observation`` dict for skill ``flag_scoreboard_gap`` with ``agent_id='uvm_environment'``.

    Side effects:
        None in-process. A bound adapter may read/write silicon-store artifacts, submit farm jobs,
        or publish findings into engineering memory.

    Failure behavior:
        Until an adapter is bound, the observation typically reports ``not_run`` and does not
        invoke simulators, formal engines, OpenROAD, Yosys, or OpenSTA. Empty fields are still
        forwarded so the adapter can reject them explicitly.
    """
    # Payload keys mirror config.yaml skill params so AgentService can validate and dispatch.
    payload = {
        'summary': summary,  # One-sentence finding or record for engineering memory.
        'evidence_refs': evidence_refs,  # Comma-separated artifact URIs that support the finding.
        'severity': severity,  # Finding severity: low, medium, high, or critical.
        'recommended_recipient': recommended_recipient,  # Agent id that should act on the finding next.
    }
    if params:
        # Optional extras override base keys so framework adapters can extend the contract.
        payload.update(params)
    return tool_observation(
        'flag_scoreboard_gap',  # Skill id; must match this agent's config.yaml skills[].callable.
        payload,  # Structured arguments consumed by the bound framework adapter.
        agent_id='uvm_environment',  # Telemetry and journal attribution for this specialist.
    )


@tool(description='Publish a monitor that does not implement a contract clause.')
def flag_protocol_monitor_mismatch(
    summary: str = "",  # One-sentence finding or record for engineering memory.
    evidence_refs: str = "",  # Comma-separated artifact URIs that support the finding.
    severity: str = "",  # Finding severity: low, medium, high, or critical.
    recommended_recipient: str = "",  # Agent id that should act on the finding next.
    params: dict | None = None,  # Optional adapter-specific fields merged into the observation payload.
) -> dict:
    """Publish a monitor that does not implement a contract clause.

    Purpose:
        For the UVM environment specialist that authors drivers, monitors, scoreboards, agents, and sequences for one RTL block: Publish a monitor that does not implement a contract clause.
        Invoking ``flag_protocol_monitor_mismatch`` records the intended verification operation for agent ``uvm_environment``.
        A bound framework adapter performs the real EDA work; this process only builds the observation.

    Arguments:
        summary: One-sentence finding or record for engineering memory.
        evidence_refs: Comma-separated artifact URIs that support the finding.
        severity: Finding severity: low, medium, high, or critical.
        recommended_recipient: Agent id that should act on the finding next.
        params: Optional adapter-specific fields merged into the observation payload.

    Returns:
        A ``tool_observation`` dict for skill ``flag_protocol_monitor_mismatch`` with ``agent_id='uvm_environment'``.

    Side effects:
        None in-process. A bound adapter may read/write silicon-store artifacts, submit farm jobs,
        or publish findings into engineering memory.

    Failure behavior:
        Until an adapter is bound, the observation typically reports ``not_run`` and does not
        invoke simulators, formal engines, OpenROAD, Yosys, or OpenSTA. Empty fields are still
        forwarded so the adapter can reject them explicitly.
    """
    # Payload keys mirror config.yaml skill params so AgentService can validate and dispatch.
    payload = {
        'summary': summary,  # One-sentence finding or record for engineering memory.
        'evidence_refs': evidence_refs,  # Comma-separated artifact URIs that support the finding.
        'severity': severity,  # Finding severity: low, medium, high, or critical.
        'recommended_recipient': recommended_recipient,  # Agent id that should act on the finding next.
    }
    if params:
        # Optional extras override base keys so framework adapters can extend the contract.
        payload.update(params)
    return tool_observation(
        'flag_protocol_monitor_mismatch',  # Skill id; must match this agent's config.yaml skills[].callable.
        payload,  # Structured arguments consumed by the bound framework adapter.
        agent_id='uvm_environment',  # Telemetry and journal attribution for this specialist.
    )

