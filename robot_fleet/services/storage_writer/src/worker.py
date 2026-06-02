"""
Storage writer worker.

Connects to NATS JetStream as a durable pull consumer in queue group
``storage-writers``, fetches telemetry events in batches, writes them
to Parquet via the ParquetSink, and acks processed messages.
"""

import asyncio
import logging

from packages.proto.telemetry_pb2 import TelemetryEvent
from packages.message_bus import MessageBus
from packages.config import PARQUET_STORAGE_ROOT

from .manifest import write_manifest
from .parquet_sink import ParquetSink

logger = logging.getLogger(__name__)

BATCH_SIZE = 100
FETCH_TIMEOUT = 1.0


async def run_storage_writer(bus: MessageBus) -> None:
    """
    Main loop: pull batches from the bus, deserialize, write to Parquet.
    Runs until cancelled.
    """
    sink = ParquetSink(root=PARQUET_STORAGE_ROOT)

    sub = await bus.subscribe(
        subject="telemetry.>",
        consumer_name="storage-writers",
        deliver_policy="all",
        queue_group="storage-writers",
    )

    logger.info(
        "Storage writer started — consuming telemetry.> as 'storage-writers', "
        "writing Parquet to %s",
        PARQUET_STORAGE_ROOT,
    )

    def _flush_and_update_manifests() -> None:
        done_partitions = sink.flush_all()
        for part_dir in done_partitions:
            write_manifest(part_dir, episode_complete=True)

    try:
        while True:
            msg = await sub.next_msg(timeout=FETCH_TIMEOUT)
            if msg is None:
                if sink.should_flush():
                    _flush_and_update_manifests()
                continue

            try:
                event = TelemetryEvent()
                event.ParseFromString(msg.data)
                await sub.ack(msg)

                if event.tags.get("persist") != "true":
                    continue

                sink.ingest(event)
            except Exception:
                logger.exception("Failed to process message seq=%s", msg.sequence)

            if sink.should_flush():
                _flush_and_update_manifests()

    except asyncio.CancelledError:
        logger.info("Storage writer shutting down, flushing remaining rows...")
        _flush_and_update_manifests()
        await sub.unsubscribe()
