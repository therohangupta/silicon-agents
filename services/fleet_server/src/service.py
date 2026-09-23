"""
Fleet Manager gRPC service implementation.

This module is the heart of the Fleet Server process. It defines:

  * ``TaskServerClient`` — lightweight holder for an agent task-server host/port
    (legacy helper; most paths now read host/port from registry agent protos).
  * ``configure_logging`` — verbose / SQL-debug logging switches used by serve().
  * ``FleetManagerService`` — implements every RPC on the generated
    ``fleet_manager_pb2_grpc.FleetManagerServicer`` interface:
      - Agent lifecycle: Register / Unregister / List / Get / GetStatus /
        Deploy / Undeploy (deploy stubs are UNIMPLEMENTED).
      - Goals CRUD: Create / Get / List / Delete.
      - Tasks CRUD: Create / Update / Get / List / Delete (mutations force
        the owning plan into MANUAL_PLAN / MANUAL_ALLOCATION strategy).
      - Plans: Create (planner + optional allocator), AllocatePlan, Get /
        List / Delete, StartPlan (spawns ``Executor`` in the background).
  * ``serve`` — constructs the aio gRPC server, optionally resets DB tables,
    initializes the registry schema, binds ``[::]:port``, and waits for
    termination (with engine dispose on exit).

Planning strategies invoked from CreatePlan (via SDK ``get_planning_strategy``):
  - MONOLITHIC — single sequential DAGPlan for all goals.
  - DAG — one DAG per goal, concatenated (no cross-goal edges).
  - BIG_DAG — one unified DAG allowing cross-goal dependencies.
  - MANUAL_PLAN — empty plan shell; no LLM planner call.
  - Replanner is NOT selected here; Executor invokes it on failure.

Allocation strategies invoked via SDK ``get_allocation_strategy``:
  - LP — PuLP integer program minimizing max agent load.
  - LLM — GPT-4 structured Allocation parse.
  - COST_BASED — iterative LLM rounds over DAG frontier.
  - NONE / MANUAL_ALLOCATION — skip automatic allocation.

Gateway events (``emit_*``) are fired after successful mutations so the
dashboard can invalidate caches without polling.
"""

# gRPC core types / status codes used when failing RPCs.
import grpc
# ThreadPoolExecutor backs the aio server's worker pool for callbacks.
from concurrent import futures
# Dict/Optional typing for update kwargs and optional DB URL.
from typing import Dict, Optional
# asyncio.create_task launches Executor.execute() without blocking StartPlan.
import asyncio
# os.getenv("TESTING") bypasses planners in test environments.
import os
# logging for RPC diagnostics and serve() startup banners.
import logging
# timestamp_pb2 imported for protobuf timestamp compatibility (proto deps).
from google.protobuf import timestamp_pb2
# Generated request/response/enum message types for the FleetManager API.
from packages.proto import fleet_manager_pb2
# Generated Servicer base class and add_* registration helper.
from packages.proto import fleet_manager_pb2_grpc
# Persistent registry of agents/goals/tasks/plans backed by SQLAlchemy.
from packages.fleet_sdk.src.instance_registry import AgentInstanceRegistry
# SDK owns strategy implementations and DAG materialization.
from packages.fleet_sdk.src.planners.base import get_planning_strategy
from packages.fleet_sdk.src.allocators.base import get_allocator
# ORM Base.metadata used when --reset-db drops/recreates tables.
from packages.fleet_sdk.src.models import Base
# Default DATABASE_URL and GRPC_SERVER_PORT when callers omit overrides.
from packages.config import DATABASE_URL, GRPC_SERVER_PORT
# datetime/timedelta kept for potential timestamp helpers / proto interop.
from datetime import datetime, timedelta
# text() runs raw SQL to list public tables after initialization.
from sqlalchemy import text
# Fire-and-forget Gateway notifications after mutations.
from .events import emit_task_changed, emit_plan_changed, emit_agent_changed


# Simple class to store task server connection information
class TaskServerClient:
    """
    Simple class to store task server connection information.

    Historically used to cache host/port for agent task servers. Current
    Executor paths read ``agent.task_server_info`` from the registry instead,
    but this helper remains for compatibility with older call sites.
    """

    def __init__(self, task_server_host: str, task_server_port: int):
        """
        Store connection coordinates for an agent's task HTTP/gRPC server.

        Args:
            task_server_host: Hostname or IP where the agent listens.
            task_server_port: Port number for the agent task server.
        """
        # Hostname/IP string used by clients to reach the agent.
        self.task_server_host = task_server_host
        # Integer port paired with the host above.
        self.task_server_port = task_server_port


# Configure root logger if not already configured by another importer.
if not logging.getLogger().handlers:
    # BasicConfig only when no handlers exist to avoid duplicate log lines.
    logging.basicConfig(
        level=logging.WARNING,  # Default to WARNING level until configure_logging.
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]  # Emit to stderr/stdout stream.
    )

# Module-level logger used throughout FleetManagerService and serve().
logger = logging.getLogger(__name__)


def configure_logging(verbose: bool = False, sql_debug: bool = False):
    """
    Configure logging based on verbose and sql_debug flags.

    Called once from ``serve()`` before DB init so startup messages honor the
    operator's CLI flags from ``__main__``.

    Args:
        verbose: If True, enables detailed application logging (DEBUG).
        sql_debug: If True, enables SQLAlchemy engine SQL statement logging.
    """
    # Configure application logging level from the verbose flag.
    log_level = logging.DEBUG if verbose else logging.INFO
    # Apply the chosen level to this module's logger.
    logger.setLevel(log_level)

    # Configure SQL logging if requested.
    if sql_debug:
        # Surface SQL statements at INFO when operators pass --sql-debug.
        logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
    else:
        # Keep SQL logging at WARNING to avoid noise in normal runs.
        logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

    # Configure other modules (agent task server client logs) to match.
    task_server_logger = logging.getLogger('task_server')
    # Align task_server logger with the same verbose/info level.
    task_server_logger.setLevel(log_level)


class FleetManagerService(fleet_manager_pb2_grpc.FleetManagerServicer):
    """
    gRPC server for agent fleet management.

    Implements the generated ``FleetManagerServicer`` RPCs. All durable state
    flows through ``AgentInstanceRegistry``. Planner/allocator/executor
    modules are imported lazily inside the RPCs that need them to keep
    module import time low and avoid circular imports with planners.
    """

    def __init__(self, db_url: Optional[str] = None):
        """
        Initialize the service with a registry bound to ``db_url``.

        Args:
            db_url: PostgreSQL connection URL. If None, the registry uses its
                own default (typically ``packages.config.DATABASE_URL``).
        """
        # Primary persistence/facade for agents, goals, tasks, and plans.
        self.registry = AgentInstanceRegistry(db_url=db_url)
        # Store stream contexts by agent_id (reserved for streaming RPCs).
        self._streams_contexts = {}
        # Store session contexts by agent_id (reserved for sessionful flows).
        self._session_contexts = {}

    async def initialize(self):
        """
        Initialize the service by setting up the database schema.

        Delegates to ``registry.initialize()`` which creates tables if needed.
        Must be awaited from ``serve()`` before accepting RPCs.
        """
        # Create/verify ORM tables via the registry's async engine.
        await self.registry.initialize()

    async def cleanup(self):
        """
        Dispose the async engine and release DB connections.

        Invoked from ``serve()``'s finally block so connection pools do not
        leak on shutdown or cancellation.
        """
        # Dispose SQLAlchemy async engine / pooled connections.
        await self.registry.engine.dispose()

    async def _mark_plan_manual(self, plan_id: int) -> None:
        """
        Mark a plan as manually defined/allocated based on its current tasks.

        Any direct task mutation (create/update/delete) implies the operator
        took ownership of the plan graph, so we force:
          - planning_strategy = MANUAL_PLAN
          - allocation_strategy = MANUAL_ALLOCATION if ANY task has agent_id,
            else NONE

        Also recomputes ``goal_ids`` from the tasks currently on the plan.

        Args:
            plan_id: Plan whose strategies should be rewritten.

        Raises:
            RuntimeError: If ``update_plan`` returns a falsy result.
        """
        # Load all tasks currently associated with this plan.
        tasks = await self.registry.list_tasks(plan_ids=[plan_id])
        # True if at least one task already has an agent assignment string.
        has_any_agent = any(getattr(t, "agent_id", "") for t in tasks)
        # Rebuild goal_ids from tasks (positive ids only), sorted for stability.
        goal_ids = sorted({int(getattr(t, "goal_id", 0)) for t in tasks if int(getattr(t, "goal_id", 0) or 0) > 0})

        # Choose MANUAL_ALLOCATION when assignments exist; otherwise NONE.
        allocation_strategy = (
            fleet_manager_pb2.AllocationStrategy.MANUAL_ALLOCATION
            if has_any_agent
            else fleet_manager_pb2.AllocationStrategy.NONE
        )

        # Persist the manual planning strategy + computed allocation strategy.
        updated = await self.registry.update_plan(
            plan_id=plan_id,
            goal_ids=goal_ids,
            planning_strategy=int(fleet_manager_pb2.PlanningStrategy.MANUAL_PLAN),
            allocation_strategy=int(allocation_strategy),
        )
        # Fail loudly if the registry could not apply the strategy update.
        if not updated:
            raise RuntimeError(f"Failed to update plan strategies for plan_id={plan_id}")

    async def RegisterAgent(self, request, context):
        """
        Register an agent with the fleet manager.

        Persists agent metadata (type, capabilities, optional container /
        deployment / task_server info). Returns ALREADY_EXISTS when the
        registry rejects a duplicate agent_id.

        Args:
            request: ``RegisterAgentRequest`` with agent fields.
            context: gRPC aio servicer context for status codes.

        Returns:
            ``RegisterAgentResponse`` with success flag, message, and agent.
        """
        # Log the incoming registration attempt with the agent id.
        logger.info(f"Registering agent: {request.agent_id}")
        try:
            # Use the instance registry to register the agent persistently.
            agent = await self.registry.register_agent(
                agent_id=request.agent_id,
                agent_type=request.agent_type,
                description=request.description,
                capabilities=list(request.capabilities),
                container_info=request.container if hasattr(request, 'container') else None,
                deployment_info=request.deployment if hasattr(request, 'deployment') else None,
                task_server_info=request.task_server_info if hasattr(request, 'task_server_info') else None
            )

            # Registry returns falsy/None when the agent_id already exists.
            if not agent:
                # Map duplicate to gRPC ALREADY_EXISTS for clients.
                context.set_code(grpc.StatusCode.ALREADY_EXISTS)
                context.set_details(f"Agent with ID {request.agent_id} already exists")
                return fleet_manager_pb2.RegisterAgentResponse(
                    success=False,
                    message=f"Agent with ID {request.agent_id} already exists"
                )

            # Confirm success in logs for operators watching the server.
            logger.info(f"Successfully registered agent: {request.agent_id}")
            # Notify Gateway/dashboard that a new agent appeared.
            emit_agent_changed(request.agent_id, action="registered")
            # Return the registered agent proto to the caller.
            return fleet_manager_pb2.RegisterAgentResponse(
                success=True,
                message=f"Successfully registered agent: {request.agent_id}",
                agent=agent
            )

        except Exception as e:
            # Unexpected errors become INTERNAL with the exception message.
            logger.error(f"Error registering agent: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Failed to register agent: {str(e)}")
            return fleet_manager_pb2.RegisterAgentResponse(
                success=False,
                message=f"Error: {str(e)}"
            )

    async def DeployAgent(self, request, context):
        """
        Deploy an agent container (not yet implemented).

        Always returns UNIMPLEMENTED. Container orchestration is reserved
        for a future ContainerManager integration.

        Args:
            request: ``DeployAgentRequest`` (unused today).
            context: gRPC context set to UNIMPLEMENTED.

        Returns:
            ``DeployAgentResponse`` with success=False.
        """
        # Signal to clients that deploy is not available yet.
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Container deployment not yet implemented")
        return fleet_manager_pb2.DeployAgentResponse(
            success=False,
            message="Container deployment not yet implemented"
        )

    async def UndeployAgent(self, request, context):
        """
        Undeploy an agent container (not yet implemented).

        Always returns UNIMPLEMENTED, mirroring DeployAgent.

        Args:
            request: ``UndeployAgentRequest`` (unused today).
            context: gRPC context set to UNIMPLEMENTED.

        Returns:
            ``UndeployAgentResponse`` with success=False.
        """
        # Signal to clients that undeploy is not available yet.
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Container undeployment not yet implemented")
        return fleet_manager_pb2.UndeployAgentResponse(
            success=False,
            message="Container undeployment not yet implemented"
        )

    async def UnregisterAgent(self, request, context):
        """
        Unregister an agent from the fleet manager.

        If the agent appears deployed (has a container_id), attempts to stop
        it via ``container_manager`` before deleting the registry row. Stop
        failures are logged as warnings and do not block unregister.

        Args:
            request: ``UnregisterAgentRequest`` with agent_id.
            context: gRPC context for NOT_FOUND / INTERNAL codes.

        Returns:
            ``UnregisterAgentResponse`` describing success or failure.
        """
        # Log which agent is being removed.
        logger.info(f"Unregistering agent: {request.agent_id}")
        try:
            # Check if agent exists first before attempting delete.
            agent = await self.registry.get_agent(request.agent_id)
            if not agent:
                # Unknown agent_id → NOT_FOUND.
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Agent with ID {request.agent_id} not found")
                return fleet_manager_pb2.UnregisterAgentResponse(
                    success=False,
                    message=f"Agent with ID {request.agent_id} not found"
                )

            # Check if agent is deployed (has container metadata).
            if agent.HasField('container') and agent.container.container_id:
                # Try to undeploy the agent first via container_manager.
                try:
                    await self.container_manager.stop_agent(
                        agent_id=request.agent_id,
                        host=agent.deployment.docker_host,
                        docker_port=agent.deployment.docker_port
                    )
                except Exception as e:
                    # Soft-fail: still proceed to delete registry row.
                    logger.warning(f"Failed to undeploy agent {request.agent_id} before unregistering: {str(e)}")

            # Delete the agent from the registry (durable remove).
            success = await self.registry.delete_agent(request.agent_id)

            # delete_agent returning False indicates an unexpected failure.
            if not success:
                context.set_code(grpc.StatusCode.INTERNAL)
                context.set_details(f"Failed to unregister agent {request.agent_id}")
                return fleet_manager_pb2.UnregisterAgentResponse(
                    success=False,
                    message=f"Failed to unregister agent {request.agent_id}"
                )

            # Log successful removal for operators.
            logger.info(f"Successfully unregistered agent: {request.agent_id}")
            # Notify Gateway that the agent is gone.
            emit_agent_changed(request.agent_id, action="unregistered")
            return fleet_manager_pb2.UnregisterAgentResponse(
                success=True,
                message=f"Successfully unregistered agent: {request.agent_id}"
            )

        except Exception as e:
            # Catch-all for unexpected unregister failures.
            logger.error(f"Error unregistering agent: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Failed to unregister agent: {str(e)}")
            return fleet_manager_pb2.UnregisterAgentResponse(
                success=False,
                message=f"Error: {str(e)}"
            )

    async def ListAgents(self, request, context):
        """
        List agents in the fleet manager with optional filter.

        Filter enum values:
          - ALL — every registered agent.
          - DEPLOYED — agents with a non-empty container_id.
          - REGISTERED — agents in REGISTERED or RUNNING status states.

        Args:
            request: ``ListAgentsRequest`` including filter enum.
            context: gRPC context for INTERNAL errors.

        Returns:
            ``ListAgentsResponse`` with the filtered agent list (or empty).
        """
        # Announce list operation for tracing.
        logger.info("Listing agents")
        try:
            # List all agents from the registry without filter first.
            agents = await self.registry.list_agents()

            # Apply filter if specified by collecting matching agents.
            filtered_agents = []
            for agent in agents:
                if request.filter == fleet_manager_pb2.ListAgentsRequest.Filter.ALL:
                    # ALL: include every agent unconditionally.
                    filtered_agents.append(agent)
                elif request.filter == fleet_manager_pb2.ListAgentsRequest.Filter.DEPLOYED:
                    # DEPLOYED: require container metadata with an id.
                    if agent.HasField('container') and agent.container.container_id:
                        filtered_agents.append(agent)
                elif request.filter == fleet_manager_pb2.ListAgentsRequest.Filter.REGISTERED:
                    # REGISTERED: include REGISTERED or RUNNING status states.
                    if (agent.status.state == fleet_manager_pb2.AgentStatus.State.REGISTERED or
                        agent.status.state == fleet_manager_pb2.AgentStatus.State.RUNNING):
                        filtered_agents.append(agent)

            # Log how many agents survived the filter.
            logger.info(f"Found {len(filtered_agents)} agents")
            return fleet_manager_pb2.ListAgentsResponse(
                agents=filtered_agents
            )

        except Exception as e:
            # On failure return an empty list with INTERNAL status.
            logger.error(f"Error listing agents: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Failed to list agents: {str(e)}")
            return fleet_manager_pb2.ListAgentsResponse()

    async def GetAgent(self, request, context):
        """
        Get a specific agent by ID.

        Args:
            request: ``GetAgentRequest`` with agent_id.
            context: gRPC context for INTERNAL errors.

        Returns:
            ``GetAgentResponse`` with agent or error string (not found is soft).
        """
        # Log the lookup key.
        logger.info(f"Getting agent: {request.agent_id}")
        try:
            # Fetch a single agent proto from the registry.
            agent = await self.registry.get_agent(request.agent_id)
            if not agent:
                # Soft-not-found via error field (no gRPC NOT_FOUND here).
                return fleet_manager_pb2.GetAgentResponse(
                    error=f"Agent with ID {request.agent_id} not found"
                )
            # Success path returns the agent and clears error.
            return fleet_manager_pb2.GetAgentResponse(agent=agent, error="")
        except Exception as e:
            # Unexpected failures become INTERNAL with error payload.
            logger.error(f"Error getting agent: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Failed to get agent: {str(e)}")
            return fleet_manager_pb2.GetAgentResponse(error=f"Failed to get agent: {str(e)}")

    async def GetAgentStatus(self, request, context):
        """
        Get the status of an agent.

        Derives a coarse status from registry data: RUNNING if a container_id
        is present, otherwise REGISTERED. Unknown/not-found uses UNKNOWN.

        Args:
            request: ``GetAgentStatusRequest`` with agent_id.
            context: gRPC context for NOT_FOUND / INTERNAL.

        Returns:
            ``AgentStatus`` message with state enum and message string.
        """
        # Log which agent's status is requested.
        logger.info(f"Getting status for agent: {request.agent_id}")
        try:
            # Get agent from registry to inspect container/status fields.
            agent = await self.registry.get_agent(request.agent_id)
            if not agent:
                # Missing agent → NOT_FOUND + UNKNOWN state payload.
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Agent with ID {request.agent_id} not found")
                return fleet_manager_pb2.AgentStatus(
                    state=fleet_manager_pb2.AgentStatus.State.UNKNOWN,
                    message=f"Agent with ID {request.agent_id} not found"
                )

            # Default: registered but not necessarily container-running.
            status_state = fleet_manager_pb2.AgentStatus.State.REGISTERED
            status_message = f"Agent {request.agent_id} is registered"

            # Elevate to RUNNING when container metadata includes an id.
            if agent.HasField('container') and agent.container.container_id:
                status_state = fleet_manager_pb2.AgentStatus.State.RUNNING
                status_message = f"Agent {request.agent_id} container is running"

            # Create and return AgentStatus with derived state/message.
            return fleet_manager_pb2.AgentStatus(
                state=status_state,
                message=status_message
            )

        except Exception as e:
            # Unexpected errors map to UNKNOWN with error text.
            logger.error(f"Error getting agent status: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Failed to get agent status: {str(e)}")
            return fleet_manager_pb2.AgentStatus(
                state=fleet_manager_pb2.AgentStatus.State.UNKNOWN,
                message=f"Error: {str(e)}"
            )

    async def CreateGoal(self, request, context):
        """
        Create a new goal from a free-text description.

        Goals are the inputs to planners (CreatePlan requires goal_ids unless
        MANUAL_PLAN).

        Args:
            request: ``CreateGoalRequest`` with description.
            context: gRPC context for INTERNAL errors.

        Returns:
            ``CreateGoalResponse`` with the created goal or error.
        """
        # Log the goal description being created.
        logger.info(f"Creating new goal: {request.description}")
        try:
            # Create goal using registry persistence.
            goal = await self.registry.create_goal(
                description=request.description
            )

            # Registry failure → INTERNAL without a goal payload.
            if not goal:
                context.set_code(grpc.StatusCode.INTERNAL)
                context.set_details("Failed to create goal")
                return fleet_manager_pb2.CreateGoalResponse(
                    error="Failed to create goal"
                )

            # Log the assigned goal_id for correlation.
            logger.info(f"Successfully created goal: {goal.goal_id}")
            return fleet_manager_pb2.CreateGoalResponse(
                goal=goal
            )

        except Exception as e:
            # Unexpected create failures.
            logger.error(f"Error creating goal: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Failed to create goal: {str(e)}")
            return fleet_manager_pb2.CreateGoalResponse(
                error=f"Error: {str(e)}"
            )

    async def GetGoal(self, request, context):
        """
        Get a specific goal by ID.

        Args:
            request: ``GetGoalRequest`` with goal_id.
            context: gRPC context for NOT_FOUND / INTERNAL.

        Returns:
            ``GetGoalResponse`` with goal or error.
        """
        # Log the goal id being fetched.
        logger.info(f"Getting goal: {request.goal_id}")
        try:
            # Get goal from registry by primary key.
            goal = await self.registry.get_goal(request.goal_id)

            if not goal:
                # Missing goal → NOT_FOUND.
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Goal with ID {request.goal_id} not found")
                return fleet_manager_pb2.GetGoalResponse(
                    error=f"Goal with ID {request.goal_id} not found"
                )

            # Success path.
            logger.info(f"Successfully retrieved goal: {request.goal_id}")
            return fleet_manager_pb2.GetGoalResponse(
                goal=goal
            )

        except Exception as e:
            # Unexpected get failures.
            logger.error(f"Error getting goal: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Failed to get goal: {str(e)}")
            return fleet_manager_pb2.GetGoalResponse(
                error=f"Error: {str(e)}"
            )

    async def ListGoals(self, request, context):
        """
        List all goals currently stored in the registry.

        Args:
            request: ``ListGoalsRequest`` (no filters today).
            context: gRPC context for INTERNAL errors.

        Returns:
            ``ListGoalsResponse`` with goals or error.
        """
        # Announce list operation.
        logger.info("Listing goals")
        try:
            # Get goals from registry (full table scan of goals).
            goals = await self.registry.list_goals()

            # Log cardinality for operators.
            logger.info(f"Found {len(goals)} goals")
            return fleet_manager_pb2.ListGoalsResponse(
                goals=goals
            )

        except Exception as e:
            # Unexpected list failures.
            logger.error(f"Error listing goals: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Failed to list goals: {str(e)}")
            return fleet_manager_pb2.ListGoalsResponse(
                error=f"Error: {str(e)}"
            )

    async def DeleteGoal(self, request, context):
        """
        Delete a goal by ID, returning the deleted goal snapshot.

        Args:
            request: ``DeleteGoalRequest`` with goal_id.
            context: gRPC context for NOT_FOUND / INTERNAL.

        Returns:
            ``DeleteGoalResponse`` with deleted goal or error.
        """
        # Log which goal is being deleted.
        logger.info(f"Deleting goal: {request.goal_id}")
        try:
            # Get goal first to return it in the response after delete.
            goal = await self.registry.get_goal(request.goal_id)

            if not goal:
                # Cannot delete a missing goal.
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Goal with ID {request.goal_id} not found")
                return fleet_manager_pb2.DeleteGoalResponse(
                    error=f"Goal with ID {request.goal_id} not found"
                )

            # Delete goal from durable storage.
            success = await self.registry.delete_goal(request.goal_id)

            if not success:
                # Registry reported delete failure.
                context.set_code(grpc.StatusCode.INTERNAL)
                context.set_details(f"Failed to delete goal {request.goal_id}")
                return fleet_manager_pb2.DeleteGoalResponse(
                    error=f"Failed to delete goal {request.goal_id}"
                )

            # Success: return the pre-delete snapshot.
            logger.info(f"Successfully deleted goal: {request.goal_id}")
            return fleet_manager_pb2.DeleteGoalResponse(
                goal=goal
            )

        except Exception as e:
            # Unexpected delete failures.
            logger.error(f"Error deleting goal: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Failed to delete goal: {str(e)}")
            return fleet_manager_pb2.DeleteGoalResponse(
                error=f"Error: {str(e)}"
            )

    async def CreateTask(self, request, context):
        """
        Create a new task, optionally linked to agent/goal/plan.

        If ``agent_id`` is set without ``agent_type``, infers type from the
        registered agent. When ``plan_id`` is set, marks that plan as manual
        because the operator mutated the task graph directly.

        Args:
            request: ``CreateTaskRequest`` with description and optional links.
            context: gRPC context for INTERNAL errors.

        Returns:
            ``CreateTaskResponse`` with task or error.
        """
        # Log the human description for the new task.
        logger.info(f"Creating new task: {request.description}")
        try:
            # Extra debug dump of the full request proto.
            logger.info(f"Creating new task DEBUG: {request}")
            # Prefer explicit agent_type; may infer from agent_id below.
            agent_type = request.agent_type if request.agent_type else None
            if request.agent_id and not agent_type:
                # Look up the agent to copy its agent_type onto the task.
                agent = await self.registry.get_agent(request.agent_id)
                if agent:
                    agent_type = agent.agent_type
            # Create task using registry persistence helpers.
            task = await self.registry.create_task(
                description=request.description,
                agent_id=request.agent_id if request.agent_id else None,
                goal_id=request.goal_id if request.goal_id else None,
                plan_id=request.plan_id if request.plan_id else None,
                agent_type=agent_type,
                dependency_task_ids=list(request.dependency_task_ids) if request.dependency_task_ids else None
            )

            # Registry failure → INTERNAL.
            if not task:
                context.set_code(grpc.StatusCode.INTERNAL)
                context.set_details("Failed to create task")
                return fleet_manager_pb2.CreateTaskResponse(
                    error="Failed to create task"
                )

            # Any task mutation should mark the plan as manual (strategy recomputation happens server-side)
            if request.plan_id:
                await self._mark_plan_manual(int(request.plan_id))

            # Log success and notify Gateway of the new pending task.
            logger.info(f"Successfully created task: {task.task_id}")
            emit_task_changed(task.task_id, plan_id=request.plan_id or None, status="pending")
            return fleet_manager_pb2.CreateTaskResponse(
                task=task
            )

        except Exception as e:
            # Unexpected create failures.
            logger.error(f"Error creating task: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Failed to create task: {str(e)}")
            return fleet_manager_pb2.CreateTaskResponse(
                error=f"Error: {str(e)}"
            )

    async def UpdateTask(self, request, context):
        """
        Update fields of an existing task.

        Supports optional description, goal_id, agent_id (empty string clears
        assignment), and dependency_task_ids when the update flag is set.
        Always re-marks the owning plan as manual after a successful update.

        Args:
            request: ``UpdateTaskRequest`` with task_id and optional fields.
            context: gRPC context for NOT_FOUND / INTERNAL.

        Returns:
            ``UpdateTaskResponse`` with updated task or error.
        """
        # Log which task is being patched.
        logger.info(f"Updating task: {request.task_id}")
        try:
            # Load existing task to verify presence and discover plan_id.
            existing = await self.registry.get_task(request.task_id)
            if not existing:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Task with ID {request.task_id} not found")
                return fleet_manager_pb2.UpdateTaskResponse(
                    error=f"Task with ID {request.task_id} not found"
                )

            # Accumulate only fields that were explicitly present on the request.
            update_kwargs: Dict[str, object] = {}

            # Optional description patch via protobuf HasField.
            if hasattr(request, "HasField") and request.HasField("description"):
                update_kwargs["description"] = request.description

            # Optional goal_id patch.
            if hasattr(request, "HasField") and request.HasField("goal_id"):
                update_kwargs["goal_id"] = int(request.goal_id)

            # Optional agent_id patch (empty string clears assignment + type).
            if hasattr(request, "HasField") and request.HasField("agent_id"):
                # If present and empty string, clear assignment
                if request.agent_id == "":
                    update_kwargs["agent_id"] = None
                    update_kwargs["agent_type"] = None
                else:
                    update_kwargs["agent_id"] = request.agent_id
                    # Infer agent_type from agent_id (so DAG/UI can render it)
                    agent = await self.registry.get_agent(request.agent_id)
                    if agent:
                        update_kwargs["agent_type"] = agent.agent_type

            # Replace dependency list only when the update flag is true.
            if request.update_dependency_task_ids:
                update_kwargs["dependency_task_ids"] = list(request.dependency_task_ids)

            # Persist the partial update via the registry.
            updated_task = await self.registry.update_task(request.task_id, **update_kwargs)
            if not updated_task:
                context.set_code(grpc.StatusCode.INTERNAL)
                context.set_details(f"Failed to update task with ID {request.task_id}")
                return fleet_manager_pb2.UpdateTaskResponse(
                    error=f"Failed to update task with ID {request.task_id}"
                )

            # Recompute manual strategies on the owning plan if any.
            plan_id = int(getattr(existing, "plan_id", 0) or 0)
            if plan_id:
                await self._mark_plan_manual(plan_id)

            # Notify Gateway and return the updated task proto.
            logger.info(f"Successfully updated task: {request.task_id}")
            emit_task_changed(request.task_id, plan_id=plan_id or None, status="updated")
            return fleet_manager_pb2.UpdateTaskResponse(task=updated_task)

        except Exception as e:
            # Unexpected update failures.
            logger.error(f"Error updating task: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Failed to update task: {str(e)}")
            return fleet_manager_pb2.UpdateTaskResponse(
                error=f"Error: {str(e)}"
            )

    async def GetTask(self, request, context):
        """
        Get a specific task by ID.

        Args:
            request: ``GetTaskRequest`` with task_id.
            context: gRPC context for NOT_FOUND / INTERNAL.

        Returns:
            ``GetTaskResponse`` with task or error.
        """
        # Log the task id being fetched.
        logger.info(f"Getting task: {request.task_id}")
        try:
            # Get task from registry by primary key.
            task = await self.registry.get_task(request.task_id)

            if not task:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Task with ID {request.task_id} not found")
                return fleet_manager_pb2.GetTaskResponse(
                    error=f"Task with ID {request.task_id} not found"
                )

            # Success path.
            logger.info(f"Successfully retrieved task: {request.task_id}")
            return fleet_manager_pb2.GetTaskResponse(
                task=task
            )

        except Exception as e:
            # Unexpected get failures.
            logger.error(f"Error getting task: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Failed to get task: {str(e)}")
            return fleet_manager_pb2.GetTaskResponse(
                error=f"Error: {str(e)}"
            )

    async def ListTasks(self, request, context):
        """
        List tasks with optional filtering by plan, goal, and/or agent ids.

        Args:
            request: ``ListTasksRequest`` with optional repeated filter ids.
            context: gRPC context for INTERNAL errors.

        Returns:
            ``ListTasksResponse`` with tasks (empty list on error) and error.
        """
        # Log the filter sets for debugging list queries.
        logger.info(f"Listing tasks with filters: plan_ids={request.plan_ids}, goal_ids={request.goal_ids}, agent_ids={request.agent_ids}")

        try:
            # Pass None for empty repeated fields so registry skips those filters.
            tasks = await self.registry.list_tasks(
                plan_ids=list(request.plan_ids) if request.plan_ids else None,
                goal_ids=list(request.goal_ids) if request.goal_ids else None,
                agent_ids=list(request.agent_ids) if request.agent_ids else None
            )

            return fleet_manager_pb2.ListTasksResponse(
                tasks=tasks
            )
        except Exception as e:
            # On failure return empty tasks plus error string.
            logger.error(f"Error listing tasks: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Failed to list tasks: {str(e)}")
            return fleet_manager_pb2.ListTasksResponse(
                tasks=[],
                error=f"Error: {str(e)}"
            )

    async def DeleteTask(self, request, context):
        """
        Delete a task by ID and fix up dependent tasks.

        The registry returns updated dependent task ids (dependencies rewritten)
        and the owning plan_id so we can mark the plan manual afterward.

        Args:
            request: ``DeleteTaskRequest`` with task_id.
            context: gRPC context for NOT_FOUND / INTERNAL.

        Returns:
            ``DeleteTaskResponse`` with success flag and updated_task_ids.
        """
        # Log which task is being deleted.
        logger.info(f"Deleting task: {request.task_id}")

        try:
            # delete_task also rewrites dependents and reports plan_id.
            success, updated_task_ids, plan_id = await self.registry.delete_task(request.task_id)
            if not success:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Task with ID {request.task_id} not found")
                return fleet_manager_pb2.DeleteTaskResponse(
                    success=False,
                    deleted_task_id=request.task_id,
                    updated_task_ids=[],
                    error=f"Task with ID {request.task_id} not found",
                )

            # Any task mutation should mark the plan as manual (strategy recomputation happens server-side)
            if plan_id is not None:
                await self._mark_plan_manual(plan_id)

            # Log dependents that were rewritten after the delete.
            logger.info(f"Successfully deleted task: {request.task_id}, updated dependents: {updated_task_ids}")
            emit_task_changed(request.task_id, plan_id=plan_id, status="deleted")
            return fleet_manager_pb2.DeleteTaskResponse(
                success=True,
                deleted_task_id=request.task_id,
                updated_task_ids=updated_task_ids,
                error="",
            )

        except Exception as e:
            # Unexpected delete failures.
            logger.error(f"Error deleting task: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Failed to delete task: {str(e)}")
            return fleet_manager_pb2.DeleteTaskResponse(
                success=False,
                deleted_task_id=request.task_id,
                updated_task_ids=[],
                error=f"Error: {str(e)}",
            )

    async def CreatePlan(self, request, context):
        """
        Create a new plan via manual shell, test bypass, or planner+allocator.

        Flow:
          1. MANUAL_PLAN → empty plan shell (no LLM), emit created, return.
          2. Auto-plan requires at least one goal_id (else INVALID_ARGUMENT).
          3. If TESTING env is truthy → empty plan without planner (tests).
          4. Else SDK ``get_planning_strategy(strategy).plan(goal_ids)`` then
             SDK ``Planner.create_plan(...)``.
          5. If allocation_strategy != NONE → SDK ``Allocator.allocate``.
          6. Return the fully loaded plan proto.

        Planners: monolithic (sequential), DAG (per-goal graphs), big_dag
        (cross-goal graph). Allocators: lp, llm, cost_based.

        Args:
            request: ``CreatePlanRequest`` with strategies, goals, name/desc.
            context: gRPC context for INVALID_ARGUMENT / INTERNAL.

        Returns:
            ``CreatePlanResponse`` with plan or error.
        """
        try:
            # Get the requested planning strategy and allocation strategy
            # These are already enum objects from protobuf deserialization
            planning_strategy = request.planning_strategy
            allocation_strategy = request.allocation_strategy
            # Materialize repeated goal ids into a plain Python list.
            goal_ids = list(request.goal_ids) if request.goal_ids else []
            # Optional human metadata for the plan record.
            name = request.name
            description = request.description

            # MANUAL strategy: create empty plan shell for user-defined tasks
            if planning_strategy == fleet_manager_pb2.PlanningStrategy.MANUAL_PLAN:
                logger.info("Creating manual plan shell (no auto-planning)")
                plan = await self.registry.create_plan(
                    planning_strategy=planning_strategy,
                    allocation_strategy=allocation_strategy,
                    goal_ids=goal_ids,
                    task_ids=[],
                    name=name,
                    description=description
                )
                emit_plan_changed(plan.plan_id, status="created")
                return fleet_manager_pb2.CreatePlanResponse(plan=plan)

            # Auto-planning requires goals
            if not goal_ids:
                context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                context.set_details("At least one goal ID must be provided for auto-planning")
                return fleet_manager_pb2.CreatePlanResponse(
                    error="At least one goal ID must be provided for auto-planning"
                )

            # For testing environments, create a plan directly without using the planner
            test_mode = os.getenv("TESTING", "false").lower() in ("true", "1", "yes")
            if test_mode:
                logger.info("Running in test mode, bypassing planner")
                plan = await self.registry.create_plan(
                    planning_strategy=planning_strategy,
                    allocation_strategy=allocation_strategy,
                    goal_ids=goal_ids,
                    task_ids=[],
                    name=name,
                    description=description
                )
                emit_plan_changed(plan.plan_id, status="created")
                return fleet_manager_pb2.CreatePlanResponse(plan=plan)

            # Strategy implementations are SDK-owned; this service only
            # orchestrates RPC, persistence, eventing, and execution.
            planner = get_planning_strategy(planning_strategy, self.registry)

            # Generate plan using the planner
            try:
                logger.info(f"Generating plan for goals {goal_ids} using {planning_strategy} planner")
                graph = await planner.plan(goal_ids)

                # Debug: Check what the planner has stored for artifacts/prompts.
                logger.debug("PLANNER DEBUG: planning_prompts = %s", getattr(planner, 'planning_prompts', 'NOT SET'))
                logger.debug("PLANNER DEBUG: planning_artifacts = %s", getattr(planner, 'planning_artifacts', 'NOT SET'))
                logger.debug("PLANNER DEBUG: server_logs = %s", getattr(planner, 'server_logs', 'NOT SET'))

                # Collect server logs from planner (fallback synthetic line).
                server_logs = getattr(planner, 'server_logs', [])
                if not server_logs:
                    server_logs = [f"Planning completed successfully for goals {goal_ids} using {planning_strategy} strategy"]

                # Persist the canonical DAG using SDK two-pass materialization.
                plan_id = await planner.persist_dag(
                    graph,
                    planning_strategy=planning_strategy,
                    allocation_strategy=allocation_strategy,
                    goal_ids=goal_ids,
                    name=name,
                    description=description,
                )
                logger.info(f"Successfully created and saved plan {plan_id}")
            except Exception as e:
                # Planner failures surface as INTERNAL CreatePlan errors.
                logger.error(f"Error during planning: {str(e)}")
                context.set_code(grpc.StatusCode.INTERNAL)
                context.set_details(f"Planning failed: {str(e)}")
                return fleet_manager_pb2.CreatePlanResponse(
                    error=f"Planning failed: {str(e)}"
                )

            # Allocate tasks if allocation strategy is not NONE
            if allocation_strategy != fleet_manager_pb2.AllocationStrategy.NONE:
                allocator = get_allocator(allocation_strategy, registry=self.registry)
                allocation = await allocator.allocate(plan_id)
                logger.info("Task allocation complete: %s", allocation)

                # Store allocation artifacts in the plan for UI/debug replay.
                await self.registry.update_plan(
                    plan_id,
                    allocation_prompts=getattr(allocator, 'allocation_prompts', {}),
                    allocation_artifacts=getattr(allocator, 'allocation_artifacts', {}),
                    server_logs=getattr(allocator, 'server_logs', [])
                )
            else:
                # Operator chose to assign agents manually later.
                logger.info("Skipping allocation (strategy=NONE)")

            # Get the plan with all tasks embedded for the response.
            plan = await self.registry.get_plan(plan_id)
            logger.debug("Retrieved plan: %s", plan)

            logger.info(f"Successfully created plan: {plan_id}")
            emit_plan_changed(plan_id, status="created")
            response = fleet_manager_pb2.CreatePlanResponse(plan=plan)
            logger.debug("Created response: %s", response)
            return response

        except Exception as e:
            # Outer catch for unexpected CreatePlan failures (with traceback).
            logger.debug("Exception in gRPC CreatePlan: %s", e)
            import traceback
            logger.debug("Traceback: %s", traceback.format_exc())
            logger.error(f"Error creating plan: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Failed to create plan: {str(e)}")
            return fleet_manager_pb2.CreatePlanResponse(
                error=f"Error: {str(e)}"
            )

    async def AllocatePlan(self, request, context):
        """
        Allocate agents to tasks in an existing plan.

        Used when a plan was created with allocation_strategy=NONE or when
        re-running allocation with a different strategy. Requires the plan to
        exist and to already contain tasks.

        Args:
            request: ``AllocatePlanRequest`` with plan_id + allocation_strategy.
            context: gRPC context for NOT_FOUND / FAILED_PRECONDITION / INTERNAL.

        Returns:
            ``AllocatePlanResponse`` with updated plan or error.
        """
        # Log plan id and requested allocation strategy enum.
        logger.info(f"Allocating plan {request.plan_id} with strategy: {request.allocation_strategy}")
        try:
            plan_id = request.plan_id
            allocation_strategy = request.allocation_strategy

            # Check plan exists before attempting allocation.
            plan = await self.registry.get_plan(plan_id)
            if not plan:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Plan {plan_id} not found")
                return fleet_manager_pb2.AllocatePlanResponse(
                    error=f"Plan {plan_id} not found"
                )

            # Check there are tasks to allocate (empty plans cannot allocate).
            if not plan.task_ids:
                context.set_code(grpc.StatusCode.FAILED_PRECONDITION)
                context.set_details(f"Plan {plan_id} has no tasks to allocate")
                return fleet_manager_pb2.AllocatePlanResponse(
                    error=f"Plan {plan_id} has no tasks to allocate"
                )

            # Allocation strategies and persistence protocol are SDK-owned.
            allocator = get_allocator(allocation_strategy, registry=self.registry)
            allocation = await allocator.allocate(plan_id)
            logger.info(f"Allocation complete for plan {plan_id}: {allocation}")

            # Update plan's allocation strategy and allocation data in DB
            await self.registry.update_plan(
                plan_id=plan_id,
                allocation_strategy=allocation_strategy,
                allocation_prompts=getattr(allocator, 'allocation_prompts', None),
                allocation_artifacts=getattr(allocator, 'allocation_artifacts', None)
            )

            # Get updated plan (includes newly assigned agent_ids on tasks).
            updated_plan = await self.registry.get_plan(plan_id)

            return fleet_manager_pb2.AllocatePlanResponse(plan=updated_plan)

        except Exception as e:
            # Unexpected allocation failures.
            logger.error(f"Error allocating plan: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Failed to allocate plan: {str(e)}")
            return fleet_manager_pb2.AllocatePlanResponse(
                error=f"Error: {str(e)}"
            )

    async def GetPlan(self, request, context):
        """
        Get a specific plan by ID.

        Args:
            request: ``GetPlanRequest`` with plan_id.
            context: gRPC context for NOT_FOUND / INTERNAL.

        Returns:
            ``GetPlanResponse`` with plan or error.
        """
        # Log the plan id being fetched.
        logger.info(f"Getting plan: {request.plan_id}")
        try:
            # Get plan from registry (includes task_ids and strategies).
            plan = await self.registry.get_plan(request.plan_id)

            if not plan:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Plan with ID {request.plan_id} not found")
                return fleet_manager_pb2.GetPlanResponse(
                    error=f"Plan with ID {request.plan_id} not found"
                )

            # Success path.
            logger.info(f"Successfully retrieved plan: {request.plan_id}")
            return fleet_manager_pb2.GetPlanResponse(
                plan=plan
            )

        except Exception as e:
            # Unexpected get failures.
            logger.error(f"Error getting plan: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Failed to get plan: {str(e)}")
            return fleet_manager_pb2.GetPlanResponse(
                error=f"Error: {str(e)}"
            )

    async def ListPlans(self, request, context):
        """
        List all plans in the registry.

        Args:
            request: ``ListPlansRequest`` (no filters today).
            context: gRPC context for INTERNAL errors.

        Returns:
            ``ListPlansResponse`` with plans or error.
        """
        # Announce list operation.
        logger.info("Listing plans")
        try:
            # Get plans from registry.
            plans = await self.registry.list_plans()

            # Log cardinality.
            logger.info(f"Found {len(plans)} plans")
            return fleet_manager_pb2.ListPlansResponse(
                plans=plans
            )

        except Exception as e:
            # Unexpected list failures.
            logger.error(f"Error listing plans: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Failed to list plans: {str(e)}")
            return fleet_manager_pb2.ListPlansResponse(
                error=f"Error: {str(e)}"
            )

    async def DeletePlan(self, request, context):
        """
        Delete a plan by ID, returning the deleted plan snapshot.

        Args:
            request: ``DeletePlanRequest`` with plan_id.
            context: gRPC context for NOT_FOUND / INTERNAL.

        Returns:
            ``DeletePlanResponse`` with deleted plan or error.
        """
        # Log which plan is being deleted.
        logger.info(f"Deleting plan: {request.plan_id}")
        try:
            # Get plan first to return it in the response after delete.
            plan = await self.registry.get_plan(request.plan_id)

            if not plan:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Plan with ID {request.plan_id} not found")
                return fleet_manager_pb2.DeletePlanResponse(
                    error=f"Plan with ID {request.plan_id} not found"
                )

            # Delete plan (and associated rows per registry semantics).
            success = await self.registry.delete_plan(request.plan_id)

            if not success:
                context.set_code(grpc.StatusCode.INTERNAL)
                context.set_details(f"Failed to delete plan {request.plan_id}")
                return fleet_manager_pb2.DeletePlanResponse(
                    error=f"Failed to delete plan {request.plan_id}"
                )

            # Notify Gateway and return pre-delete snapshot.
            logger.info(f"Successfully deleted plan: {request.plan_id}")
            emit_plan_changed(request.plan_id, status="deleted")
            return fleet_manager_pb2.DeletePlanResponse(
                plan=plan
            )

        except Exception as e:
            # Unexpected delete failures.
            logger.error(f"Error deleting plan: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Failed to delete plan: {str(e)}")
            return fleet_manager_pb2.DeletePlanResponse(
                error=f"Error: {str(e)}"
            )

    async def StartPlan(
        self, request: fleet_manager_pb2.StartPlanRequest, context
    ) -> fleet_manager_pb2.StartPlanResponse:
        """
        Start executing a plan asynchronously via ``Executor``.

        IMPORTANT: Only fully allocated plans can be executed. A plan is
        executable if and only if ALL tasks have an agent_id assigned. This
        invariant distinguishes an ExecutablePlan from an UnallocatedPlan.
        Partial allocation returns FAILED_PRECONDITION with details.

        The RPC returns immediately after spawning ``executor.execute()`` as
        an asyncio Task; progress is tracked via plan/task status + events.

        Args:
            request: ``StartPlanRequest`` with plan_id.
            context: gRPC context for NOT_FOUND / FAILED_PRECONDITION / INTERNAL.

        Returns:
            ``StartPlanResponse`` with empty error on accept, else error text.
        """
        # Lazy import to avoid circular imports with executor package.
        from packages.fleet_sdk.src.executor.executor import Executor
        plan_id = request.plan_id
        logger.info(f"Received StartPlan request for plan_id: {plan_id}")

        try:
            # Step 1: Verify plan exists
            plan = await self.registry.get_plan(plan_id)
            if not plan:
                error_msg = f"Plan {plan_id} not found"
                logger.error(error_msg)
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(error_msg)
                return fleet_manager_pb2.StartPlanResponse(error=error_msg)

            # Step 2: Check allocation status - CRITICAL VALIDATION
            allocation_status = await self.registry.get_plan_allocation_status(plan_id)

            if not allocation_status['is_executable']:
                # Unpack diagnostic fields for a precise error message.
                status = allocation_status['status']
                total = allocation_status['total_tasks']
                allocated = allocation_status['allocated_tasks']
                unallocated_ids = allocation_status['unallocated_task_ids']

                if status == 'empty':
                    error_msg = f"Plan {plan_id} has no tasks. Cannot execute an empty plan."
                elif status == 'unallocated':
                    error_msg = (
                        f"Plan {plan_id} is UNALLOCATED. "
                        f"All {total} tasks need agent assignments before execution. "
                        f"Run allocation first using the 'allocate' command or API."
                    )
                elif status == 'partially_allocated':
                    error_msg = (
                        f"Plan {plan_id} is PARTIALLY ALLOCATED ({allocated}/{total} tasks assigned). "
                        f"Tasks without agents: {unallocated_ids}. "
                        f"All tasks must have agent assignments before execution."
                    )
                else:
                    error_msg = f"Plan {plan_id} is not executable (status: {status})"

                # Reject start until allocation is complete.
                logger.error(error_msg)
                context.set_code(grpc.StatusCode.FAILED_PRECONDITION)
                context.set_details(error_msg)
                return fleet_manager_pb2.StartPlanResponse(error=error_msg)

            # Step 3: Plan is executable - proceed with execution
            logger.info(f"Plan {plan_id} is fully allocated ({allocation_status['total_tasks']} tasks). Starting execution...")

            # Start execution asynchronously in the background
            # The executor will handle updating plan status to executing and completed
            executor = Executor(plan_id=plan_id, registry=self.registry)
            asyncio.create_task(executor.execute())

            # Return immediately - execution will continue in background
            return fleet_manager_pb2.StartPlanResponse(error="")

        except Exception as e:
            # Unexpected start failures include traceback in logs.
            error_msg = f"Failed to start plan {plan_id}: {e}"
            logger.error(error_msg, exc_info=True)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(error_msg)
            return fleet_manager_pb2.StartPlanResponse(error=error_msg)


async def serve(port: int = GRPC_SERVER_PORT, db_url: str = None, reset_db: bool = False, verbose: bool = False, sql_debug: bool = False):
    """
    Start the Fleet Manager gRPC aio server and block until termination.

    Steps:
      1. configure_logging(verbose, sql_debug)
      2. Resolve db_url (argument or DATABASE_URL default)
      3. Construct grpc.aio.server + FleetManagerService
      4. Optionally drop_all tables when reset_db is True
      5. initialize() to create schema
      6. Log public SQL table names for operator visibility
      7. Register servicer, bind insecure ``[::]:port``, start, wait
      8. finally: service.cleanup() disposes the DB engine

    Args:
        port: Port to listen on (dual-stack via ``[::]``).
        db_url: PostgreSQL connection URL. If None, uses default connection.
        reset_db: If True, drops and recreates all database tables on startup.
        verbose: If True, enables detailed application logging.
        sql_debug: If True, enables SQL debug logging.
    """
    # Configure logging based on verbose and sql_debug flags
    configure_logging(verbose, sql_debug)

    # Fall back to packages.config.DATABASE_URL when caller omitted db_url.
    if not db_url:
        db_url = DATABASE_URL
    logger.info("Using database: %s", db_url)

    # Create the service first (registry bound to db_url).
    logger.info("Creating service...")
    # aio server with a small thread pool for sync callbacks if any.
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
    service = FleetManagerService(db_url)

    # Initialize the database with reset flag (destructive).
    if reset_db:
        logger.info("Resetting database tables...")
        async with service.registry.engine.begin() as conn:
            # Drop every table known to the ORM Base metadata.
            await conn.run_sync(Base.metadata.drop_all)
            logger.info("All tables dropped successfully")

    # Initialize/create tables using the service's registry.
    logger.info("Creating database tables...")
    await service.initialize()
    logger.info("Database initialization complete")

    # Print all available SQL tables for operator confirmation.
    async with service.registry.engine.connect() as conn:
        result = await conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'"))
        tables = result.fetchall()
        logger.info("Available SQL tables:")
        for table in tables:
            logger.info("- %s", table[0])

    # Wire the FleetManagerService implementation into the gRPC server.
    fleet_manager_pb2_grpc.add_FleetManagerServicer_to_server(service, server)
    # Bind insecure port on all interfaces (IPv6 dual-stack form).
    server.add_insecure_port(f'[::]:{port}')
    logger.info("Fleet Manager Server is now serving on port %s", port)

    try:
        # Start accepting RPCs and block until termination/cancellation.
        await server.start()
        await server.wait_for_termination()
    finally:
        # Clean up resources even when cancelled by __main__ stop_event.
        await service.cleanup()
