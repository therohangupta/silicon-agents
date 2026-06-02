"""
gRPC server implementing the TelemetryIngestion service.

Runs on a separate port (TELEMETRY_GRPC_PORT) alongside the FastAPI HTTP server.
Validates incoming events, assigns ingest timestamps, deduplicates, and publishes
to the message bus.
"""

import asyncio
import logging
import time

import grpc
from grpc import aio as grpc_aio

from packages.proto import telemetry_pb2, telemetry_pb2_grpc
from packages.message_bus import MessageBus

from .validation import validate_event, check_sequence
from .dedup import get_dedup_cache

logger = logging.getLogger(__name__)

_MODALITY_SUBJECT = {
    telemetry_pb2.STATE: "state",
    telemetry_pb2.ACTION: "action",
    telemetry_pb2.VISION: "vision",
    telemetry_pb2.EVENT: "event",
}


class TelemetryIngestionServicer(telemetry_pb2_grpc.TelemetryIngestionServicer):
    """gRPC servicer that ingests telemetry events from robots."""

    def __init__(self, bus: MessageBus):
        self._bus = bus

    async def StreamTelemetry(self, request_iterator, context):
        """Bidirectional streaming: receives events, sends acks."""
        logger.info("gRPC StreamTelemetry: new client connected from %s", context.peer())
        dedup = get_dedup_cache()
        async for event in request_iterator:
            logger.info("gRPC event received: robot=%s modality=%s stream=%s", event.robot_id, event.modality, event.stream_name)
            ack = telemetry_pb2.IngestAck()
            try:
                if dedup.is_duplicate(event.event_id):
                    ack.ok = True
                    ack.accepted = 0
                    yield ack
                    continue

                err = validate_event(event)
                if err:
                    ack.ok = False
                    ack.error = err
                    ack.rejected = 1
                    ack.rejected_event_ids.append(event.event_id)
                    yield ack
                    continue

                seq_err = check_sequence(event)
                if seq_err:
                    logger.warning("Sequence violation: %s", seq_err)

                event.ingest_time_ns = time.time_ns()

                mod_name = _MODALITY_SUBJECT.get(event.modality, "unknown")
                subject = f"telemetry.{mod_name}.{event.robot_id}"
                await self._bus.publish(subject, event.SerializeToString())

                ack.ok = True
                ack.accepted = 1
            except Exception as e:
                logger.exception("Error ingesting streamed event")
                ack.ok = False
                ack.error = str(e)
                ack.rejected = 1

            yield ack

    async def IngestBatch(self, request, context):
        """Unary batch ingest."""
        dedup = get_dedup_cache()
        accepted = 0
        rejected = 0
        last_error = ""
        rejected_ids: list[str] = []

        for event in request.events:
            try:
                if dedup.is_duplicate(event.event_id):
                    continue

                err = validate_event(event)
                if err:
                    rejected += 1
                    last_error = err
                    rejected_ids.append(event.event_id)
                    continue

                seq_err = check_sequence(event)
                if seq_err:
                    logger.warning("Sequence violation: %s", seq_err)

                event.ingest_time_ns = time.time_ns()

                mod_name = _MODALITY_SUBJECT.get(event.modality, "unknown")
                subject = f"telemetry.{mod_name}.{event.robot_id}"
                await self._bus.publish(subject, event.SerializeToString())
                accepted += 1
            except Exception as e:
                rejected += 1
                last_error = str(e)
                rejected_ids.append(event.event_id)

        return telemetry_pb2.IngestAck(
            ok=rejected == 0,
            accepted=accepted,
            rejected=rejected,
            error=last_error,
            rejected_event_ids=rejected_ids,
        )


async def start_grpc_server(bus: MessageBus, port: int) -> grpc_aio.Server:
    """Create and start the gRPC server. Returns the server for later shutdown."""
    server = grpc_aio.server()
    telemetry_pb2_grpc.add_TelemetryIngestionServicer_to_server(
        TelemetryIngestionServicer(bus), server
    )
    server.add_insecure_port(f"[::]:{port}")
    await server.start()
    logger.info("Telemetry gRPC server listening on port %d", port)
    return server
