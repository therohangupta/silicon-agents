"""Async Postgres-backed registry for the fleet control plane.

``AgentInstanceRegistry`` is the persistence façade used by ``fleet_server``
# Loop: for agents, goals, plans, tasks, task executions, and metric events. It owns.
for agents, goals, plans, tasks, task executions, and metric events. It owns
the async SQLAlchemy engine/session factory, schema creation, and the CRUD
methods that the gRPC FleetManager servicer calls.

Proto messages (``fleet_manager_pb2``) are the public return types; ORM models
from ``.models`` are the storage types. Converters in ``models`` bridge the two.
The ``db_retry`` decorator retries transient DB failures while never retrying
``IntegrityError`` (permanent constraint violations).

This module is the heart of the fleet gRPC control plane's durable state —
heartbeat scanners, planners, allocators, and the Gateway all ultimately
read/write through these methods.
"""

from typing import Dict, Optional, List, Any
from google.protobuf import timestamp_pb2
import grpc

import json
import asyncio
from functools import wraps
from datetime import datetime
import logging
from google.protobuf.json_format import MessageToDict

from sqlalchemy import create_engine, Column, String, Integer, JSON, DateTime, ForeignKey, update, text
from sqlalchemy.orm import sessionmaker, relationship, selectinload, undefer
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, AsyncEngine, create_async_engine
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.attributes import flag_modified

from packages.proto import fleet_manager_pb2
from .models import (
    Base, AgentModel, TaskModel, PlanModel, GoalModel, MetricEvent, TaskExecutionModel,
    agent_model_to_proto, task_model_to_proto, plan_model_to_proto, goal_model_to_proto,
    agent_proto_to_model, task_proto_to_model, plan_proto_to_model, goal_proto_to_model,
)

# Create a logger for this module
logger = logging.getLogger(__name__)

# --- Removed Dataclasses --- 
# AgentMetadata, AgentDeployment, AgentContainer, MCPClient, and RegisteredAgent 
# are now redundant. We use AgentModel for DB (with JSON fields for complex types)
# and fleet_manager_pb2 messages (Agent, Goal, Task, Plan) for API/return types.

def configure_registry_logging(verbose: bool = False):
    """Configure logging for the registry module
    
    Args:
        verbose: If True, enables detailed logging
    """
    if verbose:
        # Log at setLevel so operators can diagnose this path.
        logger.setLevel(logging.DEBUG)
    else:
        # Log at setLevel so operators can diagnose this path.
        logger.setLevel(logging.WARNING)  # Only show warnings and errors by default

# Configure SQL logging to only show errors
for logger_name in ['sqlalchemy.engine', 'sqlalchemy.pool', 'sqlalchemy.dialects', 'sqlalchemy.orm']:
    # Call ``logging.getLogger``.
    logging.getLogger(logger_name).setLevel(logging.ERROR)

def db_retry(max_retries=3, delay=1):
    """Decorator for retrying database operations"""
    def decorator(func):
        """ `decorator` — fleet registry operation; see method body for control-plane behavior."""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            """Async `wrapper` — fleet registry operation; see method body for control-plane behavior."""
            last_error = None
            # Loop: for attempt in range(max_retries).
            for attempt in range(max_retries):
                # Try the fallible work below.
                try:
                    # Hand ``await func(*args, **kwargs)`` back to the caller.
                    return await func(*args, **kwargs)
                # On except Exception as e: recover or re-raise as appropriate.
                except Exception as e:
                    # Don't retry on integrity errors - these are permanent
                    if isinstance(e, IntegrityError):
                        raise
                    # Local ``last_error`` ← e.
                    last_error = e
                    # Only when (attempt < max_retries - 1).
                    if attempt < max_retries - 1:
                        # Await ``asyncio.sleep`` and continue once it completes.
                        await asyncio.sleep(delay)
            # Raise ``last_error`` to signal this failure mode to callers.
            raise last_error
        # Hand ``wrapper`` back to the caller.
        return wrapper
    # Hand ``decorator`` back to the caller.
    return decorator

class AgentInstanceRegistry:
    """Registry for managing agent instances using PostgreSQL as backend storage"""
    
    def __init__(self, db_url: str, engine: Optional[AsyncEngine] = None):
        """Initializes the registry with a database URL or an existing engine."""
        if engine:
            # Bind ``engine`` from engine for later use on this instance.
            self.engine = engine
        else:
            # Bind ``engine`` from create_async_engine( for later use on this instance.
            self.engine = create_async_engine(
                db_url,
                # Local ``echo`` ← False,  # Enable SQL logging for debugging.
                echo=False,  # Enable SQL logging for debugging
            )
        # Bind ``async_session_factory`` from async_sessionmaker( for later use on this instance.
        self.async_session_factory = async_sessionmaker(
            self.engine, expire_on_commit=False
        )

    async def initialize(self):
        """Initialize the database schema"""
        logger.debug("Creating tables if they don't exist...")
        
        # Hold ``self.engine.begin()`` for the duration of the indented block.
        async with self.engine.begin() as conn:
            # Await ``conn.run_sync`` and continue once it completes.
            await conn.run_sync(Base.metadata.create_all)
        
        # Log at debug so operators can diagnose this path.
        logger.debug("Database initialization complete")

    @db_retry()
    async def register_agent(
        self,
        agent_id: str,
        agent_type: str,
        description: str,
        capabilities: List[str],
        status: int = fleet_manager_pb2.AgentStatus.State.REGISTERED,
        container_info: Optional[fleet_manager_pb2.ContainerInfo] = None, # Match proto type
        deployment_info: Optional[fleet_manager_pb2.DeploymentInfo] = None, # Match proto type
        task_server_info: Optional[fleet_manager_pb2.TaskServerInfo] = None, # Renamed proto type
    ) -> Optional[fleet_manager_pb2.Agent]:
        """Register a new agent or update existing one."""
        
        # Prepare data for AgentModel (handle potential None values)
        now = datetime.now()
        # Ensure we have the correct proto message types, default to empty if None
        container_info_msg = container_info or fleet_manager_pb2.ContainerInfo()
        # Local ``deployment_info_msg`` ← deployment_info or fleet_manager_pb2.DeploymentInfo().
        deployment_info_msg = deployment_info or fleet_manager_pb2.DeploymentInfo()
        # Local ``task_server_info_msg`` ← task_server_info or fleet_manager_pb2.TaskServerInfo() # Renamed.
        task_server_info_msg = task_server_info or fleet_manager_pb2.TaskServerInfo() # Renamed

        # Convert proto messages to dictionaries for JSON storage
        container_dict = MessageToDict(container_info_msg, preserving_proto_field_name=True) if container_info_msg else {}
        # Local ``deployment_dict`` ← MessageToDict(deployment_info_msg, preserving_proto_field_name=Tr….
        deployment_dict = MessageToDict(deployment_info_msg, preserving_proto_field_name=True) if deployment_info_msg else {}
        # Local ``task_server_dict`` ← MessageToDict(task_server_info_msg, preserving_proto_field_name=T….
        task_server_dict = MessageToDict(task_server_info_msg, preserving_proto_field_name=True) if task_server_info_msg else {} # Renamed variable

        # Hold ``self.async_session_factory()`` for the duration of the indented block.
        async with self.async_session_factory() as session:
            # Hold ``session.begin()`` for the duration of the indented block.
            async with session.begin():
                # Check if agent already exists using scalar_one_or_none
                existing_agent_result = await session.execute(
                    # Call ``select``.
                    select(AgentModel)
                    # Call ``.options``.
                    .options(selectinload(AgentModel.tasks).options(undefer(TaskModel.dependency_task_ids)))
                    # Call ``.where``.
                    .where(AgentModel.agent_id == agent_id)
                )
                # Local ``existing_agent`` ← existing_agent_result.scalar_one_or_none().
                existing_agent = existing_agent_result.scalar_one_or_none()

                # Only when (existing_agent).
                if existing_agent:
                    # Update existing agent (optional, or raise error)
                    logging.warning(f"Agent {agent_id} already exists. Update not implemented yet.")
                    # Pass the loaded tasks to the converter
                    return agent_model_to_proto(existing_agent, existing_agent.tasks)

                # Create new AgentModel instance with direct arguments
                agent_model = AgentModel(
                    # Local ``agent_id`` ← agent_id,.
                    agent_id=agent_id,
                    # Local ``agent_type`` ← agent_type,.
                    agent_type=agent_type,
                    # Local ``description`` ← description,.
                    description=description,
                    # Local ``capabilities`` ← capabilities,.
                    capabilities=capabilities,
                    # Local ``status`` ← status,.
                    status=status,
                    # Store the dictionaries directly in the JSON fields matching model names
                    container_info=container_dict, # Use prepared dict
                    # Local ``deployment_info`` ← deployment_dict, # Use prepared dict.
                    deployment_info=deployment_dict, # Use prepared dict
                    # Local ``task_server_info`` ← task_server_dict, # Use prepared dict.
                    task_server_info=task_server_dict, # Use prepared dict
                    # Local ``last_updated`` ← now.
                    last_updated=now
                )
                # Call ``session.add``.
                session.add(agent_model)
                # Await ``session.flush`` and continue once it completes.
                await session.flush() # Flush to get potential errors early

                # Pass empty list for tasks as it's a new agent
                return agent_model_to_proto(agent_model, [])

    @db_retry()
    async def update_agent(
        self,
        agent_id: str,
        # Pass updates as optional dictionaries or individual fields
        metadata_update: Optional[Dict[str, Any]] = None,
        deployment_update: Optional[Dict[str, Any]] = None,
        container_update: Optional[Dict[str, Any]] = None,
        task_server_update: Optional[Dict[str, Any]] = None, # Renamed parameter
        capabilities_update: Optional[List[str]] = None,
        status_update: Optional[str] = None,
        task_ids_update: Optional[List[int]] = None # Use dedicated methods for task assignment? 
    ) -> Optional[fleet_manager_pb2.Agent]:
        """Update an existing agent's information."""
        
        # Hold ``self.async_session_factory()`` for the duration of the indented block.
        async with self.async_session_factory() as session:
            # Hold ``session.begin()`` for the duration of the indented block.
            async with session.begin():
                # Local ``agent_model`` ← await session.get(AgentModel, agent_id).
                agent_model = await session.get(AgentModel, agent_id)
                # Only when (not agent_model).
                if not agent_model:
                    # Log at warning so operators can diagnose this path.
                    logger.warning(f"Agent with ID {agent_id} not found for update.")
                    # Hand ``None`` back to the caller.
                    return None

                # Local ``updated`` ← False.
                updated = False
                # Update fields if new data is provided
                if metadata_update is not None:
                    # Ensure existing dict is updated, not replaced if it's None initially
                    if agent_model.agent_metadata is None: agent_model.agent_metadata = {}
                    # Call ``agent_model.agent_metadata.update``.
                    agent_model.agent_metadata.update(metadata_update)
                    # Local ``updated`` ← True.
                    updated = True
                # Only when (deployment_update is not None).
                if deployment_update is not None:
                    # Only when (agent_model.deployment_info is None: agent_model.deployment_info = {}).
                    if agent_model.deployment_info is None: agent_model.deployment_info = {}
                    # Call ``agent_model.deployment_info.update``.
                    agent_model.deployment_info.update(deployment_update)
                    # Local ``updated`` ← True.
                    updated = True
                # Only when (container_update is not None).
                if container_update is not None:
                    # Only when (agent_model.container_info is None: agent_model.container_info = {}).
                    if agent_model.container_info is None: agent_model.container_info = {}
                    # Call ``agent_model.container_info.update``.
                    agent_model.container_info.update(container_update)
                    # Local ``updated`` ← True.
                    updated = True
                # Only when (task_server_update is not None: # Renamed variable).
                if task_server_update is not None: # Renamed variable
                    # Only when (agent_model.task_server_info is None: agent_model.task_server_info = {} # Rename…).
                    if agent_model.task_server_info is None: agent_model.task_server_info = {} # Renamed attribute
                    agent_model.task_server_info.update(task_server_update) # Renamed attribute and variable
                    # Local ``updated`` ← True.
                    updated = True
                # Only when (capabilities_update is not None).
                if capabilities_update is not None:
                    agent_model.capabilities = capabilities_update
                    # Local ``updated`` ← True.
                    updated = True
                # Only when (status_update is not None).
                if status_update is not None:
                    # Add validation against fleet_manager_pb2.AgentStatus enum? 
                    agent_model.status = status_update
                    # Local ``updated`` ← True.
                    updated = True
                # Only when (task_ids_update is not None).
                if task_ids_update is not None:
                    # Consider if overwriting the list is the desired behavior
                    agent_model.task_ids = task_ids_update
                    # Local ``updated`` ← True.
                    updated = True

                # Only when (updated).
                if updated:
                    # Call ``agent_model.last_updated = datetime.utcnow``.
                    agent_model.last_updated = datetime.utcnow()
                    # Await ``session.flush`` and continue once it completes.
                    await session.flush()
                    # Log at info so operators can diagnose this path.
                    logger.info(f"Updated agent ID {agent_id}")
                else:
                    # Log at info so operators can diagnose this path.
                    logger.info(f"No updates specified for agent ID {agent_id}")

                # Re-fetch with tasks loaded to pass to converter
                updated_agent_result = await session.execute(
                    # Call ``select``.
                    select(AgentModel)
                    # Call ``.options``.
                    .options(selectinload(AgentModel.tasks).options(undefer(TaskModel.dependency_task_ids)))
                    # Call ``.where``.
                    .where(AgentModel.agent_id == agent_id)
                )
                # Local ``agent_model`` ← updated_agent_result.scalar_one().
                agent_model = updated_agent_result.scalar_one()

                # Pass the loaded tasks to the conversion function
                return agent_model_to_proto(agent_model, agent_model.tasks)

    @db_retry()
    async def update_agent_status(self, agent_id: str, status: int) -> Optional[fleet_manager_pb2.Agent]:
        """Update the status of a agent by ID. Status should be an integer enum value."""
        async with self.async_session_factory() as session:
            # Hold ``session.begin()`` for the duration of the indented block.
            async with session.begin():
                # Local ``agent`` ← await session.get(AgentModel, agent_id).
                agent = await session.get(AgentModel, agent_id)
                # Only when (not agent).
                if not agent:
                    # Log at warning so operators can diagnose this path.
                    logger.warning(f"Agent with ID {agent_id} not found for update.")
                    # Hand ``None`` back to the caller.
                    return None
                agent.status = status
                # Await ``session.flush`` and continue once it completes.
                await session.flush()
                # Eagerly load tasks using selectinload in a new query
                stmt = (
                    # Call ``select``.
                    select(AgentModel)
                    # Call ``.options``.
                    .options(selectinload(AgentModel.tasks))
                    # Call ``.where``.
                    .where(AgentModel.agent_id == agent_id)
                )
                # Local ``result`` ← await session.execute(stmt).
                result = await session.execute(stmt)
                # Local ``agent_with_tasks`` ← result.scalar_one().
                agent_with_tasks = result.scalar_one()
                # Hand ``agent_model_to_proto(agent_with_tasks, agent_with_tasks.tasks)`` back to the caller.
                return agent_model_to_proto(agent_with_tasks, agent_with_tasks.tasks)

    @db_retry()
    async def delete_agent(self, agent_id: str) -> bool:
        """Remove a agent registration from the database"""
        async with self.async_session_factory() as session:
            # Hold ``session.begin()`` for the duration of the indented block.
            async with session.begin():
                # Find the agent
                result = await session.execute(
                    # Call ``select``.
                    select(AgentModel).where(AgentModel.agent_id == agent_id)
                )
                # Local ``agent`` ← result.scalar_one_or_none().
                agent = result.scalar_one_or_none()
                
                # Only when (not agent).
                if not agent:
                    # Log at warning so operators can diagnose this path.
                    logger.warning(f"Attempted to unregister non-existent agent ID: {agent_id}")
                    # Hand ``False`` back to the caller.
                    return False
                
                # Remove agent_id reference from all associated tasks
                await session.execute(
                    # Call ``update``.
                    update(TaskModel)
                    # Call ``.where``.
                    .where(TaskModel.agent_id == agent_id)
                    # Call ``.values``.
                    .values(agent_id=None)
                )
                # Log at info so operators can diagnose this path.
                logger.info(f"Removed agent ID {agent_id} references from all tasks")
                
                # Delete the agent
                await session.delete(agent)
                # Log at info so operators can diagnose this path.
                logger.info(f"Unregistered agent ID: {agent_id}")
                # Hand ``True`` back to the caller.
                return True

    @db_retry()
    async def get_agent(self, agent_id: str) -> Optional[fleet_manager_pb2.Agent]:
        """Get a specific agent by ID"""
        async with self.async_session_factory() as session:
            # Eagerly load tasks relationship
            stmt = (
                # Call ``select``.
                select(AgentModel)
                # Call ``.options``.
                .options(selectinload(AgentModel.tasks).options(undefer(TaskModel.dependency_task_ids)))
                # Call ``.where``.
                .where(AgentModel.agent_id == agent_id)
            )
            # Local ``result`` ← await session.execute(stmt).
            result = await session.execute(stmt)
            # Local ``agent_model`` ← result.scalar_one_or_none().
            agent_model = result.scalar_one_or_none()
            
            # Only when (agent_model).
            if agent_model:
                # Convert model to proto (tasks were eager loaded)
                # Pass the loaded tasks to the converter
                return agent_model_to_proto(agent_model, agent_model.tasks)
            else:
                # Log at warning so operators can diagnose this path.
                logger.warning(f"Agent with ID {agent_id} not found.")
                # Hand ``None`` back to the caller.
                return None

    @db_retry()
    async def list_agents(self) -> List[fleet_manager_pb2.Agent]:
        """List all registered agents"""
        async with self.async_session_factory() as session:
            # Eagerly load tasks relationship for all agents
            stmt = (
                # Call ``select``.
                select(AgentModel)
                # Call ``.options``.
                .options(selectinload(AgentModel.tasks).options(undefer(TaskModel.dependency_task_ids)))
            )
            # Local ``result`` ← await session.execute(stmt).
            result = await session.execute(stmt)
            # Local ``agent_models`` ← result.scalars().all().
            agent_models = result.scalars().all()
            
            # Local ``agent_protos`` ← [].
            agent_protos = []
            # Loop: for model in agent_models.
            for model in agent_models:
                # Log at debug so operators can diagnose this path.
                logger.debug(f"[list_agents] Processing agent model: {model.agent_id}")
                # Convert model to proto (tasks were eager loaded)
                # Pass the loaded tasks to the conversion function
                agent_protos.append(agent_model_to_proto(model, model.tasks))
                
            # Log at info so operators can diagnose this path.
            logger.info(f"Listed {len(agent_protos)} agents.")
            # Hand ``agent_protos`` back to the caller.
            return agent_protos

    @db_retry()
    async def update_container_info(self, agent_id: str, container_info: fleet_manager_pb2.ContainerInfo) -> None:
        """Update container info for a registered agent"""
        async with self.async_session_factory() as session:
            # Local ``result`` ← await session.execute(.
            result = await session.execute(
                # Call ``select``.
                select(AgentModel).where(AgentModel.agent_id == agent_id)
            )
            # Local ``agent_model`` ← result.scalar_one_or_none().
            agent_model = result.scalar_one_or_none()
            
            # Log at info so operators can diagnose this path.
            logger.info(f"Updating container info for agent {agent_id}")
            # Log at info so operators can diagnose this path.
            logger.info(f"Container info: {container_info}")
            
            # Only when (agent_model).
            if agent_model:
                # Get existing container data or initialize if None
                container_data = agent_model.container_info if agent_model.container_info else {}
                
                # Only when (container_info is None).
                if container_info is None:
                    # For undeployment, preserve the original image and environment
                    container_data = {
                        "image": container_data.get("image", ""),
                        "environment": container_data.get("environment", {}),
                        "container_id": None
                    }
                else:
                    # Convert ContainerInfo proto to dictionary
                    container_data = MessageToDict(container_info, preserving_proto_field_name=True)
                
                # Update the container_info field
                agent_model.container_info = container_data
                
                # Save to database
                session.add(agent_model)
                # Await ``session.commit`` and continue once it completes.
                await session.commit()
            else:
                # Log at warning so operators can diagnose this path.
                logger.warning(f"Warning: Agent {agent_id} not found in database")

    async def get_agent_status(self, agent_id: str, deployment_status: str = "unknown") -> Optional[fleet_manager_pb2.AgentStatus]:
        """Get status of a registered agent"""
        agent = await self.get_agent(agent_id)
        # Only when (not agent).
        if not agent:
            # Hand ``None`` back to the caller.
            return None

        # Create a AgentStatus with the fields defined in the proto file
        if agent.container.container_info:
            # Agent is deployed and running
            return fleet_manager_pb2.AgentStatus(
                # Local ``state`` ← fleet_manager_pb2.AgentStatus.State.RUNNING,.
                state=fleet_manager_pb2.AgentStatus.State.RUNNING,
                # Local ``message`` ← f"Agent {agent_id} is running".
                message=f"Agent {agent_id} is running"
            )
        else:
            # Agent is registered but not deployed
            return fleet_manager_pb2.AgentStatus(
                # Local ``state`` ← fleet_manager_pb2.AgentStatus.State.REGISTERED,.
                state=fleet_manager_pb2.AgentStatus.State.REGISTERED,
                # Local ``message`` ← f"Agent {agent_id} is registered".
                message=f"Agent {agent_id} is registered"
            )

    @db_retry()
    async def create_goal(self, description: str) -> Optional[fleet_manager_pb2.Goal]:
        """Create a new goal"""
        async with self.async_session_factory() as session:
            # Hold ``session.begin()`` for the duration of the indented block.
            async with session.begin():
                # Create GoalModel instance
                new_goal = GoalModel(
                    # Local ``description`` ← description,.
                    description=description,
                    # status="PENDING" # Add status if needed in model/proto
                )
                # Call ``session.add``.
                session.add(new_goal)
                # Await ``session.flush`` and continue once it completes.
                await session.flush() # Flush to get the auto-generated ID
                
                # Log at info so operators can diagnose this path.
                logger.info(f"Created goal with ID: {new_goal.goal_id}")
                
                # Optionally raise an error or proceed without linking missing tasks

                # Link found tasks
                goal_model = new_goal
                # tasks_result = await session.execute(select(TaskModel).where(TaskModel.goal_id == new_goal.goal_id))
                # goal_model.tasks = tasks_result.scalars().all() # Assign tasks if relationship isn't automatically loaded

            # Await ``session.flush`` and continue once it completes.
            await session.flush() # Ensure links are persisted before converting

            # Explicitly load the tasks relationship before converting to proto
            # This prevents MissingGreenlet errors caused by lazy loading during conversion
            stmt = (
                # Call ``select``.
                select(GoalModel)
                # Call ``.options``.
                .options(selectinload(GoalModel.tasks).options(undefer(TaskModel.dependency_task_ids)))
                # Call ``.where``.
                .where(GoalModel.goal_id == goal_model.goal_id)
            )
            # Local ``result`` ← await session.execute(stmt).
            result = await session.execute(stmt)
            # Local ``refreshed_goal`` ← result.scalar_one().
            refreshed_goal = result.scalar_one()

            # Pass the loaded tasks to the conversion function
            return goal_model_to_proto(refreshed_goal, refreshed_goal.tasks)

    @db_retry()
    async def delete_goal(self, goal_id: int) -> bool:
        """Delete a goal by ID and associated tasks"""
        async with self.async_session_factory() as session:
            # Hold ``session.begin()`` for the duration of the indented block.
            async with session.begin():
                # Find the goal
                goal = await session.get(GoalModel, goal_id)
                # Only when (not goal).
                if not goal:
                    # Log at warning so operators can diagnose this path.
                    logger.warning(f"Goal with ID {goal_id} not found for deletion.")
                    # Hand ``False`` back to the caller.
                    return False
            
                # Find plans associated with this goal and remove the goal_id from their list
                # This assumes goal_ids is a list of integers stored in JSON
                potential_plans = await session.execute(select(PlanModel)) # Select all plans for simplicity
                # Loop: for plan in potential_plans.scalars().all().
                for plan in potential_plans.scalars().all():
                    # Only when (isinstance(plan.goal_ids, list) and goal_id in plan.goal_ids).
                    if isinstance(plan.goal_ids, list) and goal_id in plan.goal_ids:
                        # Call ``plan.goal_ids.remove``.
                        plan.goal_ids.remove(goal_id)
                        # Explicitly mark JSON column as modified to ensure changes are saved
                        flag_modified(plan, "goal_ids")
                        # Log at debug so operators can diagnose this path.
                        logger.debug(f"Removed goal ID {goal_id} from plan ID {plan.plan_id}.goal_ids")
            
                # Flush changes to plans before deleting the goal
                await session.flush()

                # Delete the goal - tasks will be deleted automatically because of cascade="all, delete-orphan"
                await session.delete(goal)
                # Log at info so operators can diagnose this path.
                logger.info(f"Deleted goal ID: {goal_id} and all associated tasks")
                # Hand ``True`` back to the caller.
                return True

    @db_retry()
    async def list_goals(self) -> List[fleet_manager_pb2.Goal]:
        """List all goals in the system, with their tasks."""
        async with self.async_session_factory() as session:
            # Local ``result`` ← await session.execute(select(GoalModel)).
            result = await session.execute(select(GoalModel))
            # Local ``goal_models`` ← result.scalars().all().
            goal_models = result.scalars().all()
            # Get all tasks in a single query
            tasks_result = await session.execute(select(TaskModel))
            # Local ``all_tasks`` ← tasks_result.scalars().all().
            all_tasks = tasks_result.scalars().all()
            # Group tasks by goal_id
            tasks_by_goal = {}
            # Loop: for task in all_tasks.
            for task in all_tasks:
                # Only when (task.goal_id is not None).
                if task.goal_id is not None:
                    # Call ``tasks_by_goal.setdefault``.
                    tasks_by_goal.setdefault(task.goal_id, []).append(task)
            # Local ``goal_protos`` ← [].
            goal_protos = []
            # Loop: for goal in goal_models.
            for goal in goal_models:
                # Local ``goal_proto`` ← fleet_manager_pb2.Goal().
                goal_proto = fleet_manager_pb2.Goal()
                goal_proto.goal_id = goal.goal_id
                goal_proto.description = goal.description or ""
                # Local ``tasks`` ← tasks_by_goal.get(goal.goal_id, []).
                tasks = tasks_by_goal.get(goal.goal_id, [])
                # Call ``goal_proto.task_ids.extend``.
                goal_proto.task_ids.extend([task.task_id for task in tasks])
                # Call ``goal_protos.append``.
                goal_protos.append(goal_model_to_proto(goal, tasks))
            # Hand ``goal_protos`` back to the caller.
            return goal_protos

    @db_retry()
    async def get_goal(self, goal_id: int) -> Optional[fleet_manager_pb2.Goal]:
        """Retrieve a goal by its ID."""
        async with self.async_session_factory() as session:
            # Eagerly load tasks associated with the goal
            stmt = (
                # Call ``select``.
                select(GoalModel)
                # Call ``.options``.
                .options(selectinload(GoalModel.tasks).options(undefer(TaskModel.dependency_task_ids)))
                # Call ``.where``.
                .where(GoalModel.goal_id == goal_id)
            )
            # Local ``result`` ← await session.execute(stmt).
            result = await session.execute(stmt)
            # Local ``goal_model`` ← result.scalar_one_or_none().
            goal_model = result.scalar_one_or_none()
            # Only when (goal_model).
            if goal_model:
                # Pass both the goal model and its loaded tasks to goal_model_to_proto
                return goal_model_to_proto(goal_model, goal_model.tasks)
            else:
                # Log at warning so operators can diagnose this path.
                logger.warning(f"Goal with ID {goal_id} not found.")
                # Hand ``None`` back to the caller.
                return None

    @db_retry()
    async def create_task(
        self,
        description: str,
        agent_id: Optional[str] = None, # Changed type hint to str
        goal_id: Optional[int] = None,
        plan_id: Optional[int] = None,
        dependency_task_ids: Optional[List[int]] = None,
        status: int = fleet_manager_pb2.TaskStatus.TASK_PENDING,
        agent_type: Optional[str] = None  # Add agent_type parameter
    ) -> Optional[fleet_manager_pb2.Task]:
        """Create a new task and assign it optionally to a agent and goal"""
        async with self.async_session_factory() as session:
            # Hold ``session.begin()`` for the duration of the indented block.
            async with session.begin():
                # Validate Agent ID if provided
                if agent_id is not None:
                    # Get AgentModel using string agent_id
                    agent = await session.get(AgentModel, agent_id)
                    # Only when (not agent).
                    if not agent:
                        # Log at warning so operators can diagnose this path.
                        logger.warning(f"Agent with ID {agent_id} not found for task assignment.")
                        # Hand ``None`` back to the caller.
                        return None

                # Check if plan exists, create if not
                if plan_id is not None:
                    # Local ``plan`` ← await session.get(PlanModel, plan_id).
                    plan = await session.get(PlanModel, plan_id)
                
                # Only when (plan_id is None or not plan).
                if plan_id is None or not plan:
                    # Create a new plan with default strategies
                    logger.info(f"Creating new plan for goal {goal_id}")
                    # Local ``plan`` ← await self.create_plan(.
                    plan = await self.create_plan(
                        # Local ``planning_strategy`` ← fleet_manager_pb2.PlanningStrategy.PLANNING_STRATEGY_UNSPECIFIED,….
                        planning_strategy=fleet_manager_pb2.PlanningStrategy.PLANNING_STRATEGY_UNSPECIFIED,  # Default strategy
                        # Local ``allocation_strategy`` ← fleet_manager_pb2.AllocationStrategy.ALLOCATION_STRATEGY_UNSPECIF….
                        allocation_strategy=fleet_manager_pb2.AllocationStrategy.ALLOCATION_STRATEGY_UNSPECIFIED,  # Default strategy
                        # Local ``goal_ids`` ← [goal_id] if goal_id else [].
                        goal_ids=[goal_id] if goal_id else []
                    )
                    # Local ``plan_id`` ← plan.plan_id.
                    plan_id = plan.plan_id
                
                # Local ``new_task`` ← TaskModel(.
                new_task = TaskModel(
                    # Local ``description`` ← description,.
                    description=description,
                    # Local ``agent_id`` ← agent_id,.
                    agent_id=agent_id,
                    # Local ``goal_id`` ← goal_id,.
                    goal_id=goal_id,
                    # Local ``plan_id`` ← plan_id,.
                    plan_id=plan_id,
                    # Local ``dependency_task_ids`` ← dependency_task_ids or [],.
                    dependency_task_ids=dependency_task_ids or [],
                    # Local ``status`` ← status,.
                    status=status,
                    # Local ``agent_type`` ← agent_type  # Pass agent_type to the model.
                    agent_type=agent_type  # Pass agent_type to the model
                )
                # Call ``session.add``.
                session.add(new_task)
                # Await ``session.flush`` and continue once it completes.
                await session.flush() # Get the auto-generated task_id
                
                # Log at info so operators can diagnose this path.
                logger.info(f"Created task with ID: {new_task.task_id}")
                
                # Convert to proto
                return task_model_to_proto(new_task)

    @db_retry()
    async def update_task_status(self, task_id: int, status: int) -> Optional[fleet_manager_pb2.Task]:
        """Update the status of a task by ID. Status should be an integer enum value."""
        async with self.async_session_factory() as session:
            # Hold ``session.begin()`` for the duration of the indented block.
            async with session.begin():
                # Local ``task`` ← await session.get(TaskModel, task_id).
                task = await session.get(TaskModel, task_id)
                # Only when (not task).
                if not task:
                    # Log at warning so operators can diagnose this path.
                    logger.warning(f"Task with ID {task_id} not found for update.")
                    # Hand ``None`` back to the caller.
                    return None
                task.status = status
                # Await ``session.flush`` and continue once it completes.
                await session.flush()
                # Hand ``task_model_to_proto(task)`` back to the caller.
                return task_model_to_proto(task)

    @db_retry()
    async def update_task(self, task_id: int, **kwargs) -> Optional[fleet_manager_pb2.Task]:
        """Update fields of a task by ID. Accepts any TaskModel column as kwarg (e.g., plan_id, goal_id, agent_id, status, etc.)."""
        async with self.async_session_factory() as session:
            # Hold ``session.begin()`` for the duration of the indented block.
            async with session.begin():
                # Local ``task`` ← await session.get(TaskModel, task_id).
                task = await session.get(TaskModel, task_id)
                # Only when (not task).
                if not task:
                    # Log at warning so operators can diagnose this path.
                    logger.warning(f"Task with ID {task_id} not found for update.")
                    # Hand ``None`` back to the caller.
                    return None
                # Loop: for key, value in kwargs.items().
                for key, value in kwargs.items():
                    # Only when (hasattr(task, key)).
                    if hasattr(task, key):
                        # Call ``setattr``.
                        setattr(task, key, value)
                # Await ``session.flush`` and continue once it completes.
                await session.flush()
                # Hand ``task_model_to_proto(task)`` back to the caller.
                return task_model_to_proto(task)

    @db_retry()
    async def delete_task(self, task_id: int) -> tuple[bool, list[int], Optional[int]]:
        """Delete a task and remove it from any dependent tasks' dependency_task_ids.

        This is the ONLY deletion behavior to avoid leaving dangling dependencies.

        Returns:
            (success, updated_task_ids, plan_id)
        """
        async with self.async_session_factory() as session:
            # Hold ``session.begin()`` for the duration of the indented block.
            async with session.begin():
                # Local ``task_model`` ← await session.get(TaskModel, task_id).
                task_model = await session.get(TaskModel, task_id)
                # Only when (not task_model).
                if not task_model:
                    # Log at warning so operators can diagnose this path.
                    logger.warning(f"Task with ID {task_id} not found for delete.")
                    # Hand ``False, [], None`` back to the caller.
                    return False, [], None

                # Local ``plan_id`` ← task_model.plan_id.
                plan_id = task_model.plan_id
                updated_task_ids: list[int] = []

                # Only unlink dependents within the same plan.
                if plan_id is not None:
                    # Local ``tasks_result`` ← await session.execute(.
                    tasks_result = await session.execute(
                        # Call ``select``.
                        select(TaskModel).where(TaskModel.plan_id == plan_id)
                    )
                    # Loop: for t in tasks_result.scalars().all().
                    for t in tasks_result.scalars().all():
                        # Only when (not isinstance(t.dependency_task_ids, list)).
                        if not isinstance(t.dependency_task_ids, list):
                            continue
                        # Only when (task_id in t.dependency_task_ids).
                        if task_id in t.dependency_task_ids:
                            t.dependency_task_ids = [d for d in t.dependency_task_ids if d != task_id]
                            # Call ``updated_task_ids.append``.
                            updated_task_ids.append(t.task_id)

                # Await ``session.delete`` and continue once it completes.
                await session.delete(task_model)
                # Await ``session.flush`` and continue once it completes.
                await session.flush()
                # Log at info so operators can diagnose this path.
                logger.info(f"Deleted task with ID: {task_id}, updated dependents: {updated_task_ids}")
                # Hand ``True, updated_task_ids, plan_id`` back to the caller.
                return True, updated_task_ids, plan_id

    @db_retry()
    async def list_tasks(self, plan_ids: Optional[List[int]] = None, goal_ids: Optional[List[int]] = None, 
                         agent_ids: Optional[List[str]] = None) -> List[fleet_manager_pb2.Task]:
        """List tasks with optional filtering.
        
        Args:
            plan_ids: Optional list of plan IDs to filter by
            goal_ids: Optional list of goal IDs to filter by
            agent_ids: Optional list of agent IDs to filter by
            
        Returns:
            List of matching Task protos
        """
        async with self.async_session_factory() as session:
            # Start with a base query
            query = select(TaskModel)
            
            # Add filters if provided
            if plan_ids and len(plan_ids) > 0:
                # Log at debug so operators can diagnose this path.
                logger.debug(f"Filtering tasks by plan_ids: {plan_ids}")
                # Since a task is associated with only one plan, check if the task's plan_id is in the list
                query = query.where(TaskModel.plan_id.in_(plan_ids))
                
            # Only when (goal_ids and len(goal_ids) > 0).
            if goal_ids and len(goal_ids) > 0:
                # Log at debug so operators can diagnose this path.
                logger.debug(f"Filtering tasks by goal_ids: {goal_ids}")
                # Since a task is associated with only one goal, check if the task's goal_id is in the list
                query = query.where(TaskModel.goal_id.in_(goal_ids))
                
            # Only when (agent_ids and len(agent_ids) > 0).
            if agent_ids and len(agent_ids) > 0:
                # Log at debug so operators can diagnose this path.
                logger.debug(f"Filtering tasks by agent_ids: {agent_ids}")
                # Local ``query`` ← query.where(TaskModel.agent_id.in_(agent_ids)).
                query = query.where(TaskModel.agent_id.in_(agent_ids))
            
            # Execute the query
            result = await session.execute(query)
            # Local ``task_models`` ← result.scalars().all().
            task_models = result.scalars().all()
            
            # Local ``task_protos`` ← [].
            task_protos = []
            # Loop: for model in task_models.
            for model in task_models:
                # Log at debug so operators can diagnose this path.
                logger.debug(f"Processing task model: {model.task_id}")
                # Convert model to proto
                task_protos.append(task_model_to_proto(model))
                
            # Log at info so operators can diagnose this path.
            logger.info(f"Listed {len(task_protos)} tasks with filters: plan_ids={plan_ids}, goal_ids={goal_ids}, agent_ids={agent_ids}")
            # Hand ``task_protos`` back to the caller.
            return task_protos

    @db_retry()
    async def get_task(self, task_id: int) -> Optional[fleet_manager_pb2.Task]:
        """Get a specific task by ID"""
        async with self.async_session_factory() as session:
            # Local ``task_model`` ← await session.get(TaskModel, task_id).
            task_model = await session.get(TaskModel, task_id)
            
            # Only when (task_model).
            if task_model:
                # Log at debug so operators can diagnose this path.
                logger.debug(f"Found task model: {task_model.task_id}")
                # Hand ``task_model_to_proto(task_model)`` back to the caller.
                return task_model_to_proto(task_model)
            else:
                # Log at warning so operators can diagnose this path.
                logger.warning(f"Task with ID {task_id} not found.")
                # Hand ``None`` back to the caller.
                return None

    @db_retry()
    async def get_tasks_by_agent(self, agent_id: int) -> List[fleet_manager_pb2.Task]:
        """Get all tasks assigned to a specific agent"""
        async with self.async_session_factory() as session:
            # Local ``result`` ← await session.execute(.
            result = await session.execute(
                # Call ``select``.
                select(TaskModel).where(TaskModel.agent_id == agent_id)
            )
            # Local ``task_models`` ← result.scalars().all().
            task_models = result.scalars().all()
            # Local ``task_protos`` ← [].
            task_protos = []
            # Loop: for model in task_models.
            for model in task_models:
                # Call ``task_protos.append``.
                task_protos.append(task_model_to_proto(model))
            # Log at info so operators can diagnose this path.
            logger.info(f"Found {len(task_protos)} tasks for agent ID {agent_id}")
            # Hand ``task_protos`` back to the caller.
            return task_protos

    @db_retry()
    async def get_tasks_by_goal(self, goal_id: int) -> List[fleet_manager_pb2.Task]:
        """Get all tasks associated with a specific goal"""
        async with self.async_session_factory() as session:
            # Local ``result`` ← await session.execute(.
            result = await session.execute(
                # Call ``select``.
                select(TaskModel).where(TaskModel.goal_id == goal_id)
            )
            # Local ``task_models`` ← result.scalars().all().
            task_models = result.scalars().all()
            # Local ``task_protos`` ← [].
            task_protos = []
            # Loop: for model in task_models.
            for model in task_models:
                # Call ``task_protos.append``.
                task_protos.append(task_model_to_proto(model))
            # Log at info so operators can diagnose this path.
            logger.info(f"Found {len(task_protos)} tasks for goal ID {goal_id}")
            # Hand ``task_protos`` back to the caller.
            return task_protos

    @db_retry()
    async def get_task_status(self, task_id: int) -> Optional[str]:
        """Get the status of a specific task"""
        task_proto = await self.get_task(task_id)
        # Only when (task_proto).
        if task_proto:
            # Convert enum value to string name
            return fleet_manager_pb2.TaskStatus.Name(task_proto.status)
        # Hand ``None`` back to the caller.
        return None

    # --- Plan Management ---
    @db_retry()
    async def create_plan(
        self,
        planning_strategy: fleet_manager_pb2.PlanningStrategy,
        allocation_strategy: fleet_manager_pb2.AllocationStrategy,
        task_ids: Optional[List[int]] = None,
        goal_ids: Optional[List[int]] = None,
        planning_prompts: Optional[Dict[str, str]] = None,
        allocation_prompts: Optional[Dict[str, str]] = None,
        planning_artifacts: Optional[Dict] = None,
        allocation_artifacts: Optional[Dict] = None,
        server_logs: Optional[str] = None,
        name: str = "",
        description: str = ""
    ) -> Optional[fleet_manager_pb2.Plan]:
        """Create a new plan and link it to tasks and optionally goals."""
        logger.info(f"Attempting to create plan with strategy {planning_strategy} ({type(planning_strategy)}) and allocation {allocation_strategy} ({type(allocation_strategy)}) for tasks {task_ids} and goals {goal_ids}")
        # Hold ``self.async_session_factory()`` for the duration of the indented block.
        async with self.async_session_factory() as session:
            # Hold ``session.begin()`` for the duration of the indented block.
            async with session.begin():
                # Convert strategy enum value to its integer representation for storage
                strategy_int = int(planning_strategy)
                # Local ``allocation_int`` ← int(allocation_strategy).
                allocation_int = int(allocation_strategy)
                # Log at info so operators can diagnose this path.
                logger.info(f"Converted strategies: planning={strategy_int}, allocation={allocation_int}")
                # Log at debug so operators can diagnose this path.
                logger.debug("DB CREATE: Storing planning_prompts: %s, planning_artifacts: %s, server_logs: %s",
                             planning_prompts is not None, planning_artifacts is not None, server_logs is not None)
                # Local ``new_plan`` ← PlanModel(.
                new_plan = PlanModel(
                    # Local ``planning_strategy`` ← strategy_int,.
                    planning_strategy=strategy_int,
                    # Local ``allocation_strategy`` ← allocation_int,.
                    allocation_strategy=allocation_int,
                    # Local ``goal_ids`` ← goal_ids or [],.
                    goal_ids=goal_ids or [],
                    # Local ``planning_prompts`` ← planning_prompts,.
                    planning_prompts=planning_prompts,
                    # Local ``allocation_prompts`` ← allocation_prompts,.
                    allocation_prompts=allocation_prompts,
                    # Local ``planning_artifacts`` ← planning_artifacts,.
                    planning_artifacts=planning_artifacts,
                    # Local ``allocation_artifacts`` ← allocation_artifacts,.
                    allocation_artifacts=allocation_artifacts,
                    # Local ``server_logs`` ← server_logs,.
                    server_logs=server_logs,
                    # Local ``name`` ← name,.
                    name=name,
                    # Local ``description`` ← description.
                    description=description
                )
                # Log at info so operators can diagnose this path.
                logger.info(f"Creating plan with name='{name}', description='{description}'")
                # Call ``session.add``.
                session.add(new_plan)
                # Await ``session.flush`` and continue once it completes.
                await session.flush() # Persist to get plan_id
                # Log at info so operators can diagnose this path.
                logger.info(f"Plan created with ID: {new_plan.plan_id}")
                # Link tasks if provided
                if task_ids:
                    # Loop: for tid in task_ids.
                    for tid in task_ids:
                        # Local ``task`` ← await session.get(TaskModel, tid).
                        task = await session.get(TaskModel, tid)
                        # Only when (task).
                        if task:
                            task.plan_id = new_plan.plan_id
                # Await ``session.flush`` and continue once it completes.
                await session.flush()
                # Fetch tasks for the new plan
                plan_tasks = [task for task in (await session.execute(select(TaskModel).where(TaskModel.plan_id == new_plan.plan_id))).scalars().all()]
                # Convert to proto
                return plan_model_to_proto(new_plan, plan_tasks)

    @db_retry()
    async def get_plan(self, plan_id: int) -> Optional[fleet_manager_pb2.Plan]:
        """Retrieve a plan by its ID, including linked tasks."""
        async with self.async_session_factory() as session:
            # Find the plan model
            result = await session.execute(
                # Call ``select``.
                select(PlanModel).where(PlanModel.plan_id == plan_id)
            )
            # Local ``plan_model`` ← result.scalar_one_or_none().
            plan_model = result.scalar_one_or_none()
            # Only when (plan_model is None).
            if plan_model is None:
                # Log at warning so operators can diagnose this path.
                logger.warning(f"Plan with ID {plan_id} not found.")
                # Hand ``None`` back to the caller.
                return None
            
            # Query all tasks for this plan
            plan_tasks = [task for task in (await session.execute(select(TaskModel).where(TaskModel.plan_id == plan_id))).scalars().all()]
            # Log at debug so operators can diagnose this path.
            logger.debug("Plan %s tasks: %s", plan_id, plan_tasks)
            # Convert to proto
            return plan_model_to_proto(plan_model, plan_tasks)

    @db_retry()
    async def get_plan_allocation_status(self, plan_id: int) -> dict:
        """Get the allocation status of a plan.
        
        Returns:
            dict with:
                - status: 'unallocated' | 'partially_allocated' | 'fully_allocated'
                - total_tasks: int
                - allocated_tasks: int
                - unallocated_task_ids: List[int] - task IDs without agent assignment
                - is_executable: bool - True only if fully_allocated
        """
        async with self.async_session_factory() as session:
            # Get all tasks for this plan
            tasks_result = await session.execute(
                # Call ``select``.
                select(TaskModel).where(TaskModel.plan_id == plan_id)
            )
            # Local ``tasks`` ← tasks_result.scalars().all().
            tasks = tasks_result.scalars().all()
            
            # Local ``total`` ← len(tasks).
            total = len(tasks)
            # Local ``allocated`` ← sum(1 for t in tasks if t.agent_id is not None and t.agent_id != ….
            allocated = sum(1 for t in tasks if t.agent_id is not None and t.agent_id != '')
            # Local ``unallocated_ids`` ← [t.task_id for t in tasks if t.agent_id is None or t.agent_id == ….
            unallocated_ids = [t.task_id for t in tasks if t.agent_id is None or t.agent_id == '']
            
            # Only when (total == 0).
            if total == 0:
                # Local ``status`` ← 'empty'.
                status = 'empty'
            elif allocated == 0:
                # Local ``status`` ← 'unallocated'.
                status = 'unallocated'
            elif allocated < total:
                # Local ``status`` ← 'partially_allocated'.
                status = 'partially_allocated'
            else:
                # Local ``status`` ← 'fully_allocated'.
                status = 'fully_allocated'
            
            # Hand ``{`` back to the caller.
            return {
                'status': status,
                'total_tasks': total,
                'allocated_tasks': allocated,
                'unallocated_task_ids': unallocated_ids,
                'is_executable': status == 'fully_allocated' and total > 0
            }

    @db_retry()
    async def list_plans(self) -> List[fleet_manager_pb2.Plan]:
        """List all plans in the system"""
        async with self.async_session_factory() as session:
            # Get all plans
            result = await session.execute(select(PlanModel))
            # Local ``plan_models`` ← result.scalars().all().
            plan_models = result.scalars().all()
            # Get all tasks in a single query
            tasks_result = await session.execute(select(TaskModel))
            # Local ``all_tasks`` ← tasks_result.scalars().all().
            all_tasks = tasks_result.scalars().all()
            # Group tasks by plan_id
            tasks_by_plan = {}
            # Loop: for task in all_tasks.
            for task in all_tasks:
                # Only when (task.plan_id is not None).
                if task.plan_id is not None:
                    # Call ``tasks_by_plan.setdefault``.
                    tasks_by_plan.setdefault(task.plan_id, []).append(task)
            # Local ``plan_protos`` ← [].
            plan_protos = []
            # Loop: for plan in plan_models.
            for plan in plan_models:
                # Fetch tasks for the plan
                plan_tasks = tasks_by_plan.get(plan.plan_id, [])
                # Convert to proto
                plan_protos.append(plan_model_to_proto(plan, plan_tasks))
            # Hand ``plan_protos`` back to the caller.
            return plan_protos

    @db_retry()
    async def update_plan(
        self,
        plan_id: int,
        goal_ids: Optional[List[int]] = None,
        task_ids: Optional[List[int]] = None,
        planning_strategy: Optional[fleet_manager_pb2.PlanningStrategy] = None,
        allocation_strategy: Optional[fleet_manager_pb2.AllocationStrategy] = None,
        execution_status: Optional[int] = None,
        planning_prompts: Optional[Dict[str, str]] = None,
        allocation_prompts: Optional[Dict[str, str]] = None,
        planning_artifacts: Optional[Dict] = None,
        allocation_artifacts: Optional[Dict] = None,
        server_logs: Optional[List[str]] = None,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Optional[fleet_manager_pb2.Plan]:
        """Update a plan's information."""
        async with self.async_session_factory() as session:
            # Hold ``session.begin()`` for the duration of the indented block.
            async with session.begin():
                # Get the plan
                plan_result = await session.execute(
                    # Call ``select``.
                    select(PlanModel).where(PlanModel.plan_id == plan_id)
                )
                # Local ``plan_model`` ← plan_result.scalar_one_or_none().
                plan_model = plan_result.scalar_one_or_none()
                # Only when (not plan_model).
                if not plan_model:
                    # Log at warning so operators can diagnose this path.
                    logger.warning(f"Plan with ID {plan_id} not found.")
                    # Hand ``None`` back to the caller.
                    return None

                # Update fields if provided
                if planning_strategy is not None:
                    plan_model.planning_strategy = planning_strategy
                # Only when (allocation_strategy is not None).
                if allocation_strategy is not None:
                    plan_model.allocation_strategy = allocation_strategy
                # Only when (goal_ids is not None).
                if goal_ids is not None:
                    plan_model.goal_ids = goal_ids
                # Only when (planning_prompts is not None).
                if planning_prompts is not None:
                    plan_model.planning_prompts = planning_prompts
                # Only when (allocation_prompts is not None).
                if allocation_prompts is not None:
                    plan_model.allocation_prompts = allocation_prompts
                # Only when (execution_status is not None).
                if execution_status is not None:
                    plan_model.execution_status = execution_status
                # Only when (planning_artifacts is not None).
                if planning_artifacts is not None:
                    plan_model.planning_artifacts = planning_artifacts
                # Only when (allocation_artifacts is not None).
                if allocation_artifacts is not None:
                    plan_model.allocation_artifacts = allocation_artifacts
                # Only when (server_logs is not None).
                if server_logs is not None:
                    plan_model.server_logs = "\n".join(server_logs) if isinstance(server_logs, list) else server_logs
                # Only when (name is not None).
                if name is not None:
                    plan_model.name = name
                # Only when (description is not None).
                if description is not None:
                    plan_model.description = description
                # Unlink all existing tasks if task_ids is provided
                if task_ids is not None:
                    # Unlink all current tasks from this plan
                    tasks_result = await session.execute(select(TaskModel).where(TaskModel.plan_id == plan_id))
                    # Loop: for task in tasks_result.scalars().all().
                    for task in tasks_result.scalars().all():
                        task.plan_id = None
                    # Link new tasks
                    for tid in task_ids:
                        # Local ``task`` ← await session.get(TaskModel, tid).
                        task = await session.get(TaskModel, tid)
                        # Only when (task).
                        if task:
                            task.plan_id = plan_id
                # Await ``session.flush`` and continue once it completes.
                await session.flush()
                # Fetch tasks for the updated plan
                plan_tasks = [task for task in (await session.execute(select(TaskModel).where(TaskModel.plan_id == plan_id))).scalars().all()]
                # Convert to proto
                return plan_model_to_proto(plan_model, plan_tasks)

    @db_retry()
    async def copy_plan_tasks(self, source_plan_id: int, target_plan_id: int) -> bool:
        """Copy all tasks from source plan to target plan with new task IDs."""
        async with self.async_session_factory() as session:
            # Hold ``session.begin()`` for the duration of the indented block.
            async with session.begin():
                # Get all tasks from the source plan
                source_tasks = (await session.execute(
                    # Call ``select``.
                    select(TaskModel).where(TaskModel.plan_id == source_plan_id)
                )).scalars().all()

                # Only when (not source_tasks).
                if not source_tasks:
                    # Log at warning so operators can diagnose this path.
                    logger.warning(f"No tasks found in source plan {source_plan_id}")
                    # Hand ``True`` back to the caller.
                    return True

                # Copy each task to the target plan
                for source_task in source_tasks:
                    # Local ``new_task`` ← TaskModel(.
                    new_task = TaskModel(
                        # Local ``description`` ← source_task.description,.
                        description=source_task.description,
                        # Local ``goal_id`` ← source_task.goal_id,.
                        goal_id=source_task.goal_id,
                        # Local ``plan_id`` ← target_plan_id,.
                        plan_id=target_plan_id,
                        # Local ``agent_id`` ← source_task.agent_id,.
                        agent_id=source_task.agent_id,
                        # Local ``agent_type`` ← source_task.agent_type,.
                        agent_type=source_task.agent_type,
                        # Local ``status`` ← 1,  # PENDING — always reset on copy.
                        status=1,  # PENDING — always reset on copy
                        # Local ``result`` ← None,.
                        result=None,
                        # Local ``dependency_task_ids`` ← source_task.dependency_task_ids.copy() if source_task.dependency_….
                        dependency_task_ids=source_task.dependency_task_ids.copy() if source_task.dependency_task_ids else []
                    )
                    # Call ``session.add``.
                    session.add(new_task)

                # Await ``session.flush`` and continue once it completes.
                await session.flush()

                # Update dependency_task_ids to point to the new task IDs
                # We need to map old task IDs to new task IDs
                old_to_new_task_ids = {}
                # Local ``all_new_tasks`` ← (await session.execute(.
                all_new_tasks = (await session.execute(
                    # Call ``select``.
                    select(TaskModel).where(TaskModel.plan_id == target_plan_id)
                )).scalars().all()

                # Create mapping from old to new task IDs
                source_tasks_list = list(source_tasks)
                # Loop: for i, (old_task, new_task) in enumerate(zip(source_tasks_list, all_new_tasks)).
                for i, (old_task, new_task) in enumerate(zip(source_tasks_list, all_new_tasks)):
                    old_to_new_task_ids[old_task.task_id] = new_task.task_id

                # Update dependency_task_ids for all new tasks
                for new_task in all_new_tasks:
                    # Only when (new_task.dependency_task_ids).
                    if new_task.dependency_task_ids:
                        new_task.dependency_task_ids = [
                            # Call ``old_to_new_task_ids.get``.
                            old_to_new_task_ids.get(old_id, old_id)
                            # Loop: for old_id in new_task.dependency_task_ids.
                            for old_id in new_task.dependency_task_ids
                        ]

                # Await ``session.flush`` and continue once it completes.
                await session.flush()
                # Log at info so operators can diagnose this path.
                logger.info(f"Copied {len(source_tasks)} tasks from plan {source_plan_id} to plan {target_plan_id}")
                # Hand ``True`` back to the caller.
                return True

    @db_retry()
    async def delete_plan(self, plan_id: int) -> bool:
        """Delete a plan by its ID and all associated tasks."""
        async with self.async_session_factory() as session:
            # Hold ``session.begin()`` for the duration of the indented block.
            async with session.begin():
                # Local ``result`` ← await session.execute(select(PlanModel).where(PlanModel.plan_id =….
                result = await session.execute(select(PlanModel).where(PlanModel.plan_id == plan_id))
                # Local ``plan_model`` ← result.scalar_one_or_none().
                plan_model = result.scalar_one_or_none()

                # Only when (plan_model).
                if plan_model:
                    # Delete the plan - tasks will be deleted automatically because of cascade="all, delete-orphan"
                    await session.delete(plan_model)
                    # Await ``session.flush`` and continue once it completes.
                    await session.flush()
                    # Log at info so operators can diagnose this path.
                    logger.info(f"Deleted plan with ID: {plan_id} and all associated tasks.")
                    # Hand ``True`` back to the caller.
                    return True
                else:
                    # Log at warning so operators can diagnose this path.
                    logger.warning(f"Plan with ID {plan_id} not found for deletion.")
                    # Hand ``False`` back to the caller.
                    return False


    # =========================================================================
    # Execution Context / Structured Task Results
    # =========================================================================

    async def record_task_execution(
        self,
        task_id: int,
        plan_id: Optional[int],
        agent_id: Optional[str],
        result: Dict[str, Any],
        context_snapshot: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Persist a structured task execution result for world-state reconstruction."""
        async with self.async_session_factory() as session:
            # Local ``execution`` ← TaskExecutionModel(.
            execution = TaskExecutionModel(
                # Local ``task_id`` ← task_id,.
                task_id=task_id,
                # Local ``plan_id`` ← plan_id,.
                plan_id=plan_id,
                # Local ``agent_id`` ← agent_id,.
                agent_id=agent_id,
                # Local ``result`` ← result,.
                result=result,
                # Local ``context_snapshot`` ← context_snapshot or {},.
                context_snapshot=context_snapshot or {},
            )
            # Call ``session.add``.
            session.add(execution)
            # Await ``session.commit`` and continue once it completes.
            await session.commit()

    async def list_task_executions(self, plan_id: int) -> list[dict]:
        """Return structured task execution records for a plan in completion order."""
        async with self.async_session_factory() as session:
            # Local ``stmt`` ← (.
            stmt = (
                # Call ``select``.
                select(TaskExecutionModel)
                # Call ``.where``.
                .where(TaskExecutionModel.plan_id == plan_id)
                # Call ``.order_by``.
                .order_by(TaskExecutionModel.completed_at.asc())
            )
            # Local ``result`` ← await session.execute(stmt).
            result = await session.execute(stmt)
            # Local ``rows`` ← result.scalars().all().
            rows = result.scalars().all()
            # Hand ``[`` back to the caller.
            return [
                {
                    "id": row.id,
                    "task_id": row.task_id,
                    "plan_id": row.plan_id,
                    "agent_id": row.agent_id,
                    "started_at": row.started_at.isoformat() if row.started_at else None,
                    "completed_at": row.completed_at.isoformat() if row.completed_at else None,
                    "result": row.result,
                    "context_snapshot": row.context_snapshot or {},
                }
                # Loop: for row in rows.
                for row in rows
            ]

    # =========================================================================
    # Metrics
    # =========================================================================

    async def record_metric(
        self,
        service: str,
        event_type: str,
        entity_id: str = None,
        duration_ms: int = None,
        success: bool = None,
        metadata: dict = None,
    ) -> None:
        """Record a metric event to the database (fire-and-forget safe)."""
        try:
            # Hold ``self.async_session_factory()`` for the duration of the indented block.
            async with self.async_session_factory() as session:
                # Local ``event`` ← MetricEvent(.
                event = MetricEvent(
                    # Local ``service`` ← service,.
                    service=service,
                    # Local ``event_type`` ← event_type,.
                    event_type=event_type,
                    # Local ``entity_id`` ← entity_id,.
                    entity_id=entity_id,
                    # Local ``duration_ms`` ← duration_ms,.
                    duration_ms=duration_ms,
                    # Local ``success`` ← success,.
                    success=success,
                    # Local ``metadata_`` ← metadata,.
                    metadata_=metadata,
                )
                # Call ``session.add``.
                session.add(event)
                # Await ``session.commit`` and continue once it completes.
                await session.commit()
        # On except Exception as e: recover or re-raise as appropriate.
        except Exception as e:
            # Log at debug so operators can diagnose this path.
            logger.debug("Failed to record metric: %s", e)

    async def list_metrics(
        self,
        service: str = None,
        event_type: str = None,
        since_seconds: int = None,
        limit: int = 200,
    ) -> list:
        """Query stored metrics with optional filters."""
        from datetime import datetime, timedelta, timezone
        # Hold ``self.async_session_factory()`` for the duration of the indented block.
        async with self.async_session_factory() as session:
            # Local ``stmt`` ← select(MetricEvent).order_by(MetricEvent.timestamp.desc()).
            stmt = select(MetricEvent).order_by(MetricEvent.timestamp.desc())
            # Only when (service).
            if service:
                # Local ``stmt`` ← stmt.where(MetricEvent.service == service).
                stmt = stmt.where(MetricEvent.service == service)
            # Only when (event_type).
            if event_type:
                # Local ``stmt`` ← stmt.where(MetricEvent.event_type == event_type).
                stmt = stmt.where(MetricEvent.event_type == event_type)
            # Only when (since_seconds).
            if since_seconds:
                # Local ``cutoff`` ← datetime.now(timezone.utc) - timedelta(seconds=since_seconds).
                cutoff = datetime.now(timezone.utc) - timedelta(seconds=since_seconds)
                # Local ``stmt`` ← stmt.where(MetricEvent.timestamp >= cutoff).
                stmt = stmt.where(MetricEvent.timestamp >= cutoff)
            # Local ``stmt`` ← stmt.limit(limit).
            stmt = stmt.limit(limit)
            # Local ``result`` ← await session.execute(stmt).
            result = await session.execute(stmt)
            # Local ``rows`` ← result.scalars().all().
            rows = result.scalars().all()
            # Hand ``[`` back to the caller.
            return [
                {
                    "id": r.id,
                    "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                    "service": r.service,
                    "event_type": r.event_type,
                    "entity_id": r.entity_id,
                    "duration_ms": r.duration_ms,
                    "success": r.success,
                    "metadata": r.metadata_,
                }
                # Loop: for r in rows.
                for r in rows
            ]
