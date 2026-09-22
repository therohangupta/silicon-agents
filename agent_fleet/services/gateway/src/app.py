"""
Agent Fleet Dashboard — FastAPI application factory and lifespan.

This module builds the ASGI ``FastAPI`` instance used by uvicorn. It wires:

1. **Lifespan** — initialize the gRPC bridge to the fleet server; best-effort
   connect a NATS JetStream consumer for telemetry fan-out; on shutdown,
   signal WebSocket clients, cancel the consumer, close bus/bridge/telemetry.
2. **CORS** — allow browser origins from ``CORS_ORIGINS`` so the dashboard-web
   SPA can call `/api` and upgrade WebSockets.
3. **Request metrics middleware** — asynchronously record each HTTP request's
   method, path, status, and duration via the bridge registry (never fails the
   request if metrics recording errors).
4. **Routers** — combined `/api` router plus ports compatibility router,
   WebSocket/event router, and agent-telemetry WebSocket/REST routes.
5. **Health** — root ``GET /health`` for probes.

The module-level ``app = create_app()`` is what ``main.py`` re-exports. Import
side effects include configuring the root logger and constructing middleware
stacks. NATS unavailability only logs a warning; REST/gRPC still work, but
telemetry WebSockets will not receive bus events until NATS is available.
"""

import asyncio
import logging
import time

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

# CORS allow-list and NATS URL from shared config re-exports.
from .config import CORS_ORIGINS, NATS_URL
# Bridge lifecycle used by lifespan and by metrics middleware (get_bridge).
from .dependencies import init_bridge, close_bridge, get_bridge
# Aggregated REST API under /api.
from .routers import api_router
# WebSocket + internal event POST endpoints (no /api prefix on WS paths).
from .routers import websocket as websocket_mod
# Per-agent telemetry WS and blob proxy routes.
from .routers import agent_telemetry as agent_telemetry_mod
# In-process pub-sub used to wake WS clients on fleet mutations / shutdown.
from .routers.websocket import event_bus
# Back-compat /api/ports/* router defined alongside embodiments.
from .routers.embodiments import ports_router
# Shared httpx client used when proxying Telemetry health.
from .services import close_telemetry_client
# Durable NATS consumer loop for telemetry.> fan-out to WS subscribers.
from .consumers.telemetry_consumer import run_telemetry_consumer
# JetStream bus implementation used to connect and ensure TELEMETRY stream.
from packages.message_bus.nats_jetstream import NatsJetStreamBus

# Configure process-wide logging early so lifespan and middleware messages appear.
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
# Module logger for startup/shutdown diagnostics.
logger = logging.getLogger(__name__)


class RequestMetricsMiddleware(BaseHTTPMiddleware):
    """
    ASGI middleware that records one metric event per completed HTTP request.

    Purpose:
        Emit observability rows (service=gateway, event_type=api_request) with
        method+path as entity_id, duration_ms, success flag, and status_code
        metadata so operators can chart gateway latency and error rates.

    Side effects:
        Schedules an async ``record_metric`` task on the running event loop.
        Swallow all exceptions so metrics never break client requests.

    Failure behavior:
        If the bridge is unavailable or recording fails, the exception is
        ignored and the original response is still returned unchanged.
    """

    async def dispatch(self, request: Request, call_next):
        """
        Time the downstream handler and fire-and-forget a metric write.

        Args:
            request: Incoming Starlette/FastAPI request.
            call_next: Next middleware or route callable.

        Returns:
            The ``Response`` produced by the rest of the stack.

        Side effects:
            May create a background task calling ``bridge.registry.record_metric``.

        Failure behavior:
            Metrics failures are swallowed; HTTP response path is unaffected.
            Handler exceptions propagate normally from ``call_next``.
        """
        # Monotonic clock avoids wall-clock jumps skewing duration.
        start = time.monotonic()
        # Run the remainder of the middleware/route chain.
        response = await call_next(request)
        # Convert elapsed seconds to integer milliseconds for storage.
        duration_ms = int((time.monotonic() - start) * 1000)

        try:
            # Resolve the singleton bridge created in lifespan.
            bridge = get_bridge()
            # Local import keeps the middleware importable even if asyncio was
            # already imported at module level; matches original behavior.
            import asyncio
            # Schedule metric persistence without awaiting (do not slow the response).
            asyncio.get_running_loop().create_task(
                bridge.registry.record_metric(
                    service="gateway",
                    event_type="api_request",
                    # Encode verb + path as the metric entity for grouping in UI.
                    entity_id=f"{request.method} {request.url.path}",
                    duration_ms=duration_ms,
                    # Treat 4xx/5xx as unsuccessful for success-rate charts.
                    success=response.status_code < 400,
                    metadata={"status_code": response.status_code},
                )
            )
        except Exception:
            # Metrics must never fail the user-facing request.
            pass

        # Always return the downstream response object.
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage gateway startup and shutdown resources around request serving.

    Purpose:
        Initialize gRPC bridge before traffic; start NATS telemetry consumer
        when JetStream is reachable; tear down orderly on process exit.

    Args:
        app: FastAPI application instance receiving lifespan context. The
            connected ``NatsJetStreamBus`` is stored on ``app.state.message_bus``.

    Yields:
        Control to FastAPI while the app is serving; code after ``yield`` runs
        on shutdown.

    Side effects:
        Calls ``init_bridge()``; may ``connect``/``ensure_stream`` on NATS;
        creates ``run_telemetry_consumer`` task; on exit notifies ``event_bus``,
        cancels consumer, closes bus/bridge/telemetry client.

    Failure behavior:
        NATS failures are logged as warnings and the app still serves REST.
        Shutdown cancellation of the consumer expects ``CancelledError``.
    """
    # Open gRPC client + registry before accepting traffic that Depends(get_bridge).
    init_bridge()

    # Build JetStream bus pointed at configured NATS URL (best-effort below).
    bus = NatsJetStreamBus(url=NATS_URL)
    # Consumer task handle; remains None if connect/ensure_stream fails.
    consumer_task = None
    try:
        # Establish NATS connection for the TELEMETRY stream.
        await bus.connect()
        # Ensure stream exists with subject filter telemetry.> for agent events.
        await bus.ensure_stream("TELEMETRY", ["telemetry.>"])
        # Run the durable gateway-realtime consumer until cancelled.
        consumer_task = asyncio.create_task(run_telemetry_consumer(bus))
        logger.info("Gateway NATS telemetry consumer started")
    except Exception:
        # REST/gRPC path remains usable; telemetry WS simply won't get bus events.
        logger.warning(
            "NATS JetStream unavailable at %s — telemetry WS will not work",
            NATS_URL,
            exc_info=True,
        )
    # Expose bus on app.state for any code that needs the same connection.
    app.state.message_bus = bus

    # Hand control to FastAPI request loop until shutdown is requested.
    yield

    # Wake WS subscribers with a synthetic shutdown key so handlers exit cleanly.
    event_bus.notify(["__shutdown__"])
    # Cancel background consumer if it was started.
    if consumer_task is not None:
        consumer_task.cancel()
        try:
            # Await cancellation completion to avoid dangling tasks.
            await consumer_task
        except asyncio.CancelledError:
            # Expected when cancelling the consumer loop.
            pass
    # Close NATS connection (safe even if connect never succeeded, per bus impl).
    await bus.close()
    # Tear down gRPC singleton.
    close_bridge()
    # Close shared Telemetry httpx client if it was opened.
    await close_telemetry_client()


def create_app() -> FastAPI:
    """
    Construct and configure the FastAPI application instance.

    Purpose:
        Attach metadata, lifespan, CORS, metrics middleware, and all routers
        including the root health probe.

    Args:
        None.

    Returns:
        A ready-to-serve ``FastAPI`` application (not yet bound to a port).

    Side effects:
        Registers middleware and includes routers; defines nested ``health_check``.

    Failure behavior:
        Propagates import/router errors at construction time. Does not contact
        gRPC/NATS until lifespan runs.
    """
    # Create FastAPI with OpenAPI title/description and lifespan hook.
    app = FastAPI(
        title="Agent Fleet Dashboard API",
        description="""
REST API for managing agent fleets, goals, plans, and execution.

## Features

- **Agents**: Register, monitor, and manage agent instances
- **Goals**: Define high-level objectives for the fleet
- **Plans**: Generate task DAGs using LLM planners
- **Execution**: Monitor real-time plan execution via WebSocket
        """,
        version="1.0.0",
        lifespan=lifespan
    )
    
    # Allow dashboard-web (and other configured origins) to call the API with cookies.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Record per-request metrics after CORS so preflight still works normally.
    app.add_middleware(RequestMetricsMiddleware)
    
    # Mount all domain REST routers under /api (agents, goals, plans, ...).
    app.include_router(api_router)
    
    # Historical clients expect /api/ports/*; ports_router already has /ports prefix.
    app.include_router(ports_router, prefix="/api", tags=["Ports"])
    
    # Global-updates / execution WS and POST /internal/events (fleet → gateway).
    app.include_router(websocket_mod.router)
    # Per-agent telemetry WS, latest REST, and blob proxy.
    app.include_router(agent_telemetry_mod.router)
    
    # Nested health route registered on this app instance (not on api_router).
    @app.get("/health", tags=["Health"])
    async def health_check():
        """
        Liveness probe for load balancers and orchestration.

        Purpose:
            Confirm the ASGI process is up without checking gRPC/NATS deps.

        Args:
            None.

        Returns:
            JSON ``{"status": "healthy", "service": "agent-fleet-dashboard"}``.

        Side effects:
            None.

        Failure behavior:
            Always returns 200 if the process can serve this route.
        """
        return {"status": "healthy", "service": "agent-fleet-dashboard"}
    
    # Hand the configured app to the caller (and to module-level assignment).
    return app


# Eagerly create the singleton application imported by main.py / uvicorn.
app = create_app()
