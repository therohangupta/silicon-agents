"""Transport contracts for submitting agent work and receiving results."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field

from .execution import CodeExecution, ExecutionTrace, MemoryOp, SkillCall


class ArtifactRef(BaseModel):
    """Pointer to an artifact stored outside the task envelope."""

    uri: str
    name: str
    format: str = "json"
    size_bytes: int = 0
    schema_hint: dict[str, Any] = Field(default_factory=dict)
    description: str = ""
    producer_task_id: str = ""
    producer_agent_id: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TaskSummary(BaseModel):
    """Compact description of a completed task available as context."""

    task_id: int | str
    description: str
    agent_id: Optional[str] = None
    result_summary: str = ""
    artifacts: dict[str, Any] = Field(default_factory=dict)


class ExecutionContextSnapshot(BaseModel):
    """Bounded execution context supplied with a task request."""

    plan_summary: str = ""
    completed_tasks: list[TaskSummary] = Field(default_factory=list)
    execution_facts: list[str] = Field(default_factory=list)
    available_artifacts: list[ArtifactRef] = Field(default_factory=list)
    agent_memory_hint: Optional[str] = None


class AgentTaskRequest(BaseModel):
    """Task submitted to an agent runtime."""

    task_id: str
    description: str
    goal_id: Optional[int] = None
    plan_id: Optional[int] = None
    workspace_uri: Optional[str] = None
    context: Optional[ExecutionContextSnapshot] = None
    inputs: dict[str, Any] = Field(default_factory=dict)
    required_capabilities: list[str] = Field(default_factory=list)
    record_episode: bool = False


class AgentTaskResult(BaseModel):
    """Task result returned from an agent runtime."""

    success: bool
    message: str
    artifacts: dict[str, Any] = Field(default_factory=dict)
    artifact_refs: list[ArtifactRef] = Field(default_factory=list)
    traces: list[ExecutionTrace] = Field(default_factory=list)
    replan: bool = False
    error: Optional[str] = None
    outcome: str = ""
    reason_code: str = ""

    @property
    def skill_calls(self) -> list[SkillCall]:
        """Skill calls recorded in this result."""

        return [
            SkillCall(**trace.payload)
            for trace in self.traces
            if trace.trace_type == "skill_call"
        ]

    @property
    def memory_updates(self) -> list[MemoryOp]:
        """Memory operations recorded in this result."""

        return [
            MemoryOp(**trace.payload)
            for trace in self.traces
            if trace.trace_type == "memory_op"
        ]

    @property
    def code_executions(self) -> list[CodeExecution]:
        """Code executions recorded in this result."""

        return [
            CodeExecution(**trace.payload)
            for trace in self.traces
            if trace.trace_type == "code_execution"
        ]
