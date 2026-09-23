"""Task-graph and allocation schemas shared by planners, allocators, and executor."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field, model_validator


class DAGNode(BaseModel):
    id: str
    description: str
    goal_id: int | None = None
    depends_on: list[str] = Field(default_factory=list)
    agent_type: Optional[str] = None
    required_capabilities: list[str] = Field(default_factory=list)


class DAGPlan(BaseModel):
    nodes: list[DAGNode]

    @model_validator(mode="after")
    def validate_dependencies(self) -> "DAGPlan":
        node_ids = [node.id for node in self.nodes]
        if len(node_ids) != len(set(node_ids)):
            raise ValueError("DAG node ids must be unique")
        known_ids = set(node_ids)
        for node in self.nodes:
            missing = set(node.depends_on) - known_ids
            if missing:
                raise ValueError(
                    f"node '{node.id}' has unknown dependencies: {sorted(missing)}"
                )
            if node.id in node.depends_on:
                raise ValueError(f"node '{node.id}' cannot depend on itself")
        self.topological_order()
        return self

    def topological_order(self) -> list[DAGNode]:
        by_id = {node.id: node for node in self.nodes}
        remaining = {node.id: set(node.depends_on) for node in self.nodes}
        ordered: list[DAGNode] = []
        while remaining:
            ready = sorted(node_id for node_id, deps in remaining.items() if not deps)
            if not ready:
                raise ValueError("DAG contains a dependency cycle")
            for node_id in ready:
                ordered.append(by_id[node_id])
                del remaining[node_id]
            completed = set(ready)
            for deps in remaining.values():
                deps.difference_update(completed)
        return ordered


class WorkflowNode(DAGNode):
    inputs: dict[str, Any] = Field(default_factory=dict)
    acceptance_criteria: list[str] = Field(default_factory=list)
    retry_limit: int = 0


class WorkflowGraph(DAGPlan):
    workflow_id: str
    nodes: list[WorkflowNode]


class PlannedDAG(BaseModel):
    plan_id: int
    task_ids_by_node: dict[str, int]


class AllocatedDAGNode(BaseModel):
    task_id: int
    description: str
    goal_id: int
    agent_id: str
    depends_on: list[int] = Field(default_factory=list)


class AllocatedDAGPlan(BaseModel):
    nodes: list[AllocatedDAGNode]


class AgentTask(BaseModel):
    task_id: int
    agent_id: str


class Allocation(BaseModel):
    allocations: list[AgentTask]
