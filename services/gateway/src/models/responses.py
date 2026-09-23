"""
Response models for gateway API output documentation and typing.

These Pydantic models describe JSON shapes returned to the dashboard. They are
used as FastAPI ``response_model`` annotations (and for OpenAPI generation).
They do not themselves perform I/O; handlers typically return dicts from
``GRPCBridge`` that FastAPI filters/coerces through these schemas.

``Config.from_attributes = True`` allows ORM-like objects to be accepted if a
handler ever returns them directly. Defaults document typical initial states
(e.g. goal ``pending``, task ``pending``, plan ``not_executed``).
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
# Default port shown on template cards when YAML omits connection.port.
from packages.config import DEFAULT_AGENT_BASE_PORT


# =============================================================================
# Agent Models
# =============================================================================

class TaskServerInfo(BaseModel):
    """
    Network location of an agent's HTTP task server.

    Purpose:
        Embed host/port inside ``AgentResponse`` so the UI can display reachability
        targets and build direct health URLs.

    Fields:
        host: Hostname or IP.
        port: TCP port.

    Side effects:
        None.

    Failure behavior:
        Missing required fields → response validation error (500) if handler
        returns incomplete data.
    """
    host: str = Field(..., description="Hostname or IP address")
    port: int = Field(..., description="Port number")


class AgentResponse(BaseModel):
    """
    Agent information returned by list/get/register agent endpoints.

    Purpose:
        Document the fleet agent view for OpenAPI and type-check responses.

    Fields:
        Identity (agent_id, agent_type), capabilities, status string,
        optional task_server_info, and optional current_task_id.

    Side effects:
        None.

    Failure behavior:
        FastAPI may drop unexpected keys; missing required fields error at response time.
    """
    agent_id: str = Field(..., description="Unique agent identifier")
    agent_type: str = Field(..., description="Agent type (from YAML metadata)")
    capabilities: List[str] = Field(default_factory=list, description="Agent capabilities")
    status: str = Field(default="available", description="Current agent status")
    task_server_info: Optional[TaskServerInfo] = Field(
        None, 
        description="Network location of agent's task server"
    )
    current_task_id: Optional[int] = Field(
        None, 
        description="ID of task currently being executed"
    )

    class Config:
        # Allow construction from objects with attributes (ORM / protobuf wrappers).
        from_attributes = True


# =============================================================================
# Goal Models
# =============================================================================

class GoalResponse(BaseModel):
    """
    Goal payload returned by goal CRUD endpoints.

    Purpose:
        Standardize goal_id, description, status, related task_ids, and optional
        created_at for the dashboard.

    Side effects:
        None.

    Failure behavior:
        Response validation errors if required fields absent.
    """
    goal_id: int = Field(..., description="Unique goal identifier")
    description: str = Field(..., description="Goal description")
    status: str = Field(default="pending", description="Goal status")
    task_ids: List[int] = Field(default_factory=list, description="IDs of tasks associated with this goal")
    created_at: Optional[str] = Field(None, description="Creation timestamp")

    class Config:
        from_attributes = True


# =============================================================================
# Task Models
# =============================================================================

class TaskResponse(BaseModel):
    """
    Task payload returned by task and nested plan endpoints.

    Purpose:
        Represent atomic work units with assignment, dependencies, status, and
        optional result text for execution UIs.

    Side effects:
        None.

    Failure behavior:
        Response validation errors if required fields absent.
    """
    task_id: int = Field(..., description="Unique task identifier")
    description: str = Field(..., description="Task description")
    goal_id: int = Field(..., description="Associated goal ID")
    plan_id: Optional[int] = Field(None, description="Associated plan ID")
    agent_id: Optional[str] = Field(None, description="Assigned agent ID")
    agent_type: Optional[str] = Field(None, description="Required agent type")
    status: str = Field(default="pending", description="Execution status")
    dependency_task_ids: List[int] = Field(
        default_factory=list, 
        description="IDs of tasks this depends on"
    )
    result: Optional[str] = Field(None, description="Execution result/output")

    class Config:
        from_attributes = True


class TaskDeleteResponse(BaseModel):
    """
    Result of deleting a task, including dependents updated server-side.

    Purpose:
        Tell the UI which dependency edges were rewritten after deletion.

    Fields:
        success, deleted_task_id, updated_task_ids, optional error string.

    Side effects:
        None (describes prior mutation).

    Failure behavior:
        Routers raise HTTP 400 before returning this when success is false.
    """
    success: bool = Field(..., description="Whether the delete succeeded")
    deleted_task_id: int = Field(..., description="The deleted task ID")
    updated_task_ids: List[int] = Field(default_factory=list, description="Tasks updated to remove dependency")
    error: Optional[str] = Field(None, description="Error message if any")


# =============================================================================
# Plan Models
# =============================================================================

class PlanResponse(BaseModel):
    """
    Plan payload including strategies, tasks, and optional planner artifacts.

    Purpose:
        Give the dashboard everything needed for plan detail views: ids, strategy
        enums, allocation/execution status strings, nested tasks, and optional
        prompt/artifact/log blobs enriched from the database.

    Side effects:
        None.

    Failure behavior:
        Response validation if required strategy/name fields missing.
    """
    plan_id: int = Field(..., description="Unique plan identifier")
    name: str = Field(..., description="User-defined plan name")
    description: str = Field(..., description="User-defined plan description")
    goal_ids: List[int] = Field(default_factory=list, description="Goals this plan addresses")
    task_ids: List[int] = Field(default_factory=list, description="Tasks in this plan")
    tasks: List[TaskResponse] = Field(default_factory=list, description="Full task objects")
    planning_strategy: int = Field(..., description="Strategy used for planning (enum value)")
    allocation_strategy: int = Field(..., description="Strategy used for allocation (enum value)")
    allocation_status: str = Field(
        default="unknown",
        description="'unallocated', 'partially_allocated', or 'fully_allocated'"
    )
    execution_status: str = Field(
        default="not_executed",
        description="'not_executed', 'executing', 'completed', or 'failed'"
    )
    status: str = Field(default="created", description="Plan execution status")
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    planning_prompts: Optional[Dict[str, str]] = Field(None, description="Prompts used for planning")
    allocation_prompts: Optional[Dict[str, str]] = Field(None, description="Prompts used for allocation")
    planning_artifacts: Optional[Dict] = Field(None, description="Artifacts from planning process")
    allocation_artifacts: Optional[Dict] = Field(None, description="Artifacts from allocation process")
    server_logs: Optional[str] = Field(None, description="Server-side logs from planning/allocation")
    dag_structure: Optional[Dict] = Field(None, description="DAG structure for visualization")

    class Config:
        from_attributes = True


# =============================================================================
# Agent template catalog
# =============================================================================

class AgentTemplateResponse(BaseModel):
    """Agent type template discovered from ``agents/**/config.yaml``."""
    name: str = Field(..., description="Template name")
    description: str = Field(default="", description="Template description")
    capabilities: List[str] = Field(default_factory=list, description="Available capabilities")
    default_port: int = Field(default=DEFAULT_AGENT_BASE_PORT, description="Default task server port")
    config_path: str = Field(..., description="Path to YAML configuration")
    container_image: str = Field(default="", description="Docker image if containerized")
    category: str = Field(default="", description="Track and EDA domain, such as frontend/rtl")
    track: str = Field(default="", description="frontend, backend, or other")
    eda: str = Field(default="", description="EDA function inside the track")

    class Config:
        from_attributes = True
