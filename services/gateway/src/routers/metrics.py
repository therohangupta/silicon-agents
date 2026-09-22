"""
Metrics query endpoint for gateway observability (``/api/metrics``).

Exposes ``MetricEvent`` rows stored via the instance registry (including those
written by ``RequestMetricsMiddleware`` for each API request). Supports
optional filters by service name, event type, and a rolling time window.

HTTP behavior:

- ``GET ""`` → **200** ``{"metrics": [...], "count": N}`` on success
- On query failure → **200** with empty list plus ``"error"`` key (soft fail
  so the metrics UI does not hard-break the dashboard)
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query

from ..dependencies import get_bridge

# Tagged Metrics in OpenAPI; path /api/metrics.
router = APIRouter(prefix="/metrics", tags=["Metrics"])
logger = logging.getLogger(__name__)


@router.get("")
async def list_metrics(
    service: Optional[str] = Query(None, description="Filter by service name"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    since: Optional[int] = Query(None, description="Only events from the last N seconds"),
    limit: int = Query(200, ge=1, le=1000, description="Max rows to return"),
):
    """
    Return stored metric events with optional filters.

    Args:
        service: Optional service name filter (e.g. ``gateway``).
        event_type: Optional event type filter (e.g. ``api_request``).
        since: If set, only events from the last N seconds.
        limit: Max rows (1–1000, default 200).

    Returns:
        Dict with ``metrics`` list and ``count``; may include ``error`` string.

    Side effects:
        Async DB query via ``bridge.registry.list_metrics``.

    Failure behavior:
        Logs exception and returns empty metrics with error field (**200**),
        not HTTP 500, so observability panels degrade gracefully.
        **422** if limit out of range.
    """
    # Resolve bridge outside Depends signature to match original handler style.
    bridge = get_bridge()
    try:
        # Delegate filtering/limit to the registry implementation.
        rows = await bridge.registry.list_metrics(
            service=service,
            event_type=event_type,
            since_seconds=since,
            limit=limit,
        )
        return {"metrics": rows, "count": len(rows)}
    except Exception:
        logger.exception("Failed to query metrics")
        return {"metrics": [], "count": 0, "error": "Failed to query metrics"}
