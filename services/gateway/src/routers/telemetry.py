"""
In-memory telemetry heartbeat ingest for agents (``/api/telemetry``).

Agents can POST heartbeats here instead of being polled. The gateway stores
``last_seen``-style records in a process-local dict. This is a lightweight
path distinct from NATS JetStream agent telemetry streams and from the
Telemetry microservice used for preferred health queries.

HTTP behavior:

- ``POST /heartbeat`` → always **200** ``{"ok": True, "agent_id": ...}``
  after updating the in-memory map (**422** if body fails validation).

Note: data is lost on process restart; production may move this to Redis or
fleet-server ownership as noted in-module.
"""

import time
from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel


class HeartbeatPayload(BaseModel):
    """
    JSON body for agent heartbeat ingest.

    Purpose:
        Carry agent identity plus optional reachability/busy flags and timestamp.

    Fields:
        agent_id: Required fleet agent id.
        reachable: Defaults True.
        busy: Optional busy flag.
        ts: Optional unix timestamp; server fills ``time.time()`` when omitted.

    Side effects:
        None at validation.

    Failure behavior:
        Missing agent_id → HTTP **422**.
    """
    agent_id: str
    reachable: bool = True
    busy: Optional[bool] = None
    ts: Optional[float] = None


# In-memory last heartbeat per agent (ts, reachable, busy).
# In production this could be Redis or fleet-server owned.
_heartbeats: dict[str, dict] = {}


def get_last_heartbeat(agent_id: str) -> Optional[dict]:
    """
    Look up the latest stored heartbeat for one agent.

    Args:
        agent_id: Agent key used at ingest time.

    Returns:
        Heartbeat dict or None if never seen.

    Side effects:
        None.

    Failure behavior:
        Never raises.
    """
    return _heartbeats.get(agent_id)


def get_all_heartbeats() -> dict[str, dict]:
    """
    Snapshot all in-memory heartbeats.

    Args:
        None.

    Returns:
        Shallow copy of the heartbeat map.

    Side effects:
        None (copy isolates callers).

    Failure behavior:
        Never raises.
    """
    return dict(_heartbeats)


# Mounted at /api/telemetry via api_router.
router = APIRouter(prefix="/telemetry", tags=["Telemetry"])


@router.post("/heartbeat")
async def ingest_heartbeat(payload: HeartbeatPayload):
    """
    Accept a heartbeat from an agent and replace any prior record.

    Purpose:
        Replace polling that agent for ``/health`` with push semantics.

    Args:
        payload: Validated heartbeat body.

    Returns:
        ``{"ok": True, "agent_id": ...}``.

    Side effects:
        Mutates ``_heartbeats`` for ``payload.agent_id``.

    Failure behavior:
        **422** on invalid body; **200** on success. Does not persist to disk.
    """
    # Use client-supplied ts when present; otherwise stamp with server time.
    ts = payload.ts if payload.ts is not None else time.time()
    # Overwrite the entire record for this agent id.
    _heartbeats[payload.agent_id] = {
        "ts": ts,
        "reachable": payload.reachable,
        "busy": payload.busy,
    }
    return {"ok": True, "agent_id": payload.agent_id}
