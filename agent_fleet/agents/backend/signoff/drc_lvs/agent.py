"""DRC/LVS/ERC/DFM Agent.

This package implements the DRC/LVS/ERC/DFM worker for backend signoff. It runs and triages geometry, connectivity, electrical, density, and manufacturability checks on a placed-and-routed candidate, then separates real layout defects from setup errors such as a wrong rule deck or cell view.

In a silicon tapeout flow, physical verification is a hard gate: a short, open, or spacing violation that escapes to mask will scrap wafers. This agent never waives violations or edits layout; it only submits checks, reads markers, clusters findings, and publishes defects for routing or ECO owners.

Package layout under ``agent_fleet/agents/backend/signoff/drc_lvs/``:
- ``config.yaml`` declares identity, boundaries, skills, memory, and deployment.
- ``agent.py`` loads that spec into an ``EdaAgent`` subclass.
- ``tools.py`` exposes the stable tool/operation contracts as observation stubs until an
  EDA framework adapter is bound (OpenROAD, OpenSTA, licensed PV/IR/thermal tools, etc.).
- ``server.py`` hosts the FastAPI ``AgentService`` on port 8260.
- ``Dockerfile`` / ``requirements.txt`` package the HTTP worker for fleet deployment.

Domain focus: physical verification (DRC, LVS, ERC, density, DFM). Typical EDA artifacts touched include DRC/LVS markers, rule decks, shorts/opens, manufacturability.
"""

from pathlib import Path  # Resolve this agent's package directory for config.yaml discovery.

from domains.eda.agent import EdaAgent  # Shared silicon EdaAgent base: spec load, context, skills.


class DrcLvsAgent(EdaAgent):
    """Concrete DRC/LVS/ERC/DFM Agent bound to this directory's ``config.yaml``.

    Purpose:
        Specialize ``EdaAgent`` for physical verification (DRC, LVS, ERC, density, DFM) without embedding tool logic in the
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
