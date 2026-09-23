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
from ..formats.formats import DAGPlan
# logging for planner lifecycle and save_plan_to_db diagnostics.
import logging
# BaseAllocator imported historically; get_planner does not allocate itself.
from ..allocators.base import BaseAllocator
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
    async def plan(self, goal_ids: List[int]) -> DAGPlan:
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


    async def persist_dag(
        self,
        graph: DAGPlan,
        *,
        planning_strategy: int,
        allocation_strategy: int,
        goal_ids: List[int],
        default_goal_id: Optional[int] = None,
        name: str = "",
        description: str = "",
    ) -> int:
        """Create plan rows from a proposed DAG using the two-pass protocol."""
        plan = await self.registry.create_plan(
            planning_strategy=planning_strategy,
            allocation_strategy=allocation_strategy,
            goal_ids=goal_ids,
            task_ids=[],
            planning_prompts=self.planning_prompts,
            planning_artifacts=self.planning_artifacts,
            server_logs="\n".join(self.server_logs) if self.server_logs else None,
            name=name,
            description=description,
        )
        if not plan:
            raise ValueError(f"Failed to create plan for goals: {goal_ids}")
        plan_id = int(plan.plan_id)
        task_ids_by_node: dict[str, int] = {}
        for node in graph.topological_order():
            goal_id = node.goal_id if node.goal_id is not None else default_goal_id
            if goal_id is None:
                raise ValueError(f"node '{node.id}' has no goal_id")
            task = await self.registry.create_task(
                description=node.description,
                goal_id=goal_id,
                plan_id=plan_id,
                agent_type=node.agent_type,
                required_capabilities=node.required_capabilities or None,
            )
            if task is None:
                raise RuntimeError(f"failed to persist DAG node '{node.id}'")
            task_ids_by_node[node.id] = int(task.task_id)
        for node in graph.nodes:
            dependency_task_ids = [task_ids_by_node[n] for n in node.depends_on]
            if dependency_task_ids:
                await self.registry.update_task(
                    task_ids_by_node[node.id],
                    dependency_task_ids=dependency_task_ids,
                )
        await self.registry.update_plan(plan_id, task_ids=list(task_ids_by_node.values()))
        return plan_id


from .types import BigDAGPlanner, DAGPlanner, MonolithicPlanner
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


get_planning_strategy = get_planner
