"""
HTTP batch ingest endpoint for telemetry events.

Accepts JSON-encoded TelemetryBatch, validates each event,
deduplicates, augments with ingest_time_ns, and publishes to the message bus.
"""

import logging
import time
from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel

from packages.proto.telemetry_pb2 import TelemetryEvent, TelemetryBatch, Modality
from google.protobuf.json_format import ParseDict, MessageToDict

from ..validation import validate_event, check_sequence
from ..dedup import get_dedup_cache

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/telemetry", tags=["Telemetry Ingest"])

_MODALITY_SUBJECT = {
    Modality.STATE: "state",
    Modality.ACTION: "action",
    Modality.VISION: "vision",
    Modality.EVENT: "event",
}


class IngestResponse(BaseModel):
    ok: bool
    accepted: int = 0
    rejected: int = 0
    errors: list[str] = []
    rejected_event_ids: list[str] = []


@router.post("/ingest")
async def ingest_batch(request: Request) -> IngestResponse:
    """
    Accept a JSON array of telemetry events (TelemetryBatch.events).
    Validates, deduplicates, augments, and publishes each to the message bus.
    """
    body = await request.json()
    events_raw = body if isinstance(body, list) else body.get("events", [body])

    bus = request.app.state.message_bus
    dedup = get_dedup_cache()
    accepted = 0
    rejected = 0
    errors: list[str] = []
    rejected_ids: list[str] = []

    for raw in events_raw:
        try:
            event = TelemetryEvent()
            ParseDict(raw, event)

            if dedup.is_duplicate(event.event_id):
                continue

            err = validate_event(event)
            if err:
                rejected += 1
                errors.append(f"{event.event_id}: {err}")
                rejected_ids.append(event.event_id)
                continue

            seq_err = check_sequence(event)
            if seq_err:
                logger.warning("Sequence violation: %s", seq_err)

            event.ingest_time_ns = time.time_ns()

            mod_name = _MODALITY_SUBJECT.get(event.modality, "unknown")
            subject = f"telemetry.{mod_name}.{event.robot_id}"
            await bus.publish(subject, event.SerializeToString())
            accepted += 1

        except Exception as e:
            rejected += 1
            eid = raw.get("event_id", "?") if isinstance(raw, dict) else "?"
            errors.append(f"{eid}: {e}")
            rejected_ids.append(eid)
            logger.warning("Failed to ingest event: %s", e)

    return IngestResponse(
        ok=rejected == 0,
        accepted=accepted,
        rejected=rejected,
        errors=errors[:20],
        rejected_event_ids=rejected_ids,
    )
