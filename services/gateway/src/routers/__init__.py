"""
FastAPI router package for the Agent Fleet Dashboard gateway.

Each submodule owns a domain of HTTP endpoints. ``api_router`` aggregates the
REST surface under the ``/api`` prefix and is included by ``app.create_app``.

Domain routers (mounted on ``api_router``):

- ``telemetry`` — agent heartbeat ingest (in-memory last-seen).
- ``agents`` — registration, health, YAML refresh, allocations.
- ``goals`` / ``plans`` / ``tasks`` — CRUD and plan lifecycle.
- ``agent_templates`` — agent type catalog from YAML scan.
- ``methods`` / ``strategies`` — planner/allocator metadata for the UI.
- ``metrics`` — stored MetricEvent query API.

Not mounted on ``api_router`` (included separately in ``app.py``):

- ``websocket`` — ``/ws/*`` and ``POST /internal/events``.
- ``agent_telemetry`` — per-agent telemetry WS, latest REST, blob proxy.
- ``prompts`` — legacy/alternate methods-by-name router (not currently included
  on ``api_router``; kept for reference/compatibility).

Importing this package constructs ``api_router`` and attaches child routers;
it does not start the ASGI server.
"""

from fastapi import APIRouter

# Import domain router modules so their APIRouter instances exist.
from . import agents, goals, plans, tasks, agent_templates, methods, strategies, telemetry, metrics, agent_telemetry

# Combined router: all children are reachable under /api/...
api_router = APIRouter(prefix="/api")

# Include all domain routers (order affects OpenAPI grouping only).
api_router.include_router(telemetry.router)
api_router.include_router(agents.router, tags=["Agents"])
api_router.include_router(goals.router, tags=["Goals"])
api_router.include_router(plans.router, tags=["Plans"])
api_router.include_router(tasks.router, tags=["Tasks"])
api_router.include_router(agent_templates.router, tags=["Agent templates"])
api_router.include_router(methods.router, tags=["Methods"])
api_router.include_router(strategies.router, tags=["Strategies"])
api_router.include_router(metrics.router)

# Public export for app.create_app and star-imports.
__all__ = ["api_router"]
