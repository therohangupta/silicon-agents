"""RTL Integration Agent — agent class entry point.

This module defines the thin `RtlIntegrationAgent` wrapper used by the agent fleet runtime.
It does not implement EDA algorithms itself. Instead it loads the sibling `config.yaml`
specification (capabilities, boundaries, ports, context policy) through `EDAAgent.load_config`
and exposes that spec on the class so `server.py` and the orchestrator share one source of truth.

In the frontend chip-design flow this agent operates at the **rtl** stage.
Block-level candidates that passed local lint/CDC/clock/low-power checks are merged here. Integration marks stale downstream verification results so the fleet does not trust outdated evidence.

Runtime behavior: constructing the class or importing this module does not launch tools,
touch RTL files, or open network sockets. Side effects begin only when `AgentService`
serves HTTP tasks that invoke callables from `tools.py`.
"""

from pathlib import Path  # Locates this agent's directory so config.yaml is found independent of cwd.

from domains.eda.runtime import EDAAgent  # Shared EDA agent base: spec loading, context, and skill dispatch.


class RtlIntegrationAgent(EDAAgent):
    """Fleet agent for `rtl_integration` (RTL Integration Agent).

    Purpose:
        Provide a typed agent object whose `spec` attribute mirrors `config.yaml`, including
        stage `rtl`, role `worker`, connection port `8214`, and the
        advertised capabilities that the planner may schedule.

    Arguments:
        None at class body level. Instances are constructed by `AgentService.from_agent`
        using the class object and the path to `config.yaml`.

    Returns / attributes:
        `spec` is a loaded agent specification object produced by `EDAAgent.load_config`.
        It is evaluated at class-definition time so import failures surface early if YAML
        is missing or malformed.

    Side effects:
        Reading `config.yaml` from disk when the class body executes. No EDA tools run here.

    Failure behavior:
        If `config.yaml` is absent or invalid, `EDAAgent.load_config` raises and the container fails
        at import/startup rather than serving a silent misconfiguration.
    """

    # Load sibling config.yaml (metadata, skills, boundaries) into the class-level spec.
    eda_config = EDAAgent.load_config(Path(__file__).resolve().parent)
