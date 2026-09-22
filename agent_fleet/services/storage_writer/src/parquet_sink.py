"""
Parquet sink that buffers telemetry events and writes partitioned Parquet files.

Each modality (state, action, vision, event) has its own long-format table
schema with shared envelope columns. Files land on disk as::

  {root}/{modality}/agent_id={X}/task_id={Y}/date={Z}/part-{ts}_{uuid}.parquet

Flush triggers: ``FLUSH_ROW_THRESHOLD`` rows across buffers or
``FLUSH_TIME_SECS`` since last flush. Only events that passed the worker's
``persist=true`` filter should be ingested here.
"""

# Logging for write confirmations.
import logging
# Monotonic clock for flush timing; time.time for part filenames.
import time
# Unique suffix in part filenames.
import uuid
# UTC date partition key.
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional  # historical; used in type hints if extended

# Arrow table construction and Parquet I/O.
import pyarrow as pa
import pyarrow.parquet as pq

# Protobuf enums and event type.
from packages.proto.telemetry_pb2 import TelemetryEvent, Modality, Completeness

# Module logger.
logger = logging.getLogger(__name__)

# Flush after this many buffered rows OR this many seconds, whichever comes first.
FLUSH_ROW_THRESHOLD = 10_000
FLUSH_TIME_SECS = 60.0


# Common envelope columns carried through to every Parquet table so that
# downstream consumers (ML pipelines, replay tools) can join / sort / filter
# without needing to parse the proto again.
_ENVELOPE_COLS = [
    ("timestamp_ns", pa.int64()),
    ("agent_id", pa.string()),
    ("task_id", pa.string()),
    ("step_index", pa.uint64()),
    ("sequence_id", pa.uint64()),
    ("source_id", pa.string()),
    ("completeness", pa.string()),
    ("done", pa.bool_()),
    ("sync_group", pa.string()),
]

# Long-format state: one row per labeled signal value.
STATE_SCHEMA = pa.schema([
    *_ENVELOPE_COLS,
    ("stream_name", pa.string()),
    ("signal_name", pa.string()),
    ("position", pa.float64()),
    ("velocity", pa.float64()),
    ("effort", pa.float64()),
    ("unit", pa.string()),
])

# Long-format action targets.
ACTION_SCHEMA = pa.schema([
    *_ENVELOPE_COLS,
    ("stream_name", pa.string()),
    ("action_type", pa.string()),
    ("signal_name", pa.string()),
    ("target_position", pa.float64()),
    ("target_velocity", pa.float64()),
    ("unit", pa.string()),
])

# Vision rows reference blob URIs rather than inline pixels.
VISION_SCHEMA = pa.schema([
    *_ENVELOPE_COLS,
    ("camera_name", pa.string()),
    ("uri", pa.string()),
    ("frame_index", pa.uint64()),
    ("width", pa.int32()),
    ("height", pa.int32()),
    ("encoding", pa.string()),
    ("compression", pa.string()),
])

# Discrete event log rows.
EVENT_SCHEMA = pa.schema([
    *_ENVELOPE_COLS,
    ("event_type", pa.string()),
    ("severity", pa.string()),
    ("message", pa.string()),
])


class ParquetSink:
    """Buffers telemetry rows and periodically flushes to partitioned Parquet files.

    Maintains one list buffer and schema per modality. ``ingest`` expands a
    ``TelemetryEvent`` into flat dict rows; ``flush_all`` writes Hive-style
    partitions and clears buffers. ``should_flush`` encodes the row/time policy.
    """

    def __init__(self, root: str):
        """Create empty modality buffers rooted at *root*.

        Args:
            root: Filesystem root for modality partitions (``PARQUET_STORAGE_ROOT``).
        """
        # Base directory for all modality trees.
        self._root = Path(root)
        # Per-modality row buffers (list of dicts matching schemas).
        self._buffers: dict[str, list[dict]] = {
            "state": [],
            "action": [],
            "vision": [],
            "event": [],
        }
        # Schema lookup used when building Arrow tables.
        self._schemas = {
            "state": STATE_SCHEMA,
            "action": ACTION_SCHEMA,
            "vision": VISION_SCHEMA,
            "event": EVENT_SCHEMA,
        }
        # Monotonic timestamp of last successful flush_all.
        self._last_flush = time.monotonic()

    def ingest(self, event: TelemetryEvent) -> None:
        """Convert a TelemetryEvent to flat rows and buffer them by modality.

        Dispatches on ``event.modality`` to the appropriate ``_ingest_*`` helper.
        Unknown modalities are silently ignored.
        """
        # State → long-format signal rows.
        if event.modality == Modality.STATE:
            self._ingest_state(event)
        # Action → long-format target rows.
        elif event.modality == Modality.ACTION:
            self._ingest_action(event)
        # Vision → one row per BlobRef.
        elif event.modality == Modality.VISION:
            self._ingest_vision(event)
        # Event → single discrete log row.
        elif event.modality == Modality.EVENT:
            self._ingest_event(event)

    def should_flush(self) -> bool:
        """Return True when buffered rows or elapsed time exceed thresholds."""
        # Total rows across all modality buffers.
        total = sum(len(b) for b in self._buffers.values())
        # Seconds since last flush_all.
        elapsed = time.monotonic() - self._last_flush
        # Either condition alone is enough to flush.
        return total >= FLUSH_ROW_THRESHOLD or elapsed >= FLUSH_TIME_SECS

    def flush_all(self) -> list[Path]:
        """Write all buffered rows to Parquet files and clear buffers.

        Returns the list of partition directories that had rows with done=true
        so callers can mark episode_complete in manifests.
        """
        # Collect parent dirs of files that included a done flag.
        done_partitions: list[Path] = []
        # Flush each modality independently.
        for modality, rows in self._buffers.items():
            # Skip empty buffers.
            if not rows:
                continue
            # Remember if any row in this batch completed an episode.
            has_done = any(r.get("done") for r in rows)
            # Write partitioned parts; capture paths written.
            written = self._write_parquet(modality, rows)
            # Map files back to their partition directories when done seen.
            if has_done:
                done_partitions.extend(p.parent for p in written)
            # Clear the buffer for this modality.
            rows.clear()
        # Reset the flush timer.
        self._last_flush = time.monotonic()
        return done_partitions

    def _envelope_dict(self, event: TelemetryEvent) -> dict:
        """Extract common envelope columns carried through to every Parquet row."""
        return {
            "timestamp_ns": event.event_time_ns,
            "agent_id": event.agent_id,
            "task_id": event.task_id,
            "step_index": event.step_index,
            "sequence_id": event.sequence_id,
            "source_id": event.source_id,
            # Store enum as string name for SQL-friendly Parquet.
            "completeness": Completeness.Name(event.completeness),
            "done": event.done,
            "sync_group": event.sync_group,
        }

    def _ingest_state(self, event: TelemetryEvent) -> None:
        """Expand state signals into long-format buffered rows."""
        # Shared envelope for every signal value from this event.
        base = self._envelope_dict(event)
        # Each Signal may carry multiple values with parallel labels.
        for sig in event.state.signals:
            n_vals = len(sig.values)
            # Default labels to the signal name repeated when labels absent.
            labels = list(sig.labels) if sig.labels else [sig.name] * n_vals
            for i, val in enumerate(sig.values):
                # Append one row per value index.
                self._buffers["state"].append({
                    **base,
                    "stream_name": event.stream_name,
                    "signal_name": labels[i] if i < len(labels) else sig.name,
                    "position": val,
                    # Historical: velocity mirrors values[i] when present.
                    "velocity": sig.values[i] if len(sig.values) > i else 0.0,
                    "effort": 0.0,
                    "unit": sig.unit,
                })

    def _ingest_action(self, event: TelemetryEvent) -> None:
        """Expand action signals into long-format buffered rows."""
        base = self._envelope_dict(event)
        # Enum name for action_type column.
        at = event.action.ActionType.Name(event.action.action_type)
        for sig in event.action.signals:
            n_vals = len(sig.values)
            labels = list(sig.labels) if sig.labels else [sig.name] * n_vals
            for i, val in enumerate(sig.values):
                self._buffers["action"].append({
                    **base,
                    "stream_name": event.stream_name,
                    "action_type": at,
                    "signal_name": labels[i] if i < len(labels) else sig.name,
                    "target_position": val,
                    "target_velocity": 0.0,
                    "unit": sig.unit,
                })

    def _ingest_vision(self, event: TelemetryEvent) -> None:
        """Buffer one vision row per BlobRef on the event."""
        base = self._envelope_dict(event)
        for blob in event.vision.blobs:
            self._buffers["vision"].append({
                **base,
                "camera_name": event.vision.camera_name,
                "uri": blob.uri,
                "frame_index": blob.frame_index,
                "width": blob.width,
                "height": blob.height,
                "encoding": blob.encoding,
                "compression": blob.compression,
            })

    def _ingest_event(self, event: TelemetryEvent) -> None:
        """Buffer a single discrete event-log row."""
        # Local import keeps Severity out of module import cycle concerns.
        from packages.proto.telemetry_pb2 import Severity
        base = self._envelope_dict(event)
        sev = Severity.Name(event.event.severity)
        self._buffers["event"].append({
            **base,
            "event_type": event.event.event_type,
            "severity": sev,
            "message": event.event.message,
        })

    def _write_parquet(self, modality: str, rows: list[dict]) -> list[Path]:
        """Write rows to partitioned Parquet files. Returns paths written.

        Builds one Arrow table then filters per (agent_id, task_id) partition
        for the UTC date. Empty row lists return immediately.
        """
        # Nothing to write.
        if not rows:
            return []

        # Schema for this modality.
        schema = self._schemas[modality]
        # Materialize all rows as a single table before partitioning.
        table = pa.Table.from_pylist(rows, schema=schema)

        # Distinct partition keys present in this flush.
        agent_ids = set(r["agent_id"] for r in rows)
        task_ids = set(r["task_id"] for r in rows)
        # Hive-style date partition in UTC.
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        written: list[Path] = []

        # Cartesian product of agent/task keys seen in the batch.
        for rid in agent_ids:
            for tid in task_ids:
                # Build Hive-style directory path.
                partition_dir = (
                    self._root / modality
                    / f"agent_id={rid}"
                    / f"task_id={tid}"
                    / f"date={date_str}"
                )
                # Ensure directory exists.
                partition_dir.mkdir(parents=True, exist_ok=True)

                # Unique part filename to avoid collisions across writers.
                filename = f"part-{int(time.time() * 1000)}_{uuid.uuid4().hex[:6]}.parquet"
                path = partition_dir / filename

                # Boolean mask selecting this partition's rows.
                mask = pa.array([
                    r["agent_id"] == rid and r["task_id"] == tid
                    for r in rows
                ])
                subset = table.filter(mask)

                # Snappy-compressed Parquet for a balance of size and speed.
                pq.write_table(
                    subset,
                    str(path),
                    compression="snappy",
                )
                written.append(path)
                logger.info(
                    "Wrote %d rows to %s",
                    subset.num_rows,
                    path,
                )

        return written
