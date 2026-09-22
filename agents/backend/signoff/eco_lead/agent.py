"""ECO Lead.

This package implements the ECO Lead for backend signoff. It plans the smallest late functional, timing, power, or physical change that closes a finding while minimizing disruption, preserving logical equivalence where required, and naming every signoff check the change invalidates.

Late ECOs are high-risk because they can silently invalidate STA corners, SPEF, DRC/LVS, and IR/EM results that were already green. This agent authorizes nothing unilaterally: it plans, requests RTL/equivalence/timing/physical revalidation, and asks a human before the ECO is applied to the baseline.

Package layout under ``agents/backend/signoff/eco_lead/``:
- ``config.yaml`` declares identity, boundaries, skills, memory, and deployment.
- ``agent.py`` loads that spec into an ``EdaAgent`` subclass.
- ``tools.py`` exposes the stable tool/operation contracts as observation stubs until an
  EDA framework adapter is bound (OpenROAD, OpenSTA, licensed PV/IR/thermal tools, etc.).
- ``server.py`` hosts the FastAPI ``AgentService`` on port 8261.
- ``Dockerfile`` / ``requirements.txt`` package the HTTP worker for fleet deployment.

Domain focus: engineering change orders (ECO) for late RTL/timing/power/physical fixes. Typical EDA artifacts touched include ECO scope, equivalence, impacted STA/DRC/LVS gates, human authorization.
"""

from pathlib import Path  # Resolve this agent's package directory for config.yaml discovery.

from domains.eda.agent import EdaAgent  # Shared silicon EdaAgent base: spec load, context, skills.


class EcoLeadAgent(EdaAgent):
    """Concrete ECO Lead bound to this directory's ``config.yaml``.

    Purpose:
        Specialize ``EdaAgent`` for engineering change orders (ECO) for late RTL/timing/power/physical fixes without embedding tool logic in the
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
