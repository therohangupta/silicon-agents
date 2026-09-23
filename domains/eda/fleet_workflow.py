"""Adapt EDA workflow messages onto the shared fleet task graph."""

from __future__ import annotations

from typing import Any, Protocol

from packages.fleet_sdk.src.allocators.base import get_allocator
from packages.fleet_sdk.src.formats.formats import PlannedDAG, WorkflowGraph, WorkflowNode
from packages.fleet_sdk.src.planners.base import BasePlanner

from .schemas.messages import WorkflowSpec


class TaskRegistry(Protocol):
    async def create_plan(self, **kwargs: Any) -> Any: ...
    async def create_task(self, **kwargs: Any) -> Any: ...
    async def update_task(self, task_id: int, **kwargs: Any) -> Any: ...
    async def update_plan(self, plan_id: int, **kwargs: Any) -> Any: ...


def to_fleet_workflow(workflow: WorkflowSpec) -> WorkflowGraph:
    """Adapt a versioned EDA lead workflow into the generic fleet DAG model."""
    return WorkflowGraph(
        workflow_id=workflow.workflow_id,
        nodes=[
            WorkflowNode(
                id=task.id,
                description=task.objective,
                required_capabilities=[task.capability] if task.capability else [],
                agent_type=task.agent_type or None,
                depends_on=task.depends_on,
                acceptance_criteria=(
                    ["independent validation required"]
                    if "validator" in task.agent_type else []
                ),
            )
            for task in workflow.tasks
        ],
    )


class _WorkflowPlanner(BasePlanner):
    async def plan(self, goal_ids: list[int]):
        raise NotImplementedError("workflow planning uses persist_dag only")


async def plan_eda_workflow(
    workflow: WorkflowSpec,
    registry: TaskRegistry,
    *,
    planning_strategy: int,
    allocation_strategy: int,
    goal_id: int,
) -> PlannedDAG:
    """Persist a lead proposal through the shared fleet planner base."""
    planner = _WorkflowPlanner(registry=registry)  # type: ignore[arg-type]
    plan_id = await planner.persist_dag(
        to_fleet_workflow(workflow),
        planning_strategy=planning_strategy,
        allocation_strategy=allocation_strategy,
        goal_ids=[goal_id],
        default_goal_id=goal_id,
    )
    return PlannedDAG(plan_id=plan_id, task_ids_by_node={})


async def plan_and_allocate_eda_workflow(
    workflow: WorkflowSpec,
    registry: TaskRegistry,
    *,
    planning_strategy: int,
    allocation_strategy: int,
    goal_id: int,
) -> PlannedDAG:
    """Create an EDA plan and assign agents through SDK allocators."""
    planned = await plan_eda_workflow(
        workflow,
        registry,
        planning_strategy=planning_strategy,
        allocation_strategy=allocation_strategy,
        goal_id=goal_id,
    )
    from packages.proto import fleet_manager_pb2

    if allocation_strategy != fleet_manager_pb2.AllocationStrategy.NONE:
        await get_allocator(allocation_strategy, registry=registry).allocate(planned.plan_id)
    return planned
