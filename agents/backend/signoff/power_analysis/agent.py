"""Power-Analysis Agent.

This package implements the Power-Analysis worker for backend signoff. It estimates vector-based or vectorless dynamic power, leakage, and clock-network power, then compares results against the block and chip budgets.

Power numbers drive package thermal limits, IR stimuli, and product power envelopes. The adapter target starts at OpenROAD report_power and can bind a signoff power tool. Activity-file provenance matters: vectorless estimates can swing widely when toggling assumptions change.

Package layout under ``agents/backend/signoff/power_analysis/``:
- ``config.yaml`` declares identity, boundaries, skills, memory, and deployment.
- ``agent.py`` loads that spec into an ``EdaAgent`` subclass.
- ``tools.py`` exposes the stable tool/operation contracts as observation stubs until an
  EDA framework adapter is bound (OpenROAD, OpenSTA, licensed PV/IR/thermal tools, etc.).
- ``server.py`` hosts the FastAPI ``AgentService`` on port 8257.
- ``Dockerfile`` / ``requirements.txt`` package the HTTP worker for fleet deployment.

Domain focus: vector-based and vectorless power estimation. Typical EDA artifacts touched include dynamic/leakage/clock power vs block budget, activity uncertainty.
"""

from pathlib import Path  # Resolve this agent's package directory for config.yaml discovery.

from domains.eda.agent import EdaAgent  # Shared silicon EdaAgent base: spec load, context, skills.


class PowerAnalysisAgent(EdaAgent):
    """Concrete Power-Analysis Agent bound to this directory's ``config.yaml``.

    Purpose:
        Specialize ``EdaAgent`` for vector-based and vectorless power estimation without embedding tool logic in the
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
