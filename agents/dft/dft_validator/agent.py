"""DFT Validator agent class (dft_validator).

Independent DFT gate: re-runs scan integrity, fault coverage, BIST checks, and test-mode timing from primary artifacts and decides whether the DFT contract passes. Cannot promote baselines or waive coverage itself.

This module defines the concrete ``DftValidatorAgent`` subclass of ``EdaAgent``.
The class does not implement tool bodies itself: runtime behavior comes from
``tools.py`` (skill callables) and ``config.yaml`` (fleet metadata, boundaries,
delegation graph, ports, and context policy). ``EdaAgent.read_spec`` loads that
YAML from this directory when the class body evaluates ``spec = ...``.

In the dft track, planners open tasks against this agent via the HTTP
service in ``server.py``. Until an EDA or lab framework adapter is bound,
tools return structured ``not_run`` observations rather than driving ATPG,
scan insertion, MBIST, or bench instruments.

Original short description preserved for continuity: Independent DFT Validator.
"""

from pathlib import Path  # Locate this agent's directory for config.yaml / tools.py adjacency.

from domains.eda.agent import EdaAgent  # Shared chip-design agent base (memory, context, act).


class DftValidatorAgent(EdaAgent):
    """DFT Validator specialist bound to this directory's fleet manifest.

    Purpose:
        Provide a typed ``EdaAgent`` subclass whose ``spec`` is the YAML in this
        folder so the fleet server and gateway can discover ports, skills, and
        boundaries for dft_validator.

    Behavior:
        Inherits ``handle`` / ``act`` from ``EdaAgent``. Skill execution resolves
        callables listed under ``skills`` in ``config.yaml`` to functions in
        ``tools.py``. No local methods override that path.

    Side effects:
        Class attribute ``spec`` is loaded at import time by reading
        ``config.yaml`` next to this file. A missing or invalid YAML raises
        during import.

    Failure:
        If ``read_spec`` cannot parse the directory, importing ``agent`` fails
        and ``server.py`` cannot start the HTTP process.
    """

    # Load AgentSpec from sibling config.yaml (name, port, skills, context policy).
    spec = EdaAgent.read_spec(Path(__file__).resolve().parent)
