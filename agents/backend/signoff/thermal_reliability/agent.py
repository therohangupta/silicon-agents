"""Thermal and Reliability Agent.

This package implements the Thermal and Reliability worker for backend signoff. It evaluates temperature maps, aging and variation margins, and reliability limits, then turns risks into proposed constraints or an isolated physical change.

Hotspots raise leakage and slow transistors; aging and EM couple to the same power map that IR/EM and power_analysis consume. This agent never silently raises a thermal limit to force a pass, and it does not edit canonical constraints—only proposals and isolated candidates.

Package layout under ``agents/backend/signoff/thermal_reliability/``:
- ``config.yaml`` declares identity, boundaries, skills, memory, and deployment.
- ``agent.py`` loads that spec into an ``EdaAgent`` subclass.
- ``tools.py`` exposes the stable tool/operation contracts as observation stubs until an
  EDA framework adapter is bound (OpenROAD, OpenSTA, licensed PV/IR/thermal tools, etc.).
- ``server.py`` hosts the FastAPI ``AgentService`` on port 8259.
- ``Dockerfile`` / ``requirements.txt`` package the HTTP worker for fleet deployment.

Domain focus: thermal, aging, variation, and reliability margins. Typical EDA artifacts touched include hotspots, aging margins, thermal feedback to leakage/delay, package assumptions.
"""

from pathlib import Path  # Resolve this agent's package directory for config.yaml discovery.

from domains.eda.agent import EdaAgent  # Shared silicon EdaAgent base: spec load, context, skills.


class ThermalReliabilityAgent(EdaAgent):
    """Concrete Thermal and Reliability Agent bound to this directory's ``config.yaml``.

    Purpose:
        Specialize ``EdaAgent`` for thermal, aging, variation, and reliability margins without embedding tool logic in the
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
