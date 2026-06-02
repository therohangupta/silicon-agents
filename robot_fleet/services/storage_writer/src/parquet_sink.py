"""
Parquet sink that buffers telemetry events and writes partitioned Parquet files.

Each modality (state, action, vision, event) has its own long-format table schema.
Files are partitioned on disk as:
  {root}/{modality}/robot_id={X}/task_id={Y}/date={Z}/part-{ts}_{uuid}.parquet
"""

import logging
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import pyarrow as pa
import pyarrow.parquet as pq

from packages.proto.telemetry_pb2 import TelemetryEvent, Modality, Completeness

logger = logging.getLogger(__name__)

# Flush after this many buffered rows OR this many seconds, whichever comes first
FLUSH_ROW_THRESHOLD = 10_000
FLUSH_TIME_SECS = 60.0


# Common envelope columns carried through to every Parquet table so that
# downstream consumers (ML pipelines, replay tools) can join / sort / filter
# without needing to parse the proto again.
_ENVELOPE_COLS = [
    ("timestamp_ns", pa.int64()),
    ("robot_id", pa.string()),
    ("task_id", pa.string()),
    ("step_index", pa.uint64()),
    ("sequence_id", pa.uint64()),
    ("source_id", pa.string()),
    ("completeness", pa.string()),
    ("done", pa.bool_()),
    ("sync_group", pa.string()),
]

STATE_SCHEMA = pa.schema([
    *_ENVELOPE_COLS,
    ("stream_name", pa.string()),
    ("signal_name", pa.string()),
    ("position", pa.float64()),
    ("velocity", pa.float64()),
    ("effort", pa.float64()),
    ("unit", pa.string()),
])

ACTION_SCHEMA = pa.schema([
    *_ENVELOPE_COLS,
    ("stream_name", pa.string()),
    ("action_type", pa.string()),
    ("signal_name", pa.string()),
    ("target_position", pa.float64()),
    ("target_velocity", pa.float64()),
    ("unit", pa.string()),
])

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

EVENT_SCHEMA = pa.schema([
    *_ENVELOPE_COLS,
    ("event_type", pa.string()),
    ("severity", pa.string()),
    ("message", pa.string()),
])


class ParquetSink:
    """Buffers telemetry rows and periodically flushes to partitioned Parquet files."""

    def __init__(self, root: str):
        self._root = Path(root)
        self._buffers: dict[str, list[dict]] = {
            "state": [],
            "action": [],
            "vision": [],
            "event": [],
        }
        self._schemas = {
            "state": STATE_SCHEMA,
            "action": ACTION_SCHEMA,
            "vision": VISION_SCHEMA,
            "event": EVENT_SCHEMA,
        }
        self._last_flush = time.monotonic()

    def ingest(self, event: TelemetryEvent) -> None:
        """Convert a TelemetryEvent to flat rows and buffer them."""
        if event.modality == Modality.STATE:
            self._ingest_state(event)
        elif event.modality == Modality.ACTION:
            self._ingest_action(event)
        elif event.modality == Modality.VISION:
            self._ingest_vision(event)
        elif event.modality == Modality.EVENT:
            self._ingest_event(event)

    def should_flush(self) -> bool:
        total = sum(len(b) for b in self._buffers.values())
        elapsed = time.monotonic() - self._last_flush
        return total >= FLUSH_ROW_THRESHOLD or elapsed >= FLUSH_TIME_SECS

    def flush_all(self) -> list[Path]:
        """Write all buffered rows to Parquet files and clear buffers.

        Returns the list of partition directories that had rows with done=true.
        """
        done_partitions: list[Path] = []
        for modality, rows in self._buffers.items():
            if not rows:
                continue
            has_done = any(r.get("done") for r in rows)
            written = self._write_parquet(modality, rows)
            if has_done:
                done_partitions.extend(p.parent for p in written)
            rows.clear()
        self._last_flush = time.monotonic()
        return done_partitions

    def _envelope_dict(self, event: TelemetryEvent) -> dict:
        """Extract common envelope columns carried through to every Parquet row."""
        return {
            "timestamp_ns": event.event_time_ns,
            "robot_id": event.robot_id,
            "task_id": event.task_id,
            "step_index": event.step_index,
            "sequence_id": event.sequence_id,
            "source_id": event.source_id,
            "completeness": Completeness.Name(event.completeness),
            "done": event.done,
            "sync_group": event.sync_group,
        }

    def _ingest_state(self, event: TelemetryEvent) -> None:
        base = self._envelope_dict(event)
        for sig in event.state.signals:
            n_vals = len(sig.values)
            labels = list(sig.labels) if sig.labels else [sig.name] * n_vals
            for i, val in enumerate(sig.values):
                self._buffers["state"].append({
                    **base,
                    "stream_name": event.stream_name,
                    "signal_name": labels[i] if i < len(labels) else sig.name,
                    "position": val,
                    "velocity": sig.values[i] if len(sig.values) > i else 0.0,
                    "effort": 0.0,
                    "unit": sig.unit,
                })

    def _ingest_action(self, event: TelemetryEvent) -> None:
        base = self._envelope_dict(event)
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
        """Write rows to partitioned Parquet files. Returns paths written."""
        if not rows:
            return []

        schema = self._schemas[modality]
        table = pa.Table.from_pylist(rows, schema=schema)

        robot_ids = set(r["robot_id"] for r in rows)
        task_ids = set(r["task_id"] for r in rows)
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        written: list[Path] = []

        for rid in robot_ids:
            for tid in task_ids:
                partition_dir = (
                    self._root / modality
                    / f"robot_id={rid}"
                    / f"task_id={tid}"
                    / f"date={date_str}"
                )
                partition_dir.mkdir(parents=True, exist_ok=True)

                filename = f"part-{int(time.time() * 1000)}_{uuid.uuid4().hex[:6]}.parquet"
                path = partition_dir / filename

                mask = pa.array([
                    r["robot_id"] == rid and r["task_id"] == tid
                    for r in rows
                ])
                subset = table.filter(mask)

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
