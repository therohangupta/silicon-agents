"""
Agent Fleet Gateway application package (`src`).

This package is the FastAPI-based HTTP and WebSocket edge for the Agent Fleet
dashboard. Callers (browser UI, operators, and other services) talk REST and
WebSockets here; the gateway translates those requests into fleet-manager gRPC
calls, database reads via the instance registry, Telemetry HTTP proxies, and
NATS JetStream telemetry fan-out.

Modules of note:

- ``main`` — uvicorn entry that re-exports the FastAPI ``app`` instance.
- ``app`` — application factory, CORS, request metrics middleware, lifespan
  (gRPC bridge + NATS telemetry consumer).
- ``config`` — re-exports shared ``packages.config`` settings for local imports.
- ``dependencies`` — singleton ``GRPCBridge`` for FastAPI ``Depends()``.
- ``grpc_bridge`` — protobuf ↔ JSON dict adapters and fleet RPC wrappers.
- ``routers`` — domain REST routes under ``/api`` plus WebSocket endpoints.
- ``services`` — health checks, YAML embodiment scanner, port helpers, telemetry client.
- ``consumers`` — durable NATS consumer that caches and fans telemetry events.
- ``models`` — Pydantic request/response schemas for OpenAPI and validation.

Behavior is intentionally thin at the edge: mutation authority remains with the
fleet server; this package adapts transport and presentation only.
"""
