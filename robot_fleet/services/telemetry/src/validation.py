"""
Shared validation logic for incoming TelemetryEvent messages.

Checks required fields, sequence monotonicity, payload consistency,
and max payload size.
"""

import logging
from typing import Optional

from packages.proto.telemetry_pb2 import TelemetryEvent, Modality

logger = logging.getLogger(__name__)

MAX_EVENT_BYTES = 1_048_576  # 1 MB

_last_seq: dict[tuple[str, str, str], int] = {}


def validate_event(event: TelemetryEvent) -> Optional[str]:
    """
    Validate a TelemetryEvent.  Returns an error string on failure, None on success.
    """
    if not event.event_id:
        return "missing event_id"
    if not event.robot_id:
        return "missing robot_id"
    if event.modality == Modality.MODALITY_UNSPECIFIED:
        return "modality must be specified"
    if not event.stream_name:
        return "missing stream_name"

    payload_field = event.WhichOneof("payload")
    if payload_field is None:
        return "missing payload"

    expected = {
        Modality.STATE: "state",
        Modality.ACTION: "action",
        Modality.VISION: "vision",
        Modality.EVENT: "event",
    }
    if expected.get(event.modality) != payload_field:
        return f"modality {Modality.Name(event.modality)} but payload is '{payload_field}'"

    if event.ByteSize() > MAX_EVENT_BYTES:
        return f"event too large ({event.ByteSize()} bytes, max {MAX_EVENT_BYTES})"

    if payload_field == "state":
        err = _validate_signals(event.state.signals)
        if err:
            return err
    elif payload_field == "action":
        err = _validate_signals(event.action.signals)
        if err:
            return err

    return None


def check_sequence(event: TelemetryEvent) -> Optional[str]:
    """
    Enforce strictly increasing sequence_id per (robot_id, task_id, modality, stream_name).
    Returns error string if violated, None if OK.
    Non-blocking: skips check if sequence_id is 0 (unset).

    Note: sequence_id is per-stream ordering, distinct from step_index which is
    per-(robot_id, task_id) across all streams.
    """
    if event.sequence_id == 0:
        return None

    key = (event.robot_id, event.task_id, event.modality, event.stream_name)
    last = _last_seq.get(key, 0)
    if event.sequence_id <= last:
        return (
            f"sequence_id {event.sequence_id} <= last seen {last} "
            f"for ({event.robot_id}, {event.task_id}, "
            f"{Modality.Name(event.modality)}, {event.stream_name})"
        )
    _last_seq[key] = event.sequence_id
    return None


def _validate_signals(signals) -> Optional[str]:
    for sig in signals:
        if sig.labels and len(sig.labels) != len(sig.values):
            return (
                f"signal '{sig.name}': labels length ({len(sig.labels)}) "
                f"!= values length ({len(sig.values)})"
            )
    return None
