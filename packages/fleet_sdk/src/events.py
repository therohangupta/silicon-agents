"""Fire-and-forget Gateway event emitter used by fleet-server and executor."""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

import httpx

from packages.config import GATEWAY_EVENT_URL

logger = logging.getLogger(__name__)
_client: Optional[httpx.AsyncClient] = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(timeout=3.0)
    return _client


async def _post_event(payload: dict) -> None:
    try:
        resp = await _get_client().post(GATEWAY_EVENT_URL, json=payload)
        logger.debug("Event sent (%s): %s", resp.status_code, payload.get("type"))
    except Exception as exc:
        logger.debug("Event delivery failed (non-fatal): %s", exc)


def emit(event_type: str, **kwargs) -> None:
    payload = {"type": event_type, **kwargs}
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_post_event(payload))
    except RuntimeError:
        pass
    except Exception:
        logger.exception("Unexpected error scheduling event emission")


def emit_task_changed(task_id: int, plan_id: Optional[int] = None, status: Optional[str] = None) -> None:
    emit("task.state_changed", task_id=task_id, plan_id=plan_id, status=status)


def emit_plan_changed(plan_id: int, status: Optional[str] = None) -> None:
    emit("plan.state_changed", plan_id=plan_id, status=status)


def emit_agent_changed(agent_id: str, action: str = "updated") -> None:
    emit("agent.changed", agent_id=agent_id, action=action)
