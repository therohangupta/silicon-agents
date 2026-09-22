"""
HTTP batch ingest endpoint for telemetry events.

Accepts JSON-encoded events (a bare list, a ``{events: [...]}`` wrapper, or a
single object), converts each dict to a ``TelemetryEvent`` via
``ParseDict``, validates, deduplicates, stamps ``ingest_time_ns``, and
publishes to NATS. Returns an ``IngestResponse`` summarizing accepted /
rejected counts and truncated error strings.
"""

# Logging for per-event failures and sequence warnings.
import logging
# time.time_ns for ingest_time_ns.
import time
# Any kept for loose JSON typing at the boundary.
from typing import Any  # noqa: F401

# Request gives access to app.state.message_bus.
from fastapi import APIRouter, Request
# Response model for OpenAPI / validation.
from pydantic import BaseModel

# Protobuf TelemetryEvent and Modality enum.
from packages.proto.telemetry_pb2 import TelemetryEvent, TelemetryBatch, Modality  # TelemetryBatch unused but historical
from google.protobuf.json_format import ParseDict, MessageToDict  # MessageToDict unused historically

# Shared validation with gRPC path.
from ..validation import validate_event, check_sequence
# Shared event_id LRU.
from ..dedup import get_dedup_cache

# Module logger.
logger = logging.getLogger(__name__)

# Routes under /telemetry.
router = APIRouter(prefix="/telemetry", tags=["Telemetry Ingest"])

# Modality enum -> subject path segment (mirrors grpc_server).
_MODALITY_SUBJECT = {
    Modality.STATE: "state",
    Modality.ACTION: "action",
    Modality.VISION: "vision",
    Modality.EVENT: "event",
}


class IngestResponse(BaseModel):
    """JSON response summarizing a batch ingest attempt."""

    # True only when rejected == 0.
    ok: bool
    # Count of events published to the bus.
    accepted: int = 0
    # Count of validation/parse failures.
    rejected: int = 0
    # Human-readable errors (capped when returned).
    errors: list[str] = []
    # event_ids that failed validation or parse.
    rejected_event_ids: list[str] = []


@router.post("/ingest")
async def ingest_batch(request: Request) -> IngestResponse:
    """
    Accept a JSON array of telemetry events (or TelemetryBatch.events shape).

    Validates, deduplicates, augments with ingest_time_ns, and publishes each
    accepted event to ``telemetry.{modality}.{agent_id}``. Duplicate event_ids
    are skipped without counting as rejected. Errors list is truncated to 20
    entries in the response.
    """
    # Raw JSON body from the client.
    body = await request.json()
    # Normalize list | {events: [...]} | single object into an iterable.
    events_raw = body if isinstance(body, list) else body.get("events", [body])

    # Bus installed on app.state during lifespan (may be disconnected).
    bus = request.app.state.message_bus
    # Shared dedup with gRPC.
    dedup = get_dedup_cache()
    # Aggregate counters / messages.
    accepted = 0
    rejected = 0
    errors: list[str] = []
    rejected_ids: list[str] = []

    # Process each raw dict/object independently.
    for raw in events_raw:
        try:
            # Fresh protobuf message to populate.
            event = TelemetryEvent()
            # JSON dict -> protobuf fields.
            ParseDict(raw, event)

            # Skip duplicates silently.
            if dedup.is_duplicate(event.event_id):
                continue

            # Hard validation.
            err = validate_event(event)
            if err:
                rejected += 1
                errors.append(f"{event.event_id}: {err}")
                rejected_ids.append(event.event_id)
                continue

            # Soft sequence warning.
            seq_err = check_sequence(event)
            if seq_err:
                logger.warning("Sequence violation: %s", seq_err)

            # Server ingest timestamp.
            event.ingest_time_ns = time.time_ns()

            # Publish serialized event to modality subject.
            mod_name = _MODALITY_SUBJECT.get(event.modality, "unknown")
            subject = f"telemetry.{mod_name}.{event.agent_id}"
            await bus.publish(subject, event.SerializeToString())
            accepted += 1

        except Exception as e:
            # Parse or publish failure.
            rejected += 1
            # Best-effort event_id for the error list.
            eid = raw.get("event_id", "?") if isinstance(raw, dict) else "?"
            errors.append(f"{eid}: {e}")
            rejected_ids.append(eid)
            logger.warning("Failed to ingest event: %s", e)

    # Build response; cap errors to keep payloads small.
    return IngestResponse(
        ok=rejected == 0,
        accepted=accepted,
        rejected=rejected,
        errors=errors[:20],
        rejected_event_ids=rejected_ids,
    )
