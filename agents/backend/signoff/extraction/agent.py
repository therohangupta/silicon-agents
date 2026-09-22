"""Extraction Agent.

This package implements the Extraction worker for backend signoff. It produces versioned parasitic models (SPEF) from the routed design, records completeness and corner configuration, and flags missing nets, couplings, or required corners.

Signoff static timing and IR/power analysis are only as good as the parasitics. The adapter target starts at OpenROAD estimate_parasitics and can bind a licensed signoff extractor behind the same tool operations. This agent does not run STA; it feeds SPEF refs to timing_debug, sta_lead, power_analysis, and ir_em.

Package layout under ``agents/backend/signoff/extraction/``:
- ``config.yaml`` declares identity, boundaries, skills, memory, and deployment.
- ``agent.py`` loads that spec into an ``EdaAgent`` subclass.
- ``tools.py`` exposes the stable tool/operation contracts as observation stubs until an
  EDA framework adapter is bound (OpenROAD, OpenSTA, licensed PV/IR/thermal tools, etc.).
- ``server.py`` hosts the FastAPI ``AgentService`` on port 8254.
- ``Dockerfile`` / ``requirements.txt`` package the HTTP worker for fleet deployment.

Domain focus: parasitic extraction (SPEF) for signoff STA and power. Typical EDA artifacts touched include SPEF completeness, extraction corners, OpenROAD estimate_parasitics.
"""

from pathlib import Path  # Resolve this agent's package directory for config.yaml discovery.

from domains.eda.agent import EdaAgent  # Shared silicon EdaAgent base: spec load, context, skills.


class ExtractionAgent(EdaAgent):
    """Concrete Extraction Agent bound to this directory's ``config.yaml``.

    Purpose:
        Specialize ``EdaAgent`` for parasitic extraction (SPEF) for signoff STA and power without embedding tool logic in the
        class body. All capabilities live in ``tools.py`` and are declared as skills in
        ``config.yaml`` so the orchestrator can discover and invoke them.

    Attributes:
        spec: Loaded agent manifest (metadata, boundaries, skills, deployment). Populated
            at import time from the sibling ``config.yaml`` via ``EdaAgent.read_spec``.

    Side effects:
        Reading the class attribute triggers a filesystem read of ``config.yaml`` when the
        class body is evaluated. No EDA tools are launched at import time.

    Failures:
        ``EdaAgent.read_spec`` raises if ``config.yaml`` is missing or malformed, which
        prevents the HTTP server from starting with a silent empty capability set.
    """

    # Load the Agent Fleet manifest from this package directory (name, skills, port, bounds).
    spec = EdaAgent.read_spec(Path(__file__).resolve().parent)
