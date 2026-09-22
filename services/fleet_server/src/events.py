"""
Fire-and-forget Gateway event emitter for the Fleet Server.

After any mutating Fleet Manager operation (task create/update/delete, plan
create/delete/start, agent register/unregister), call one of the ``emit_*``
helpers so the Gateway can push WebSocket invalidation messages to connected
dashboard clients.

Design notes:
  - Emission is non-blocking: ``emit`` schedules an asyncio Task and returns
    immediately so gRPC handlers are not delayed by HTTP latency.
  - Failures are intentionally soft: network errors are logged at DEBUG and
    never raised to callers (dashboard freshness is best-effort).
  - A module-level ``httpx.AsyncClient`` is reused to avoid connection churn.
  - If no event loop is running (sync contexts / tests), emission is a no-op.

The Gateway URL defaults via ``packages.config.GATEWAY_EVENT_URL`` (typically
``http://localhost:8000/internal/events``).
"""

# asyncio is used to schedule the POST onto the running event loop.
import asyncio
# logging records successful and failed deliveries without raising.
import logging
# Optional typing for the shared AsyncClient singleton.
from typing import Optional

# httpx performs the async HTTP POST to the Gateway internal events endpoint.
import httpx

# GATEWAY_EVENT_URL is the configured POST target for mutation notifications.
from packages.config import GATEWAY_EVENT_URL

# Module logger; keep messages at DEBUG so production logs stay quiet unless
# operators intentionally raise the level for event debugging.
logger = logging.getLogger(__name__)

# Lazily created shared AsyncClient; None until first use or after close.
_client: Optional[httpx.AsyncClient] = None


def _get_client() -> httpx.AsyncClient:
    """
    Return a process-wide ``httpx.AsyncClient``, creating it if needed.

    Recreates the client when the previous instance was closed so subsequent
    emits after a shutdown/restart path still work. Timeout is short (3s)
    because event delivery must not hang the background Task indefinitely.

    Returns:
        A live ``httpx.AsyncClient`` bound to a 3-second request timeout.
    """
    # Mutate the module-level singleton; callers always go through this helper.
    global _client
    # Create or replace when missing or already closed by a prior lifecycle.
    if _client is None or _client.is_closed:
        # Short timeout: failed emits should fail fast and be forgotten.
        _client = httpx.AsyncClient(timeout=3.0)
    # Always return the (possibly newly created) shared client.
    return _client


async def _post_event(payload: dict) -> None:
    """
    POST a single event payload to the Gateway events URL.

    This coroutine is scheduled by ``emit`` and must never raise into the
    gRPC handler. All exceptions are caught and logged at DEBUG.

    Args:
        payload: JSON-serializable dict including at least a ``type`` key
            (for example ``task.state_changed``) plus entity identifiers.
    """
    try:
        # Perform the HTTP POST with the shared client; body is JSON.
        resp = await _get_client().post(GATEWAY_EVENT_URL, json=payload)
        # Log status + event type for opportunistic debugging of delivery.
        logger.debug("Event sent (%s): %s", resp.status_code, payload.get("type"))
    except Exception as exc:
        # Non-fatal by design: dashboard may lag until next poll/refresh.
        logger.debug("Event delivery failed (non-fatal): %s", exc)


def emit(event_type: str, **kwargs) -> None:
    """
    Fire-and-forget: schedule an event POST without blocking the caller.

    Builds a payload ``{"type": event_type, **kwargs}`` and creates an
    asyncio Task on the running loop. If there is no running loop (sync
    contexts), the call is silently ignored.

    Args:
        event_type: Gateway event type string (e.g. ``plan.state_changed``).
        **kwargs: Additional JSON fields (ids, status, action, etc.).
    """
    # Merge the type with arbitrary keyword fields into one JSON body.
    payload = {"type": event_type, **kwargs}
    try:
        # Require an already-running loop; gRPC aio handlers always have one.
        loop = asyncio.get_running_loop()
        # Schedule the POST; do not await — keep the gRPC path non-blocking.
        loop.create_task(_post_event(payload))
    except RuntimeError:
        # No running event loop (expected in sync contexts / some unit tests).
        pass
    except Exception:
        # Unexpected scheduling failures should be visible but not crash RPC.
        logger.exception("Unexpected error scheduling event emission")


def emit_task_changed(task_id: int, plan_id: Optional[int] = None, status: Optional[str] = None) -> None:
    """
    Notify the Gateway that a task's state changed.

    Called after create/update/delete/start/complete/fail paths in the
    FleetManager service and Executor so UIs can invalidate task views.

    Args:
        task_id: Database / proto task identifier that changed.
        plan_id: Optional owning plan id for scoped invalidation.
        status: Optional human-readable status hint (pending, deleted, etc.).
    """
    # Delegate to the generic emitter with the canonical task event type.
    emit("task.state_changed", task_id=task_id, plan_id=plan_id, status=status)


def emit_plan_changed(plan_id: int, status: Optional[str] = None) -> None:
    """
    Notify the Gateway that a plan's state changed.

    Called after plan create/delete and when execution status transitions
    (executing / completed / failed).

    Args:
        plan_id: Plan identifier that changed.
        status: Optional status string (created, deleted, executing, ...).
    """
    # Delegate to the generic emitter with the canonical plan event type.
    emit("plan.state_changed", plan_id=plan_id, status=status)


def emit_agent_changed(agent_id: str, action: str = "updated") -> None:
    """
    Notify the Gateway that an agent's registration lifecycle changed.

    Args:
        agent_id: Stable agent instance identifier string.
        action: Lifecycle verb such as ``registered`` or ``unregistered``.
    """
    # Delegate to the generic emitter with the canonical agent event type.
    emit("agent.changed", agent_id=agent_id, action=action)
