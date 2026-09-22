from __future__ import annotations

"""Module ``client_sdk/python/src/models/types.py``.

Typed models shared by client SDK HTTP and realtime layers.

Part of the Gateway client SDK: callers use HTTP and WebSocket helpers to talk to the BFF without coupling to fleet_server gRPC.

Hand-written source for ``types.py``. Behavior is unchanged; comments document control-plane / agent-runtime intent for maintainers.
"""


from dataclasses import dataclass
from typing import Any, Optional, Literal


# Local ``TaskStatus`` ← Literal["unknown", "pending", "in_progress", "completed", "cancel….
TaskStatus = Literal["unknown", "pending", "in_progress", "completed", "cancelled", "failed"]
# Local ``AgentState`` ← Literal["unknown", "registered", "deploying", "running", "error",….
AgentState = Literal["unknown", "registered", "deploying", "running", "error", "stopped"]


@dataclass(frozen=True)
class Agent:
    """``Agent`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
    agent_id: str
    agent_type: str
    capabilities: list[str]
    status: Optional[AgentState] = None


@dataclass(frozen=True)
class Task:
    """``Task`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
    task_id: int
    description: str
    dependency_task_ids: list[int]
    status: TaskStatus
    goal_id: Optional[int] = None
    plan_id: Optional[int] = None
    agent_id: Optional[str] = None
    agent_type: Optional[str] = None
    result: Optional[str] = None


@dataclass(frozen=True)
class Plan:
    """``Plan`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
    plan_id: int
    name: str
    description: str
    planning_strategy: int
    allocation_strategy: int
    task_ids: list[int]
    goal_ids: list[int]
    tasks: Optional[list[Task]] = None


# Local ``JsonDict`` ← dict[str, Any].
JsonDict = dict[str, Any]

