"""Protocol for EDA and verification framework adapters.

Agent tools call named operations. The adapter talks to OpenROAD, Yosys,
OpenSTA, a licensed tool, or an RTL simulator. Agents do not shell out
themselves. Implementations must expose a ``framework`` name and an
``invoke`` method that returns a ``ToolObservation``.

The default process binding is ``NoOpEdaAdapter``. Named factories in
``frameworks.py`` currently return unbound placeholders that raise
``NotImplementedError`` until real integrations are wired.
"""

from __future__ import annotations

# Params typing for invoke().
from typing import Any, Protocol

# Structured result every adapter must return.
from ..schemas.messages import ToolObservation


class EdaAdapter(Protocol):
    """Framework binding for an EDA or verification tool.

    Agent tools call named operations. The adapter talks to OpenROAD, Yosys,
    OpenSTA, a licensed tool, or an RTL simulator. Agents do not shell out
    themselves.

    Structural protocol: any object with ``framework`` and a compatible
    ``invoke`` method can be installed via ``bind_eda_adapter``.
    """

    # Short framework name stamped onto ToolObservation.framework.
    framework: str

    def invoke(
        self,
        operation: str,
        params: dict[str, Any],
        *,
        agent_id: str = "",
    ) -> ToolObservation:
        """Run or record ``operation`` and return a structured observation.

        Args:
            operation: Named operation the agent requested (tool-specific).
            params: Parameter dictionary for the operation.
            agent_id: Optional id of the calling agent.

        Returns:
            A ``ToolObservation`` describing status, summary, metrics, and
            optional job handle / artifacts.

        Side effects:
            Implementation-defined (may submit scheduler jobs, write files,
            or—for the no-op adapter—do nothing beyond building the model).

        Failures:
            Implementation-defined; unbound placeholders raise
            ``NotImplementedError``.
        """
        ...
