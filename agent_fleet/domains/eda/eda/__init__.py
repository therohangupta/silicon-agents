"""EDA / verification framework adapter registry for agent tools.

Agents never shell out to OpenROAD, Yosys, OpenSTA, or RTL simulators
directly. They call named operations through an ``EdaAdapter``. This package
holds:

* ``EdaAdapter`` protocol (``base.py``) — the invoke contract.
* ``NoOpEdaAdapter`` (``noop.py``) — default binding that records intent with
  ``status=not_run`` and must not be treated as evidence.
* Unbound named factories (``frameworks.py``) — placeholders that raise until
  real bindings exist.
* Process-global bind/get/reset helpers and ``tool_observation`` — what agent
  ``tools.py`` modules call to produce observation dicts.

``bind_eda_adapter`` swaps the process-wide adapter (e.g. in tests or when a
container is configured with a real framework). ``reset_eda_adapter`` restores
the no-op default.
"""

from __future__ import annotations

# Flexible params typing for tool_observation.
from typing import Any, Optional

# Observation model returned by adapters and dumped to dict for TaskResult.
from ..schemas.messages import ToolObservation
# Protocol describing framework invoke().
from .base import EdaAdapter
# Default adapter that does not execute tools.
from .noop import NoOpEdaAdapter

# Process-wide adapter; starts as no-op until bind_eda_adapter replaces it.
_adapter: EdaAdapter = NoOpEdaAdapter()


def bind_eda_adapter(adapter: EdaAdapter) -> None:
    """Install ``adapter`` as the process-wide EDA framework binding.

    Args:
        adapter: Object satisfying the ``EdaAdapter`` protocol.

    Returns:
        None.

    Side effects:
        Replaces the module-global ``_adapter`` used by ``get_eda_adapter``
        and ``tool_observation``.

    Failures:
        None; invalid adapters fail later on ``invoke``.
    """
    # Allow assignment to the module-level adapter singleton.
    global _adapter
    # Swap in the caller-provided binding for subsequent tool calls.
    _adapter = adapter


def get_eda_adapter() -> EdaAdapter:
    """Return the currently bound EDA framework adapter.

    Returns:
        The process-global ``EdaAdapter`` (no-op by default).

    Side effects:
        None.

    Failures:
        None.
    """
    # Read the singleton without copying so binds are immediately visible.
    return _adapter


def reset_eda_adapter() -> None:
    """Restore the process-wide adapter to a fresh ``NoOpEdaAdapter``.

    Returns:
        None.

    Side effects:
        Calls ``bind_eda_adapter(NoOpEdaAdapter())``.

    Failures:
        None.
    """
    # Convenience for tests that need to undo a prior bind.
    bind_eda_adapter(NoOpEdaAdapter())


def tool_observation(
    operation: str,
    params: Optional[dict[str, Any]] = None,
    *,
    agent_id: str = "",
) -> dict[str, Any]:
    """Invoke the bound adapter and return a JSON-ready observation dict.

    This is the usual entrypoint from per-agent ``tools.py`` callables.

    Args:
        operation: Named framework operation to request.
        params: Optional parameter dict; defaults to empty.
        agent_id: Optional agent id stamped onto the observation.

    Returns:
        ``ToolObservation.model_dump(mode="json")`` from the adapter result.

    Side effects:
        Whatever the bound adapter performs (no-op by default).

    Failures:
        Propagates ``NotImplementedError`` from unbound named frameworks and
        any adapter-specific errors.
    """
    # Call the current adapter with normalized params.
    observation: ToolObservation = get_eda_adapter().invoke(
        operation,
        params or {},
        agent_id=agent_id,
    )
    # Serialize for TaskResult.observations which expects plain dicts.
    return observation.model_dump(mode="json")
