"""
Event-driven WebSocket endpoints and internal fleet event ingest.

The fleet server POSTs mutation notifications to ``POST /internal/events``.
This module maps those event types to React Query cache keys and broadcasts
them through an in-process ``EventBus`` to:

- ``WS /ws/global-updates`` — invalidate dashboard queries (no idle polling).
- ``WS /ws/execution/{plan_id}`` — refetch that plan's tasks when any event
  arrives (plus keepalive pings).

On gateway shutdown, ``app.lifespan`` calls ``event_bus.notify(["__shutdown__"])``
so WS loops exit cleanly. This router is mounted without the ``/api`` prefix.
"""

import asyncio
import logging
import time
from typing import Dict, List, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request
from pydantic import BaseModel

# Root-level router (paths are absolute: /ws/..., /internal/...).
router = APIRouter()
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Event bus: lightweight in-process pub-sub with per-subscriber queues
# ---------------------------------------------------------------------------

class EventBus:
    """
    Broadcasts invalidation signals to all connected WebSocket clients.

    Purpose:
        Decouple HTTP event ingest from WebSocket send loops. Each subscriber
        gets its own ``asyncio.Queue`` so concurrent clients do not race on a
        shared buffer.

    Side effects:
        ``notify`` performs non-blocking ``put_nowait`` on every queue.

    Failure behavior:
        ``put_nowait`` may raise ``QueueFull`` if a queue were bounded; these
        queues are unbounded by default so puts should not fail under normal load.
    """

    def __init__(self):
        """
        Create an empty subscriber set.

        Args:
            None.

        Returns:
            None.

        Side effects:
            Initializes ``_subscribers``.

        Failure behavior:
            None.
        """
        # Each connected WS handler owns one queue in this set.
        self._subscribers: Set[asyncio.Queue] = set()

    def notify(self, query_keys: List[str]) -> None:
        """
        Push the same query-key list to every subscriber queue.

        Args:
            query_keys: React Query keys (or ``["__shutdown__"]``) to deliver.

        Returns:
            None.

        Side effects:
            Enqueues onto all subscriber queues (may wake many WS tasks).

        Failure behavior:
            Propagates queue put errors if any occur.
        """
        for q in self._subscribers:
            q.put_nowait(query_keys)

    def subscribe(self) -> asyncio.Queue:
        """
        Register a new subscriber queue for this process.

        Args:
            None.

        Returns:
            Fresh unbounded ``asyncio.Queue`` already added to the set.

        Side effects:
            Mutates ``_subscribers``.

        Failure behavior:
            None under normal memory conditions.
        """
        q: asyncio.Queue = asyncio.Queue()
        self._subscribers.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue) -> None:
        """
        Remove a subscriber queue (e.g. on WebSocket disconnect).

        Args:
            q: Queue previously returned by ``subscribe``.

        Returns:
            None.

        Side effects:
            Discards ``q`` from ``_subscribers`` if present.

        Failure behavior:
            Never raises (``discard``).
        """
        self._subscribers.discard(q)


# Process-wide bus shared with app.lifespan shutdown signaling.
event_bus = EventBus()


# ---------------------------------------------------------------------------
# Map fleet events → React Query keys
# ---------------------------------------------------------------------------

# Which frontend query caches should invalidate for each fleet event type.
_EVENT_TO_QUERIES: Dict[str, List[str]] = {
    "task.state_changed": ["tasks", "plans"],
    "plan.state_changed": ["plans", "tasks"],
    "agent.changed":      ["agents", "agent-health", "agent-allocations"],
    "telemetry.health_changed": ["agent-health"],
}


def _derive_query_keys(event_type: str) -> List[str]:
    """
    Map a fleet event type string to React Query invalidation keys.

    Args:
        event_type: Event ``type`` field from ``FleetEvent``.

    Returns:
        Known mapping list, or a broad default covering plans/tasks/agents.

    Side effects:
        None.

    Failure behavior:
        Never raises; unknown types get the default list.
    """
    return _EVENT_TO_QUERIES.get(event_type, ["plans", "tasks", "agents"])


# ---------------------------------------------------------------------------
# POST /internal/events — called by fleet server (fire-and-forget)
# ---------------------------------------------------------------------------

class FleetEvent(BaseModel):
    """
    Payload posted by the fleet server when domain state mutates.

    Purpose:
        Carry enough identity fields for logging/future filtering while the
        current implementation only uses ``type`` to derive query keys.

    Fields:
        type: Required event type string.
        task_id / plan_id / agent_id / agent_ids / status / action: Optional context.

    Side effects:
        None at validation.

    Failure behavior:
        Missing type → HTTP **422**.
    """
    type: str
    task_id: int | None = None
    plan_id: int | None = None
    agent_id: str | None = None
    agent_ids: list[str] | None = None  # for telemetry.health_changed
    status: str | None = None
    action: str | None = None


@router.post("/internal/events", tags=["Internal"])
async def receive_fleet_event(event: FleetEvent):
    """
    Accept a fleet mutation event and broadcast invalidation to WS clients.

    Purpose:
        Replace sleep-loop polling with push-driven UI refreshes.

    Args:
        event: Validated fleet event body.

    Returns:
        ``{"ok": True}``.

    Side effects:
        ``event_bus.notify`` wakes global-updates and execution subscribers.

    Failure behavior:
        **422** on invalid body; **200** on success. Does not authenticate in this module.
    """
    keys = _derive_query_keys(event.type)
    event_bus.notify(keys)
    return {"ok": True}


# ---------------------------------------------------------------------------
# WebSocket /ws/global-updates — pushes invalidation to the frontend
# ---------------------------------------------------------------------------

@router.websocket("/ws/global-updates")
async def websocket_global_updates(websocket: WebSocket):
    """
    Event-driven WebSocket that emits invalidate messages for React Query.

    Purpose:
        Tell the SPA which query keys to refetch only when the fleet reports a
        mutation; send ``ping`` every 30s of idle to keep the connection alive.

    Args:
        websocket: Accepted ASGI WebSocket.

    Returns:
        None (streaming handler).

    Side effects:
        Subscribes to ``event_bus``; sends JSON frames; unsubscribes in finally.

    Failure behavior:
        Disconnect ends the loop quietly; other errors are logged. Shutdown key
        ``["__shutdown__"]`` breaks the loop during app teardown.
    """
    # Complete the WebSocket handshake.
    await websocket.accept()

    # Immediate ack so the UI can show realtime mode is active.
    await websocket.send_json({
        "type": "connected",
        "message": "Real-time updates enabled (event-driven)"
    })

    # Register for invalidation broadcasts.
    queue = event_bus.subscribe()

    try:
        while True:
            try:
                # Wait for an event or idle timeout for keepalive.
                keys = await asyncio.wait_for(queue.get(), timeout=30.0)
            except asyncio.TimeoutError:
                # Keep proxies/browsers from dropping idle sockets.
                await websocket.send_json({"type": "ping"})
                continue

            # Lifespan asks all WS handlers to exit.
            if keys == ["__shutdown__"]:
                break

            # Push invalidation payload with a server timestamp.
            await websocket.send_json({
                "type": "invalidate",
                "queries": keys,
                "timestamp": time.time(),
            })
    except WebSocketDisconnect:
        # Client closed the socket; normal path.
        pass
    except Exception:
        logger.exception("WebSocket global-updates handler failed")
    finally:
        # Always detach so notify does not retain dead queues.
        event_bus.unsubscribe(queue)


# ---------------------------------------------------------------------------
# WebSocket /ws/execution/{plan_id} — plan-specific task updates
# ---------------------------------------------------------------------------

class ExecutionConnectionManager:
    """
    Track active execution WebSockets keyed by plan id.

    Purpose:
        Allow optional targeted broadcasts (``broadcast``) while the primary
        update path today re-lists tasks inside each socket's event loop.

    Side effects:
        Mutates ``active`` on connect/disconnect.

    Failure behavior:
        ``broadcast`` logs per-client send failures and continues.
    """

    def __init__(self):
        """
        Initialize the empty plan→connections map.

        Args:
            None.

        Returns:
            None.

        Side effects:
            Sets ``self.active`` to ``{}``.

        Failure behavior:
            None.
        """
        self.active: Dict[int, List[WebSocket]] = {}

    async def connect(self, ws: WebSocket, plan_id: int):
        """
        Accept a WebSocket and register it under ``plan_id``.

        Args:
            ws: Incoming socket.
            plan_id: Plan whose execution the client is watching.

        Returns:
            None.

        Side effects:
            Accepts the connection; appends to ``active[plan_id]``.

        Failure behavior:
            Propagates accept errors.
        """
        await ws.accept()
        self.active.setdefault(plan_id, []).append(ws)

    def disconnect(self, ws: WebSocket, plan_id: int):
        """
        Remove a WebSocket from the plan's connection list.

        Args:
            ws: Socket that disconnected.
            plan_id: Plan key used at connect time.

        Returns:
            None.

        Side effects:
            Removes ``ws``; deletes the plan key when the list empties.

        Failure behavior:
            No-op if already removed.
        """
        conns = self.active.get(plan_id, [])
        if ws in conns:
            conns.remove(ws)
            if not conns:
                del self.active[plan_id]

    async def broadcast(self, plan_id: int, message: dict):
        """
        Send a JSON message to all sockets watching ``plan_id``.

        Args:
            plan_id: Target plan.
            message: JSON-serializable payload.

        Returns:
            None.

        Side effects:
            Awaits ``send_json`` per active socket.

        Failure behavior:
            Logs exceptions per client and continues to remaining clients.
        """
        for ws in self.active.get(plan_id, []):
            try:
                await ws.send_json(message)
            except Exception:
                logger.exception("Failed to send execution update to WebSocket client for plan %s", plan_id)


# Shared manager instance for execution sockets.
execution_manager = ExecutionConnectionManager()


@router.websocket("/ws/execution/{plan_id}")
async def websocket_execution(websocket: WebSocket, plan_id: int):
    """
    Plan-scoped WebSocket that pushes task list snapshots on fleet events.

    Purpose:
        Keep an execution view updated by re-fetching tasks for ``plan_id``
        whenever the event bus wakes (any invalidation), plus idle pings.

    Args:
        websocket: Client socket.
        plan_id: Plan to monitor.

    Returns:
        None (streaming handler).

    Side effects:
        Uses ``get_bridge().list_tasks``; registers with event bus and manager.

    Failure behavior:
        Disconnect ends quietly; other errors logged; shutdown key breaks loop.
        Requires initialized bridge (may error if called before lifespan init).
    """
    # Local import avoids circular import at module load time.
    from ..dependencies import get_bridge

    bridge = get_bridge()
    await execution_manager.connect(websocket, plan_id)
    queue = event_bus.subscribe()

    try:
        while True:
            try:
                keys = await asyncio.wait_for(queue.get(), timeout=30.0)
            except asyncio.TimeoutError:
                await websocket.send_json({"type": "ping"})
                continue

            if keys == ["__shutdown__"]:
                break

            # Refresh the full task list for this plan on any bus wake-up.
            tasks = bridge.list_tasks(plan_ids=[plan_id])
            await websocket.send_json({
                "type": "tasks_update",
                "plan_id": plan_id,
                "tasks": [t if isinstance(t, dict) else t.dict() for t in tasks],
            })
    except WebSocketDisconnect:
        pass
    except Exception:
        logger.exception("WebSocket execution handler failed for plan %s", plan_id)
    finally:
        event_bus.unsubscribe(queue)
        execution_manager.disconnect(websocket, plan_id)
