"""Firmware / Test Program agent class (firmware_test_program).

Drafts boot flows, diagnostics, and ATE/characterization test programs used to exercise silicon. Cannot widen approved test limits; flags undiagnosable changes.

This module defines the concrete ``FirmwareTestProgramAgent`` subclass of ``EDAAgent``.
The class does not implement tool bodies itself: runtime behavior comes from
``tools.py`` (skill callables) and ``config.yaml`` (fleet metadata, boundaries,
delegation graph, ports, and context policy). ``EDAAgent.load_config`` loads that
YAML from this directory when the class body evaluates ``eda_config = ...``.

In the validation track, planners open tasks against this agent via the HTTP
service in ``server.py``. Until an EDA or lab framework adapter is bound,
tools return structured ``not_run`` observations rather than driving ATPG,
scan insertion, MBIST, or bench instruments.

Original short description preserved for continuity: Firmware and Test-Program Agent.
"""

from pathlib import Path  # Locate this agent's directory for config.yaml / tools.py adjacency.

from domains.eda.runtime import EDAAgent  # Shared chip-design agent base (memory, context, act).


class FirmwareTestProgramAgent(EDAAgent):
    """Firmware / Test Program specialist bound to this directory's fleet manifest.

    Purpose:
        Provide a typed ``EDAAgent`` subclass whose ``eda_config`` is the YAML in this
        folder so the fleet server and gateway can discover ports, skills, and
        boundaries for firmware_test_program.

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
