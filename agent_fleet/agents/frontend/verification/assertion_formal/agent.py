"""Assertion/Formal Agent class for the EDA chip-design agent fleet.

This module defines the specialist that writes SVA assertions, assumptions, and cover properties and drives formal proof campaigns on the frontend
(RTL/verification) track of the silicon agent fleet.

The class is intentionally thin: behavioral policy, skill lists, boundaries, and
connection metadata live in ``config.yaml``. ``EdaAgent.read_spec`` loads that
YAML when the class body is evaluated so the running process matches the
checked-in fleet contract. Tool implementations live in ``tools.py``; the HTTP
service entrypoint lives in ``server.py``.

Original responsibility statement preserved from the agent brief:
Create properties and assumptions, and submit formal proof tasks.

"""

from pathlib import Path  # Resolves this agent's directory independent of process cwd.

from domains.eda.agent import EdaAgent  # Shared EDA agent base: spec loading, memory, tool dispatch.


class AssertionFormalAgent(EdaAgent):
    """Assertion/Formal Agent — Create properties and assumptions, and submit formal proof tasks.

    Purpose:
        Provide the concrete ``EdaAgent`` subclass whose ``spec`` describes how
        this specialist participates in coverage closure for a pinned RTL
        candidate. Runtime behavior is driven by skills in ``tools.py``.

    Attributes:
        spec: AgentSpec loaded from this directory's ``config.yaml``. Loading is
            a class-body side effect evaluated at import time.

    Failure behavior:
        If ``config.yaml`` is missing or invalid, ``read_spec`` raises and the
        service cannot start. No EDA tool is invoked by constructing the class.
    """

    # Absolute package directory so Docker WORKDIR vs repo-root launches both resolve config.yaml.
    spec = EdaAgent.read_spec(Path(__file__).resolve().parent)
