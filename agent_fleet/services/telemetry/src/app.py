"""
Telemetry service FastAPI application.

Wires CORS, HTTP routers, and a lifespan that starts:

- the gateway health-changed publisher and timeout scanner,
- a NATS JetStream bus with the TELEMETRY stream (best-effort; heartbeat-only
  mode continues if NATS is down),
- the TelemetryIngestion gRPC server on ``TELEMETRY_GRPC_PORT``.

HTTP surfaces: ``/ingest/heartbeat``, ``/health/*``, ``/telemetry/ingest``,
``/telemetry/blob``, and ``/healthz``. Import ``app`` from ``main`` for uvicorn.
"""

# asyncio for background scanner task and cancellation on shutdown.
import asyncio
# stdlib logging configured once at import for the service process.
import logging
# time.time stamps health_changed events from the scanner.
import time
# asynccontextmanager implements FastAPI lifespan startup/shutdown.
from contextlib import asynccontextmanager

# FastAPI application and CORS middleware.
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure root logging is configured before other modules log.
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")

# Config knobs used during lifespan.
from .config import (
    CORS_ORIGINS,
    HEARTBEAT_SCANNER_INTERVAL_SECS,
    NATS_URL,
    TELEMETRY_GRPC_PORT,
)
# Event model for timeout-driven publishes.
from .events import HealthChangedEvent
# Singleton heartbeat store used by the scanner.
from .heartbeat_store import get_heartbeat_store
# HTTP publisher toward the gateway.
from .publishing import GatewayHealthChangedPublisher
# HTTP route modules mounted below.
from .routers import ingest, health
from .routers import telemetry_ingest, blob_upload
# gRPC server starter (separate port from HTTP).
from .grpc_server import start_grpc_server

# JetStream bus implementation shared with storage_writer.
from packages.message_bus.nats_jetstream import NatsJetStreamBus

# Logger for lifespan and scanner messages.
logger = logging.getLogger(__name__)


async def _timeout_scanner(publisher: GatewayHealthChangedPublisher) -> None:
    """Periodically check for agents that stopped heartbeating and push events.

    Sleeps ``HEARTBEAT_SCANNER_INTERVAL_SECS``, calls
    ``HeartbeatStore.check_timeouts``, and when any agent ids timed out,
    publishes a ``HealthChangedEvent`` so the gateway/UI learn about
    unreachability without waiting for another heartbeat. Exceptions are
    logged; the loop continues until the task is cancelled on shutdown.
    """
    # Resolve the process-wide store once; it is a singleton.
    store = get_heartbeat_store()
    # Infinite loop until CancelledError from lifespan.
    while True:
        # Pace scans to avoid busy-waiting under the lock.
        await asyncio.sleep(HEARTBEAT_SCANNER_INTERVAL_SECS)
        try:
            # Returns ids that just flipped unreachable.
            timed_out = store.check_timeouts()
            if timed_out:
                # Info log helps operators correlate UI flaps with timeouts.
                logger.info("Timeout detected for %s", timed_out)
                # Notify gateway with current wall-clock ts.
                await publisher.publish(
                    HealthChangedEvent(agent_ids=timed_out, ts=time.time())
                )
        except Exception:
            # Never kill the scanner on a single bad iteration.
            logger.exception("Error in timeout scanner")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: start publisher, NATS, gRPC; tear them down on exit.

    Startup order: health publisher + scanner task, then message bus connect /
    ensure TELEMETRY stream, then gRPC server. Yields to serve requests.
    Shutdown cancels the scanner, stops gRPC with grace, closes the bus and
    publisher. NATS/gRPC failures are warnings so heartbeat-only mode works.
    """
    # --- Health-changed publisher (existing) ---
    # Concrete HTTP publisher implementing the HealthChangedPublisher protocol.
    publisher = GatewayHealthChangedPublisher()
    # Stash on app.state for Depends(get_publisher).
    app.state.health_changed_publisher = publisher
    # Background task for timeout-driven health_changed events.
    scanner = asyncio.create_task(_timeout_scanner(publisher))

    # --- Message bus (NATS JetStream) ---
    # Construct bus with configured URL (may be unreachable in heartbeats-only).
    bus = NatsJetStreamBus(url=NATS_URL)
    try:
        # Open NATS connection.
        await bus.connect()
        # Ensure stream captures all telemetry.> subjects for storage_writer.
        await bus.ensure_stream("TELEMETRY", ["telemetry.>"])
        logger.info("NATS JetStream connected and TELEMETRY stream ensured")
    except Exception:
        # Soft-fail: HTTP telemetry ingest will error, heartbeats still work.
        logger.warning(
            "NATS JetStream unavailable at %s — telemetry ingest will fail. "
            "Heartbeat-only mode still works.",
            NATS_URL,
            exc_info=True,
        )
    # Always attach bus (even if connect failed) so routes can see the object.
    app.state.message_bus = bus

    # --- gRPC server ---
    grpc_server = None
    try:
        # Start TelemetryIngestion on TELEMETRY_GRPC_PORT.
        grpc_server = await start_grpc_server(bus, TELEMETRY_GRPC_PORT)
    except Exception:
        # Soft-fail: HTTP path remains available.
        logger.warning("Failed to start telemetry gRPC server", exc_info=True)

    # Hand control to FastAPI request serving.
    yield

    # --- Shutdown ---
    # Signal the scanner loop to stop.
    scanner.cancel()
    try:
        # Await cancellation so we do not leak the task.
        await scanner
    except asyncio.CancelledError:
        # Expected when cancelling; swallow.
        pass
    # Stop gRPC if it started.
    if grpc_server is not None:
        await grpc_server.stop(grace=5)
    # Close NATS connection.
    await bus.close()
    # Close httpx client inside the publisher.
    await publisher.close()


# Construct the FastAPI application with metadata and lifespan hook.
app = FastAPI(
    title="Telemetry Service",
    description="Heartbeat ingest, telemetry ingest, and health API for the agent fleet",
    version="0.2.0",
    lifespan=lifespan,
)

# Allow browser dashboard origins from shared config.
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount heartbeat ingest routes under /ingest.
app.include_router(ingest.router)
# Mount health read API under /health.
app.include_router(health.router)
# Mount HTTP batch telemetry ingest under /telemetry.
app.include_router(telemetry_ingest.router)
# Mount blob upload under /telemetry/blob.
app.include_router(blob_upload.router)


@app.get("/healthz", tags=["Meta"])
async def healthz():
    """Liveness probe for orchestrators.

    Returns a tiny JSON ``{"status": "ok"}`` without touching NATS or the
    heartbeat store so kube/compose healthchecks stay cheap and reliable.
    """
    return {"status": "ok"}
