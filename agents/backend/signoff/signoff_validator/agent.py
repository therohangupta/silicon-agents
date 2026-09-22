"""Independent Signoff Validator.

This package implements the Independent Signoff Validator for backend signoff. It reads primary signoff artifacts for a frozen candidate, reproduces critical checks, audits waivers, and decides whether every required gate passed.

Producing agents must not grade their own homework. This validator treats missing inputs as failures, compares agent summaries against primary artifacts, and refuses to pass a tapeout claim that rests on an incomplete waiver or a single-corner STA run.

Package layout under ``agents/backend/signoff/signoff_validator/``:
- ``config.yaml`` declares identity, boundaries, skills, memory, and deployment.
- ``agent.py`` loads that spec into an ``EdaAgent`` subclass.
- ``tools.py`` exposes the stable tool/operation contracts as observation stubs until an
  EDA framework adapter is bound (OpenROAD, OpenSTA, licensed PV/IR/thermal tools, etc.).
- ``server.py`` hosts the FastAPI ``AgentService`` on port 8262.
- ``Dockerfile`` / ``requirements.txt`` package the HTTP worker for fleet deployment.

Domain focus: independent signoff gate grading and waiver audit. Typical EDA artifacts touched include reproduce STA/DRC/LVS, audit waivers, emit pass/fail signoff gate.
"""

from pathlib import Path  # Resolve this agent's package directory for config.yaml discovery.

from domains.eda.agent import EdaAgent  # Shared silicon EdaAgent base: spec load, context, skills.


class SignoffValidatorAgent(EdaAgent):
    """Concrete Independent Signoff Validator bound to this directory's ``config.yaml``.

    Purpose:
        Specialize ``EdaAgent`` for independent signoff gate grading and waiver audit without embedding tool logic in the
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
