from __future__ import annotations

"""Module ``client_sdk/python/src/realtime/events.py``.

WebSocket / realtime event clients for Gateway live updates.

Part of the Gateway client SDK: callers use HTTP and WebSocket helpers to talk to the BFF without coupling to fleet_server gRPC.

Hand-written source for ``events.py``. Behavior is unchanged; comments document control-plane / agent-runtime intent for maintainers.
"""


from dataclasses import dataclass
from typing import Any, Literal, Union


@dataclass(frozen=True)
class Connected:
    """``Connected`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
    type: Literal["connected"]
    message: str


@dataclass(frozen=True)
class Invalidate:
    """``Invalidate`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
    type: Literal["invalidate"]
    queries: list[str]
    timestamp: float


@dataclass(frozen=True)
class TasksUpdate:
    """``TasksUpdate`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
    type: Literal["tasks_update"]
    plan_id: int
    tasks: list[dict[str, Any]]


# Local ``GatewayRealtimeMessage`` ← Union[Connected, Invalidate, TasksUpdate, dict[str, Any]].
GatewayRealtimeMessage = Union[Connected, Invalidate, TasksUpdate, dict[str, Any]]

