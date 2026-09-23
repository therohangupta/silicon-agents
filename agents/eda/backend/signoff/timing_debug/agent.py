"""Timing-Debug Agent.

This package implements the Timing-Debug worker for backend signoff. It runs STA queries, classifies setup, hold, recovery, removal, and clock failures, and traces them to a physical or logical cause for sta_lead and repair owners.

The adapter target is OpenSTA (report_checks and related queries) consuming SPEF from extraction and SDC constraints. This agent diagnoses; it does not own MMMC strategy or authorize constraint edits—that remains with sta_lead and humans.

Package layout under ``agents/backend/signoff/timing_debug/``:
- ``config.yaml`` declares identity, boundaries, skills, memory, and deployment.
- ``agent.py`` loads that spec into an ``EDAAgent`` subclass.
- ``tools.py`` exposes the stable tool/operation contracts as observation stubs until an
  EDA framework adapter is bound (OpenROAD, OpenSTA, licensed PV/IR/thermal tools, etc.).
- ``server.py`` hosts the FastAPI ``AgentService`` on port 8256.
- ``Dockerfile`` / ``requirements.txt`` package the HTTP worker for fleet deployment.

Domain focus: STA query and path classification (setup/hold/recovery/removal/clock). Typical EDA artifacts touched include OpenSTA report_checks, WNS/TNS, path cause tracing, unconstrained endpoints.
"""

from pathlib import Path  # Resolve this agent's package directory for config.yaml discovery.

from domains.eda.runtime import EDAAgent  # Shared silicon EDAAgent base: spec load, context, skills.


class TimingDebugAgent(EDAAgent):
    """Concrete Timing-Debug Agent bound to this directory's ``config.yaml``.

    Purpose:
        Specialize ``EDAAgent`` for STA query and path classification (setup/hold/recovery/removal/clock) without embedding tool logic in the
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
