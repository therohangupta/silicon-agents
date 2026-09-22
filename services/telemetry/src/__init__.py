"""Telemetry service implementation package (``services.telemetry.src``).

Contains the FastAPI application factory and lifespan wiring, the in-memory
heartbeat store used by the gateway health API, HTTP routers for heartbeat
ingest / health / telemetry batch / blob upload, the TelemetryIngestion gRPC
server, shared validation and event-id deduplication, and publishers that
notify the gateway when effective reachability changes.

Nothing is re-exported at this package level on purpose: callers either import
``app`` from ``main`` for uvicorn or invoke ``__main__.main`` for the CLI
entrypoint. Keeping the package ``__init__`` empty of side effects avoids
importing FastAPI, NATS, and gRPC stacks merely because another module
touched ``services.telemetry.src``.
"""
