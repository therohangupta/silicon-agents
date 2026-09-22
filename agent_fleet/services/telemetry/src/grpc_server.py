"""
gRPC server implementing the TelemetryIngestion service.

Runs on a separate port (``TELEMETRY_GRPC_PORT``) alongside the FastAPI HTTP
server. Validates incoming events, assigns ``ingest_time_ns``, deduplicates by
``event_id``, and publishes serialized protos to NATS subjects
``telemetry.{modality}.{agent_id}``. Exposes bidirectional ``StreamTelemetry``
and unary ``IngestBatch``.
"""

# asyncio available for future concurrent helpers (servicer is async via grpc.aio).
import asyncio  # noqa: F401  # retained for parity with historic imports
# Logging for connect/ingest diagnostics.
import logging
# time.time_ns stamps ingest_time_ns on accepted events.
import time

# Sync grpc symbols unused directly; aio server is what we start.
import grpc  # noqa: F401
from grpc import aio as grpc_aio

# Generated TelemetryIngestion stubs and message types.
from packages.proto import telemetry_pb2, telemetry_pb2_grpc
# MessageBus protocol implemented by NatsJetStreamBus.
from packages.message_bus import MessageBus

# Shared validation / sequence checks with HTTP ingest.
from .validation import validate_event, check_sequence
# Process-wide event_id LRU shared with HTTP path.
from .dedup import get_dedup_cache

# Module logger.
logger = logging.getLogger(__name__)

# Map protobuf Modality enum values to NATS subject path segments.
_MODALITY_SUBJECT = {
    telemetry_pb2.STATE: "state",
    telemetry_pb2.ACTION: "action",
    telemetry_pb2.VISION: "vision",
    telemetry_pb2.EVENT: "event",
}


class TelemetryIngestionServicer(telemetry_pb2_grpc.TelemetryIngestionServicer):
    """gRPC servicer that ingests telemetry events from agents.

    Holds a reference to the shared ``MessageBus``. Both RPCs dedupe, validate,
    optionally warn on sequence violations, stamp ingest time, publish, and
    return ``IngestAck`` summaries.
    """

    def __init__(self, bus: MessageBus):
        """Store the bus used for all publish calls.

        Args:
            bus: Connected (or best-effort) message bus from app lifespan.
        """
        # Keep bus on the instance for StreamTelemetry / IngestBatch.
        self._bus = bus

    async def StreamTelemetry(self, request_iterator, context):
        """Bidirectional streaming: receives events, yields acks one-for-one.

        For each inbound ``TelemetryEvent``: skip duplicates (ack ok, accepted
        0), reject invalid events (ack with error), warn on sequence issues,
        stamp ``ingest_time_ns``, publish to the modality subject, then yield
        an ``IngestAck``. Unexpected exceptions mark the ack as rejected.
        """
        # Peer address helps debug which agent connected.
        logger.info("gRPC StreamTelemetry: new client connected from %s", context.peer())
        # Shared LRU with HTTP ingest.
        dedup = get_dedup_cache()
        # Async iterate the client stream.
        async for event in request_iterator:
            # Trace each event at info for operator visibility.
            logger.info(
                "gRPC event received: agent=%s modality=%s stream=%s",
                event.agent_id,
                event.modality,
                event.stream_name,
            )
            # Fresh ack message for this event.
            ack = telemetry_pb2.IngestAck()
            try:
                # Duplicate event_id: treat as success with zero accepted.
                if dedup.is_duplicate(event.event_id):
                    ack.ok = True
                    ack.accepted = 0
                    yield ack
                    continue

                # Hard validation failure: reject with error text.
                err = validate_event(event)
                if err:
                    ack.ok = False
                    ack.error = err
                    ack.rejected = 1
                    ack.rejected_event_ids.append(event.event_id)
                    yield ack
                    continue

                # Soft sequence check: log but still publish.
                seq_err = check_sequence(event)
                if seq_err:
                    logger.warning("Sequence violation: %s", seq_err)

                # Server-side ingest timestamp in nanoseconds.
                event.ingest_time_ns = time.time_ns()

                # Resolve modality name for the subject; unknown -> "unknown".
                mod_name = _MODALITY_SUBJECT.get(event.modality, "unknown")
                # Subject pattern consumed by storage_writer.
                subject = f"telemetry.{mod_name}.{event.agent_id}"
                # Publish serialized protobuf bytes.
                await self._bus.publish(subject, event.SerializeToString())

                # Success ack for this single event.
                ack.ok = True
                ack.accepted = 1
            except Exception as e:
                # Catch-all so one bad event does not kill the stream.
                logger.exception("Error ingesting streamed event")
                ack.ok = False
                ack.error = str(e)
                ack.rejected = 1

            # Always yield an ack (success or failure path).
            yield ack

    async def IngestBatch(self, request, context):
        """Unary batch ingest of ``request.events``.

        Walks every event with the same dedupe/validate/sequence/publish
        pipeline as the stream RPC, aggregating accepted/rejected counts and
        rejected ids into one ``IngestAck``. Duplicate ids are skipped without
        counting as rejected.
        """
        # Shared dedup cache.
        dedup = get_dedup_cache()
        # Counters for the aggregate ack.
        accepted = 0
        rejected = 0
        last_error = ""
        rejected_ids: list[str] = []

        # Process each event in the batch independently.
        for event in request.events:
            try:
                # Duplicates: skip silently (not counted as rejected).
                if dedup.is_duplicate(event.event_id):
                    continue

                # Validation failure increments rejected.
                err = validate_event(event)
                if err:
                    rejected += 1
                    last_error = err
                    rejected_ids.append(event.event_id)
                    continue

                # Soft sequence warning.
                seq_err = check_sequence(event)
                if seq_err:
                    logger.warning("Sequence violation: %s", seq_err)

                # Stamp ingest time.
                event.ingest_time_ns = time.time_ns()

                # Publish to modality subject.
                mod_name = _MODALITY_SUBJECT.get(event.modality, "unknown")
                subject = f"telemetry.{mod_name}.{event.agent_id}"
                await self._bus.publish(subject, event.SerializeToString())
                accepted += 1
            except Exception as e:
                # Count unexpected failures as rejected.
                rejected += 1
                last_error = str(e)
                rejected_ids.append(event.event_id)

        # ok is true only when nothing was rejected.
        return telemetry_pb2.IngestAck(
            ok=rejected == 0,
            accepted=accepted,
            rejected=rejected,
            error=last_error,
            rejected_event_ids=rejected_ids,
        )


async def start_grpc_server(bus: MessageBus, port: int) -> grpc_aio.Server:
    """Create and start the gRPC server. Returns the server for later shutdown.

    Builds an aio server, registers ``TelemetryIngestionServicer``, binds
    insecure ``[::]:port`` (IPv6 any / IPv4-mapped), starts it, logs the port,
    and returns the server object so lifespan can ``stop(grace=...)``.
    """
    # Create an async gRPC server instance.
    server = grpc_aio.server()
    # Register our servicer implementation.
    telemetry_pb2_grpc.add_TelemetryIngestionServicer_to_server(
        TelemetryIngestionServicer(bus), server
    )
    # Listen on all interfaces at the configured port (no TLS in this build).
    server.add_insecure_port(f"[::]:{port}")
    # Begin accepting connections.
    await server.start()
    logger.info("Telemetry gRPC server listening on port %d", port)
    # Caller owns shutdown.
    return server
