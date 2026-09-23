"""SQLAlchemy ORM models and proto converters for the fleet control plane.

These tables mirror the messages in ``packages/proto/fleet_manager.proto``
and are the persistence layer behind ``AgentInstanceRegistry``. JSON columns
hold nested proto messages (``TaskServerInfo``, ``ContainerInfo``, etc.) so
the schema stays flat while the gRPC API stays nested.

Conversion helpers (``*_model_to_proto`` / ``*_proto_to_model``) are the
bridge between ORM rows and ``fleet_manager_pb2`` messages returned on the
wire. Callers must eager-load relationships (tasks) before converting when
``task_ids`` must be populated.
"""

# datetime defaults for last_updated timestamps.
from datetime import datetime
# Column types and declarative helpers for the ORM schema.
from sqlalchemy import Boolean, Column, String, Integer, JSON, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship, declarative_base, backref, selectinload
from sqlalchemy import select
# logging for converter diagnostics if needed by callers.
import logging
# List/Optional for converter signatures.
from typing import List, Optional
# Generated proto messages and enums.
from packages.proto import fleet_manager_pb2
# JSON dict ↔ protobuf nested message helpers.
from google.protobuf.json_format import MessageToDict, ParseDict
# func.now() for server-side created_at defaults.
from sqlalchemy import func
from uuid import uuid4
from sqlalchemy.orm import Session

# Declarative base shared by every fleet control-plane table.
Base = declarative_base()
# Module logger (available for registry/converter diagnostics).
logger = logging.getLogger(__name__)

# --- SQLAlchemy Models matching proto ---


class AgentModel(Base):
    """Persisted agent registration row (mirrors ``fleet_manager_pb2.Agent``)."""

    # Local ``__tablename__`` ← 'agents'.
    __tablename__ = 'agents'
    # Unique agent instance id (primary key).
    agent_id = Column(String, primary_key=True)
    # Logical agent type / name (e.g. requirements, cts).
    agent_type = Column(String, nullable=False)
    # Optional human description.
    description = Column(String, nullable=True)
    # JSON list of capability strings advertised at registration.
    capabilities = Column(JSON, nullable=False)
    # AgentStatus.State integer for enum compatibility with proto.
    status = Column(Integer, nullable=True)  # Store as integer for enum compatibility
    # Nested ContainerInfo as a JSON dict.
    container_info = Column(JSON, nullable=True)
    # Nested DeploymentInfo as a JSON dict.
    deployment_info = Column(JSON, nullable=True)
    # Nested TaskServerInfo (host/port) as a JSON dict.
    task_server_info = Column(JSON, nullable=True)
    # Last mutation time (registration, heartbeat-driven updates, etc.).
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # Tasks currently assigned to this agent.
    tasks = relationship("TaskModel", back_populates="agent", cascade="all, delete-orphan")


class GoalModel(Base):
    """Persisted planning goal (mirrors ``fleet_manager_pb2.Goal``)."""

    # Local ``__tablename__`` ← 'goals'.
    __tablename__ = 'goals'
    # Autoincrement goal primary key.
    goal_id = Column(Integer, primary_key=True, autoincrement=True)
    # Natural-language goal description used by planners.
    description = Column(String, nullable=False)
    # Tasks that realize this goal.
    tasks = relationship("TaskModel", back_populates="goal", cascade="all, delete-orphan")


class PlanModel(Base):
    """Persisted execution plan (mirrors ``fleet_manager_pb2.Plan`` plus extras)."""

    # Local ``__tablename__`` ← 'plans'.
    __tablename__ = 'plans'
    # Autoincrement plan primary key.
    plan_id = Column(Integer, primary_key=True, autoincrement=True)
    # PlanningStrategy enum stored as int.
    planning_strategy = Column(Integer, nullable=False) # Store as integer
    # AllocationStrategy enum stored as int.
    allocation_strategy = Column(Integer, nullable=False, default=0) # Store as integer
    # Authoritative list of goal ids (may be empty for manual plans).
    goal_ids = Column(JSON, nullable=True)  # List of int64 (authoritative, can be empty)
    # Prompts captured during planning for audit/replay.
    planning_prompts = Column(JSON, nullable=True)  # Store prompts used for planning
    # Prompts captured during allocation for audit/replay.
    allocation_prompts = Column(JSON, nullable=True)  # Store prompts used for allocation
    # Structured planning artifacts (DAG nodes, etc.).
    planning_artifacts = Column(JSON, nullable=True)  # Store artifacts from planning (DAG structure, etc.)
    # Structured allocation artifacts (assignments, costs).
    allocation_artifacts = Column(JSON, nullable=True)  # Store artifacts from allocation
    # Server-side log text accumulated during plan lifecycle.
    server_logs = Column(Text, nullable=True)  # Store server-side logs
    # 0=not_executed, 1=executing, 2=completed, 3=failed.
    execution_status = Column(Integer, default=0)  # 0=not_executed, 1=executing, 2=completed, 3=failed
    # Required user-facing plan name.
    name = Column(String, nullable=False)  # User-defined plan name (required)
    # Required user-facing plan description.
    description = Column(Text, nullable=False)  # User-defined plan description (required)
    # Creation timestamp from the database clock.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # Tasks belonging to this plan.
    tasks = relationship("TaskModel", back_populates="plan", cascade="all, delete-orphan")


class TaskModel(Base):
    """Persisted work item (mirrors ``fleet_manager_pb2.Task``)."""

    # Local ``__tablename__`` ← 'tasks'.
    __tablename__ = 'tasks'
    # Autoincrement task primary key.
    task_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    # Natural-language task description sent to the agent.
    description = Column(String, nullable=False)
    # Assigned agent id (nullable until allocation).
    agent_id = Column(String, ForeignKey("agents.agent_id"), nullable=True, index=True)
    # Parent goal id when the task belongs to a goal.
    goal_id = Column(Integer, ForeignKey("goals.goal_id"), nullable=True, index=True)
    # Parent plan id when the task belongs to a plan.
    plan_id = Column(Integer, ForeignKey("plans.plan_id"), nullable=True, index=True)
    # TaskStatus enum integer (defaults to PENDING).
    status = Column(Integer, default=fleet_manager_pb2.TaskStatus.TASK_PENDING)
    # JSON list of prerequisite task ids (DAG edges).
    dependency_task_ids = Column(JSON, nullable=True, default=[])
    # Desired agent type when agent_id is not yet bound.
    agent_type = Column(String, nullable=True)
    # Explicit capability requirements supplied by the task graph.
    required_capabilities = Column(JSON, nullable=False, default=list)
    # Execution result / output text after completion.
    result = Column(Text, nullable=True)  # Execution result/output
    # ORM relationships back to goal / agent / plan.
    goal = relationship("GoalModel", back_populates="tasks")
    # Local ``agent`` ← relationship("AgentModel", back_populates="tasks").
    agent = relationship("AgentModel", back_populates="tasks")
    # Local ``plan`` ← relationship("PlanModel", back_populates="tasks").
    plan = relationship("PlanModel", back_populates="tasks")


class TaskExecutionModel(Base):
    """Historical execution record for a single task run."""

    # Local ``__tablename__`` ← 'task_executions'.
    __tablename__ = 'task_executions'
    # Surrogate primary key for the execution row.
    id = Column(Integer, primary_key=True, autoincrement=True)
    # Task that was executed.
    task_id = Column(Integer, ForeignKey("tasks.task_id"), nullable=False, index=True)
    # Plan context when known.
    plan_id = Column(Integer, ForeignKey("plans.plan_id"), nullable=True, index=True)
    # Agent that performed the run.
    agent_id = Column(String, ForeignKey("agents.agent_id"), nullable=True, index=True)
    # Wall-clock start time.
    started_at = Column(DateTime(timezone=True), nullable=True)
    # Wall-clock completion time (defaults to now on insert).
    completed_at = Column(DateTime(timezone=True), server_default=func.now())
    # Structured result payload from the agent.
    result = Column(JSON, nullable=False)
    # Optional snapshot of execution context for debugging/replay.
    context_snapshot = Column(JSON, nullable=True)


class MetricEvent(Base):
    """Row written by ``packages.metrics.track_operation`` via the registry."""

    # Local ``__tablename__`` ← 'metric_events'.
    __tablename__ = 'metric_events'
    # Surrogate primary key.
    id = Column(Integer, primary_key=True, autoincrement=True)
    # When the metric was recorded.
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    # Service name (e.g. fleet_server).
    service = Column(String, nullable=False)
    # Operation label (e.g. plan_execution).
    event_type = Column(String, nullable=False)
    # Optional entity id (plan/task/agent).
    entity_id = Column(String, nullable=True)
    # Duration of the timed block in milliseconds.
    duration_ms = Column(Integer, nullable=True)
    # Whether the timed block completed without raising.
    success = Column(Boolean, nullable=True)
    # Extra caller-supplied metadata (column name ``metadata`` in SQL).
    metadata_ = Column("metadata", JSON, nullable=True)

# --- Model to Proto Conversion Utilities ---


def agent_model_to_proto(agent_model: 'AgentModel', tasks: Optional[List['TaskModel']] = None) -> 'fleet_manager_pb2.Agent':
    """Convert an AgentModel (and optional tasks) into a proto Agent message."""
    # Fresh Agent message to populate field-by-field.
    agent_proto = fleet_manager_pb2.Agent()
    agent_proto.agent_id = agent_model.agent_id
    agent_proto.agent_type = agent_model.agent_type
    agent_proto.description = agent_model.description or ""
    # Call ``agent_proto.capabilities.extend``.
    agent_proto.capabilities.extend(agent_model.capabilities or [])

    # Set AgentStatus message from the stored integer state.
    if isinstance(agent_model.status, int):
        agent_proto.status.state = agent_model.status
    else:
        # Default to REGISTERED if status is not an int
        agent_proto.status.state = fleet_manager_pb2.AgentStatus.State.REGISTERED

    # Populate TaskServerInfo from the JSON column when present.
    if agent_model.task_server_info and isinstance(agent_model.task_server_info, dict):
        # Call ``ParseDict``.
        ParseDict(agent_model.task_server_info, agent_proto.task_server_info)
    
    # Populate DeploymentInfo from the JSON column when present.
    if agent_model.deployment_info and isinstance(agent_model.deployment_info, dict):
        # Call ``ParseDict``.
        ParseDict(agent_model.deployment_info, agent_proto.deployment)

    # Populate ContainerInfo from the JSON column when present.
    if agent_model.container_info and isinstance(agent_model.container_info, dict):
        # Call ``ParseDict``.
        ParseDict(agent_model.container_info, agent_proto.container)

    # Attach related task ids when the caller eager-loaded them.
    if tasks:
        # Call ``agent_proto.task_ids.extend``.
        agent_proto.task_ids.extend([task.task_id for task in tasks])
    # Hand ``agent_proto`` back to the caller.
    return agent_proto


def task_model_to_proto(task_model: TaskModel) -> fleet_manager_pb2.Task:
    """Convert TaskModel SQLAlchemy model to Task protobuf message."""
    # Guard against None so callers can chain without checks.
    if not task_model:
        # Hand ``fleet_manager_pb2.Task()`` back to the caller.
        return fleet_manager_pb2.Task()
    
    # Construct with required / commonly-set fields.
    task_proto = fleet_manager_pb2.Task(
        # Local ``task_id`` ← task_model.task_id,.
        task_id=task_model.task_id,
        # Local ``description`` ← task_model.description or "",.
        description=task_model.description or "",
        # Local ``status`` ← task_model.status,.
        status=task_model.status,
        # Ensure dependency_task_ids is a list of integers, handle None or empty string
        dependency_task_ids=task_model.dependency_task_ids if isinstance(task_model.dependency_task_ids, list) else [],
        # Local ``agent_type`` ← task_model.agent_type if task_model.agent_type is not None else "….
        agent_type=task_model.agent_type if task_model.agent_type is not None else "", # Add agent_type to proto
        # Local ``result`` ← task_model.result if task_model.result is not None else "" # Add ….
        result=task_model.result if task_model.result is not None else "", # Add result to proto
        required_capabilities=(
            task_model.required_capabilities
            if isinstance(task_model.required_capabilities, list)
            else []
        ),
    )
    # Conditionally set optional fields if they have values
    if task_model.agent_id is not None:
        task_proto.agent_id = task_model.agent_id
    # Only when (task_model.goal_id is not None).
    if task_model.goal_id is not None:
        task_proto.goal_id = task_model.goal_id
    # Only when (task_model.plan_id is not None).
    if task_model.plan_id is not None:
        task_proto.plan_id = task_model.plan_id
    # Only when (task_model.result is not None).
    if task_model.result is not None:
        task_proto.result = task_model.result
        
    # Hand ``task_proto`` back to the caller.
    return task_proto


def goal_model_to_proto(goal_model: 'GoalModel', tasks: Optional[List['TaskModel']] = None) -> 'fleet_manager_pb2.Goal':
    """Convert a GoalModel (and optional tasks) into a proto Goal message."""
    goal_proto = fleet_manager_pb2.Goal()
    goal_proto.goal_id = goal_model.goal_id
    goal_proto.description = goal_model.description or ""
    # Only when (tasks).
    if tasks:
        # Call ``goal_proto.task_ids.extend``.
        goal_proto.task_ids.extend([task.task_id for task in tasks])
    # Hand ``goal_proto`` back to the caller.
    return goal_proto

# --- Proto to Model Conversion Functions ---


def agent_proto_to_model(proto: fleet_manager_pb2.Agent) -> AgentModel:
    """Convert a proto Agent into a detached AgentModel instance."""
    return AgentModel(
        # Local ``agent_id`` ← proto.agent_id,.
        agent_id=proto.agent_id,
        # Local ``agent_type`` ← proto.agent_type,.
        agent_type=proto.agent_type,
        # Local ``description`` ← proto.description,.
        description=proto.description,
        # Local ``capabilities`` ← list(proto.capabilities),.
        capabilities=list(proto.capabilities),
        # Local ``status`` ← proto.status.state,.
        status=proto.status.state,
        # Nested messages become JSON dicts for the ORM columns.
        container_info=MessageToDict(proto.container, preserving_proto_field_name=True) if proto.HasField('container') else None,
        # Local ``deployment_info`` ← MessageToDict(proto.deployment, preserving_proto_field_name=True)….
        deployment_info=MessageToDict(proto.deployment, preserving_proto_field_name=True) if proto.HasField('deployment') else None,
        # Local ``task_server_info`` ← MessageToDict(proto.task_server_info, preserving_proto_field_name….
        task_server_info=MessageToDict(proto.task_server_info, preserving_proto_field_name=True) if proto.HasField('task_server_info') else None,
        # Local ``last_updated`` ← proto.last_updated.ToDatetime() if proto.HasField('last_updated')….
        last_updated=proto.last_updated.ToDatetime() if proto.HasField('last_updated') else None
    )


def task_proto_to_model(proto: fleet_manager_pb2.Task) -> TaskModel:
    """Convert a proto Task into a detached TaskModel instance."""
    return TaskModel(
        # Local ``task_id`` ← proto.task_id,.
        task_id=proto.task_id,
        # Local ``description`` ← proto.description,.
        description=proto.description,
        # Local ``goal_id`` ← proto.goal_id if proto.goal_id else None,.
        goal_id=proto.goal_id if proto.goal_id else None,
        # Local ``plan_id`` ← proto.plan_id if proto.plan_id else None,.
        plan_id=proto.plan_id if proto.plan_id else None,
        # Local ``dependency_task_ids`` ← list(proto.dependency_task_ids),.
        dependency_task_ids=list(proto.dependency_task_ids),
        # Local ``agent_id`` ← proto.agent_id if proto.agent_id else None,.
        agent_id=proto.agent_id if proto.agent_id else None,
        # Note: stores the enum *name* string here historically.
        status=fleet_manager_pb2.TaskStatus.Name(proto.status),
        # Local ``agent_type`` ← proto.agent_type if proto.HasField('agent_type') else None,.
        agent_type=proto.agent_type if proto.HasField('agent_type') else None,
        # Local ``result`` ← proto.result if proto.HasField('result') else None.
        result=proto.result if proto.HasField('result') else None
    )


def goal_proto_to_model(proto: fleet_manager_pb2.Goal) -> GoalModel:
    """Convert a proto Goal into a detached GoalModel (tasks linked separately)."""
    return GoalModel(
        # Local ``goal_id`` ← proto.goal_id,.
        goal_id=proto.goal_id,
        # Local ``description`` ← proto.description.
        description=proto.description
        # tasks handled separately
    )

# Make sync: Data should be loaded *before* calling this.


def plan_model_to_proto(plan_model: 'PlanModel', tasks: Optional[List['TaskModel']] = None) -> 'fleet_manager_pb2.Plan':
    """Convert a PlanModel into a proto Plan (prompts/artifacts stay DB-only)."""
    plan_proto = fleet_manager_pb2.Plan()
    plan_proto.plan_id = plan_model.plan_id
    plan_proto.planning_strategy = plan_model.planning_strategy
    # Call ``plan_proto.allocation_strategy = getattr``.
    plan_proto.allocation_strategy = getattr(plan_model, 'allocation_strategy', 0)
    # Call ``plan_proto.execution_status = getattr``.
    plan_proto.execution_status = getattr(plan_model, 'execution_status', 0)
    plan_proto.name = plan_model.name
    plan_proto.description = plan_model.description
    # Only when (plan_model.goal_ids).
    if plan_model.goal_ids:
        # Call ``plan_proto.goal_ids.extend``.
        plan_proto.goal_ids.extend(plan_model.goal_ids)
    # Only when (tasks).
    if tasks:
        # Call ``plan_proto.task_ids.extend``.
        plan_proto.task_ids.extend([task.task_id for task in tasks])

    # Note: Additional plan data (prompts, artifacts, logs) is stored in database
    # but not included in protobuf since the protobuf files weren't regenerated.
    # This data is fetched separately by the grpc_bridge when needed.

    # Hand ``plan_proto`` back to the caller.
    return plan_proto


def plan_proto_to_model(proto: fleet_manager_pb2.Plan) -> PlanModel:
    """Convert Plan protobuf message to PlanModel SQLAlchemy object."""
    return PlanModel(
        # Local ``plan_id`` ← proto.plan_id,.
        plan_id=proto.plan_id,
        # Store the integer value of the enum
        planning_strategy=proto.planning_strategy,
        # Local ``allocation_strategy`` ← proto.allocation_strategy,.
        allocation_strategy=proto.allocation_strategy,
        # Local ``execution_status`` ← proto.execution_status if proto.HasField('execution_status') else….
        execution_status=proto.execution_status if proto.HasField('execution_status') else 0,
        # Local ``name`` ← proto.name,.
        name=proto.name,
        # Local ``description`` ← proto.description.
        description=proto.description
    )
