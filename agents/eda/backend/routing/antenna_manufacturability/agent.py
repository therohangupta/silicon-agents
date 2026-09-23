"""Antenna and Manufacturability Agent.

Process antenna rules limit charge collected on metal during etch that can damage gate oxide. Also covers via reliability, metal density, and patterning risks. Fixes include diodes, jumpers, and layer hops (OpenROAD repair_antennas).

This module defines the thin agent class that the HTTP service in ``server.py``
instantiates. Behavior (memory, context assembly, tool dispatch, journaling) is
inherited from ``domains.eda.runtime.EDAAgent``. The only local responsibility is
to bind ``eda_config`` by reading ``config.yaml`` from this directory so role, stage,
boundaries, skills, and connection port (8253) are authoritative.

Side effects of importing this module are limited to class definition and a
one-time ``EDAAgent.load_config`` call when the class body executes. No EDA tool runs
until ``EDAAgent.handle`` / tool callables in ``tools.py`` are invoked.
"""

# Path is used to locate this agent's directory so config.yaml can be resolved.
from pathlib import Path

# EDAAgent provides handle/act, memory journaling, and skill invocation for chip-design agents.
from domains.eda.runtime import EDAAgent


class AntennaManufacturabilityAgent(EDAAgent):
    """Concrete fleet agent for: Detect antenna, via-reliability, density, and patterning risks; fix and check electrical side effects.

    Purpose:
        Register this agent's ``EDAAgentConfig`` and inherit task handling from ``EDAAgent``.

    Attributes:
        spec: Loaded from sibling ``config.yaml`` (role=worker, stage=routing,
            HTTP port=8253). Skills listed there map to callables in ``tools.py``.

    Side effects:
        Class-body evaluation calls ``EDAAgent.load_config``, which parses YAML and may
        raise if the spec is missing or invalid. No network listen occurs here.

    Failures:
        ``TypeError`` later in ``EDAAgent.__init__`` if ``eda_config`` is not an ``EDAAgentConfig``.
        Spec load errors propagate from the registry/YAML loader.
    """

    # Resolve the directory containing this file, then load EDAAgentConfig from config.yaml.
    eda_config = EDAAgent.load_config(Path(__file__).resolve().parent)
