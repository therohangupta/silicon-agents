"""Cross-Partition Boundary Coordinator.

When a chip is partitioned, abutting blocks must agree on pins, feedthroughs, routing channels, power straps, clock handoff, and timing budgets. This coordinator checks consistency without editing either placement's canonical database.

This module defines the thin agent class that the HTTP service in ``server.py``
instantiates. Behavior (memory, context assembly, tool dispatch, journaling) is
inherited from ``domains.eda.runtime.EDAAgent``. The only local responsibility is
to bind ``eda_config`` by reading ``config.yaml`` from this directory so role, stage,
boundaries, skills, and connection port (8246) are authoritative.

Side effects of importing this module are limited to class definition and a
one-time ``EDAAgent.load_config`` call when the class body executes. No EDA tool runs
until ``EDAAgent.handle`` / tool callables in ``tools.py`` are invoked.
"""

# Path is used to locate this agent's directory so config.yaml can be resolved.
from pathlib import Path

# EDAAgent provides handle/act, memory journaling, and skill invocation for chip-design agents.
from domains.eda.runtime import EDAAgent


class BoundaryCoordinatorAgent(EDAAgent):
    """Concrete fleet agent for: Check timing budgets, pins, feedthroughs, channels, power, clocks, and constraints across partitions.

    Purpose:
        Register this agent's ``EDAAgentConfig`` and inherit task handling from ``EDAAgent``.

    Attributes:
        spec: Loaded from sibling ``config.yaml`` (role=worker, stage=placement,
            HTTP port=8246). Skills listed there map to callables in ``tools.py``.

    Side effects:
        Class-body evaluation calls ``EDAAgent.load_config``, which parses YAML and may
        raise if the spec is missing or invalid. No network listen occurs here.

    Failures:
        ``TypeError`` later in ``EDAAgent.__init__`` if ``eda_config`` is not an ``EDAAgentConfig``.
        Spec load errors propagate from the registry/YAML loader.
    """

    # Resolve the directory containing this file, then load EDAAgentConfig from config.yaml.
    eda_config = EDAAgent.load_config(Path(__file__).resolve().parent)
