"""
HTTP client proxy to the Telemetry microservice for agent health.

The gateway prefers heartbeat-derived health over direct agent polling. This
module maintains a process-wide ``httpx.AsyncClient`` pointed at
``TELEMETRY_URL`` and exposes summary and per-agent health fetches used by
``routers/agents.py``.

On transport or non-success status codes, helpers return empty/None so the UI
degrades gracefully (agents show "No heartbeat received yet") instead of
failing the entire health endpoint with 500. The shared client is closed by
``app.lifespan`` via ``close_telemetry_client`` / ``close_client``.
"""

import logging
from typing import Dict, Any, Optional

import httpx

# Base URL of the Telemetry service (no trailing path required).
from ..config import TELEMETRY_URL

# Module logger for non-fatal Telemetry reachability issues.
logger = logging.getLogger(__name__)

# Lazily created shared AsyncClient; None until first get_client() call.
_client: Optional[httpx.AsyncClient] = None


async def get_client() -> httpx.AsyncClient:
    """
    Return (and lazily create) the shared Telemetry HTTP client.

    Purpose:
        Reuse one connection pool across health queries for efficiency.

    Args:
        None.

    Returns:
        Process-wide ``httpx.AsyncClient`` with a 5.0s timeout.

    Side effects:
        Creates ``_client`` on first call.

    Failure behavior:
        Propagates AsyncClient construction errors (rare).
    """
    global _client
    # Create once; subsequent callers share the same instance.
    if _client is None:
        _client = httpx.AsyncClient(timeout=5.0)
    return _client


async def close_client() -> None:
    """
    Close and clear the shared Telemetry HTTP client.

    Purpose:
        Release sockets during gateway shutdown.

    Args:
        None.

    Returns:
        None.

    Side effects:
        Awaits ``aclose()`` when a client exists; sets ``_client`` to None.

    Failure behavior:
        Propagates aclose errors to the lifespan shutdown path.
    """
    global _client
    if _client is not None:
        # Gracefully close pooled connections.
        await _client.aclose()
        # Force the next get_client() to construct a fresh client if needed.
        _client = None


async def get_health_summary() -> Dict[str, Dict[str, Any]]:
    """
    Fetch aggregated agent health from Telemetry ``GET /health/summary``.

    Purpose:
        Drive ``GET /api/agents/health/all`` when ``source=telemetry`` by
        joining Telemetry's host:port keys with fleet agent ids in the router.

    Args:
        None.

    Returns:
        Dict keyed by Telemetry's agent key (often ``host:port``) on HTTP 200;
        empty dict on any error or non-200.

    Side effects:
        Outbound HTTP GET to Telemetry.

    Failure behavior:
        Logs a warning and returns ``{}`` (no raise) so UI degrades gracefully.
    """
    try:
        # Ensure the shared client exists.
        client = await get_client()
        # Hit the summary endpoint on the Telemetry service.
        resp = await client.get(f"{TELEMETRY_URL}/health/summary")
        if resp.status_code == 200:
            # Pass through JSON object as-is for the router to join.
            return resp.json()
        logger.warning("Telemetry /health/summary returned %d", resp.status_code)
    except Exception as e:
        logger.warning("Failed to fetch health summary from Telemetry: %s", e)
    # Soft-fail empty mapping.
    return {}


async def get_agent_health(agent_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch health for one agent from Telemetry ``GET /health/{agent_id}``.

    Purpose:
        Power per-agent health when ``source=telemetry``.

    Args:
        agent_id: Identifier Telemetry uses for the agent (fleet agent_id).

    Returns:
        JSON dict on 200; ``None`` on 404 or any error/non-200.

    Side effects:
        Outbound HTTP GET to Telemetry.

    Failure behavior:
        Logs warnings for unexpected statuses/exceptions; returns None (no raise).
    """
    try:
        client = await get_client()
        resp = await client.get(f"{TELEMETRY_URL}/health/{agent_id}")
        if resp.status_code == 200:
            return resp.json()
        if resp.status_code == 404:
            # Unknown to Telemetry yet — treat as no heartbeat.
            return None
        logger.warning("Telemetry /health/%s returned %d", agent_id, resp.status_code)
    except Exception as e:
        logger.warning("Failed to fetch health for %s from Telemetry: %s", agent_id, e)
    return None
