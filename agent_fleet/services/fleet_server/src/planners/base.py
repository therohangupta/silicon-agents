"""
Planner base classes, shared helpers, and ``get_planner`` factory.

This module is the foundation for all planning strategies used by the Fleet
Manager when creating plans automatically:

  * ``BasePlanner`` — abstract class that owns an ``AgentInstanceRegistry``,
    accumulates ``planning_prompts`` / ``planning_artifacts`` / ``server_logs``,
    loads the union of agent capabilities, formats an agent-context string for
    LLM prompts, persists Plan JSON via ``save_plan_to_db``, and converts
    ``DAGPlan`` graphs into the unified ``Plan`` index-based schema.
  * ``get_planner`` — maps protobuf ``PlanningStrategy`` to MonolithicPlanner,
    DAGPlanner, or BigDAGPlanner. MANUAL_PLAN raises because the gRPC service
    creates empty shells without an LLM planner.

Concrete planners live under ``types/`` and only implement ``plan(goal_ids)``.
The Replanner is a special BasePlanner subclass used by the Executor on
failure; it is not returned by ``get_planner``.
"""

# os reads OPENAI_API_KEY for the module-level OpenAI client.
import os
# OpenAI client used by some historical paths; concrete planners often create
# their own clients in __init__.
from openai import OpenAI
# json.loads parses planner Plan JSON before DB persistence.
import json
# asyncio retained for potential async helpers / historical imports.
import asyncio
# re retained for potential prompt/text cleanup helpers.
import re
# Enum retained for historical strategy enums (protobuf enums preferred now).
from enum import Enum
# Typing for goal lists, prompt dicts, capability sets, etc.
from typing import List, Dict, Optional, Any, Set
# ABC/abstractmethod enforce the plan() contract on subclasses.
from abc import ABC, abstractmethod
# Registry provides agents/goals/tasks/plans persistence.
from packages.fleet_sdk.src.instance_registry import AgentInstanceRegistry
# Default DB URL when a planner is constructed without an explicit registry.
from packages.config import DATABASE_URL
# Shared Pydantic schemas for Plan/DAG conversion and allocation types.
from ..formats.formats import Plan, DAGPlan, TaskPlanItem, Allocation, AgentTask
# logging for planner lifecycle and save_plan_to_db diagnostics.
import logging
# BaseAllocator imported historically; get_planner does not allocate itself.
from ..allocators.base import BaseAllocator
# load_dotenv ensures OPENAI_API_KEY is present when planners construct clients.
from dotenv import load_dotenv

# Load .env into the process environment before reading OPENAI_API_KEY.
load_dotenv()
# Module-level OpenAI client (concrete planners also construct their own).
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Logger for BasePlanner and get_planner messages.
logger = logging.getLogger(__name__)


class BasePlanner(ABC):
    """
    Abstract base class for all planners.

    Subclasses must implement ``plan(goal_ids) -> str`` returning JSON that
    conforms to the unified ``Plan`` schema (tasks with index-based
    dependencies). DAG-oriented subclasses typically build a ``DAGPlan`` and
    call ``_convert_dag_to_plan`` before returning.
    """

    def __init__(self, db_url: Optional[str] = None, registry: Optional[AgentInstanceRegistry] = None):
        """
        Bind a registry and initialize empty artifact/prompt/log stores.

        Args:
            db_url: Optional DB URL used only when ``registry`` is omitted.
            registry: Preferred shared registry from FleetManagerService so
                planners see the same agents/goals as the gRPC process.
        """
        # Reuse the service registry when provided; else construct from db_url.
        self.registry = registry or AgentInstanceRegistry(db_url or DATABASE_URL)
        # Announce which concrete planner class was constructed.
        logger.info(f"Initialized {self.__class__.__name__}.")

        # Storage for planning artifacts and prompts (persisted onto plan rows).
        self.planning_prompts = {}
        self.planning_artifacts = {}
        self.server_logs = []

    async def _load_capabilities(self) -> Set[str]:
        """
        Load the union of all agent capabilities in the system.

        Raises if the fleet has zero agents because planners cannot produce
        feasible tasks without knowing what the fleet can do.

        Returns:
            A set of unique capability strings across all agents.
        """
        # Fetch every registered agent instance.
        agents = await self.registry.list_agents()
        if not agents:
            # Planning without agents is unsupported — fail early.
            raise ValueError("No agents found in the registry.")

        # Create a set of all unique capabilities across all agents.
        return set().union(*(set(agent.capabilities) for agent in agents))

    async def _get_agent_context_string(self) -> str:
        """
        Fetch agent details and format them into a string for the LLM context.

        Groups agents by ``agent_type``, counts instances, and lists the
        capabilities of the first instance of each type (assumes homogeneous
        capabilities within a type for the summary).

        Returns:
            Multi-line string beginning with ``AVAILABLE AGENTS AND CAPABILITIES:``
            or a message stating no agents are available.
        """
        # Load all agents for grouping.
        agents = await self.registry.list_agents()
        if not agents:
            return "No agents available in the fleet."

        # Group instance dicts by agent_type key.
        agents_by_type: Dict[str, List[Dict[str, Any]]] = {}
        for agent in agents:
            # Initialize the type bucket on first sighting.
            if agent.agent_type not in agents_by_type:
                agents_by_type[agent.agent_type] = []
            # Record id + capabilities for potential future richer prompts.
            agents_by_type[agent.agent_type].append({
                "id": agent.agent_id,
                "capabilities": agent.capabilities
            })

        # Header line for the LLM-facing summary.
        context_lines = ["AVAILABLE AGENTS AND CAPABILITIES:"]
        for agent_type, instances in agents_by_type.items():
            # Count how many instances of this type exist.
            count = len(instances)
            # Assuming all agents of the same type have the same capabilities for simplicity in the summary
            # If capabilities can vary within a type, this might need adjustment
            capabilities_str = ", ".join(sorted(list(set(instances[0]['capabilities'])))) if instances else "None"
            # One bullet per agent type with count and capability list.
            context_lines.append(f"- {count} {agent_type} agent(s) with capabilities: [{capabilities_str}]")

        # Join with literal backslash-n as historically produced for prompts.
        return "\\n".join(context_lines)

    @abstractmethod
    async def plan(self, goal_ids: List[int]) -> str:
        """
        Generate a plan for the given goals. Returns a JSON string
        conforming to the Plan schema.

        Args:
            goal_ids: List of goal IDs to include in the plan

        Returns:
            JSON string representation of the plan
        """
        # Abstract — subclasses must override; base body is never executed.
        pass

    # @abstractmethod
    # async def replan(self, plan_id: int, failed_task_id: int, failure_message: str, agent_task_assignments: Dict[int, int]) -> str:
    #     """
    #     Generate a new plan segment to recover from a failure in an existing plan.
    #
    #     Args:
    #         plan_id: The ID of the plan that failed.
    #         failed_task_id: The ID of the task that failed.
    #         failure_message: A string describing the failure.
    #         agent_task_assignments: A dictionary mapping agent_id to the task_id they were assigned at the time of failure.
    #
    #     Returns:
    #         JSON string representation of the new plan segment (in Plan format).
    #     """
    #     pass

    async def save_plan_to_db(self, plan_json: str, planning_strategy: int, allocation_strategy: int, goal_ids: List[int],
                             planning_prompts: Dict[str, str] = None, planning_artifacts: Dict = None, server_logs: str = None,
                             name: str = "", description: str = "") -> int:
        """
        Parse the plan JSON and save the plan and tasks to the database.

        Two-pass task creation:
          1. Create every task without dependencies to obtain DB ids.
          2. Remap planner-local dependency indices to DB ids and update.

        Also attaches ``self.planning_prompts`` / ``planning_artifacts`` /
        ``server_logs`` onto the plan row for dashboard replay.

        Args:
            plan_json: JSON string representation of the plan
            planning_strategy: The planning strategy enum value
            allocation_strategy: The allocation strategy enum value
            goal_ids: List of goal IDs included in the plan
            planning_prompts: Unused legacy arg; instance attrs are used.
            planning_artifacts: Unused legacy arg; instance attrs are used.
            server_logs: Unused legacy arg; instance attrs are used.
            name: Optional human plan name.
            description: Optional human plan description.

        Returns:
            The ID of the created plan

        Raises:
            ValueError: If plan creation fails.
            Exception: Propagates JSON/DB errors after logging.
        """
        try:
            # First create the plan with the correct strategy
            logger.info("Plan creation: Saving plan with prompts keys: %s", list(self.planning_prompts.keys()) if self.planning_prompts else 'None')
            logger.info("Plan creation: Saving plan with artifacts keys: %s", list(self.planning_artifacts.keys()) if self.planning_artifacts else 'None')
            logger.info("Plan creation: Saving plan with %s log entries", len(self.server_logs) if self.server_logs else 0)
            # Create the plan shell first (task_ids filled after task inserts).
            plan = await self.registry.create_plan(
                planning_strategy=planning_strategy,
                allocation_strategy=allocation_strategy,
                goal_ids=goal_ids,
                task_ids=[],  # Will be populated later
                planning_prompts=self.planning_prompts,
                planning_artifacts=self.planning_artifacts,
                server_logs="\n".join(self.server_logs) if self.server_logs else None,
                name=name,
                description=description
            )

            # Abort if the registry failed to create a plan row.
            if not plan:
                raise ValueError(f"Failed to create plan for goals: {goal_ids}")
            #
            # Capture the new primary key for linking tasks.
            plan_id = plan.plan_id

            # Parse the JSON produced by the concrete planner.
            plan_data = json.loads(plan_json)

            # Extract tasks list from the unified Plan schema.
            tasks = plan_data.get("tasks", [])

            # Empty plans are allowed; return early with no tasks linked.
            if not tasks:
                logger.warning("No tasks found in the plan")
                return plan_id

            # First pass: Create all tasks and get their IDs
            task_ids = []
            task_index_to_id = {}  # Map from task index to DB ID

            for i, task_data in enumerate(tasks):
                # Pull required fields from the planner JSON object.
                description = task_data.get("description")
                task_goal_id = task_data.get("goal_id")
                agent_type = task_data.get("agent_type")

                if description and task_goal_id is not None:
                    # Create the task using instance_registry (no deps yet).
                    task_proto = await self.registry.create_task(
                        description=description,
                        goal_id=task_goal_id,
                        plan_id=plan_id,  # Link to our plan
                        agent_type=agent_type # Pass agent_type to create_task
                    )
                    # Track DB id in order and in the index remap table.
                    task_ids.append(task_proto.task_id)
                    task_index_to_id[i] = task_proto.task_id
                    logger.info("Added task: %s for goal %s (type: %s)", description, task_goal_id, agent_type)
                else:
                    # Skip malformed planner items rather than failing the plan.
                    logger.warning("Skipping invalid task: %s", task_data)

            # Second pass: Update dependencies now that we have IDs
            for i, task_data in enumerate(tasks):
                # Planner-local indices into the tasks array.
                dependency_indices = task_data.get("dependency_task_ids", [])
                if dependency_indices:
                    # Convert indices to actual task IDs
                    dependency_ids = [task_index_to_id[idx] for idx in dependency_indices if idx in task_index_to_id]
                    if dependency_ids and i in task_index_to_id:
                        task_id = task_index_to_id[i]
                        # Persist remapped dependency edges on the task row.
                        await self.registry.update_task(
                            task_id=task_id,
                            dependency_task_ids=dependency_ids
                        )
                        logger.info("Updated task %s with dependencies: %s", task_id, dependency_ids)

            # Update the plan with the task IDs collected in pass one.
            await self.registry.update_plan(plan_id, task_ids=task_ids)

            # Return the plan primary key to CreatePlan / Replanner callers.
            return plan_id
        except Exception as e:
            # Log and re-raise so gRPC CreatePlan can map to INTERNAL.
            logger.error("Error processing plan: %s", e)
            raise

    def _convert_dag_to_plan(self, dag_plan: DAGPlan) -> str:
        """
        Convert a DAG plan to the standard Plan format.

        Maps string node ids to array indices and rewrites ``depends_on``
        edges into ``dependency_task_ids`` index lists expected by
        ``save_plan_to_db``.

        Args:
            dag_plan: DAGPlan model containing nodes with dependencies

        Returns:
            JSON string in Plan format
        """
        # Map node IDs to array indices for index-based dependency encoding.
        node_id_to_index = {node.id: i for i, node in enumerate(dag_plan.nodes)}

        # Create tasks with mapped dependencies
        tasks = []

        for node in dag_plan.nodes:
            # Convert node dependencies from IDs to indices
            dependency_indices = []
            for dep_id in node.depends_on:
                if dep_id in node_id_to_index:
                    # Successful remap of a predecessor node id.
                    dependency_indices.append(node_id_to_index[dep_id])
                else:
                    # Dangling edge — log and skip rather than crashing.
                    logger.warning("Dependency %s not found in node map", dep_id)

            # Create the task item using Pydantic model
            task = TaskPlanItem(
                description=node.description,
                goal_id=node.goal_id,
                dependency_task_ids=dependency_indices,
                agent_type=node.agent_type  # Pass through the agent_type
            )
            tasks.append(task)

        # Return as JSON string using Pydantic's json() method
        plan = Plan(tasks=tasks)
        logger.info("Converted DAG with %s nodes to Plan with %s tasks", len(dag_plan.nodes), len(tasks))
        return plan.model_dump_json()


# Import concrete planner implementations after BasePlanner is defined to
# avoid circular imports while still allowing get_planner to construct them.
from .types import MonolithicPlanner, DAGPlanner, BigDAGPlanner
# Protobuf enum used as the factory switch key.
from packages.proto.fleet_manager_pb2 import PlanningStrategy


def get_planner(strategy: int, db_url: str = None, registry: Optional[AgentInstanceRegistry] = None):
    """
    Get the appropriate planner based on the planning strategy enum value from protobuf.

    Args:
        strategy: Integer enum value from fleet_manager_pb2.PlanningStrategy
        db_url: Optional database URL (legacy; prefer passing registry)
        registry: Optional existing AgentInstanceRegistry to reuse

    Returns:
        A planner instance of the appropriate type

    Raises:
        ValueError: For MANUAL_PLAN (must be handled in service) or unknown enums.

    Note:
        MANUAL strategy should not call this function - it creates an empty plan shell
        directly in service.py without using a planner.
    """
    if strategy == PlanningStrategy.MONOLITHIC:
        # Sequential Plan across all goals.
        return MonolithicPlanner(registry)
    elif strategy == PlanningStrategy.DAG:
        # Per-goal DAGs merged without cross-goal edges.
        return DAGPlanner(registry)
    elif strategy == PlanningStrategy.BIG_DAG:
        # Single DAG allowing cross-goal dependencies.
        return BigDAGPlanner(registry)
    elif strategy == PlanningStrategy.MANUAL_PLAN:
        # Manual plans never use an LLM planner — fail explicitly.
        raise ValueError(
            "MANUAL_PLAN strategy does not use a planner. "
            "Create an empty plan shell directly via registry.create_plan() instead."
        )
    else:
        # Unknown/future enum values should fail loudly.
        raise ValueError(f"Unknown planning strategy: {strategy}")
