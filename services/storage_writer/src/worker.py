"""
Storage writer worker.

Connects to NATS JetStream as a durable pull consumer in queue group
``storage-writers``, fetches telemetry events, deserializes protobuf,
acks, and—when ``tags["persist"] == "true"``—feeds ``ParquetSink``. Flushes
on row/time thresholds and on shutdown, writing manifests for partitions
that saw ``done=true`` rows.
"""

# CancelledError handling on shutdown.
import asyncio
# Operator-visible progress and errors.
import logging

# Protobuf event type published by telemetry.
from packages.proto.telemetry_pb2 import TelemetryEvent
# MessageBus protocol (JetStream implementation at runtime).
from packages.message_bus import MessageBus
# Where Parquet files land on disk.
from packages.config import PARQUET_STORAGE_ROOT

# Sidecar writer for each flushed partition.
from .manifest import write_manifest
# Buffering + partitioned Parquet writer.
from .parquet_sink import ParquetSink

# Module logger.
logger = logging.getLogger(__name__)

# Historical batch hint (pull currently uses next_msg one-at-a-time).
BATCH_SIZE = 100
# Seconds to wait for the next message before considering a timed flush.
FETCH_TIMEOUT = 1.0


async def run_storage_writer(bus: MessageBus) -> None:
    """
    Main loop: pull messages from the bus, deserialize, write to Parquet.

    Subscribes to ``telemetry.>`` with durable name and queue group
    ``storage-writers`` and ``deliver_policy=all``. Runs until cancelled;
    on cancel flushes remaining buffers and unsubscribes. Messages without
    ``persist=true`` are acked and skipped so ephemeral streams do not fill
    disk.
    """
    # Sink buffers rows until flush thresholds.
    sink = ParquetSink(root=PARQUET_STORAGE_ROOT)

    # Durable pull subscription shared across scaled writer replicas.
    sub = await bus.subscribe(
        subject="telemetry.>",
        consumer_name="storage-writers",
        deliver_policy="all",
        queue_group="storage-writers",
    )

    # Startup breadcrumb for Compose logs.
    logger.info(
        "Storage writer started — consuming telemetry.> as 'storage-writers', "
        "writing Parquet to %s",
        PARQUET_STORAGE_ROOT,
    )

    def _flush_and_update_manifests() -> None:
        """Flush all modality buffers and refresh manifests for done partitions."""
        # Write Parquet parts; collect dirs that contained done=true rows.
        done_partitions = sink.flush_all()
        # Mark those partitions' manifests as episode_complete.
        for part_dir in done_partitions:
            write_manifest(part_dir, episode_complete=True)

    try:
        # Pull forever until CancelledError.
        while True:
            # Wait up to FETCH_TIMEOUT for the next JetStream message.
            msg = await sub.next_msg(timeout=FETCH_TIMEOUT)
            # Timeout with no message: maybe still flush on time threshold.
            if msg is None:
                if sink.should_flush():
                    _flush_and_update_manifests()
                continue

            try:
                # Deserialize protobuf bytes from the message payload.
                event = TelemetryEvent()
                event.ParseFromString(msg.data)
                # Ack promptly so redelivery does not pile up on slow disk.
                await sub.ack(msg)

                # Only durable-tagged events become Parquet rows.
                if event.tags.get("persist") != "true":
                    continue

                # Expand modality payload into buffered flat rows.
                sink.ingest(event)
            except Exception:
                # Log and continue; message was already acked above on success path.
                # On parse failure before ack, JetStream may redeliver.
                logger.exception("Failed to process message seq=%s", msg.sequence)

            # Flush when row count or elapsed time says so.
            if sink.should_flush():
                _flush_and_update_manifests()

    except asyncio.CancelledError:
        # Graceful shutdown from main._run signal handling.
        logger.info("Storage writer shutting down, flushing remaining rows...")
        # Do not lose buffered rows on stop.
        _flush_and_update_manifests()
        # Drop the consumer subscription cleanly.
        await sub.unsubscribe()
