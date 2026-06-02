"""
Robot Fleet Dashboard - FastAPI Application Factory

This module creates and configures the FastAPI application.
All routes are organized into routers in the routers/ directory.
"""

import asyncio
import logging
import time

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from .config import CORS_ORIGINS, NATS_URL
from .dependencies import init_bridge, close_bridge, get_bridge
from .routers import api_router
from .routers import websocket as websocket_mod
from .routers import live_video as live_video_mod
from .routers import robot_telemetry as robot_telemetry_mod
from .routers.websocket import event_bus
from .routers.embodiments import ports_router
from .services import close_telemetry_client
from .consumers.telemetry_consumer import run_telemetry_consumer
from packages.message_bus.nats_jetstream import NatsJetStreamBus

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


class RequestMetricsMiddleware(BaseHTTPMiddleware):
    """Records method, path, status code, and duration for every HTTP request."""

    async def dispatch(self, request: Request, call_next):
        start = time.monotonic()
        response = await call_next(request)
        duration_ms = int((time.monotonic() - start) * 1000)

        try:
            bridge = get_bridge()
            import asyncio
            asyncio.get_running_loop().create_task(
                bridge.registry.record_metric(
                    service="gateway",
                    event_type="api_request",
                    entity_id=f"{request.method} {request.url.path}",
                    duration_ms=duration_ms,
                    success=response.status_code < 400,
                    metadata={"status_code": response.status_code},
                )
            )
        except Exception:
            pass  # Metrics recording must never break requests

        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle.
    
    Initializes the gRPC bridge and NATS telemetry consumer on startup.
    """
    init_bridge()

    # Start NATS telemetry consumer (best-effort; gateway works without it)
    bus = NatsJetStreamBus(url=NATS_URL)
    consumer_task = None
    try:
        await bus.connect()
        await bus.ensure_stream("TELEMETRY", ["telemetry.>"])
        consumer_task = asyncio.create_task(run_telemetry_consumer(bus))
        logger.info("Gateway NATS telemetry consumer started")
    except Exception:
        logger.warning(
            "NATS JetStream unavailable at %s — telemetry WS will not work",
            NATS_URL,
            exc_info=True,
        )
    app.state.message_bus = bus

    yield

    event_bus.notify(["__shutdown__"])
    if consumer_task is not None:
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass
    await bus.close()
    close_bridge()
    await close_telemetry_client()


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        Configured FastAPI application instance
    """
    app = FastAPI(
        title="Robot Fleet Dashboard API",
        description="""
REST API for managing robot fleets, goals, plans, and execution.

## Features

- **Robots**: Register, monitor, and manage robot instances
- **Goals**: Define high-level objectives for the fleet
- **Plans**: Generate task DAGs using LLM planners
- **Execution**: Monitor real-time plan execution via WebSocket
- **World State**: Manage environmental facts for planning context
        """,
        version="1.0.0",
        lifespan=lifespan
    )
    
    # CORS middleware for frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(RequestMetricsMiddleware)
    
    # Include all API routers
    app.include_router(api_router)
    
    # Include ports router at /api/ports for backwards compatibility
    app.include_router(ports_router, prefix="/api", tags=["Ports"])
    
    # WebSocket + internal event endpoints (no /api prefix)
    app.include_router(websocket_mod.router)
    app.include_router(robot_telemetry_mod.router)
    app.include_router(live_video_mod.router)
    
    # Health check endpoint (root level)
    @app.get("/health", tags=["Health"])
    async def health_check():
        """Health check endpoint for load balancers and monitoring."""
        return {"status": "healthy", "service": "robot-fleet-dashboard"}
    
    return app


# Create the application instance
app = create_app()
