"""Macro-Placement Experiment Worker agent module.

This module defines the thin EDAAgent subclass that represents the
Macro-Placement Experiment Worker service inside the backend floorplan stage of the EDA agent fleet.

In silicon design terms, this agent focuses on: Hard-macro placement under halo, channel, orientation, and keepout constraints. Adapter targets OpenROAD initialize_floorplan and macro placement. Scores flyline connectivity and writes a floorplan DEF for one isolated candidate.

Boot wiring (see also server.py and README.md):
1. server.py constructs AgentService.from_agent(config.yaml, MacroPlacementAgent).
2. MacroPlacementAgent.spec is loaded from config.yaml via EDAAgent.load_config on this directory.
3. Incoming HTTP tasks are handled by EDAAgent.handle, which assembles context,
   journals start/finish, and either proposes child workflows or invokes tools.py.

Worker under floorplanning_lead. One hypothesis per task; overlaps/keepouts are hard fails.

Side effects of importing this module are limited to class definition; no EDA
tool, Yosys, OpenROAD, or licensed engine is invoked at import time.
"""

# Path is required so EDAAgent.load_config can resolve config.yaml next to this file.
from pathlib import Path

# EDAAgent is the shared chip-design task handler (memory, context, tool dispatch).
from domains.eda.runtime import EDAAgent


class MacroPlacementAgent(EDAAgent):
    """Concrete fleet agent for Macro-Placement Experiment Worker.

    Purpose:
        Bind this directory's config.yaml EDAAgentConfig onto the shared EDAAgent
        runtime so the fleet can schedule floorplan work with role
        `worker` on port 8239.

    Spec loading:
        ``eda_config`` is a class attribute assigned at import time by reading the
        sibling config.yaml. That YAML declares capabilities, skills, boundary
        may/may_not rules, delegation targets, and context policy.

    Args:
        Inherited ``__init__`` accepts optional EngineeringMemory and
        ContextService; defaults open the process-wide silicon memory.

    Returns:
        Instances expose ``async handle(request) -> AgentTaskResult`` from EDAAgent.

    Side effects:
        Constructing an instance opens engineering memory if none is supplied.
        Handling a task journals start/finish records and may invoke tools.

    Failures:
        TypeError if ``eda_config`` is missing or not an EDAAgentConfig.
        AgentPermissionError if a tool action violates boundary.may_not.
        Downstream adapter or memory errors surface as failed TaskOutcome.
    """

    # Load EDAAgentConfig from this agent's directory (config.yaml + skills -> tools).
    eda_config = EDAAgent.load_config(Path(__file__).resolve().parent)
