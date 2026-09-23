"""DFT Lead agent class (dft_lead).

Owns block- and chip-level Design-for-Test strategy: scan, ATPG, MBIST/LBIST, physical/timing handoff, and independent DFT validation. Coordinates coverage, tester time, area, power, and test-mode timing without waiving hard coverage.

This module defines the concrete ``DftLeadAgent`` subclass of ``EDAAgent``.
The class does not implement tool bodies itself: runtime behavior comes from
``tools.py`` (skill callables) and ``config.yaml`` (fleet metadata, boundaries,
delegation graph, ports, and context policy). ``EDAAgent.load_config`` loads that
YAML from this directory when the class body evaluates ``eda_config = ...``.

In the dft track, planners open tasks against this agent via the HTTP
service in ``server.py``. Until an EDA or lab framework adapter is bound,
tools return structured ``not_run`` observations rather than driving ATPG,
scan insertion, MBIST, or bench instruments.

Original short description preserved for continuity: DFT Lead.
"""

from pathlib import Path  # Locate this agent's directory for config.yaml / tools.py adjacency.

from domains.eda.runtime import EDAAgent  # Shared chip-design agent base (memory, context, act).


class DftLeadAgent(EDAAgent):
    """DFT Lead specialist bound to this directory's fleet manifest.

    Purpose:
        Provide a typed ``EDAAgent`` subclass whose ``eda_config`` is the YAML in this
        folder so the fleet server and gateway can discover ports, skills, and
        boundaries for dft_lead.

    Behavior:
        Inherits ``handle`` / ``act`` from ``EDAAgent``. Skill execution resolves
        callables listed under ``skills`` in ``config.yaml`` to functions in
        ``tools.py``. No local methods override that path.

    Side effects:
        Class attribute ``eda_config`` is loaded at import time by reading
        ``config.yaml`` next to this file. A missing or invalid YAML raises
        during import.

    Failure:
        If ``EDAAgent.load_config`` cannot parse the directory, importing ``agent`` fails
        and ``server.py`` cannot start the HTTP process.
    """

    # Load EDAAgentConfig from sibling config.yaml (name, port, skills, context policy).
    eda_config = EDAAgent.load_config(Path(__file__).resolve().parent)
