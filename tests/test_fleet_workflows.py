"""Tests for fleet_sdk workflow graphs, persistence, and allocation."""

import asyncio
from types import SimpleNamespace

import pytest

from domains.eda.fleet_workflow import to_fleet_workflow
from domains.eda.schemas.messages import WorkflowSpec, WorkflowTask
from packages.fleet_sdk.src.allocators.types.deterministic.allocator import (
    DeterministicAllocator,
)
from packages.fleet_sdk.src.formats.formats import (
    DAGNode,
    DAGPlan,
    WorkflowGraph,
    WorkflowNode,
)
from packages.fleet_sdk.src.planners.base import BasePlanner


class FakeRegistry:
    def __init__(self):
        self.next_id = 100
        self.created = []
        self.updated = {}
        self.plan_tasks = []
        self.plans = {}

    async def create_plan(self, **kwargs):
        plan = SimpleNamespace(plan_id=7)
        self.plans[7] = kwargs
        return plan

    async def create_task(self, **kwargs):
        task = SimpleNamespace(task_id=self.next_id)
        self.next_id += 1
        self.created.append((task.task_id, kwargs))
        return task

    async def update_task(self, task_id, **kwargs):
        self.updated[task_id] = kwargs

    async def update_plan(self, plan_id, **kwargs):
        self.plan_tasks = kwargs["task_ids"]


class _PersistPlanner(BasePlanner):
    async def plan(self, goal_ids):
        raise NotImplementedError


def test_workflow_graph_extends_dagplan_and_planner_persists_dependencies():
    graph = WorkflowGraph(
        workflow_id="generic-demo",
        nodes=[
            WorkflowNode(id="a", description="produce", required_capabilities=["produce"]),
            WorkflowNode(id="b", description="validate", depends_on=["a"]),
        ],
    )
    registry = FakeRegistry()
    planner = _PersistPlanner(registry=registry)  # type: ignore[arg-type]
    plan_id = asyncio.run(
        planner.persist_dag(
            graph,
            planning_strategy=1,
            allocation_strategy=4,
            goal_ids=[9],
            default_goal_id=9,
        )
    )
    assert plan_id == 7
    assert registry.updated[101]["dependency_task_ids"] == [100]
    assert registry.plan_tasks == [100, 101]
    with pytest.raises(ValueError, match="cycle"):
        DAGPlan(
            nodes=[
                DAGNode(id="a", description="a", goal_id=9, depends_on=["b"]),
                DAGNode(id="b", description="b", goal_id=9, depends_on=["a"]),
            ],
        )


def test_deterministic_allocator_enforces_capability_before_ranking():
    task = SimpleNamespace(
        task_id=1, plan_id=7, agent_type="", required_capabilities=["synth"]
    )
    wrong = SimpleNamespace(agent_id="wrong", agent_type="", capabilities=["lint"])
    right = SimpleNamespace(agent_id="right", agent_type="", capabilities=["synth"])

    class Registry:
        async def get_plan(self, plan_id):
            return SimpleNamespace(plan_id=plan_id)

        async def list_tasks(self):
            return [task]

        async def list_agents(self):
            return [wrong, right]

        async def update_task(self, task_id, **kwargs):
            return None

    allocation = asyncio.run(DeterministicAllocator(registry=Registry()).allocate(7))
    assert allocation.allocations[0].agent_id == "right"


def test_eda_workflow_is_only_an_adapter_to_generic_graph():
    eda = WorkflowSpec(
        workflow_id="lead:task",
        parent_task_id="task",
        parent_agent="lead",
        tasks=[
            WorkflowTask(id="rtl", agent_type="rtl_implementation", capability="compile_candidate"),
            WorkflowTask(
                id="gate",
                agent_type="verification_validator",
                capability="verification_validation",
                depends_on=["rtl"],
            ),
        ],
    )
    generic = to_fleet_workflow(eda)
    assert isinstance(generic, DAGPlan)
    assert generic.nodes[1].depends_on == ["rtl"]
    assert generic.nodes[1].acceptance_criteria == ["independent validation required"]
