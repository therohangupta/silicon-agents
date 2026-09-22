"""Netlist Quality agent module.

This module defines the thin EdaAgent subclass that represents the
Netlist Quality service inside the backend synthesis stage of the EDA agent fleet.

In silicon design terms, this agent focuses on: Structural netlist audit: combinational loops, undriven/unused nets, high fanout, unmapped or dont-use cells, DFT/scan survival, congestion-risk cells, and QoR regressions versus a recorded baseline. Catches defects synthesis QoR can hide.

Boot wiring (see also server.py and README.md):
1. server.py constructs AgentService.from_agent(config.yaml, NetlistQualityAgent).
2. NetlistQualityAgent.spec is loaded from config.yaml via EdaAgent.read_spec on this directory.
3. Incoming HTTP tasks are handled by EdaAgent.handle, which assembles context,
   journals start/finish, and either proposes child workflows or invokes tools.py.

Worker under synthesis_lead. Publishes findings; does not rewrite the netlist.

Side effects of importing this module are limited to class definition; no EDA
tool, Yosys, OpenROAD, or licensed engine is invoked at import time.
"""

# Path is required so read_spec can resolve config.yaml next to this file.
from pathlib import Path

# EdaAgent is the shared chip-design task handler (memory, context, tool dispatch).
from domains.eda.agent import EdaAgent


class NetlistQualityAgent(EdaAgent):
    """Concrete fleet agent for Netlist Quality.

    Purpose:
        Bind this directory's config.yaml AgentSpec onto the shared EdaAgent
        runtime so the fleet can schedule synthesis work with role
        `worker` on port 8237.

    Spec loading:
        ``spec`` is a class attribute assigned at import time by reading the
        sibling config.yaml. That YAML declares capabilities, skills, boundary
        may/may_not rules, delegation targets, and context policy.

    Args:
        Inherited ``__init__`` accepts optional EngineeringMemory and
        ContextService; defaults open the process-wide silicon memory.

    Returns:
        Instances expose ``async handle(request) -> AgentTaskResult`` from EdaAgent.

    Side effects:
        Constructing an instance opens engineering memory if none is supplied.
        Handling a task journals start/finish records and may invoke tools.

    Failures:
        TypeError if ``spec`` is missing or not an AgentSpec.
        AgentPermissionError if a tool action violates boundary.may_not.
        Downstream adapter or memory errors surface as failed TaskOutcome.
    """

    # Load AgentSpec from this agent's directory (config.yaml + skills -> tools).
    spec = EdaAgent.read_spec(Path(__file__).resolve().parent)
