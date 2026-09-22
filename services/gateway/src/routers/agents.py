"""
Agent management REST endpoints (``/api/agents``).

Handles agent registration from YAML embodiments, unregistration, health checks
(Telemetry heartbeats by default, or direct HTTP probes), YAML detail/refresh,
and allocation summary queries against the instance registry database.

All mutating operations go through ``GRPCBridge`` to the fleet manager except
allocation aggregates, which query SQLAlchemy models via ``bridge.registry``.

HTTP status summary:

- List/get → **200** / **404**
- Register/unregister/refresh → **200** or **400** (missing config, port in use,
  RPC failure); **422** on bad bodies
- Health endpoints → **200** with reachable flags (**404** if agent unknown)
- Allocations → **200** (empty counts on error, logged)
"""

import os
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from ..config import REPO_ROOT, DEFAULT_AGENT_HOST, DEFAULT_AGENT_BASE_PORT
from ..dependencies import get_bridge, GRPCBridge
from ..services import (
    check_agent_health,
    check_all_agents_health,
    get_telemetry_health_summary,
    get_telemetry_agent_health,
    get_used_ports,
    is_localhost,
    find_yaml_for_agent,
)
from ..models.requests import AgentInstanceCreate
from ..models.responses import AgentResponse

import logging

logger = logging.getLogger(__name__)

# Full paths under /api/agents after api_router mount.
router = APIRouter(prefix="/agents")


# =============================================================================
# Request Models (local to this router)
# =============================================================================

class RefreshRequest(BaseModel):
    """
    Optional body for YAML refresh endpoints.

    Purpose:
        Allow callers to override which config file is used when re-registering.

    Fields:
        config_path: Optional absolute or repo-relative YAML path.

    Side effects:
        None at validation.

    Failure behavior:
        Extra fields ignored per Pydantic defaults; empty body is valid.
    """
    config_path: Optional[str] = None


# =============================================================================
# List and Get Agents
# =============================================================================

@router.get("", response_model=List[AgentResponse])
async def list_agents(
    filter: str = "all",
    bridge: GRPCBridge = Depends(get_bridge)
):
    """
    List all registered agents with an optional fleet filter.

    Args:
        filter: ``all``, ``deployed``, or ``registered`` (passed to gRPC).
        bridge: Injected fleet bridge.

    Returns:
        List of agent dicts.

    Side effects:
        ListAgents RPC.

    Failure behavior:
        **200** on success; client errors may become **500**.
    """
    return bridge.list_agents(filter)


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    bridge: GRPCBridge = Depends(get_bridge)
):
    """
    Get a specific agent by id (via list scan in the bridge).

    Args:
        agent_id: Path parameter agent instance id.
        bridge: Injected fleet bridge.

    Returns:
        Agent payload.

    Side effects:
        Bridge list/search RPCs.

    Failure behavior:
        **404** if not found; **200** if found.
    """
    agent = bridge.get_agent_status(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    return agent


# =============================================================================
# Agent Registration
# =============================================================================

@router.post("/register")
async def register_agent(
    instance: AgentInstanceCreate,
    bridge: GRPCBridge = Depends(get_bridge)
):
    """
    Register a new agent instance from YAML with host/port overrides.

    Purpose:
        Resolve the config path, optionally enforce localhost port uniqueness,
        then call ``register_agent_with_host_port``.

    Args:
        instance: Validated registration body.
        bridge: Injected fleet bridge.

    Returns:
        Registered agent dict from the bridge success envelope.

    Side effects:
        Filesystem existence check; RegisterAgent gRPC mutation.

    Failure behavior:
        **422** invalid body; **400** if config missing, localhost port in use,
        or RPC reports failure; **200** on success.
    """
    # Resolve config path (support both absolute and relative paths)
    config_path = instance.config_path
    if not os.path.isabs(config_path):
        # Interpret relative paths from the repository root.
        config_path = str(REPO_ROOT / config_path)
    
    if not os.path.exists(config_path):
        raise HTTPException(
            status_code=400, 
            detail=f"Config not found: {instance.config_path}"
        )
    
    # For localhost, check if port is already in use
    if is_localhost(instance.host):
        used_ports = get_used_ports()
        if instance.port in used_ports:
            raise HTTPException(
                status_code=400, 
                detail=f"Port {instance.port} is already in use on localhost"
            )
    
    # Register with host and port override
    result = bridge.register_agent_with_host_port(
        config_path=config_path,
        agent_id=instance.agent_id,
        host=instance.host,
        port=instance.port
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=400, 
            detail=result.get("message", "Registration failed")
        )
    
    return result.get("agent")


@router.delete("/{agent_id}")
async def unregister_agent(
    agent_id: str,
    bridge: GRPCBridge = Depends(get_bridge)
):
    """
    Unregister an agent from the fleet.

    Args:
        agent_id: Instance to remove.
        bridge: Injected fleet bridge.

    Returns:
        Success confirmation message.

    Side effects:
        UnregisterAgent gRPC mutation.

    Failure behavior:
        **400** if RPC reports failure; **200** on success.
    """
    result = bridge.unregister_agent(agent_id)
    if not result.get("success"):
        raise HTTPException(
            status_code=400, 
            detail=result.get("message", "Unregistration failed")
        )
    return {"success": True, "message": f"Agent {agent_id} unregistered"}


# =============================================================================
# Health Checks (from Telemetry service)
# =============================================================================

@router.get("/{agent_id}/health")
async def check_agent_health_endpoint(
    agent_id: str,
    source: str = "telemetry",
    bridge: GRPCBridge = Depends(get_bridge)
):
    """
    Check whether a specific agent is reachable.

    Purpose:
        Default ``source=telemetry`` uses heartbeat-derived health from the
        Telemetry service. ``source=direct`` pings the agent's HTTP endpoints.

    Args:
        agent_id: Agent to check.
        source: ``telemetry`` (default) or ``direct``.
        bridge: Injected fleet bridge (for registry lookup of host/port).

    Returns:
        Dict including agent_id, host, port, source, and health fields.

    Side effects:
        May call Telemetry HTTP or direct agent HTTP.

    Failure behavior:
        **404** if agent unknown; **200** with reachable=False when no heartbeat
        yet or probe fails (does not 502 for unreachable agents).
    """
    agent = bridge.get_agent_status(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

    host = agent.get("task_server_info", {}).get("host", DEFAULT_AGENT_HOST)
    port = agent.get("task_server_info", {}).get("port", DEFAULT_AGENT_BASE_PORT)

    if source == "direct":
        health = await check_agent_health(host, port)
        return {"agent_id": agent_id, "host": host, "port": port, "source": "direct", **health}

    telemetry_health = await get_telemetry_agent_health(agent_id)
    if telemetry_health is None:
        return {
            "agent_id": agent_id,
            "host": host,
            "port": port,
            "source": "telemetry",
            "reachable": False,
            "error": "No heartbeat received yet",
        }
    return {
        "agent_id": agent_id,
        "host": host,
        "port": port,
        "source": "telemetry",
        **telemetry_health,
    }


@router.get("/health/all")
async def check_all_agents_health_endpoint(
    source: str = "telemetry",
    bridge: GRPCBridge = Depends(get_bridge)
):
    """
    Check health for every registered agent.

    Purpose:
        Bulk health for the dashboard. Telemetry results are keyed by host:port
        and joined to fleet agent ids here.

    Args:
        source: ``telemetry`` (default) or ``direct``.
        bridge: Injected fleet bridge.

    Returns:
        ``{"agents": [...], "source": ...}``.

    Side effects:
        Lists agents; may probe all directly or fetch Telemetry summary.

    Failure behavior:
        **200** always for the aggregate payload; individual agents may show
        reachable=False when heartbeats are missing.
    """
    agents = bridge.list_agents("all")

    if source == "direct":
        results = await check_all_agents_health(agents)
        return {"agents": results, "source": "direct"}

    # Telemetry stores health keyed only by host:port. We join with fleet registry (agent_id + host/port) here.
    telemetry_summary = await get_telemetry_health_summary()
    results = []
    for agent in agents:
        agent_id = agent["agent_id"]
        host = agent.get("task_server_info", {}).get("host", DEFAULT_AGENT_HOST)
        port = agent.get("task_server_info", {}).get("port", DEFAULT_AGENT_BASE_PORT)
        th = telemetry_summary.get(f"{host}:{port}")
        if th:
            # Preserve fleet agent_id; telemetry's "agent_id" is the host:port key
            results.append({
                **th,
                "agent_id": agent_id,
                "host": host,
                "port": port,
            })
        else:
            results.append({
                "agent_id": agent_id,
                "host": host,
                "port": port,
                "reachable": False,
                "error": "No heartbeat received yet",
            })
    return {"agents": results, "source": "telemetry"}


# =============================================================================
# YAML Configuration
# =============================================================================

@router.get("/{agent_id}/yaml")
async def get_agent_yaml_details(
    agent_id: str,
    bridge: GRPCBridge = Depends(get_bridge)
):
    """
    Return the agent plus its source YAML content when discoverable.

    Purpose:
        Locate ``config.yaml`` via ``find_yaml_for_agent`` and parse it for the UI.

    Args:
        agent_id: Registered agent id.
        bridge: Injected fleet bridge.

    Returns:
        Dict with ``agent``, ``yaml_path`` (repo-relative or None), ``yaml_content``.

    Side effects:
        May read YAML from disk.

    Failure behavior:
        **404** if agent missing; **200** with null yaml fields if file not found
        or unreadable (parse errors swallowed).
    """
    import yaml
    
    agent = bridge.get_agent_status(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    # Try to find the YAML file
    yaml_path = find_yaml_for_agent(agent)
    
    if yaml_path and os.path.exists(yaml_path):
        try:
            with open(yaml_path) as f:
                yaml_content = yaml.safe_load(f)
            return {
                "agent": agent,
                "yaml_path": str(Path(yaml_path).relative_to(REPO_ROOT)),
                "yaml_content": yaml_content
            }
        except Exception:
            # Fall through to agent-only response.
            pass
    
    # Return agent info without YAML if not found
    return {
        "agent": agent,
        "yaml_path": None,
        "yaml_content": None
    }


def _refresh_single_agent(
    bridge: GRPCBridge,
    agent_id: str, 
    config_path: Optional[str] = None
) -> dict:
    """
    Unregister and re-register one agent from YAML while keeping host/port.

    Purpose:
        Pick up capability changes after YAML edits without manual re-entry of
        network settings.

    Args:
        bridge: Fleet bridge.
        agent_id: Instance to refresh.
        config_path: Optional override path; otherwise discovered from agent type.

    Returns:
        Success/error envelope dict (not an HTTPException).

    Side effects:
        Unregister + register RPCs; filesystem path checks.

    Failure behavior:
        Returns ``success=False`` with error string; does not raise.
    """
    agent = bridge.get_agent_status(agent_id)
    if not agent:
        return {"success": False, "agent_id": agent_id, "error": f"Agent {agent_id} not found"}
    
    # Find the YAML path
    yaml_path = None
    if config_path:
        yaml_path = config_path if os.path.isabs(config_path) else str(REPO_ROOT / config_path)
    else:
        yaml_path = find_yaml_for_agent(agent)
    
    if not yaml_path or not os.path.exists(yaml_path):
        return {"success": False, "agent_id": agent_id, "error": "Could not find YAML config file"}
    
    # Preserve current host/port
    host = agent.get("task_server_info", {}).get("host", DEFAULT_AGENT_HOST)
    port = agent.get("task_server_info", {}).get("port", DEFAULT_AGENT_BASE_PORT)
    
    # Unregister and re-register with fresh YAML
    bridge.unregister_agent(agent_id)
    result = bridge.register_agent_with_host_port(
        config_path=yaml_path,
        agent_id=agent_id,
        host=host,
        port=port
    )
    
    if not result.get("success"):
        return {"success": False, "agent_id": agent_id, "error": result.get("message", "Failed to refresh")}
    
    return {
        "success": True,
        "agent_id": agent_id,
        "message": f"Agent {agent_id} refreshed from YAML",
        "agent": result.get("agent")
    }


@router.post("/{agent_id}/refresh")
async def refresh_agent_from_yaml(
    agent_id: str,
    request: RefreshRequest = RefreshRequest(),
    bridge: GRPCBridge = Depends(get_bridge)
):
    """
    Refresh one agent's registration from its YAML file.

    Args:
        agent_id: Agent to refresh.
        request: Optional config_path override.
        bridge: Injected fleet bridge.

    Returns:
        Success envelope including refreshed agent.

    Side effects:
        Unregister/register sequence via ``_refresh_single_agent``.

    Failure behavior:
        **400** when refresh helper reports failure; **200** on success.
    """
    result = _refresh_single_agent(bridge, agent_id, request.config_path)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to refresh"))
    return result


@router.post("/refresh/all")
async def refresh_all_agents_from_yaml(
    bridge: GRPCBridge = Depends(get_bridge)
):
    """
    Refresh every registered agent from its discovered YAML file.

    Args:
        bridge: Injected fleet bridge.

    Returns:
        Aggregate counts plus per-agent result list.

    Side effects:
        Multiple unregister/register cycles.

    Failure behavior:
        Always **200** with per-item success flags (partial failures allowed).
    """
    agents = bridge.list_agents("all")
    results = []
    
    for agent in agents:
        result = _refresh_single_agent(bridge, agent["agent_id"])
        results.append(result)
    
    success_count = sum(1 for r in results if r.get("success"))
    failed_count = len(results) - success_count
    
    return {
        "total": len(results),
        "success_count": success_count,
        "failed_count": failed_count,
        "results": results
    }


# =============================================================================
# Agent Allocations
# =============================================================================

@router.get("/{agent_id}/allocations")
async def get_agent_allocations(
    agent_id: str,
    bridge: GRPCBridge = Depends(get_bridge)
):
    """
    Summarize plans/goals/tasks currently allocated to an agent.

    Purpose:
        Join TaskModel rows for ``agent_id`` with PlanModel metadata for the UI.

    Args:
        agent_id: Agent whose allocations to summarize.
        bridge: Provides ``registry.async_session_factory``.

    Returns:
        Counts plus plan summaries and goal id list (zeros on empty/error).

    Side effects:
        Async SQLAlchemy queries against the fleet database.

    Failure behavior:
        Logs and returns empty allocation structure (**200**), not **500**,
        so the dashboard card degrades gracefully.
    """
    try:
        # Query tasks allocated to this agent
        from packages.fleet_sdk.src.models import TaskModel, PlanModel, GoalModel
        from sqlalchemy import select, func, distinct

        async with bridge.registry.async_session_factory() as session:
            # Get all tasks allocated to this agent
            task_query = select(
                TaskModel.task_id,
                TaskModel.plan_id,
                TaskModel.goal_id,
                PlanModel.execution_status.label('plan_status')
            ).join(
                PlanModel, TaskModel.plan_id == PlanModel.plan_id
            ).where(
                TaskModel.agent_id == agent_id,
                TaskModel.agent_id.isnot(None)  # Only allocated tasks
            )

            result = await session.execute(task_query)
            tasks_data = result.fetchall()

            if not tasks_data:
                return {
                    "agent_id": agent_id,
                    "plans_count": 0,
                    "goals_count": 0,
                    "tasks_count": 0,
                    "plans": [],
                    "goals": []
                }

            # Extract unique plan IDs from tasks
            plan_ids = set()
            plan_statuses = {}

            for task in tasks_data:
                if task.plan_id:
                    plan_ids.add(task.plan_id)
                    plan_statuses[task.plan_id] = task.plan_status

            # Get plan details for the summary and collect goal IDs
            plans_summary = []
            goal_ids = set()

            if plan_ids:
                plan_details_query = select(
                    PlanModel.plan_id,
                    PlanModel.goal_ids,
                    PlanModel.execution_status,
                    PlanModel.name,
                    PlanModel.description
                ).where(PlanModel.plan_id.in_(plan_ids))

                plan_result = await session.execute(plan_details_query)
                plans_data = plan_result.fetchall()

                for plan in plans_data:
                    # Count tasks for this agent in this plan
                    agent_tasks_in_plan = sum(1 for task in tasks_data if task.plan_id == plan.plan_id)
                    plans_summary.append({
                        "plan_id": plan.plan_id,
                        "goal_ids": plan.goal_ids or [],
                        "task_count": agent_tasks_in_plan,
                        "status": ["not_executed", "executing", "completed", "failed"][plan.execution_status or 0],
                        "name": plan.name,
                        "description": plan.description
                    })

                    # Collect goal IDs from this plan
                    if plan.goal_ids:
                        goal_ids.update(plan.goal_ids)

            return {
                "agent_id": agent_id,
                "plans_count": len(plan_ids),
                "goals_count": len(goal_ids),
                "tasks_count": len(tasks_data),
                "plans": plans_summary,
                "goals": list(goal_ids)
            }

    except Exception as e:
        logger.error("Error getting allocations for agent %s: %s", agent_id, e, exc_info=True)
        # Return empty data on error
        return {
            "agent_id": agent_id,
            "plans_count": 0,
            "goals_count": 0,
            "tasks_count": 0,
            "plans": [],
            "goals": []
        }


# Import Path for relative path handling (kept at bottom to preserve original order).
from pathlib import Path
