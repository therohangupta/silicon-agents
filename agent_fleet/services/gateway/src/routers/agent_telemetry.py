"""
Agent telemetry WebSocket, latest-state REST, and blob proxy routes.

This router is mounted at the application root (not under ``api_router``) so
paths match the dashboard contracts exactly:

- ``WS /ws/telemetry/{agent_id}`` — realtime stream fed by the NATS consumer's
  per-agent queues; sends ``initial_state`` then ``telemetry`` events / pings.
- ``GET /api/telemetry/{agent_id}/latest`` — snapshot of the consumer cache.
- ``GET /api/telemetry/blob?uri=...`` — serve local blob files or redirect to
  an S3 presigned URL for ``s3://`` URIs.

HTTP/WS failure behavior: blob missing → **404**; S3 errors → **500** JSON;
WS disconnect cleans up subscriptions in ``finally``.
"""

import asyncio
import logging
from pathlib import Path

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import FileResponse, RedirectResponse, JSONResponse

from packages.config import BLOB_STORAGE_BACKEND, BLOB_STORAGE_ROOT, S3_BUCKET, S3_REGION

from ..consumers.telemetry_consumer import (
    get_latest_state,
    subscribe_ws,
    unsubscribe_ws,
)

logger = logging.getLogger(__name__)

# No prefix: paths are absolute as declared on each decorator.
router = APIRouter(tags=["Agent Telemetry"])


@router.websocket("/ws/telemetry/{agent_id}")
async def websocket_telemetry(websocket: WebSocket, agent_id: str):
    """
    Per-agent telemetry WebSocket fed by the NATS JetStream consumer.

    Purpose:
        On connect, push cached latest streams for immediate UI paint, then
        stream new events as the consumer fans them into this socket's queue.
        Idle 30s waits emit ``ping`` keepalives.

    Args:
        websocket: Client WebSocket.
        agent_id: Fleet agent id to subscribe to.

    Returns:
        None (streaming handler).

    Side effects:
        ``subscribe_ws`` / ``unsubscribe_ws``; sends JSON frames.

    Failure behavior:
        Disconnect ends quietly; other errors logged; always unsubscribes.
        Dropped events possible if the queue fills (consumer side).
    """
    await websocket.accept()

    # Seed the UI with whatever the consumer has already cached.
    latest = get_latest_state(agent_id)
    if latest:
        await websocket.send_json({
            "type": "initial_state",
            "agent_id": agent_id,
            "streams": latest,
        })

    # Register for live fan-out from run_telemetry_consumer.
    queue = subscribe_ws(agent_id)

    try:
        while True:
            try:
                event_dict = await asyncio.wait_for(queue.get(), timeout=30.0)
            except asyncio.TimeoutError:
                await websocket.send_json({"type": "ping"})
                continue

            # Spread protobuf-derived fields under a telemetry envelope.
            await websocket.send_json({
                "type": "telemetry",
                "agent_id": agent_id,
                **event_dict,
            })
    except WebSocketDisconnect:
        pass
    except Exception:
        logger.exception("Telemetry WS error for agent %s", agent_id)
    finally:
        unsubscribe_ws(agent_id, queue)


@router.get("/api/telemetry/{agent_id}/latest")
async def get_agent_telemetry_latest(agent_id: str):
    """
    Return the latest cached telemetry events for one agent.

    Args:
        agent_id: Fleet agent id.

    Returns:
        Mapping of stream_name → event dict (may be empty).

    Side effects:
        Reads in-process cache only (no NATS I/O).

    Failure behavior:
        Always **200**; empty object if nothing cached yet.
    """
    return get_latest_state(agent_id)


@router.get("/api/telemetry/blob")
async def get_telemetry_blob(uri: str = Query(...)):
    """
    Serve or redirect to a telemetry blob referenced by URI.

    Purpose:
        - ``s3://bucket/key`` → generate presigned GET and **302** redirect.
        - Otherwise treat as local path under ``BLOB_STORAGE_ROOT`` (stripping
          a leading ``blobs/`` prefix when present) and return ``FileResponse``.

    Args:
        uri: Required query string identifying the blob.

    Returns:
        RedirectResponse, FileResponse, or JSON error body.

    Side effects:
        May call AWS S3 via boto3; may read local filesystem.

    Failure behavior:
        S3/presign errors → **500** JSON ``{"error": ...}``.
        Missing local file → **404** JSON ``{"error": "blob not found"}``.
        Missing ``uri`` query → **422**.
    """
    if uri.startswith("s3://"):
        try:
            # Lazy import so local-only deployments need not install boto3 usage path eagerly.
            import boto3
            client = boto3.client("s3", region_name=S3_REGION)
            # Split s3://bucket/key into bucket and key (first slash only).
            parts = uri.replace("s3://", "").split("/", 1)
            bucket, key = parts[0], parts[1]
            # One-hour temporary URL for the browser to fetch directly from S3.
            presigned = client.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket, "Key": key},
                ExpiresIn=3600,
            )
            return RedirectResponse(url=presigned)
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)

    # Map logical uri onto the configured local blob root.
    blob_path = Path(BLOB_STORAGE_ROOT) / uri.lstrip("/").removeprefix("blobs/")
    if blob_path.exists():
        return FileResponse(str(blob_path))
    return JSONResponse({"error": "blob not found"}, status_code=404)
