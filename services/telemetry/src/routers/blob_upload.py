"""
Blob upload endpoint for telemetry vision data.

Agents upload frames/images here; the service stores them via ``BlobStore``
and returns a URI. That URI is then included in a ``VisionPayload.BlobRef``
in subsequent telemetry events so large binaries never ride on the NATS path.
"""

# Logging for successful store operations.
import logging

# Multipart form parsing helpers from FastAPI.
from fastapi import APIRouter, File, Form, UploadFile, Request  # Request unused historically

# Singleton blob backend (local or S3).
from ..blob_store import get_blob_store

# Module logger.
logger = logging.getLogger(__name__)

# Routes under /telemetry (same prefix as batch ingest; different path).
router = APIRouter(prefix="/telemetry", tags=["Telemetry Blobs"])


@router.post("/blob")
async def upload_blob(
    agent_id: str = Form(...),
    stream_name: str = Form(...),
    file: UploadFile = File(...),
    task_id: str = Form(""),
):
    """
    Upload a blob (image frame, video clip, etc.) to storage.

    Returns the URI that should be placed in ``BlobRef.uri`` within a
    ``VisionPayload``. When *task_id* is provided the blob is stored under a
    task-scoped sub-directory so different runs never collide. Also returns
    ``size`` as the byte length of the uploaded body.
    """
    # Resolve configured backend.
    store = get_blob_store()
    # Read entire upload into memory (frames are expected to be bounded).
    data = await file.read()
    # Fall back filename when the client omitted one.
    filename = file.filename or "blob"

    # Persist and receive local or s3 URI.
    uri = await store.write(agent_id, stream_name, filename, data, task_id=task_id)
    # Operator-visible audit line for each store.
    logger.info(
        "Blob stored: agent=%s task=%s stream=%s file=%s size=%d uri=%s",
        agent_id, task_id or "(none)", stream_name, filename, len(data), uri,
    )
    # JSON response for the agent SDK.
    return {"uri": uri, "size": len(data)}
