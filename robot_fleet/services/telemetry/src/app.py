"""
Telemetry service FastAPI application.

Provides:
- /ingest/heartbeat — robots POST here (latest-wins coalescing, pluggable fan-out)
- /health/summary, /health/{robot_id} — gateway queries here
- /telemetry/ingest — HTTP batch telemetry ingest
- /telemetry/blob — blob upload (vision frames)
- gRPC TelemetryIngestion.StreamTelemetry — streaming ingest (separate port)
- /healthz — liveness probe
"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")

from .config import (
    CORS_ORIGINS,
    HEARTBEAT_SCANNER_INTERVAL_SECS,
    NATS_URL,
    TELEMETRY_GRPC_PORT,
)
from .events import HealthChangedEvent
from .heartbeat_store import get_heartbeat_store
from .publishing import GatewayHealthChangedPublisher
from .routers import ingest, health
from .routers import telemetry_ingest, blob_upload
from .grpc_server import start_grpc_server

from packages.message_bus.nats_jetstream import NatsJetStreamBus

logger = logging.getLogger(__name__)


async def _timeout_scanner(publisher: GatewayHealthChangedPublisher) -> None:
    """Periodically check for robots that stopped heartbeating and push events."""
    store = get_heartbeat_store()
    while True:
        await asyncio.sleep(HEARTBEAT_SCANNER_INTERVAL_SECS)
        try:
            timed_out = store.check_timeouts()
            if timed_out:
                logger.info("Timeout detected for %s", timed_out)
                await publisher.publish(
                    HealthChangedEvent(robot_ids=timed_out, ts=time.time())
                )
        except Exception:
            logger.exception("Error in timeout scanner")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Health-changed publisher (existing) ---
    publisher = GatewayHealthChangedPublisher()
    app.state.health_changed_publisher = publisher
    scanner = asyncio.create_task(_timeout_scanner(publisher))

    # --- Message bus (NATS JetStream) ---
    bus = NatsJetStreamBus(url=NATS_URL)
    try:
        await bus.connect()
        await bus.ensure_stream("TELEMETRY", ["telemetry.>"])
        logger.info("NATS JetStream connected and TELEMETRY stream ensured")
    except Exception:
        logger.warning(
            "NATS JetStream unavailable at %s — telemetry ingest will fail. "
            "Heartbeat-only mode still works.",
            NATS_URL,
            exc_info=True,
        )
    app.state.message_bus = bus

    # --- gRPC server ---
    grpc_server = None
    try:
        grpc_server = await start_grpc_server(bus, TELEMETRY_GRPC_PORT)
    except Exception:
        logger.warning("Failed to start telemetry gRPC server", exc_info=True)

    yield

    # --- Shutdown ---
    scanner.cancel()
    try:
        await scanner
    except asyncio.CancelledError:
        pass
    if grpc_server is not None:
        await grpc_server.stop(grace=5)
    await bus.close()
    await publisher.close()


app = FastAPI(
    title="Telemetry Service",
    description="Heartbeat ingest, telemetry ingest, and health API for the robot fleet",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest.router)
app.include_router(health.router)
app.include_router(telemetry_ingest.router)
app.include_router(blob_upload.router)


@app.get("/healthz", tags=["Meta"])
async def healthz():
    """Liveness probe for orchestrators."""
    return {"status": "ok"}
