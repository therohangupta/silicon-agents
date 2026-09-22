"""Antenna and Manufacturability Agent.

Process antenna rules limit charge collected on metal during etch that can damage gate oxide. Also covers via reliability, metal density, and patterning risks. Fixes include diodes, jumpers, and layer hops (OpenROAD repair_antennas).

This module defines the thin agent class that the HTTP service in ``server.py``
instantiates. Behavior (memory, context assembly, tool dispatch, journaling) is
inherited from ``domains.eda.agent.EdaAgent``. The only local responsibility is
to bind ``spec`` by reading ``config.yaml`` from this directory so role, stage,
boundaries, skills, and connection port (8253) are authoritative.

Side effects of importing this module are limited to class definition and a
one-time ``read_spec`` call when the class body executes. No EDA tool runs
until ``EdaAgent.handle`` / tool callables in ``tools.py`` are invoked.
"""

# Path is used to locate this agent's directory so config.yaml can be resolved.
from pathlib import Path

# EdaAgent provides handle/act, memory journaling, and skill invocation for chip-design agents.
from domains.eda.agent import EdaAgent


class AntennaManufacturabilityAgent(EdaAgent):
    """Concrete fleet agent for: Detect antenna, via-reliability, density, and patterning risks; fix and check electrical side effects.

    Purpose:
        Register this agent's ``AgentSpec`` and inherit task handling from ``EdaAgent``.

    Attributes:
        spec: Loaded from sibling ``config.yaml`` (role=worker, stage=routing,
            HTTP port=8253). Skills listed there map to callables in ``tools.py``.

    Side effects:
        Class-body evaluation calls ``EdaAgent.read_spec``, which parses YAML and may
        raise if the spec is missing or invalid. No network listen occurs here.

    Failures:
        ``TypeError`` later in ``EdaAgent.__init__`` if ``spec`` is not an ``AgentSpec``.
        Spec load errors propagate from the registry/YAML loader.
    """

    # Resolve the directory containing this file, then load AgentSpec from config.yaml.
    spec = EdaAgent.read_spec(Path(__file__).resolve().parent)
