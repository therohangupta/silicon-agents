"""
Shared validation logic for incoming TelemetryEvent messages.

Used by both HTTP batch ingest and the gRPC TelemetryIngestion servicer so
the two transports enforce identical rules: required envelope fields, modality
vs payload oneof consistency, max serialized size, and optional signal label
length checks. ``check_sequence`` separately tracks last sequence_id per
(agent, task, modality, stream) and returns a soft-error string for logging
without rejecting the publish path when callers choose to continue.
"""

# Logger for optional diagnostics (sequence path currently logs at call sites).
import logging
# Optional[str] error returns keep the API simple for callers.
from typing import Optional

# Generated protobuf types for TelemetryEvent and Modality enum.
from packages.proto.telemetry_pb2 import TelemetryEvent, Modality

# Module logger (available if we add debug traces later).
logger = logging.getLogger(__name__)

# Hard ceiling on serialized event size to protect NATS and Parquet writers.
MAX_EVENT_BYTES = 1_048_576  # 1 MB

# In-process map of last accepted sequence_id keyed by stream identity tuple.
_last_seq: dict[tuple[str, str, str], int] = {}


def validate_event(event: TelemetryEvent) -> Optional[str]:
    """Validate a TelemetryEvent. Returns an error string on failure, None on success.

    Checks ``event_id``, ``agent_id``, specified modality, ``stream_name``,
    presence of a payload oneof, that the oneof matches the modality enum,
    ByteSize against ``MAX_EVENT_BYTES``, and for state/action payloads that
    any labels list length matches values length. Does not mutate the event.
    """
    # Every durable/deduped event needs a stable id.
    if not event.event_id:
        return "missing event_id"
    # Publisher identity required for subject routing.
    if not event.agent_id:
        return "missing agent_id"
    # Unspecified modality cannot map to a NATS subject suffix.
    if event.modality == Modality.MODALITY_UNSPECIFIED:
        return "modality must be specified"
    # Stream name partitions Parquet and sequence tracking.
    if not event.stream_name:
        return "missing stream_name"

    # WhichOneof returns the active payload field name or None.
    payload_field = event.WhichOneof("payload")
    # Reject envelope-only messages with no body.
    if payload_field is None:
        return "missing payload"

    # Map modality enum to the expected oneof arm name.
    expected = {
        Modality.STATE: "state",
        Modality.ACTION: "action",
        Modality.VISION: "vision",
        Modality.EVENT: "event",
    }
    # Mismatch means a buggy producer filled the wrong payload arm.
    if expected.get(event.modality) != payload_field:
        return f"modality {Modality.Name(event.modality)} but payload is '{payload_field}'"

    # Protect bus and disk from oversized frames (vision should use blob upload).
    if event.ByteSize() > MAX_EVENT_BYTES:
        return f"event too large ({event.ByteSize()} bytes, max {MAX_EVENT_BYTES})"

    # State signals: optional labels must align with values.
    if payload_field == "state":
        err = _validate_signals(event.state.signals)
        if err:
            return err
    # Action signals: same label/value length rule.
    elif payload_field == "action":
        err = _validate_signals(event.action.signals)
        if err:
            return err

    # All checks passed.
    return None


def check_sequence(event: TelemetryEvent) -> Optional[str]:
    """Enforce strictly increasing sequence_id per stream identity.

    Key is ``(agent_id, task_id, modality, stream_name)``. Returns an error
    string if the new sequence_id is not greater than the last seen value.
    Non-blocking for producers that leave sequence_id at 0 (unset): returns
    None without updating state. Note sequence_id is per-stream ordering,
    distinct from step_index which spans modalities for a task.
    """
    # Treat zero as "producer did not set sequence"; skip monotonicity.
    if event.sequence_id == 0:
        return None

    # Tuple identity for this ordered stream.
    key = (event.agent_id, event.task_id, event.modality, event.stream_name)
    # Default last=0 so the first positive sequence always succeeds.
    last = _last_seq.get(key, 0)
    # Reject equal or regressing sequence numbers.
    if event.sequence_id <= last:
        return (
            f"sequence_id {event.sequence_id} <= last seen {last} "
            f"for ({event.agent_id}, {event.task_id}, "
            f"{Modality.Name(event.modality)}, {event.stream_name})"
        )
    # Advance the watermark for subsequent events on this key.
    _last_seq[key] = event.sequence_id
    # Success: no error string.
    return None


def _validate_signals(signals) -> Optional[str]:
    """Return an error if any signal has labels length != values length.

    Empty labels are allowed (callers may expand labels from the signal name).
    When labels are present they must be parallel to values for Parquet
    long-format expansion.
    """
    # Walk every Signal message in the repeated field.
    for sig in signals:
        # Only enforce when labels were provided.
        if sig.labels and len(sig.labels) != len(sig.values):
            return (
                f"signal '{sig.name}': labels length ({len(sig.labels)}) "
                f"!= values length ({len(sig.values)})"
            )
    # All signals consistent.
    return None
