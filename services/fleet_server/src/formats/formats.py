"""
Plan and allocation format definitions for the Fleet Server.

Planners and allocators communicate through a small set of Pydantic models
defined here. Keeping a single module of schemas ensures:

  - LLM structured outputs (``response_format=Plan`` / ``DAGPlan`` /
    ``Allocation``) validate against the same shapes the persistence layer
    expects when ``BasePlanner.save_plan_to_db`` and allocators update tasks.
  - DAG-oriented planners can emit node/edge graphs (``DAGNode`` / ``DAGPlan``)
    which ``BasePlanner._convert_dag_to_plan`` rewrites into the unified
    ``Plan`` (index-based ``dependency_task_ids``) used for DB storage.
  - The Executor consumes ``AllocatedDAGNode`` / ``AllocatedDAGPlan`` after
    agents have been assigned, so dispatch can walk dependency edges by
    concrete task ids rather than planner-local node string ids.

Do not invent ad-hoc dict shapes in planners/allocators; extend these models
if new fields are required so OpenAI parse schemas and DB mappers stay aligned.
"""

# Pydantic BaseModel provides validation and JSON schema for LLM parse modes.
from pydantic import BaseModel
# List/Dict/Any/Optional cover nested task lists and optional agent_type fields.
from typing import List, Dict, Any, Optional


class TaskPlanItem(BaseModel):
    """
    Represents a single task in a unified ``Plan`` with index-based deps.

    ``dependency_task_ids`` are zero-based indices into the parent ``Plan.tasks``
    array at planning time. ``BasePlanner.save_plan_to_db`` remaps those indices
    to real database task ids after the first create pass.
    """
    # Human-readable instruction the assigned agent will execute.
    description: str
    # Goal this task contributes to (must match a registry goal id).
    goal_id: int
    # Planner-local indices of prerequisite tasks within the same Plan.tasks.
    dependency_task_ids: List[int]
    # Optional suggested agent type string for allocators / UI rendering.
    agent_type: Optional[str] = None


class Plan(BaseModel):
    """
    Unified plan format: an ordered list of ``TaskPlanItem`` entries.

    Used as the canonical planner output after any DAG conversion, and as the
    OpenAI ``response_format`` for monolithic and replanner strategies.
    """
    # Ordered task list; dependency indices refer into this list.
    tasks: List[TaskPlanItem]


# DAG-specific formats for more natural graph-based planning (string node ids).


class DAGNode(BaseModel):
    """
    Represents a node in a directed acyclic graph (DAG) of tasks.

    Planners that think in graphs (DAG / BigDAG) emit these nodes. Node ``id``
    values are planner-local strings (e.g. ``goal1_node0``); ``depends_on``
    references other node ids. Conversion to ``Plan`` maps ids to indices.
    """
    # Planner-local unique node id (e.g., "node0", "goal1_node1").
    id: str
    # Human-readable task description for this node.
    description: str
    # Goal this node contributes to.
    goal_id: int
    # List of predecessor node ids this node depends on.
    depends_on: List[str]
    # Optional suggested agent type for later allocation.
    agent_type: Optional[str] = None


class DAGPlan(BaseModel):
    """
    DAG-based plan format: a flat list of ``DAGNode`` with explicit edges.

    Edges are encoded on each node via ``depends_on`` rather than a separate
    edge list; ``planning_artifacts`` may still project an edges array for UI.
    """
    # All nodes in the DAG; must not contain cycles.
    nodes: List[DAGNode]


class AllocatedDAGNode(BaseModel):
    """
    Executor-facing DAG node with concrete DB task id and assigned agent.

    Built by ``Executor._generate_dag`` from registry tasks after allocation.
    ``depends_on`` holds real task ids (ints), not planner string node ids.
    """
    # Database task id for this node.
    task_id: int
    # Task description copied from the registry task row.
    description: str
    # Goal id associated with the task.
    goal_id: int
    # Agent instance id assigned to execute this task.
    agent_id: str
    # Prerequisite task ids that must complete before dispatch.
    depends_on: List[int]


class AllocatedDAGPlan(BaseModel):
    """
    Full allocated DAG consumed by the Executor scheduling loop.

    ``Executor._get_agent_task_map`` topologically sorts these nodes (Kahn)
    and partitions the global order into per-agent work queues.
    """
    # All allocated nodes participating in execution.
    nodes: List[AllocatedDAGNode]


class AgentTask(BaseModel):
    """
    One task-to-agent assignment produced by an allocator.

    Allocators persist assignments by calling ``registry.update_task`` for each
    ``AgentTask``, and also return an ``Allocation`` wrapping the full list.
    """
    # Database task id being assigned.
    task_id: int
    # Agent instance id receiving the assignment.
    agent_id: str


class Allocation(BaseModel):
    """
    Allocator output envelope: a list of ``AgentTask`` assignments.

    Used as OpenAI ``response_format`` for the LLM allocator and as the return
    type for LP and cost-based allocators (even though annotations sometimes
    say ``Dict[int, str]`` historically).
    """
    # Complete set of task→agent mappings for a plan.
    allocations: List[AgentTask]
