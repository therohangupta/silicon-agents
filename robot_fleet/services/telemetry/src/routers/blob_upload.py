"""
Blob upload endpoint for telemetry vision data.

Robots upload frames/images here; the service stores them and returns a URI.
The URI is then included in a VisionPayload.BlobRef in subsequent telemetry events.
"""

import logging

from fastapi import APIRouter, File, Form, UploadFile, Request

from ..blob_store import get_blob_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/telemetry", tags=["Telemetry Blobs"])


@router.post("/blob")
async def upload_blob(
    robot_id: str = Form(...),
    stream_name: str = Form(...),
    file: UploadFile = File(...),
    task_id: str = Form(""),
):
    """
    Upload a blob (image frame, video clip, etc.) to storage.

    Returns the URI that should be placed in ``BlobRef.uri`` within a
    ``VisionPayload``.  When *task_id* is provided the blob is stored
    under a task-scoped sub-directory so different runs never collide.
    """
    store = get_blob_store()
    data = await file.read()
    filename = file.filename or "blob"

    uri = await store.write(robot_id, stream_name, filename, data, task_id=task_id)
    logger.info(
        "Blob stored: robot=%s task=%s stream=%s file=%s size=%d uri=%s",
        robot_id, task_id or "(none)", stream_name, filename, len(data), uri,
    )
    return {"uri": uri, "size": len(data)}
