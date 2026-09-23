"""Coverage Agent class for the EDA chip-design agent fleet.

This module defines the specialist that defines covergroups, merges coverage databases, and reports uncovered requirements on the frontend
(RTL/verification) track of the silicon agent fleet.

The class is intentionally thin: behavioral policy, skill lists, boundaries, and
connection metadata live in ``config.yaml``. ``EDAAgent.load_config`` loads that
YAML when the class body is evaluated so the running process matches the
checked-in fleet contract. Tool implementations live in ``tools.py``; the HTTP
service entrypoint lives in ``server.py``.

Original responsibility statement preserved from the agent brief:
Write the coverage model from requirements, then analyze code, functional, and assertion coverage and list meaningful holes.

"""

from pathlib import Path  # Resolves this agent's directory independent of process cwd.

from domains.eda.runtime import EDAAgent  # Shared EDA agent base: spec loading, memory, tool dispatch.


class CoverageAgent(EDAAgent):
    """Coverage Agent — Write the coverage model from requirements, then analyze code, functional, and assertion coverage and list meaningful holes.

    Purpose:
        Provide the concrete ``EDAAgent`` subclass whose ``eda_config`` describes how
        this specialist participates in coverage closure for a pinned RTL
        candidate. Runtime behavior is driven by skills in ``tools.py``.

    Attributes:
        spec: EDAAgentConfig loaded from this directory's ``config.yaml``. Loading is
            a class-body side effect evaluated at import time.

    Failure behavior:
        If ``config.yaml`` is missing or invalid, ``EDAAgent.load_config`` raises and the
        service cannot start. No EDA tool is invoked by constructing the class.
    """

    # Absolute package directory so Docker WORKDIR vs repo-root launches both resolve config.yaml.
    eda_config = EDAAgent.load_config(Path(__file__).resolve().parent)
