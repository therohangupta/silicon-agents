"""
Ingest endpoints for agent telemetry heartbeats.

Agents POST heartbeats here. Identity is ``host:port`` only (no separate
agent_id field). Latest-wins coalescing: the pending map retains only the
newest payload per key under an asyncio lock before applying to the
``HeartbeatStore``. When effective reachable flips, fan-out goes through the
pluggable ``HealthChangedPublisher`` (HTTP to gateway today).
"""

# asyncio.Lock protects the pending coalescing map.
import asyncio
# time.time stamps health_changed events.
import time
# Optional busy/ts fields on the payload.
from typing import Optional

# APIRouter, Depends for publisher injection.
from fastapi import APIRouter, Depends
# Pydantic model for request body validation.
from pydantic import BaseModel

# Request-scoped publisher from app.state.
from ..dependencies import get_publisher
# Event model + protocol type for Depends annotation.
from ..events import HealthChangedEvent, HealthChangedPublisher
# Singleton heartbeat store.
from ..heartbeat_store import get_heartbeat_store

# Routes under /ingest.
router = APIRouter(prefix="/ingest", tags=["Ingest"])

# Pending heartbeats per agent_id (latest wins). Protected by _pending_lock.
_pending: dict[str, "HeartbeatPayload"] = {}
# Serialize enqueue/pop so concurrent POSTs coalesce safely.
_pending_lock = asyncio.Lock()


class HeartbeatPayload(BaseModel):
    """JSON body for ``POST /ingest/heartbeat``.

    ``host`` and ``port`` form the identity key. ``reachable`` defaults True.
    ``busy`` and ``ts`` are optional; missing ``ts`` lets the store use now.
    """

    # Task server host; identity is host:port.
    host: str
    # Task server port; identity is host:port.
    port: int
    # Agent-reported reachability (default healthy).
    reachable: bool = True
    # Optional busy hint for the UI.
    busy: Optional[bool] = None
    # Optional producer timestamp; None => server time in the store.
    ts: Optional[float] = None


@router.post("/heartbeat")
async def ingest_heartbeat(
    payload: HeartbeatPayload,
    publisher: HealthChangedPublisher = Depends(get_publisher),
):
    """
    Accept a heartbeat from an agent. Identity is host:port only (no agent_id).

    Coalescing: multiple pending heartbeats for the same host:port are
    latest-wins. After applying to the store, publishes ``HealthChangedEvent``
    when effective reachable changed. Always returns ``{"ok": True}`` on the
    success path (including when a concurrent request already popped the key).
    """
    # Shared in-memory store.
    store = get_heartbeat_store()
    # Build the coalescing / agent_id key.
    key = f"{payload.host}:{payload.port}"

    # 1. Enqueue (latest wins per key)
    async with _pending_lock:
        # Overwrite any older pending payload for this key.
        _pending[key] = payload

    # 2. Pop and apply
    async with _pending_lock:
        # Take ownership of the latest payload (may be None if raced).
        to_apply = _pending.pop(key, None)
        # Another coroutine already applied this key; acknowledge quietly.
        if to_apply is None:
            return {"ok": True}

        # Persist into the ring buffer; capture whether reachable flipped.
        changed = store.record_heartbeat(
            agent_id=key,
            reachable=to_apply.reachable,
            busy=to_apply.busy,
            ts=to_apply.ts,
            host=to_apply.host,
            port=to_apply.port,
        )
        # Notify gateway only on effective-reachable transitions.
        if changed:
            await publisher.publish(
                HealthChangedEvent(
                    agent_ids=[key],
                    ts=time.time(),
                )
            )

    # Always ack success to the agent.
    return {"ok": True}
