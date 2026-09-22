"""
Request models for gateway API input validation.

These Pydantic ``BaseModel`` subclasses define the JSON bodies accepted by
mutating FastAPI endpoints (agent registration, goals, automated and manual
plans, and task create/update). Field descriptions feed OpenAPI; constraints
such as ``min_length`` produce HTTP 422 responses before route handlers run.

Defaults for agent host/port come from ``packages.config`` so the dashboard
forms match the same defaults used by port management and health checks.
``TaskUpdate`` encodes special ``agent_id`` semantics (omit vs empty string)
documented on the model and honored by ``GRPCBridge.update_task``.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
# Shared defaults so registration forms align with port_manager / health code.
from packages.config import DEFAULT_AGENT_HOST, DEFAULT_AGENT_BASE_PORT


# =============================================================================
# Agent Models
# =============================================================================

class AgentRegistration(BaseModel):
    """
    Legacy agent registration request body (prefer ``AgentInstanceCreate``).

    Purpose:
        Older clients posted ``config_path`` plus optional ``agent_id`` without
        explicit host/port overrides.

    Fields:
        config_path: Path to agent YAML.
        agent_id: Optional custom id (auto-generated server-side if omitted).

    Side effects:
        None at validation time; registration side effects occur in the router.

    Failure behavior:
        Missing ``config_path`` → FastAPI 422.
    """
    # Required path to the embodiment YAML the fleet should register from.
    config_path: str = Field(..., description="Path to agent YAML configuration")
    # Optional override; bridge may invent ``{type}-1`` when absent.
    agent_id: Optional[str] = Field(None, description="Custom agent ID (auto-generated if not provided)")


class AgentInstanceCreate(BaseModel):
    """
    Request to register a new agent instance with network coordinates.

    Purpose:
        Combine an embodiment YAML path with explicit ``agent_id``, ``host``,
        and ``port`` so localhost collisions can be validated before gRPC
        registration.

    Args / fields:
        config_path: Relative to repo root or absolute filesystem path.
        agent_id: Unique instance id in the fleet registry.
        host: Where the agent's task HTTP server listens.
        port: Task server port (also used in localhost uniqueness checks).

    Returns:
        N/A (request model). Handlers return the registered agent dict.

    Side effects:
        None during validation.

    Failure behavior:
        Invalid/missing required fields → HTTP 422 from FastAPI.
    """
    config_path: str = Field(
        ..., 
        description="Path to agent YAML config (relative to project root or absolute)"
    )
    agent_id: str = Field(
        ..., 
        description="Unique identifier for this agent instance"
    )
    host: str = Field(
        default=DEFAULT_AGENT_HOST,
        description="Hostname or IP where the agent's task server is running"
    )
    port: int = Field(
        default=DEFAULT_AGENT_BASE_PORT,
        description="Port number for the agent's task server"
    )


# =============================================================================
# Goal Models
# =============================================================================

class GoalCreate(BaseModel):
    """
    Request body for creating a high-level fleet goal.

    Purpose:
        Capture the natural-language objective that planners will decompose.

    Fields:
        description: Non-empty goal text (``min_length=1``).

    Side effects:
        None at validation; ``POST /api/goals`` performs CreateGoal RPC.

    Failure behavior:
        Empty description → HTTP 422.
    """
    description: str = Field(
        ..., 
        min_length=1,
        description="Natural language description of what should be accomplished"
    )


# =============================================================================
# Plan Models
# =============================================================================

class PlanCreate(BaseModel):
    """
    Request to create a plan using automated planning and allocation.

    Purpose:
        Supply strategy enum integers, goal ids, and display metadata for
        ``POST /api/plans``.

    Fields:
        planning_strategy: Enum int (1=monolithic, 2=dag, 3=big_dag, 4=manual).
        allocation_strategy: Enum int (1=lp, 2=llm, 3=cost_based, 4=none).
        goal_ids: At least one goal id.
        name / description: User-facing labels.

    Side effects:
        None at validation; creation runs planners/allocators on the fleet server.

    Failure behavior:
        Empty goal_ids or missing fields → HTTP 422; RPC failures → 400 in router.
    """
    planning_strategy: int = Field(
        ...,
        description="Planning strategy enum value: 1=monolithic, 2=dag, 3=big_dag, 4=manual"
    )
    allocation_strategy: int = Field(
        ...,
        description="Allocation strategy enum value: 1=lp, 2=llm, 3=cost_based, 4=none"
    )
    goal_ids: List[int] = Field(
        ...,
        min_length=1,
        description="List of goal IDs this plan should accomplish"
    )
    name: str = Field(
        ...,
        description="User-defined name for the plan"
    )
    description: str = Field(
        ...,
        description="User-defined description for the plan"
    )


class ManualTaskDefinition(BaseModel):
    """
    One task node in a manually authored plan DAG.

    Purpose:
        Allow the UI to describe tasks before the database assigns real ids by
        using ``temp_id`` and ``depends_on`` references that the plans router
        topological-sorts and remaps.

    Fields:
        temp_id: Client-local id for dependency edges.
        description: Work statement.
        goal_id: Goal this task contributes to (required by manual create).
        agent_id / agent_type: Optional pre-assignment hints.
        depends_on: List of other ``temp_id`` values.

    Side effects:
        None at validation.

    Failure behavior:
        Missing required fields → 422; bad dependency graphs → 400 in router.
    """
    temp_id: str = Field(
        ..., 
        description="Temporary ID for referencing this task in dependencies"
    )
    description: str = Field(
        ..., 
        min_length=1,
        description="What this task should accomplish"
    )
    goal_id: int = Field(
        ..., 
        description="Which goal this task contributes to"
    )
    agent_id: Optional[str] = Field(
        None, 
        description="Specific agent to assign (leave empty for unallocated)"
    )
    agent_type: Optional[str] = Field(
        None, 
        description="Required agent type/capability for this task"
    )
    depends_on: List[str] = Field(
        default_factory=list,
        description="List of temp_ids this task depends on"
    )


class ManualPlanCreate(BaseModel):
    """
    Request to create a plan with a manually defined task DAG.

    Purpose:
        Bypass automated planners: the client supplies tasks; the router creates
        a MANUAL plan shell and CreateTask calls in dependency order. Plan
        ``goal_ids`` are derived from the tasks' ``goal_id`` values.

    Fields:
        tasks: Non-empty list of ``ManualTaskDefinition``.
        name / description: Plan labels.

    Side effects:
        None at validation.

    Failure behavior:
        Empty tasks → 422; cycle/missing deps → 400 in ``create_manual_plan``.
    """
    tasks: List[ManualTaskDefinition] = Field(
        ...,
        min_length=1,
        description="List of tasks forming the plan's DAG"
    )
    name: str = Field(
        ...,
        description="User-defined name for the plan"
    )
    description: str = Field(
        ...,
        description="User-defined description for the plan"
    )


# =============================================================================
# Task Models
# =============================================================================

class TaskCreate(BaseModel):
    """
    Request body for creating an individual task outside manual plan bulk flow.

    Purpose:
        Support ``POST /api/tasks`` for testing or incremental plan editing.

    Fields:
        description, goal_id required; plan_id/agent fields optional;
        dependency_task_ids defaults to empty list.

    Side effects:
        None at validation.

    Failure behavior:
        Validation 422; RPC failure → 400 in router.
    """
    description: str = Field(..., description="Task description")
    goal_id: int = Field(..., description="Goal this task belongs to")
    plan_id: Optional[int] = Field(None, description="Plan this task belongs to")
    agent_id: Optional[str] = Field(None, description="Assigned agent ID")
    agent_type: Optional[str] = Field(None, description="Required agent type")
    dependency_task_ids: List[int] = Field(
        default_factory=list,
        description="Task IDs this task depends on"
    )


class TaskUpdate(BaseModel):
    """
    Request body for patching an existing task.

    Purpose:
        Partial update of description, goal, agent assignment, and optionally
        the full dependency list when ``update_dependency_task_ids`` is true.

    Fields:
        All fields optional except the update flag defaulting to False.
        ``agent_id`` empty string clears assignment; omit leaves unchanged.

    Side effects:
        None at validation.

    Failure behavior:
        Validation 422; failed RPC → 400 in router.
    """
    description: Optional[str] = Field(None, description="Updated task description")
    goal_id: Optional[int] = Field(None, description="Updated goal ID")
    # If provided and empty string, clears assignment; if omitted, leaves unchanged.
    agent_id: Optional[str] = Field(None, description="Assigned agent ID (empty string to clear)")
    update_dependency_task_ids: bool = Field(
        default=False,
        description="If true, dependency_task_ids replaces existing list (can be empty)",
    )
    dependency_task_ids: List[int] = Field(
        default_factory=list,
        description="Replacement dependency task IDs (only used when update_dependency_task_ids=true)",
    )
