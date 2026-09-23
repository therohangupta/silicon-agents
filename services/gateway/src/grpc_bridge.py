"""
gRPC bridge between the Dashboard HTTP API and the Fleet Manager service.

This module is the translation layer used by gateway routers: FastAPI handlers
speak JSON/dicts and Pydantic models, while the fleet server speaks protobuf
over gRPC. ``GRPCBridge`` wraps ``FleetManagerClient``, normalizes agent YAML
fields across schema generations, maps enum integers to human-readable status
strings, and optionally enriches plan payloads with columns that live only in
Postgres (prompts, artifacts, server logs, execution_status) via
``AgentInstanceRegistry``.

Requirements:

- The monorepo/agent_fleet package must be installed editable
  (``pip install -e .`` from repo root) so ``packages.proto``,
  ``packages.fleet_sdk``, and ``packages.agent_sdk`` import successfully.
- Fleet manager must be reachable at the configured host:port.
- ``DATABASE_URL`` must be valid when plan detail enrichment is requested.

Failure philosophy: most public methods catch exceptions and return
``None`` / ``{"success": False, ...}`` / ``{"error": ...}`` so routers can map
those into HTTP 400/404 without leaking raw gRPC stack traces to clients.
Logging is used for unexpected errors.
"""

import logging
from typing import List, Optional, Dict, Any

# Module logger for bridge-level diagnostics (plan DB enrichment, RPC failures).
logger = logging.getLogger(__name__)

# Generated fleet manager protobuf messages/enums (e.g. PlanningStrategy.MANUAL_PLAN).
from packages.proto import fleet_manager_pb2
# Thin sync gRPC client used for all fleet RPCs.
from packages.fleet_sdk.src.grpc_client import FleetManagerClient
# Async SQLAlchemy registry for plan extras and metrics not yet on all protos.
from packages.fleet_sdk.src.instance_registry import AgentInstanceRegistry
# ORM models used when selecting plan rows for enrichment.
from packages.fleet_sdk.src.models import PlanModel, TaskModel, GoalModel
# Defaults if bridge constructed without explicit host/port/db_url.
from packages.config import DATABASE_URL, GRPC_SERVER_HOST, GRPC_SERVER_PORT
# Validates agent config.yaml before register_* RPCs.
from packages.agent_sdk.src.config.load import load_agent_config_dict
# Imported for potential MessageToDict use; retained for parity with prior imports.
from google.protobuf.json_format import MessageToDict
# asyncio retained for callers/helpers that may schedule work (parity import).
import asyncio


# Map TaskStatus protobuf integers to API-facing lowercase strings.
TASK_STATUS_MAP = {
    0: "unknown",
    1: "pending",
    2: "in_progress",
    3: "completed",
    4: "cancelled",
    5: "failed",
}

# Map Agent lifecycle state integers to API-facing lowercase strings.
AGENT_STATE_MAP = {
    0: "unknown",
    1: "registered",
    2: "deploying",
    3: "running",
    4: "error",
    5: "stopped",
}


def _connection_from_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract the network connection block from a validated agent YAML dict.

    Purpose:
        Support agentfleet/v1 ``connection`` as well as legacy ``taskServer``
        and ``runtime`` keys so registration works across schema generations.

    Args:
        config: Full agent config mapping produced by ``load_agent_config_dict``.

    Returns:
        A dict of connection fields (may be empty if none of the keys exist).

    Side effects:
        None.

    Failure behavior:
        Never raises; missing keys yield ``{}``.
    """
    # Prefer modern key, then legacy aliases, else empty mapping.
    return config.get("connection") or config.get("taskServer") or config.get("runtime") or {}


def _deployment_from_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract deployment/container image settings from agent YAML.

    Purpose:
        Normalize ``deployment`` with a fallback to legacy ``container.image``
        when ``deployment.image`` is absent.

    Args:
        config: Validated agent configuration dict.

    Returns:
        A mutable copy of the deployment dict, possibly with ``image`` filled
        from ``container``.

    Side effects:
        Returns a new dict (``dict(...)``) so callers can ``setdefault`` safely.

    Failure behavior:
        Never raises; missing sections become empty dicts.
    """
    # Copy so we do not mutate the validated config object in place.
    dep = dict(config.get("deployment") or {})
    # Legacy YAMLs stored image under container; promote if deployment lacks it.
    if not dep.get("image") and config.get("container"):
        dep.setdefault("image", (config.get("container") or {}).get("image", ""))
    return dep


def _capabilities_from_config(config: Dict[str, Any]) -> List[str]:
    """
    Flatten capability entries from YAML into a list of string identifiers.

    Purpose:
        Protobuf registration expects a list of capability strings; YAML may
        store either plain strings or objects with ``id`` / ``description``.

    Args:
        config: Validated agent configuration dict.

    Returns:
        List of capability id/description strings (empty if none declared).

    Side effects:
        None.

    Failure behavior:
        Never raises; non-dict capabilities are stringified.
    """
    # Accumulator for flattened capability identifiers.
    caps = []
    # Iterate raw capability entries from YAML.
    for capability in config.get("capabilities", []):
        if isinstance(capability, dict):
            # Prefer stable id; fall back to human description text.
            caps.append(capability.get("id", capability.get("description", "")))
        else:
            # Scalar capability (string or other) → string for the RPC.
            caps.append(str(capability))
    return caps


class GRPCBridge:
    """
    Facade over fleet-manager gRPC plus local registry enrichment.

    Purpose:
        Give REST routers a dict-oriented API for agents, goals, plans, and
        tasks without embedding protobuf details in every handler.

    Side effects:
        Construction opens a gRPC channel and an ``AgentInstanceRegistry``
        session factory against ``db_url``. Methods perform network and DB I/O.

    Failure behavior:
        Most methods catch exceptions and return soft-failure dicts/None for
        HTTP mapping; some list helpers may propagate client errors.
    """
    
    def __init__(self, host: str = GRPC_SERVER_HOST, port: int = GRPC_SERVER_PORT, db_url: Optional[str] = None):
        """
        Create the fleet client and instance registry.

        Args:
            host: Fleet manager hostname (default from packages.config).
            port: Fleet manager gRPC port.
            db_url: Optional SQLAlchemy URL; defaults to ``DATABASE_URL``.

        Returns:
            None (constructor).

        Side effects:
            Instantiates ``FleetManagerClient`` and
            ``AgentInstanceRegistry``.

        Failure behavior:
            Propagates client/registry construction errors to the caller
            (typically lifespan ``init_bridge``).
        """
        # Compose the target address expected by FleetManagerClient.
        server_address = f"{host}:{port}"
        # Sync gRPC stub wrapper used by all RPC methods below.
        self.client = FleetManagerClient(server_address=server_address)
        # Prefer explicit db_url from dependencies.init_bridge.
        self.db_url = db_url or DATABASE_URL
        # Registry provides async DB access for plan extras and metrics.
        self.registry = AgentInstanceRegistry(self.db_url)
    
    def close(self):
        """
        Close the underlying gRPC client channel.

        Purpose:
            Release network resources during application shutdown.

        Args:
            None.

        Returns:
            None.

        Side effects:
            Calls ``self.client.close()`` when ``self.client`` is truthy.

        Failure behavior:
            Propagates exceptions from the client close path.
        """
        # Guard against partially constructed bridges.
        if self.client:
            self.client.close()
    
    def _agent_to_dict(self, agent) -> Dict[str, Any]:
        """
        Convert a fleet Agent protobuf message into a JSON-friendly dict.

        Args:
            agent: Protobuf Agent instance from list/get/register responses.

        Returns:
            Dict with agent_id, type, description, capabilities, status string,
            optional task_server_info/container, and task_ids.

        Side effects:
            None.

        Failure behavior:
            Assumes required fields exist; missing optional fields become None.
        """
        return {
            "agent_id": agent.agent_id,
            "agent_type": agent.agent_type,
            "description": agent.description,
            "capabilities": list(agent.capabilities),
            # Map nested status.state enum through AGENT_STATE_MAP when present.
            "status": AGENT_STATE_MAP.get(agent.status.state, "unknown") if agent.status else "unknown",
            "task_server_info": {
                "host": agent.task_server_info.host,
                "port": agent.task_server_info.port,
            } if agent.HasField("task_server_info") else None,
            "container": {
                "container_id": agent.container.container_id,
                "image": agent.container.image,
                "host": agent.container.host,
                "port": agent.container.port,
            } if agent.HasField("container") else None,
            "task_ids": list(agent.task_ids),
        }
    
    def _goal_to_dict(self, goal) -> Dict[str, Any]:
        """
        Convert a Goal protobuf message into a JSON-friendly dict.

        Args:
            goal: Protobuf Goal from create/list/get responses.

        Returns:
            Dict with goal_id, description, default status ``pending``,
            task_ids, and placeholder ``created_at`` (None until proto gains it).

        Side effects:
            None.

        Failure behavior:
            Does not raise for missing optional proto fields.
        """
        return {
            "goal_id": goal.goal_id,
            "description": goal.description,
            "status": "pending",  # Default status for new goals
            "task_ids": list(goal.task_ids),
            "created_at": None,  # Could be added if protobuf has timestamp
        }
    
    def _task_to_dict(self, task) -> Dict[str, Any]:
        """
        Convert a Task protobuf message into a JSON-friendly dict.

        Args:
            task: Protobuf Task from list/get/create/update responses.

        Returns:
            Dict including ids, assignment fields, dependency list, mapped
            status string, and optional result text.

        Side effects:
            None.

        Failure behavior:
            Uses ``HasField`` for optional scalars; unmapped status → ``unknown``.
        """
        return {
            "task_id": task.task_id,
            "description": task.description,
            "goal_id": task.goal_id if task.goal_id else None,
            "plan_id": task.plan_id if task.plan_id else None,
            "agent_id": task.agent_id if task.agent_id else None,
            "agent_type": task.agent_type if task.HasField("agent_type") else None,
            "dependency_task_ids": list(task.dependency_task_ids),
            "status": TASK_STATUS_MAP.get(task.status, "unknown"),
            "result": task.result if task.HasField("result") and task.result else None,
        }
    
    def _plan_to_dict(self, plan, include_tasks: bool = False) -> Dict[str, Any]:
        """
        Convert a Plan protobuf message into a JSON-friendly dict.

        Args:
            plan: Protobuf Plan message.
            include_tasks: When True, also fetch and embed task dicts for this plan.

        Returns:
            Dict with plan metadata and optionally a ``tasks`` list. Prompt/
            artifact/log fields are intentionally omitted here and merged later
            from the database in ``list_plans`` / ``get_plan``.

        Side effects:
            May call ``list_tasks`` (another gRPC round-trip) when include_tasks.

        Failure behavior:
            Propagates errors from ``list_tasks`` if include_tasks is True.
        """
        # Core fields available on the protobuf today.
        result = {
            "plan_id": plan.plan_id,
            "name": plan.name,
            "description": plan.description,
            "planning_strategy": plan.planning_strategy,
            "allocation_strategy": plan.allocation_strategy,
            "task_ids": list(plan.task_ids),
            "goal_ids": list(plan.goal_ids),
        }
        if include_tasks:
            # Nested list_tasks filters by this plan id via gRPC.
            tasks = self.list_tasks(plan_ids=[plan.plan_id])
            result["tasks"] = tasks

        # Note: Additional plan data (prompts, artifacts, logs) is fetched from database
        # in the calling methods (list_plans/get_plan) rather than from protobuf
        # since the protobuf files haven't been regenerated with the new fields

        return result

    async def _get_plan_details_from_db(self, plan_id: int) -> Optional[Dict[str, Any]]:
        """
        Load plan enrichment columns that are not yet on the Plan protobuf.

        Purpose:
            Attach planning/allocation prompts and artifacts, server logs,
            created_at ISO string, and execution_status string for the UI.

        Args:
            plan_id: Numeric plan primary key.

        Returns:
            Dict of present detail fields, or ``None`` if the row is missing
            or a database error occurs.

        Side effects:
            Opens an async SQLAlchemy session via ``self.registry``.

        Failure behavior:
            Logs and returns ``None`` on exceptions (callers keep proto-only data).
        """
        try:
            # Import select locally to avoid hard dependency at module import for
            # environments that only use pure gRPC paths in tests.
            from sqlalchemy import select

            # Borrow a session from the registry's async factory.
            async with self.registry.async_session_factory() as session:
                # Fetch the single PlanModel row for this id.
                result = await session.execute(
                    select(PlanModel).where(PlanModel.plan_id == plan_id)
                )
                # scalar_one_or_none → model or None without raising on 0 rows.
                plan_model = result.scalar_one_or_none()

                if not plan_model:
                    logger.warning(f"No plan found with ID {plan_id}")
                    return None

                # Only include keys that are actually populated on the ORM row.
                details = {}
                if plan_model.planning_prompts:
                    details['planning_prompts'] = plan_model.planning_prompts
                if plan_model.allocation_prompts:
                    details['allocation_prompts'] = plan_model.allocation_prompts
                if plan_model.planning_artifacts:
                    details['planning_artifacts'] = plan_model.planning_artifacts
                if plan_model.allocation_artifacts:
                    details['allocation_artifacts'] = plan_model.allocation_artifacts
                if plan_model.server_logs:
                    details['server_logs'] = plan_model.server_logs
                if plan_model.created_at:
                    details['created_at'] = plan_model.created_at.isoformat()

                # Mirror execution_status integers into UI strings.
                execution_status_map = {0: 'not_executed', 1: 'executing', 2: 'completed', 3: 'failed'}
                details['execution_status'] = execution_status_map.get(plan_model.execution_status, 'not_executed')

                return details
        except Exception as e:
            logger.error("Error fetching plan details from DB: %s", e, exc_info=True)
            return None

    # =========================================================================
    # Agent Operations
    # =========================================================================
    
    def list_agents(self, filter_type: str = "all") -> List[Dict[str, Any]]:
        """
        List agents known to the fleet manager.

        Args:
            filter_type: Fleet filter string such as ``all``, ``deployed``,
                or ``registered`` (passed through to the RPC).

        Returns:
            List of agent dicts from ``_agent_to_dict``.

        Side effects:
            Performs a ListAgents gRPC call.

        Failure behavior:
            Propagates client exceptions to the caller.
        """
        # Invoke fleet ListAgents with the requested filter.
        response = self.client.list_agents(filter_type)
        # Convert each protobuf Agent into a dict for JSON responses.
        return [self._agent_to_dict(r) for r in response.agents]
    
    def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Find one agent by scanning ``list_agents`` results.

        Args:
            agent_id: Target agent identifier.

        Returns:
            Matching agent dict, or ``None`` if not found or on error.

        Side effects:
            Calls ``list_agents()`` (full list RPC).

        Failure behavior:
            Logs errors and returns ``None`` rather than raising.
        """
        try:
            # Pull the full agent list then linear-search (simple, matches prior behavior).
            agents = self.list_agents()
            for agent in agents:
                if agent["agent_id"] == agent_id:
                    return agent
            return None
        except Exception as e:
            logger.error("Error getting agent status for %s: %s", agent_id, e)
            return None

    def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a single agent via the dedicated GetAgent RPC.

        Args:
            agent_id: Target agent identifier.

        Returns:
            Agent dict, or ``None`` if the response indicates error / no agent.

        Side effects:
            Performs a GetAgent gRPC call.

        Failure behavior:
            Logs and returns ``None`` on exceptions or error payloads.
        """
        try:
            response = self.client.get_agent(agent_id)
            # Some stubs surface errors as a string field rather than status codes.
            if hasattr(response, "error") and response.error:
                return None
            # Prefer HasField when the oneof/optional agent is present.
            if hasattr(response, "HasField") and response.HasField("agent"):
                return self._agent_to_dict(response.agent)
            return None
        except Exception as e:
            logger.error("Error getting agent %s: %s", agent_id, e)
            return None
    
    def register_agent_from_yaml(self, config_path: str, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate agent YAML and register using connection/deployment defaults.

        Args:
            config_path: Filesystem path to ``config.yaml``.
            agent_id: Optional override; defaults to ``{metadata.name}-1``.

        Returns:
            ``{"success", "message", "agent"}`` on success path, or
            ``{"success": False, "message": ...}`` on failure.

        Side effects:
            Reads/validates YAML; performs RegisterAgent gRPC.

        Failure behavior:
            Catches all exceptions and returns success=False with message text.
        """
        try:
            # Schema-validate and load the YAML into a dict.
            config = load_agent_config_dict(config_path)
            # Agent type is the metadata.name from the package.
            agent_type = config['metadata']['name']
            # Auto id when caller did not supply one.
            rid = agent_id if agent_id else f"{agent_type}-1"
            # Normalize connection / deployment / capabilities across schema versions.
            conn = _connection_from_config(config)
            deployment = _deployment_from_config(config)
            capabilities = _capabilities_from_config(config)
            
            # Register with YAML-derived host/port and docker settings.
            response = self.client.register_agent(
                agent_id=rid,
                agent_type=agent_type,
                description=config['metadata'].get('description', ''),
                capabilities=capabilities,
                task_server_host=conn.get('host', 'localhost'),
                task_server_port=int(conn.get('port', 8001)),
                docker_host=deployment.get('docker_host', 'localhost'),
                docker_port=int(deployment.get('docker_port', 2375)),
                container_image=deployment.get('image', ''),
                container_env=deployment.get('environment') or deployment.get('env', {}),
            )
            
            return {
                "success": response.success,
                "message": response.message,
                "agent": self._agent_to_dict(response.agent) if response.agent else None,
            }
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def register_agent_with_port(self, config_path: str, agent_id: str, port: int) -> Dict[str, Any]:
        """
        Register an agent overriding both task-server and docker ports.

        Args:
            config_path: Path to agent YAML.
            agent_id: Explicit instance id to register.
            port: Port used for task_server_port and docker_port.

        Returns:
            Success envelope with optional agent dict, or failure message dict.

        Side effects:
            YAML validation + RegisterAgent RPC.

        Failure behavior:
            Returns ``{"success": False, "message": str(e)}`` on any exception.
        """
        try:
            config = load_agent_config_dict(config_path)
            agent_type = config['metadata']['name']
            conn = _connection_from_config(config)
            deployment = _deployment_from_config(config)
            capabilities = _capabilities_from_config(config)
            
            response = self.client.register_agent(
                agent_id=agent_id,
                agent_type=agent_type,
                description=config['metadata'].get('description', ''),
                capabilities=capabilities,
                # Keep host from YAML connection block.
                task_server_host=conn.get('host', 'localhost'),
                # Caller-supplied port overrides YAML for the task server.
                task_server_port=port,
                docker_host=deployment.get('docker_host', 'localhost'),
                # Same override applied to docker_port (historical behavior).
                docker_port=port,
                container_image=deployment.get('image', ''),
                container_env=deployment.get('environment') or deployment.get('env', {}),
            )
            
            return {
                "success": response.success,
                "message": response.message,
                "agent": self._agent_to_dict(response.agent) if response.agent else None,
            }
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def register_agent_with_host_port(self, config_path: str, agent_id: str, host: str, port: int) -> Dict[str, Any]:
        """
        Register an agent with explicit task-server host and port overrides.

        Args:
            config_path: Path to agent YAML.
            agent_id: Instance id.
            host: Task server hostname/IP for the fleet to contact.
            port: Task server port.

        Returns:
            Success envelope with optional agent dict, or failure message dict.

        Side effects:
            YAML validation + RegisterAgent RPC. Docker host/port still come
            from deployment defaults (not overridden by ``host``/``port``).

        Failure behavior:
            Returns success=False message dict on exceptions.
        """
        try:
            config = load_agent_config_dict(config_path)
            agent_type = config['metadata']['name']
            deployment = _deployment_from_config(config)
            capabilities = _capabilities_from_config(config)
            
            response = self.client.register_agent(
                agent_id=agent_id,
                agent_type=agent_type,
                description=config['metadata'].get('description', ''),
                capabilities=capabilities,
                # Explicit overrides from the dashboard registration form.
                task_server_host=host,
                task_server_port=port,
                docker_host=deployment.get('docker_host', 'localhost'),
                docker_port=int(deployment.get('docker_port', 2375)),
                container_image=deployment.get('image', ''),
                container_env=deployment.get('environment') or deployment.get('env', {}),
            )
            
            return {
                "success": response.success,
                "message": response.message,
                "agent": self._agent_to_dict(response.agent) if response.agent else None,
            }
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def unregister_agent(self, agent_id: str) -> Dict[str, Any]:
        """
        Remove an agent registration from the fleet manager.

        Args:
            agent_id: Instance to unregister.

        Returns:
            ``{"success", "message"}`` from the RPC or a failure envelope.

        Side effects:
            UnregisterAgent gRPC; may impact running allocations.

        Failure behavior:
            Returns success=False with exception string.
        """
        try:
            response = self.client.unregister_agent(agent_id)
            return {"success": response.success, "message": response.message}
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    # =========================================================================
    # Goal Operations
    # =========================================================================
    
    def list_goals(self) -> List[Dict[str, Any]]:
        """
        List all goals from the fleet manager.

        Args:
            None.

        Returns:
            List of goal dicts.

        Side effects:
            ListGoals gRPC call.

        Failure behavior:
            Propagates client exceptions.
        """
        response = self.client.list_goals()
        return [self._goal_to_dict(g) for g in response.goals]
    
    def get_goal(self, goal_id: int) -> Optional[Dict[str, Any]]:
        """
        Fetch a single goal by numeric id.

        Args:
            goal_id: Goal primary key.

        Returns:
            Goal dict if present with a non-empty id, else ``None``.

        Side effects:
            GetGoal gRPC call.

        Failure behavior:
            Logs and returns ``None`` on exceptions.
        """
        try:
            response = self.client.get_goal(goal_id)
            if response.goal and response.goal.goal_id:
                return self._goal_to_dict(response.goal)
            return None
        except Exception as e:
            logger.error("Error getting goal %s: %s", goal_id, e)
            return None
    
    def create_goal(self, description: str) -> Optional[Dict[str, Any]]:
        """
        Create a new goal with the given natural-language description.

        Args:
            description: Goal text stored by the fleet server.

        Returns:
            Created goal dict, or ``None`` if the response lacks a goal.

        Side effects:
            CreateGoal gRPC mutation.

        Failure behavior:
            Logs and returns ``None`` on exceptions.
        """
        try:
            response = self.client.create_goal(description)
            if response.goal:
                return self._goal_to_dict(response.goal)
            return None
        except Exception as e:
            logger.error("Error creating goal: %s", e)
            return None
    
    def delete_goal(self, goal_id: int) -> Dict[str, Any]:
        """
        Delete a goal by id.

        Args:
            goal_id: Goal to delete.

        Returns:
            ``{"success": bool, "message": str}`` derived from response.goal /
            response.error fields.

        Side effects:
            DeleteGoal gRPC mutation.

        Failure behavior:
            Returns success=False with exception string.
        """
        try:
            response = self.client.delete_goal(goal_id)
            return {"success": bool(response.goal), "message": response.error or "Deleted"}
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    # =========================================================================
    # Plan Operations
    # =========================================================================
    
    async def list_plans(self) -> List[Dict[str, Any]]:
        """
        List all plans, merging protobuf fields with DB enrichment per plan.

        Args:
            None.

        Returns:
            List of plan dicts (enrichment best-effort per plan).

        Side effects:
            ListPlans gRPC plus async DB reads per plan id.

        Failure behavior:
            DB enrichment errors are logged; the proto-only dict is still appended.
        """
        response = self.client.list_plans()
        result = []
        for p in response.plans:
            plan_dict = self._plan_to_dict(p)
            # Fetch additional data from database
            try:
                details = await self._get_plan_details_from_db(p.plan_id)
                if details:
                    plan_dict.update(details)
            except Exception as e:
                logger.error(f"Failed to fetch plan details for {p.plan_id}: {e}")
            result.append(plan_dict)
        return result
    
    async def get_plan(self, plan_id: int) -> Optional[Dict[str, Any]]:
        """
        Fetch one plan including nested tasks and DB enrichment.

        Args:
            plan_id: Plan primary key.

        Returns:
            Enriched plan dict, or ``None`` if missing / on RPC failure.

        Side effects:
            GetPlan gRPC, ``list_tasks`` via include_tasks, async DB enrichment.

        Failure behavior:
            Logs and returns ``None`` on outer errors; enrichment errors keep
            the proto+tasks payload.
        """
        try:
            response = self.client.get_plan(plan_id)
            if response.plan and response.plan.plan_id:
                plan_dict = self._plan_to_dict(response.plan, include_tasks=True)
                # Fetch additional data from database
                try:
                    details = await self._get_plan_details_from_db(plan_id)
                    if details:
                        plan_dict.update(details)
                except Exception as e:
                    logger.error("Failed to fetch plan details for %s: %s", plan_id, e, exc_info=True)
                return plan_dict
            return None
        except Exception as e:
            logger.error("Error getting plan %s: %s", plan_id, e)
            return None

    async def list_plans_async(self) -> List[Dict[str, Any]]:
        """
        Async wrapper historically used by WebSocket code paths.

        Args:
            None.

        Returns:
            Same as ``list_plans()`` (note: returns the coroutine result of the
            async method when awaited by callers; this method itself returns
            the awaitable from calling ``self.list_plans()`` without awaiting,
            preserving prior behavior).

        Side effects:
            Same as ``list_plans`` when the returned coroutine is awaited.

        Failure behavior:
            Same as ``list_plans``.
        """
        # Preserve original non-awaited return of the coroutine object.
        return self.list_plans()

    async def _fetch_agent_health(self) -> Dict[str, Dict[str, bool]]:
        """
        Build a placeholder health map keyed by agent_id.

        Purpose:
            Historical helper for WebSocket code; currently assumes reachable
            True for every listed agent (not a live probe).

        Args:
            None.

        Returns:
            ``{agent_id: {"reachable": True}, ...}`` or ``{}`` on error.

        Side effects:
            ListAgents gRPC call.

        Failure behavior:
            Logs and returns empty dict.
        """
        try:
            # Use the existing agent health endpoint
            response = self.client.list_agents()
            health_map = {}

            # For each agent, we would need to check health
            # Since we don't have direct access to the health checking logic here,
            # we'll return a basic structure that the WebSocket can use
            for agent in response.agents:
                # This is a placeholder - in a real implementation you'd check actual health
                health_map[agent.agent_id] = {"reachable": True}  # Assume online for now

            return health_map
        except Exception as e:
            logger.error(f"Failed to fetch agent health: {e}")
            return {}
    
    def create_plan(
        self,
        planning_strategy: int,
        allocation_strategy: int,
        goal_ids: List[int],
        name: str,
        description: str
    ) -> Optional[Dict[str, Any]]:
        """
        Create a plan via automated planning/allocation strategies.

        Args:
            planning_strategy: Protobuf enum int for the planner.
            allocation_strategy: Protobuf enum int for the allocator.
            goal_ids: Goals the plan should satisfy.
            name: User-facing plan name.
            description: User-facing plan description.

        Returns:
            Plan dict including tasks, or ``None`` if the RPC returns no plan
            or raises.

        Side effects:
            CreatePlan gRPC (may invoke LLM/planners server-side).

        Failure behavior:
            Logs exception and returns ``None``.
        """
        logger.debug("Bridge create_plan called with planning=%s, allocation=%s, goals=%s, name=%s, desc=%s", planning_strategy, allocation_strategy, goal_ids, name, description)
        try:
            # Protobuf enum fields accept integers directly
            planning_enum = planning_strategy
            allocation_enum = allocation_strategy

            logger.debug("Converted to enums: planning=%s, allocation=%s", planning_enum, allocation_enum)
            response = self.client.create_plan(
                planning_strategy=planning_enum,
                goal_ids=goal_ids,
                allocation_strategy=allocation_enum,
                name=name,
                description=description
            )
            if response.plan:
                result = self._plan_to_dict(response.plan, include_tasks=True)
                return result
            logger.debug("No plan in response")
            return None
        except Exception as e:
            logger.exception("Exception in bridge: %s", e)
            return None
    
    def create_manual_plan(self, goal_ids: List[int] = None, name: Optional[str] = None, description: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Create an empty plan shell for manual task authoring.

        Purpose:
            Uses ``MANUAL_PLAN`` planning and ``NONE`` allocation so the UI can
            attach tasks via CreateTask without running automated planners.

        Args:
            goal_ids: Optional goals associated with the shell (default []).
            name: Optional plan name.
            description: Optional plan description.

        Returns:
            Plan dict without nested tasks, or ``None`` on failure.

        Side effects:
            CreatePlan gRPC with fixed strategy enums.

        Failure behavior:
            Logs and returns ``None``.
        """
        try:
            response = self.client.create_plan(
                planning_strategy=fleet_manager_pb2.PlanningStrategy.MANUAL_PLAN,
                goal_ids=goal_ids or [],
                allocation_strategy=fleet_manager_pb2.AllocationStrategy.NONE,
                name=name,
                description=description
            )
            if response.plan:
                return self._plan_to_dict(response.plan, include_tasks=False)
            return None
        except Exception as e:
            logger.error(f"Error creating manual plan: {e}")
            return None
    
    def allocate_plan(self, plan_id: int, allocation_strategy: int) -> Dict[str, Any]:
        """
        Run allocation for an existing plan's tasks.

        Args:
            plan_id: Plan to allocate.
            allocation_strategy: Allocator enum int.

        Returns:
            ``{"success": True, "plan": ...}`` or ``{"success": False, "message": ...}``.

        Side effects:
            AllocatePlan gRPC mutation.

        Failure behavior:
            Returns success=False with error message from response or exception.
        """
        try:
            response = self.client.allocate_plan(plan_id, allocation_strategy)
            if hasattr(response, 'error') and response.error:
                return {"success": False, "message": response.error}
            if response.plan:
                return {"success": True, "plan": self._plan_to_dict(response.plan, include_tasks=True)}
            return {"success": False, "message": "No plan returned"}
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def start_plan(self, plan_id: int) -> Dict[str, Any]:
        """
        Start executing a fully allocated plan.

        Args:
            plan_id: Plan to execute.

        Returns:
            ``{"error": None}`` on success path or ``{"error": str}`` on failure.
            Note: fleet may reject if any task lacks ``agent_id``.

        Side effects:
            StartPlan gRPC; begins task dispatch server-side.

        Failure behavior:
            Returns error string from response or exception.
        """
        try:
            response = self.client.start_plan(plan_id)
            return {"error": response.error if response.error else None}
        except Exception as e:
            return {"error": str(e)}

    async def update_plan(self, plan_id: int, **kwargs) -> Dict[str, Any]:
        """
        Placeholder plan update via gRPC (not fully implemented).

        Args:
            plan_id: Plan id (unused in current stub).
            **kwargs: Intended field updates (unused).

        Returns:
            ``{"success": True}`` unless an unexpected exception occurs.

        Side effects:
            None today; real updates go through ``registry.update_plan`` in routers.

        Failure behavior:
            Returns ``{"error": str(e)}`` if an exception is raised.
        """
        try:
            # This would need to be implemented in the gRPC service
            # For now, return success since we're updating via direct database access in executor
            return {"success": True}
        except Exception as e:
            return {"error": str(e)}
    
    async def get_plan_allocation_status(self, plan_id: int) -> Dict[str, Any]:
        """
        Derive allocation completeness for a plan from its task assignments.

        Args:
            plan_id: Plan to inspect.

        Returns:
            Status summary with counts and ``is_executable``, or ``{"error": ...}``.

        Side effects:
            Calls async ``get_plan`` (gRPC + DB).

        Failure behavior:
            Returns error dict if plan missing or on exception.
        """
        try:
            # Get the plan and its tasks
            plan = await self.get_plan(plan_id)
            if not plan:
                return {"error": f"Plan {plan_id} not found"}
            
            tasks = plan.get("tasks", [])
            total = len(tasks)
            # Count tasks that already have an agent_id assignment.
            allocated = sum(1 for t in tasks if t.get("agent_id"))
            unallocated_ids = [t["task_id"] for t in tasks if not t.get("agent_id")]
            
            if total == 0:
                status = "empty"
            elif allocated == 0:
                status = "unallocated"
            elif allocated < total:
                status = "partially_allocated"
            else:
                status = "fully_allocated"
            
            return {
                "plan_id": plan_id,
                "status": status,
                "total_tasks": total,
                "allocated_tasks": allocated,
                "unallocated_task_ids": unallocated_ids,
                # Executable only when every task is assigned and there is work.
                "is_executable": status == "fully_allocated" and total > 0
            }
        except Exception as e:
            return {"error": str(e)}
    
    def delete_plan(self, plan_id: int) -> Dict[str, Any]:
        """
        Delete a plan (and associated server-side cleanup).

        Args:
            plan_id: Plan to delete.

        Returns:
            Success/message envelope derived from response.goal-like fields
            (``response.plan`` / ``response.error``).

        Side effects:
            DeletePlan gRPC mutation.

        Failure behavior:
            Returns success=False with exception string.
        """
        try:
            response = self.client.delete_plan(plan_id)
            return {"success": bool(response.plan), "message": response.error or "Deleted"}
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    # =========================================================================
    # Task Operations
    # =========================================================================
    
    def list_tasks(
        self,
        plan_ids: Optional[List[int]] = None,
        goal_ids: Optional[List[int]] = None,
        agent_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        List tasks with optional plan/goal/agent filters.

        Args:
            plan_ids: Restrict to these plans when provided.
            goal_ids: Restrict to these goals when provided.
            agent_ids: Restrict to these agents when provided.

        Returns:
            List of task dicts.

        Side effects:
            ListTasks gRPC call.

        Failure behavior:
            Propagates client exceptions.
        """
        response = self.client.list_tasks(
            plan_ids=plan_ids,
            goal_ids=goal_ids,
            agent_ids=agent_ids
        )
        return [self._task_to_dict(t) for t in response.tasks]
    
    def get_task(self, task_id: int) -> Optional[Dict[str, Any]]:
        """
        Fetch a single task by id.

        Args:
            task_id: Task primary key.

        Returns:
            Task dict or ``None``.

        Side effects:
            GetTask gRPC call.

        Failure behavior:
            Logs and returns ``None`` on errors.
        """
        try:
            response = self.client.get_task(task_id)
            if response.task and response.task.task_id:
                return self._task_to_dict(response.task)
            return None
        except Exception as e:
            logger.error("Error getting task %s: %s", task_id, e)
            return None
    
    def create_task(
        self,
        description: str,
        goal_id: int,
        plan_id: int,
        agent_id: Optional[str] = None,
        agent_type: Optional[str] = None,
        dependency_task_ids: Optional[List[int]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a task attached to a goal and plan.

        Args:
            description: Task work statement.
            goal_id: Owning goal.
            plan_id: Owning plan.
            agent_id: Optional pre-assignment.
            agent_type: Optional required agent type/capability.
            dependency_task_ids: Upstream task ids (default empty).

        Returns:
            Created task dict or ``None``.

        Side effects:
            CreateTask gRPC mutation.

        Failure behavior:
            Logs and returns ``None`` when RPC fails or returns no task.
        """
        try:
            response = self.client.create_task(
                description=description,
                agent_id=agent_id,
                agent_type=agent_type,
                goal_id=goal_id,
                plan_id=plan_id,
                dependency_task_ids=dependency_task_ids or []
            )
            if response.task:
                return self._task_to_dict(response.task)
            logger.warning("create_task returned no task for plan %s", plan_id)
            return None
        except Exception as e:
            logger.error("Error creating task for plan %s: %s", plan_id, e)
            return None

    def update_task(
        self,
        task_id: int,
        description: Optional[str] = None,
        goal_id: Optional[int] = None,
        agent_id: Optional[str] = None,
        dependency_task_ids: Optional[List[int]] = None,
        update_dependency_task_ids: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """
        Update mutable fields on an existing task.

        agent_id semantics:
        - ``None``: do not modify assignment
        - ``""``: clear assignment
        - non-empty: set assignment

        Args:
            task_id: Task to update.
            description: Optional new description.
            goal_id: Optional new goal association.
            agent_id: Assignment semantics as above.
            dependency_task_ids: Dependency list (used when update flag set).
            update_dependency_task_ids: When True, replace dependency list.

        Returns:
            Updated task dict or ``None``.

        Side effects:
            UpdateTask gRPC mutation.

        Failure behavior:
            Logs and returns ``None`` on errors.
        """
        try:
            response = self.client.update_task(
                task_id=task_id,
                description=description,
                goal_id=goal_id,
                agent_id=agent_id,
                dependency_task_ids=dependency_task_ids or [],
                update_dependency_task_ids=update_dependency_task_ids,
            )
            if response.task and response.task.task_id:
                return self._task_to_dict(response.task)
            return None
        except Exception as e:
            logger.error("Error updating task %s: %s", task_id, e)
            return None

    def delete_task(self, task_id: int) -> Dict[str, Any]:
        """
        Delete a task; server unlinks dependents automatically.

        Args:
            task_id: Task to delete.

        Returns:
            Dict with success, deleted_task_id, updated_task_ids, and error.

        Side effects:
            DeleteTask gRPC mutation.

        Failure behavior:
            Returns success=False envelope with empty updated_task_ids.
        """
        try:
            response = self.client.delete_task(task_id)
            return {
                "success": bool(getattr(response, "success", False)),
                "deleted_task_id": int(getattr(response, "deleted_task_id", 0) or 0),
                "updated_task_ids": list(getattr(response, "updated_task_ids", [])),
                "error": getattr(response, "error", "") or "",
            }
        except Exception as e:
            return {"success": False, "deleted_task_id": task_id, "updated_task_ids": [], "error": str(e)}
