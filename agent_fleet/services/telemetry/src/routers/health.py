"""
Health read API for the Telemetry service.

Gateway (and other consumers) query these endpoints to get agent health
derived from heartbeats stored in ``HeartbeatStore``. Summaries include
``last_seen``, effective ``reachable``, and ``busy``. Unknown agent ids
return HTTP 404.
"""

# FastAPI router and HTTPException for 404 responses.
from fastapi import APIRouter, HTTPException

# Singleton store shared with ingest and the timeout scanner.
from ..heartbeat_store import get_heartbeat_store

# All routes under /health with OpenAPI tag "Health".
router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/summary")
async def get_health_summary():
    """
    Get health summary for all known agents.

    Returns a dict keyed by agent_id (and also by ``host:port`` when the store
    indexed them) with last_seen, reachable, and busy. Empty dict when no
    heartbeats have been recorded yet.
    """
    # Resolve the process-wide store.
    store = get_heartbeat_store()
    # Delegate map construction (includes host:port aliases).
    return store.get_all_health()


@router.get("/{agent_id}")
async def get_agent_health(agent_id: str):
    """
    Get health summary for a single agent.

    Returns 404 if the agent is unknown (has never sent a heartbeat). Path
    parameter ``agent_id`` is typically the ``host:port`` key used at ingest.
    """
    # Resolve the process-wide store.
    store = get_heartbeat_store()
    # Lookup may return None for never-seen ids.
    health = store.get_health(agent_id)
    # Translate miss into HTTP 404 for the gateway.
    if health is None:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found in telemetry store")
    # Return the summary dict as JSON.
    return health
