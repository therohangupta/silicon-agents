"""STA Lead.

This package implements the STA Lead for backend signoff. It owns multi-mode multi-corner static timing closure: classifying failures, tracing causes through timing_debug, and coordinating bounded repairs without promoting candidates or quietly editing constraints.

Signoff timing requires every required mode/corner, not a single optimistic corner. This lead plans sweeps, routes classified path groups to owners who can change logic/placement/clock, and escalates constraint edits or residual violations to a human decision.

Package layout under ``agents/backend/signoff/sta_lead/``:
- ``config.yaml`` declares identity, boundaries, skills, memory, and deployment.
- ``agent.py`` loads that spec into an ``EDAAgent`` subclass.
- ``tools.py`` exposes the stable tool/operation contracts as observation stubs until an
  EDA framework adapter is bound (OpenROAD, OpenSTA, licensed PV/IR/thermal tools, etc.).
- ``server.py`` hosts the FastAPI ``AgentService`` on port 8255.
- ``Dockerfile`` / ``requirements.txt`` package the HTTP worker for fleet deployment.

Domain focus: multi-mode multi-corner (MMMC) static timing ownership. Typical EDA artifacts touched include MMMC coverage, path-group repair coordination, constraint edit requests.
"""

from pathlib import Path  # Resolve this agent's package directory for config.yaml discovery.

from domains.eda.runtime import EDAAgent  # Shared silicon EDAAgent base: spec load, context, skills.


class StaLeadAgent(EDAAgent):
    """Concrete STA Lead bound to this directory's ``config.yaml``.

    Purpose:
        Specialize ``EDAAgent`` for multi-mode multi-corner (MMMC) static timing ownership without embedding tool logic in the
        class body. All capabilities live in ``tools.py`` and are declared as skills in
        ``config.yaml`` so the orchestrator can discover and invoke them.

    Attributes:
        spec: Loaded agent manifest (metadata, boundaries, skills, deployment). Populated
            at import time from the sibling ``config.yaml`` via ``EDAAgent.load_config``.

    Side effects:
        Reading the class attribute triggers a filesystem read of ``config.yaml`` when the
        class body is evaluated. No EDA tools are launched at import time.

    Failures:
        ``EDAAgent.load_config`` raises if ``config.yaml`` is missing or malformed, which
        prevents the HTTP server from starting with a silent empty capability set.
    """

    # Load the Agent Fleet manifest from this package directory (name, skills, port, bounds).
    eda_config = EDAAgent.load_config(Path(__file__).resolve().parent)
