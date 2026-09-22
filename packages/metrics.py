"""Lightweight observability helpers shared by fleet services.

This module provides a single async context manager, ``track_operation``,
that times a wrapped coroutine block and fire-and-forget-records a metric
row through whatever registry object the caller passed in. The registry is
duck-typed: it only needs an async ``record_metric`` method. Fleet server,
gateway, and other control-plane services use this so latency and success
flags land in the same metrics table without each call site reinventing
timing logic.

Usage::

    async with track_operation(registry, "fleet_server", "plan_execution", str(plan_id)) as meta:
        meta["tasks"] = total_tasks
        await execute_plan(...)

Recording never raises into the caller: scheduling failures and missing
event loops are swallowed after a debug log so metric plumbing cannot
break plan execution.
"""

# Standard library: asyncio schedules the fire-and-forget write.
import asyncio
# logging reports schedule failures without aborting the caller.
import logging
# time.monotonic is used so wall-clock jumps do not skew durations.
import time
# asynccontextmanager turns the generator below into a usable ``async with``.
from contextlib import asynccontextmanager
# Optional entity_id lets callers attach a plan/task/agent key when known.
from typing import Optional

# Module logger named after this file for consistent log filtering.
logger = logging.getLogger(__name__)


@asynccontextmanager
async def track_operation(
    registry,
    service: str,
    event_type: str,
    entity_id: Optional[str] = None,
):
    """Time the wrapped block and schedule a metric write on the registry.

    Parameters
    ----------
    registry:
        Object exposing ``async record_metric(...)``. Typically the fleet
        server's persistence/registry façade.
    service:
        Logical service name written into the metric row (e.g. ``fleet_server``).
    event_type:
        Short label for the operation being timed (e.g. ``plan_execution``).
    entity_id:
        Optional primary key of the entity under measurement (plan id, etc.).

    Yields
    ------
    dict
        Mutable metadata bag. Callers may stash extra fields; if non-empty
        they are passed through as ``metadata`` on the metric row.

    Notes
    -----
    On exception the metric is still recorded with ``success=False`` and the
    original exception is re-raised. Metric scheduling uses
    ``create_task`` so the write does not block the critical path.
    """
    # Capture monotonic start so duration is immune to NTP corrections.
    start = time.monotonic()
    # Assume success until an exception proves otherwise.
    success = True
    # Callers mutate this dict to attach operation-specific metadata.
    meta: dict = {}
    try:
        # Hand control to the wrapped block; yield the mutable meta bag.
        yield meta
    except Exception:
        # Mark failure so the metric reflects the aborted path.
        success = False
        # Re-raise so callers still see the original error.
        raise
    finally:
        # Convert elapsed monotonic seconds into an integer millisecond duration.
        duration_ms = int((time.monotonic() - start) * 1000)
        try:
            # Schedule recording on the running loop without awaiting it.
            asyncio.get_running_loop().create_task(
                registry.record_metric(
                    # Service that owns this measurement.
                    service=service,
                    # Operation label for aggregation/filtering.
                    event_type=event_type,
                    # Optional entity primary key.
                    entity_id=entity_id,
                    # Wall-independent duration of the wrapped block.
                    duration_ms=duration_ms,
                    # True unless the block raised.
                    success=success,
                    # Only send metadata when the caller filled something in.
                    metadata=meta if meta else None,
                )
            )
        except RuntimeError:
            # No running loop (e.g. called from sync teardown) — skip silently.
            pass  # No running event loop
        except Exception:
            # Any other scheduling/registry construction error is debug-only.
            logger.debug("Failed to schedule metric recording", exc_info=True)
