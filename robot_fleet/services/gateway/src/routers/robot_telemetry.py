"""
Robot telemetry endpoints for the gateway.

- WS /ws/telemetry/{robot_id}  — real-time telemetry stream per robot (state/action/events)
- GET /api/telemetry/{robot_id}/latest — latest cached state (REST)
- GET /api/telemetry/blob — proxy blob reads (local or presigned S3)
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

router = APIRouter(tags=["Robot Telemetry"])


@router.websocket("/ws/telemetry/{robot_id}")
async def websocket_telemetry(websocket: WebSocket, robot_id: str):
    """
    Per-robot telemetry WebSocket.

    On connect, sends the latest cached state for immediate UI population.
    Then streams new events as they arrive from the bus.
    """
    await websocket.accept()

    latest = get_latest_state(robot_id)
    if latest:
        await websocket.send_json({
            "type": "initial_state",
            "robot_id": robot_id,
            "streams": latest,
        })

    queue = subscribe_ws(robot_id)

    try:
        while True:
            try:
                event_dict = await asyncio.wait_for(queue.get(), timeout=30.0)
            except asyncio.TimeoutError:
                await websocket.send_json({"type": "ping"})
                continue

            await websocket.send_json({
                "type": "telemetry",
                "robot_id": robot_id,
                **event_dict,
            })
    except WebSocketDisconnect:
        pass
    except Exception:
        logger.exception("Telemetry WS error for robot %s", robot_id)
    finally:
        unsubscribe_ws(robot_id, queue)


@router.get("/api/telemetry/{robot_id}/latest")
async def get_robot_telemetry_latest(robot_id: str):
    """Return the latest cached telemetry events for *robot_id*."""
    return get_latest_state(robot_id)


@router.get("/api/telemetry/blob")
async def get_telemetry_blob(uri: str = Query(...)):
    """
    Serve a telemetry blob.

    - Local backend: serves the file directly.
    - S3 backend: redirects to a presigned URL.
    """
    if uri.startswith("s3://"):
        try:
            import boto3
            client = boto3.client("s3", region_name=S3_REGION)
            parts = uri.replace("s3://", "").split("/", 1)
            bucket, key = parts[0], parts[1]
            presigned = client.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket, "Key": key},
                ExpiresIn=3600,
            )
            return RedirectResponse(url=presigned)
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)

    blob_path = Path(BLOB_STORAGE_ROOT) / uri.lstrip("/").removeprefix("blobs/")
    if blob_path.exists():
        return FileResponse(str(blob_path))
    return JSONResponse({"error": "blob not found"}, status_code=404)
