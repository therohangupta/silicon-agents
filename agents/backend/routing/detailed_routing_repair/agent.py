"""Detailed-Routing Repair Agent.

Detailed routing places precise wires and vias. This agent diagnoses local shorts, opens, spacing, via, and pin-access DRC failures, repairs them on an isolated candidate, and verifies previously clean regions stay clean (OpenROAD detailed_route).

This module defines the thin agent class that the HTTP service in ``server.py``
instantiates. Behavior (memory, context assembly, tool dispatch, journaling) is
inherited from ``domains.eda.agent.EdaAgent``. The only local responsibility is
to bind ``spec`` by reading ``config.yaml`` from this directory so role, stage,
boundaries, skills, and connection port (8251) are authoritative.

Side effects of importing this module are limited to class definition and a
one-time ``read_spec`` call when the class body executes. No EDA tool runs
until ``EdaAgent.handle`` / tool callables in ``tools.py`` are invoked.
"""

# Path is used to locate this agent's directory so config.yaml can be resolved.
from pathlib import Path

# EdaAgent provides handle/act, memory journaling, and skill invocation for chip-design agents.
from domains.eda.agent import EdaAgent


class DetailedRoutingRepairAgent(EdaAgent):
    """Concrete fleet agent for: Diagnose and repair local shorts, opens, spacing, vias, and pin-access failures (OpenROAD detailed_route).

    Purpose:
        Register this agent's ``AgentSpec`` and inherit task handling from ``EdaAgent``.

    Attributes:
        spec: Loaded from sibling ``config.yaml`` (role=worker, stage=routing,
            HTTP port=8251). Skills listed there map to callables in ``tools.py``.

    Side effects:
        Class-body evaluation calls ``EdaAgent.read_spec``, which parses YAML and may
        raise if the spec is missing or invalid. No network listen occurs here.

    Failures:
        ``TypeError`` later in ``EdaAgent.__init__`` if ``spec`` is not an ``AgentSpec``.
        Spec load errors propagate from the registry/YAML loader.
    """

    # Resolve the directory containing this file, then load AgentSpec from config.yaml.
    spec = EdaAgent.read_spec(Path(__file__).resolve().parent)
