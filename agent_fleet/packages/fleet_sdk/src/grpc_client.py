"""Fleet Manager gRPC client for the agent_fleet control plane.

Wraps the generated ``FleetManagerStub`` from ``packages.proto`` behind a
small synchronous Python API used by the Gateway BFF, CLIs, and scripts.
Every method builds the matching ``fleet_manager_pb2`` request message and
delegates to the stub — no business logic lives here.

Default target address comes from ``packages.config.GRPC_SERVER_ADDRESS``
(host:port of fleet_server). The channel is insecure by default for local
and Compose deployments; production TLS would replace ``insecure_channel``.
"""

# grpc provides the insecure channel used to reach fleet_server.
import grpc
# Optional/List for optional request fields and repeated ids.
from typing import Optional, List

# Generated request/response/message types for the FleetManager service.
from packages.proto import fleet_manager_pb2
# Generated FleetManagerStub with one RPC method per service rpc.
from packages.proto import fleet_manager_pb2_grpc
# Shared host:port default for the fleet control-plane gRPC server.
from packages.config import GRPC_SERVER_ADDRESS


class FleetManagerClient:
    """Synchronous client for every FleetManager control-plane RPC.

    Use as a context manager to ensure the channel is closed::

        # Hold ``FleetManagerClient()`` for the duration of the indented block.
        with FleetManagerClient() as client:
            # Call ``client.list_agents``.
            client.list_agents()
    """

    def __init__(self, server_address: str = GRPC_SERVER_ADDRESS):
        """Open an insecure channel and bind the FleetManager stub.

        Parameters
        ----------
        server_address:
            ``host:port`` of fleet_server (defaults to config).
        """
        # Plaintext channel — sufficient for localhost / Compose networks.
        self.channel = grpc.insecure_channel(server_address)
        # Stub exposes RegisterAgent, CreatePlan, StartPlan, etc.
        self.stub = fleet_manager_pb2_grpc.FleetManagerStub(self.channel)

    def close(self):
        """Close the underlying gRPC channel."""
        self.channel.close()

    def __enter__(self):
        """Return self so ``with FleetManagerClient() as c`` works."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Always close the channel; never suppress exceptions."""
        self.close()
        # Hand ``False`` back to the caller.
        return False

    def register_agent(
        self,
        agent_id: str,
        agent_type: str,
        description: str,
        capabilities: list,
        task_server_host: str,
        task_server_port: int,
        docker_host: str = "",
        docker_port: int = 0,
        container_image: str = "",
        container_env: Optional[dict] = None,
    ):
        """Register agent metadata (task server + optional Docker deploy config).

        Persists the agent in the control-plane registry so it can later be
        deployed, listed, and assigned to tasks.
        """
        # Where the agent's HTTP task server listens for work.
        task_server_info = fleet_manager_pb2.TaskServerInfo(host=task_server_host, port=task_server_port)
        # Docker daemon endpoint used by DeployAgent when non-empty.
        deployment_info = fleet_manager_pb2.DeploymentInfo(docker_host=docker_host, docker_port=docker_port)
        # Image + env used when the control plane starts the container.
        container_config = fleet_manager_pb2.ContainerConfig(image=container_image, environment=container_env or {})
        # Assemble the full registration request.
        request = fleet_manager_pb2.RegisterAgentRequest(
            # Local ``agent_id`` ← agent_id,.
            agent_id=agent_id,
            # Local ``agent_type`` ← agent_type,.
            agent_type=agent_type,
            # Local ``description`` ← description,.
            description=description,
            # Local ``capabilities`` ← capabilities,.
            capabilities=capabilities,
            # Local ``task_server_info`` ← task_server_info,.
            task_server_info=task_server_info,
            # Local ``deployment`` ← deployment_info,.
            deployment=deployment_info,
            # Local ``container`` ← container_config,.
            container=container_config,
        )
        # Unary RPC → RegisterAgentResponse.
        return self.stub.RegisterAgent(request)

    def unregister_agent(self, agent_id: str):
        """Remove agent metadata from the registry by id."""
        return self.stub.UnregisterAgent(fleet_manager_pb2.UnregisterAgentRequest(agent_id=agent_id))

    def list_agents(self, filter_type: str = "all"):
        """List agents filtered by ALL / DEPLOYED / REGISTERED."""
        # Map friendly strings onto the proto Filter enum.
        filter_map = {
            "all": fleet_manager_pb2.ListAgentsRequest.ALL,
            "deployed": fleet_manager_pb2.ListAgentsRequest.DEPLOYED,
            "registered": fleet_manager_pb2.ListAgentsRequest.REGISTERED,
        }
        # Local ``request`` ← fleet_manager_pb2.ListAgentsRequest(filter=filter_map.get(filter_….
        request = fleet_manager_pb2.ListAgentsRequest(filter=filter_map.get(filter_type.lower(), fleet_manager_pb2.ListAgentsRequest.ALL))
        # Hand ``self.stub.ListAgents(request)`` back to the caller.
        return self.stub.ListAgents(request)

    def get_agent(self, agent_id: str):
        """Fetch one Agent message (or error) by id."""
        return self.stub.GetAgent(fleet_manager_pb2.GetAgentRequest(agent_id=agent_id))

    def list_goals(self):
        """Return every Goal in the control plane."""
        return self.stub.ListGoals(fleet_manager_pb2.ListGoalsRequest())

    def get_goal(self, goal_id: int):
        """Fetch one Goal by numeric id."""
        return self.stub.GetGoal(fleet_manager_pb2.GetGoalRequest(goal_id=goal_id))

    def create_goal(self, description: str, task_ids: Optional[List[int]] = None):
        """Create a Goal with an optional initial task_id list."""
        return self.stub.CreateGoal(fleet_manager_pb2.CreateGoalRequest(description=description, task_ids=task_ids or []))

    def delete_goal(self, goal_id: int):
        """Delete a Goal by id."""
        return self.stub.DeleteGoal(fleet_manager_pb2.DeleteGoalRequest(goal_id=goal_id))

    def list_plans(self):
        """Return every Plan in the control plane."""
        return self.stub.ListPlans(fleet_manager_pb2.ListPlansRequest())

    def get_plan(self, plan_id: int):
        """Fetch one Plan by numeric id."""
        return self.stub.GetPlan(fleet_manager_pb2.GetPlanRequest(plan_id=plan_id))

    def create_plan(
        self,
        planning_strategy,
        goal_ids: List[int],
        allocation_strategy,
        name: str = "",
        description: str = "",
    ):
        """Create a Plan from goals using the given planning/allocation strategies."""
        request = fleet_manager_pb2.CreatePlanRequest(
            # Local ``planning_strategy`` ← planning_strategy,.
            planning_strategy=planning_strategy,
            # Local ``allocation_strategy`` ← allocation_strategy,.
            allocation_strategy=allocation_strategy,
            # Local ``goal_ids`` ← goal_ids,.
            goal_ids=goal_ids,
            # Local ``name`` ← name,.
            name=name,
            # Local ``description`` ← description,.
            description=description,
        )
        # Hand ``self.stub.CreatePlan(request)`` back to the caller.
        return self.stub.CreatePlan(request)

    def allocate_plan(self, plan_id: int, allocation_strategy):
        """Run allocation for an existing unallocated plan."""
        request = fleet_manager_pb2.AllocatePlanRequest(plan_id=plan_id, allocation_strategy=allocation_strategy)
        # Hand ``self.stub.AllocatePlan(request)`` back to the caller.
        return self.stub.AllocatePlan(request)

    def start_plan(self, plan_id: int):
        """Begin execution of an allocated plan."""
        return self.stub.StartPlan(fleet_manager_pb2.StartPlanRequest(plan_id=plan_id))

    def delete_plan(self, plan_id: int):
        """Delete a Plan by id."""
        return self.stub.DeletePlan(fleet_manager_pb2.DeletePlanRequest(plan_id=plan_id))

    def list_tasks(
        self,
        plan_ids: Optional[List[int]] = None,
        goal_ids: Optional[List[int]] = None,
        agent_ids: Optional[List[str]] = None,
    ):
        """List tasks optionally filtered by plan, goal, and/or agent ids."""
        return self.stub.ListTasks(
            fleet_manager_pb2.ListTasksRequest(
                # Local ``plan_ids`` ← plan_ids or [],.
                plan_ids=plan_ids or [],
                # Local ``goal_ids`` ← goal_ids or [],.
                goal_ids=goal_ids or [],
                # Local ``agent_ids`` ← agent_ids or [],.
                agent_ids=agent_ids or [],
            )
        )

    def get_task(self, task_id: int):
        """Fetch one Task by numeric id."""
        return self.stub.GetTask(fleet_manager_pb2.GetTaskRequest(task_id=task_id))

    def create_task(
        self,
        description: str,
        agent_id: str = "",
        agent_type: str = "",
        goal_id: Optional[int] = None,
        plan_id: Optional[int] = None,
        dependency_task_ids: Optional[List[int]] = None,
    ):
        """Create a Task; proto uses 0 for unset goal_id/plan_id."""
        request = fleet_manager_pb2.CreateTaskRequest(
            # Local ``description`` ← description,.
            description=description,
            # Local ``agent_id`` ← agent_id or "",.
            agent_id=agent_id or "",
            # Local ``agent_type`` ← agent_type or "",.
            agent_type=agent_type or "",
            # Proto3 scalars default to 0; treat None as unset/0.
            goal_id=goal_id or 0,
            # Local ``plan_id`` ← plan_id or 0,.
            plan_id=plan_id or 0,
            # Local ``dependency_task_ids`` ← dependency_task_ids or [],.
            dependency_task_ids=dependency_task_ids or [],
        )
        # Hand ``self.stub.CreateTask(request)`` back to the caller.
        return self.stub.CreateTask(request)

    def update_task(
        self,
        task_id: int,
        description: Optional[str] = None,
        goal_id: Optional[int] = None,
        agent_id: Optional[str] = None,
        dependency_task_ids: Optional[List[int]] = None,
        update_dependency_task_ids: bool = False,
    ):
        """Patch a Task; optional fields are only set when not None.

        Pass ``agent_id=""`` with the field set to clear an assignment
        (see UpdateTaskRequest comments in fleet_manager.proto). Set
        ``update_dependency_task_ids=True`` to replace the dependency list
        even when empty.
        """
        request = fleet_manager_pb2.UpdateTaskRequest(
            # Local ``task_id`` ← task_id,.
            task_id=task_id,
            # Local ``update_dependency_task_ids`` ← update_dependency_task_ids,.
            update_dependency_task_ids=update_dependency_task_ids,
            # Local ``dependency_task_ids`` ← dependency_task_ids or [],.
            dependency_task_ids=dependency_task_ids or [],
        )
        # Only populate optional proto fields when the caller provided them.
        if description is not None:
            request.description = description
        # Only when (goal_id is not None).
        if goal_id is not None:
            request.goal_id = goal_id
        # Only when (agent_id is not None).
        if agent_id is not None:
            request.agent_id = agent_id
        # Hand ``self.stub.UpdateTask(request)`` back to the caller.
        return self.stub.UpdateTask(request)

    def delete_task(self, task_id: int):
        """Delete a Task by id (may update dependent tasks server-side)."""
        return self.stub.DeleteTask(fleet_manager_pb2.DeleteTaskRequest(task_id=task_id))
