"""Named EDA framework adapter factories (currently unbound placeholders).

Each factory returns an object that satisfies ``EdaAdapter`` in signature but
raises ``NotImplementedError`` on ``invoke``. Agent tools stay on the process
no-op adapter until a real binding is implemented and installed via
``bind_eda_adapter``.

Factories exist so call sites can already name ``openroad``, ``yosys``,
``opensta``, or ``rtl_eval`` without inventing stringly-typed adapters.
"""

from __future__ import annotations

# Params typing for the unbound invoke implementation.
from typing import Any

# Observation type annotated on invoke for protocol compatibility.
from ..schemas.messages import ToolObservation
# Protocol type returned by the public factory functions.
from .base import EdaAdapter


class _UnboundAdapter:
    """Placeholder for a framework that is named but not implemented yet.

    Stores the intended ``framework`` name for error messages. Any
    ``invoke`` call fails loudly so metrics cannot be mistaken for real runs.
    """

    def __init__(self, framework: str) -> None:
        """Remember which framework this placeholder stands in for.

        Args:
            framework: Framework name used in error text and attributes.

        Returns:
            None.

        Side effects:
            Sets ``self.framework``.

        Failures:
            None.
        """
        # Name shown in NotImplementedError when invoke is attempted.
        self.framework = framework

    def invoke(self, operation: str, params: dict[str, Any], *, agent_id: str = "") -> ToolObservation:
        """Refuse to run; this binding is not implemented yet.

        Args:
            operation: Requested operation name (included in the error).
            params: Ignored; accepted for protocol compatibility.
            agent_id: Ignored; accepted for protocol compatibility.

        Returns:
            Never returns normally.

        Side effects:
            None.

        Failures:
            Always raises ``NotImplementedError`` directing callers to keep
            tools on the no-op adapter until a real binding exists.
        """
        # Fail loudly so status=not_run no-op path remains the safe default.
        raise NotImplementedError(
            f"{self.framework} adapter cannot run '{operation}' yet. "
            "Agent tools stay on the no-op adapter until this binding is implemented."
        )


def openroad_adapter() -> EdaAdapter:
    """Return an unbound OpenROAD adapter placeholder.

    Returns:
        An ``_UnboundAdapter`` named ``openroad``.

    Side effects:
        None.

    Failures:
        None at construction; ``invoke`` raises later.
    """
    # Placeholder until a real OpenROAD client is wired.
    return _UnboundAdapter("openroad")


def yosys_adapter() -> EdaAdapter:
    """Return an unbound Yosys adapter placeholder.

    Returns:
        An ``_UnboundAdapter`` named ``yosys``.

    Side effects:
        None.

    Failures:
        None at construction; ``invoke`` raises later.
    """
    # Placeholder until a real Yosys client is wired.
    return _UnboundAdapter("yosys")


def opensta_adapter() -> EdaAdapter:
    """Return an unbound OpenSTA adapter placeholder.

    Returns:
        An ``_UnboundAdapter`` named ``opensta``.

    Side effects:
        None.

    Failures:
        None at construction; ``invoke`` raises later.
    """
    # Placeholder until a real OpenSTA client is wired.
    return _UnboundAdapter("opensta")


def rtl_eval_adapter() -> EdaAdapter:
    """Return an unbound RTL evaluation / simulation adapter placeholder.

    Returns:
        An ``_UnboundAdapter`` named ``rtl_eval``.

    Side effects:
        None.

    Failures:
        None at construction; ``invoke`` raises later.
    """
    # Placeholder until a real RTL eval / sim client is wired.
    return _UnboundAdapter("rtl_eval")
