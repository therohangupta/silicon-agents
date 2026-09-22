"""Verification Lead class for the EDA chip-design agent fleet.

This module defines the specialist that coordinates UVM, formal, stimulus, regression, coverage, triage, reproduction, and the independent verification gate on the frontend
(RTL/verification) track of the silicon agent fleet.

The class is intentionally thin: behavioral policy, skill lists, boundaries, and
connection metadata live in ``config.yaml``. ``EdaAgent.read_spec`` loads that
YAML when the class body is evaluated so the running process matches the
checked-in fleet contract. Tool implementations live in ``tools.py``; the HTTP
service entrypoint lives in ``server.py``.

Original responsibility statement preserved from the agent brief:
Own the verification plan and closure workflow for one pinned RTL revision. Do not personally write every test or inspect every waveform.

"""

from pathlib import Path  # Resolves this agent's directory independent of process cwd.

from domains.eda.agent import EdaAgent  # Shared EDA agent base: spec loading, memory, tool dispatch.


class VerificationLeadAgent(EdaAgent):
    """Verification Lead — Own the verification plan and closure workflow for one pinned RTL revision. Do not personally write every test or inspect every waveform.

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
