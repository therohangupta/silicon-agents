"""Clock Validation Agent.

Independent clock validation before routing: reachability of every sink, generated-clock relationships, gating enable checks, min pulse width, skew/latency/transition limits, and mode coverage. Publishes gates rather than rebuilding the tree.

This module defines the thin agent class that the HTTP service in ``server.py``
instantiates. Behavior (memory, context assembly, tool dispatch, journaling) is
inherited from ``domains.eda.agent.EdaAgent``. The only local responsibility is
to bind ``spec`` by reading ``config.yaml`` from this directory so role, stage,
boundaries, skills, and connection port (8248) are authoritative.

Side effects of importing this module are limited to class definition and a
one-time ``read_spec`` call when the class body executes. No EDA tool runs
until ``EdaAgent.handle`` / tool callables in ``tools.py`` are invoked.
"""

# Path is used to locate this agent's directory so config.yaml can be resolved.
from pathlib import Path

# EdaAgent provides handle/act, memory journaling, and skill invocation for chip-design agents.
from domains.eda.agent import EdaAgent


class ClockValidationAgent(EdaAgent):
    """Concrete fleet agent for: Independently validate clock reachability, generated clocks, gating, pulse width, skew, latency, transition, mode coverage.

    Purpose:
        Register this agent's ``AgentSpec`` and inherit task handling from ``EdaAgent``.

    Attributes:
        spec: Loaded from sibling ``config.yaml`` (role=worker, stage=clock,
            HTTP port=8248). Skills listed there map to callables in ``tools.py``.

    Side effects:
        Class-body evaluation calls ``EdaAgent.read_spec``, which parses YAML and may
        raise if the spec is missing or invalid. No network listen occurs here.

    Failures:
        ``TypeError`` later in ``EdaAgent.__init__`` if ``spec`` is not an ``AgentSpec``.
        Spec load errors propagate from the registry/YAML loader.
    """

    # Resolve the directory containing this file, then load AgentSpec from config.yaml.
    spec = EdaAgent.read_spec(Path(__file__).resolve().parent)
