"""IR/EM Agent.

This package implements the IR/EM worker for backend signoff. It analyzes static and dynamic voltage drop and electromigration current density, localizes weak power-grid regions, and applies a grid or placement repair on an isolated candidate with timing and routing rechecks.

Excessive IR drop causes timing failure and functional brownout; EM violations threaten long-term reliability. Repairs that thicken straps or move cells can hurt congestion and STA, so every applied repair must be rechecked for timing and routing before anyone promotes the candidate.

Package layout under ``agents/backend/signoff/ir_em/``:
- ``config.yaml`` declares identity, boundaries, skills, memory, and deployment.
- ``agent.py`` loads that spec into an ``EdaAgent`` subclass.
- ``tools.py`` exposes the stable tool/operation contracts as observation stubs until an
  EDA framework adapter is bound (OpenROAD, OpenSTA, licensed PV/IR/thermal tools, etc.).
- ``server.py`` hosts the FastAPI ``AgentService`` on port 8258.
- ``Dockerfile`` / ``requirements.txt`` package the HTTP worker for fleet deployment.

Domain focus: IR drop and electromigration (EM) on the power grid. Typical EDA artifacts touched include static/dynamic IR maps, EM current density, grid and placement repair.
"""

from pathlib import Path  # Resolve this agent's package directory for config.yaml discovery.

from domains.eda.agent import EdaAgent  # Shared silicon EdaAgent base: spec load, context, skills.


class IrEmAgent(EdaAgent):
    """Concrete IR/EM Agent bound to this directory's ``config.yaml``.

    Purpose:
        Specialize ``EdaAgent`` for IR drop and electromigration (EM) on the power grid without embedding tool logic in the
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
