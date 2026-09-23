from __future__ import annotations

"""Module ``agent_sdk/src/models.py``.

Agent SDK: HTTP task server, runtimes, skills, telemetry publisher, and workspace helpers for first-party agents.

Part of the agent SDK server/runtime stack: agents import these helpers to serve tasks over HTTP, run LLM/tool loops, publish telemetry, and persist plan workspaces.

Hand-written source for ``models.py``. Behavior is unchanged; comments document control-plane / agent-runtime intent for maintainers.
"""


from datetime import datetime, timezone
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

from packages.platform_config import setting


def _agent_heartbeat_interval() -> float:
    return float(setting("AGENT_HEARTBEAT_INTERVAL_SECS"))


def _default_agent_host() -> str:
    return setting("DEFAULT_AGENT_HOST")


def _default_agent_port() -> int:
    return int(setting("DEFAULT_AGENT_BASE_PORT"))


# ---------------------------------------------------------------------------
# Plan Workspace — Artifact References
# ---------------------------------------------------------------------------

class ArtifactRef(BaseModel):
    """Pointer to a large artifact stored in the plan workspace.

    Designed to be passed between agents without serializing the full payload.
    The schema/description fields allow LLM-backed agents to reason about
    whether and how to load the data without deserializing it first.
    """

    uri: str
    name: str
    format: str = "json"
    size_bytes: int = 0
    # Call ``schema_hint: dict[str, Any] = Field``.
    schema_hint: dict[str, Any] = Field(default_factory=dict)
    description: str = ""
    producer_task_id: str = ""
    producer_agent_id: str = ""
    # Call ``created_at: datetime = Field``.
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# Execution Traces
# ---------------------------------------------------------------------------

class SkillCall(BaseModel):
    """``SkillCall`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
    skill_id: str
    # Call ``args: dict[str, Any] = Field``.
    args: dict[str, Any] = Field(default_factory=dict)
    result: Any = None
    duration_ms: int = 0


class MemoryOp(BaseModel):
    """``MemoryOp`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
    op: Literal["read", "write", "search", "clear"]
    store_id: str
    key: Optional[str] = None
    value: Any = None


class CodeExecution(BaseModel):
    """``CodeExecution`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
    language: str = "python"
    code: str
    file_path: Optional[str] = None
    stdout: str = ""
    stderr: str = ""
    return_value: Any = None
    success: bool = True
    duration_ms: int = 0
    # Call ``skill_calls: list[SkillCall] = Field``.
    skill_calls: list[SkillCall] = Field(default_factory=list)


class ExecutionTrace(BaseModel):
    """``ExecutionTrace`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
    trace_type: Literal["skill_call", "code_execution", "memory_op", "event"]
    # Call ``payload: dict[str, Any] = Field``.
    payload: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Task Request / Result
# ---------------------------------------------------------------------------

class TaskSummary(BaseModel):
    """``TaskSummary`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
    task_id: int | str
    description: str
    agent_id: Optional[str] = None
    result_summary: str = ""
    # Call ``artifacts: dict[str, Any] = Field``.
    artifacts: dict[str, Any] = Field(default_factory=dict)


class ExecutionContextSnapshot(BaseModel):
    """``ExecutionContextSnapshot`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
    plan_summary: str = ""
    # Call ``completed_tasks: list[TaskSummary] = Field``.
    completed_tasks: list[TaskSummary] = Field(default_factory=list)
    execution_facts: list[str] = Field(default_factory=list)
    # Call ``available_artifacts: list[ArtifactRef] = Field``.
    available_artifacts: list[ArtifactRef] = Field(default_factory=list)
    agent_memory_hint: Optional[str] = None


class AgentTaskRequest(BaseModel):
    """``AgentTaskRequest`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
    task_id: str
    description: str
    goal_id: Optional[int] = None
    plan_id: Optional[int] = None
    workspace_uri: Optional[str] = None
    context: Optional[ExecutionContextSnapshot] = None
    # Call ``inputs: dict[str, Any] = Field``.
    inputs: dict[str, Any] = Field(default_factory=dict)
    # Call ``required_capabilities: list[str] = Field``.
    required_capabilities: list[str] = Field(default_factory=list)
    record_episode: bool = False


class AgentTaskResult(BaseModel):
    """``AgentTaskResult`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
    success: bool
    message: str
    # Call ``artifacts: dict[str, Any] = Field``.
    artifacts: dict[str, Any] = Field(default_factory=dict)
    # Call ``artifact_refs: list[ArtifactRef] = Field``.
    artifact_refs: list[ArtifactRef] = Field(default_factory=list)
    # Call ``traces: list[ExecutionTrace] = Field``.
    traces: list[ExecutionTrace] = Field(default_factory=list)
    replan: bool = False
    error: Optional[str] = None
    # Structured task outcomes (COMPLETED, UPSTREAM_CHANGE_REQUIRED, ...).
    # Empty for agents that only report success/failure.
    outcome: str = ""
    reason_code: str = ""

    @property
    def skill_calls(self) -> list[SkillCall]:
        """``skill_calls`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        return [
            # Call ``SkillCall``.
            SkillCall(**t.payload)
            # Loop: for t in self.traces.
            for t in self.traces
            # Only when (t.trace_type == "skill_call").
            if t.trace_type == "skill_call"
        ]

    @property
    def memory_updates(self) -> list[MemoryOp]:
        """``memory_updates`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        return [
            # Call ``MemoryOp``.
            MemoryOp(**t.payload)
            # Loop: for t in self.traces.
            for t in self.traces
            # Only when (t.trace_type == "memory_op").
            if t.trace_type == "memory_op"
        ]

    @property
    def code_executions(self) -> list[CodeExecution]:
        """``code_executions`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        return [
            # Call ``CodeExecution``.
            CodeExecution(**t.payload)
            # Loop: for t in self.traces.
            for t in self.traces
            # Only when (t.trace_type == "code_execution").
            if t.trace_type == "code_execution"
        ]


# ---------------------------------------------------------------------------
# Config: connection
# ---------------------------------------------------------------------------

class ConnectionConfig(BaseModel):
    """``ConnectionConfig`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
    host: str = Field(default_factory=_default_agent_host)
    port: int = Field(default_factory=_default_agent_port)
    endpoints: dict[str, str] = Field(default_factory=lambda: {
        "health": "/health",
        "execute": "/tasks/execute",
    })


# ---------------------------------------------------------------------------
# Config: backend
# ---------------------------------------------------------------------------

class BackendConfig(BaseModel):
    """``BackendConfig`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
    type: Literal["langchain", "none", "custom"] = "none"
    provider: Optional[str] = None
    model: Optional[str] = None
    temperature: float = 0.2
    system_prompt: Optional[str] = None
    # Call ``config: dict[str, Any] = Field``.
    config: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Config: execution
# ---------------------------------------------------------------------------

class ConcurrencyConfig(BaseModel):
    """``ConcurrencyConfig`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
    max_tasks: int = 1


class ExecutionConfig(BaseModel):
    """``ExecutionConfig`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
    mode: Literal["codegen", "direct_function", "tool_loop", "custom"] = "direct_function"
    language: str = "python"
    runner: str = "subprocess"
    template_prefix: Optional[str] = None
    template_suffix: Optional[str] = None
    work_dir: str = "/tmp/agent_runs"
    # Call ``concurrency: ConcurrencyConfig = Field``.
    concurrency: ConcurrencyConfig = Field(default_factory=ConcurrencyConfig)


# ---------------------------------------------------------------------------
# Config: reliability
# ---------------------------------------------------------------------------

class RetryBackoffConfig(BaseModel):
    """``RetryBackoffConfig`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
    strategy: Literal["fixed", "exponential"] = "exponential"
    base_secs: float = 2.0
    max_secs: float = 30.0


class ReliabilityConfig(BaseModel):
    """``ReliabilityConfig`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
    task_timeout_secs: float = 120.0
    max_retries: int = 0
    # Call ``retry_backoff: RetryBackoffConfig = Field``.
    retry_backoff: RetryBackoffConfig = Field(default_factory=RetryBackoffConfig)
    on_failure: Literal["replan", "abort", "skip", "dead_letter"] = "replan"
    # Call ``retry_on: list[str] = Field``.
    retry_on: list[str] = Field(default_factory=lambda: ["timeout", "transient_error"])
    # Call ``no_retry_on: list[str] = Field``.
    no_retry_on: list[str] = Field(default_factory=lambda: ["validation_error"])


# ---------------------------------------------------------------------------
# Config: capabilities (permissive — only id+description enforced)
# ---------------------------------------------------------------------------

class CapabilitySpec(BaseModel):
    """``CapabilitySpec`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
    model_config = {"extra": "allow"}

    id: str
    description: str
    # Call ``skill_params: dict[str, Any] = Field``.
    skill_params: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Config: skills
# ---------------------------------------------------------------------------

class SkillSpec(BaseModel):
    """``SkillSpec`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
    id: str
    description: str = ""
    module: str = "tools"
    callable: str
    timeout_secs: Optional[float] = None
    # Call ``args_defaults: dict[str, Any] = Field``.
    args_defaults: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Config: memory (per-store persistence)
# ---------------------------------------------------------------------------

class MemoryStoreConfig(BaseModel):
    """``MemoryStoreConfig`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
    model_config = {"extra": "allow"}

    id: str
    description: str = ""
    type: Literal["list", "key_value", "vector", "queue"] = "key_value"
    persistence: Literal["ephemeral", "redis", "file", "postgres"] = "ephemeral"
    # Call ``config: dict[str, Any] = Field``.
    config: dict[str, Any] = Field(default_factory=dict)
    # Call ``schema_def: dict[str, Any] = Field``.
    schema_def: dict[str, Any] = Field(default_factory=dict, alias="schema")
    max_items: Optional[int] = None
    ttl_secs: Optional[int] = None


class MemoryConfig(BaseModel):
    """``MemoryConfig`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
    stores: list[MemoryStoreConfig] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Config: observability
# ---------------------------------------------------------------------------

class TelemetryStreamConfig(BaseModel):
    """``TelemetryStreamConfig`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
    name: str
    description: str = ""


class TelemetryConfig(BaseModel):
    """``TelemetryConfig`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
    endpoint: str = "${TELEMETRY_URL}"
    # Call ``streams: list[TelemetryStreamConfig] = Field``.
    streams: list[TelemetryStreamConfig] = Field(default_factory=list)


class ObservabilityConfig(BaseModel):
    """``ObservabilityConfig`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
    heartbeat_interval_secs: float = Field(default_factory=_agent_heartbeat_interval)
    # Call ``telemetry: TelemetryConfig = Field``.
    telemetry: TelemetryConfig = Field(default_factory=TelemetryConfig)


# ---------------------------------------------------------------------------
# Config: deployment
# ---------------------------------------------------------------------------

class DeploymentConfig(BaseModel):
    """``DeploymentConfig`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
    image: str = ""
    dockerfile: str = "Dockerfile"
    # Call ``environment: dict[str, str] = Field``.
    environment: dict[str, str] = Field(default_factory=dict)
    # Call ``resources: dict[str, Any] = Field``.
    resources: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Config: metadata
# ---------------------------------------------------------------------------

class AgentMetadata(BaseModel):
    """``AgentMetadata`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
    name: str
    display_name: Optional[str] = None
    description: str = ""
    # Call ``labels: dict[str, str] = Field``.
    labels: dict[str, str] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Top-level AgentConfig
# ---------------------------------------------------------------------------

class AgentConfig(BaseModel):
    """``AgentConfig`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
    model_config = {"extra": "allow"}

    apiVersion: str = "agentfleet/v1"
    kind: Literal["Agent"] = "Agent"
    metadata: AgentMetadata
    # Call ``connection: ConnectionConfig = Field``.
    connection: ConnectionConfig = Field(default_factory=ConnectionConfig)
    # Call ``backend: BackendConfig = Field``.
    backend: BackendConfig = Field(default_factory=BackendConfig)
    # Call ``execution: ExecutionConfig = Field``.
    execution: ExecutionConfig = Field(default_factory=ExecutionConfig)
    # Call ``reliability: ReliabilityConfig = Field``.
    reliability: ReliabilityConfig = Field(default_factory=ReliabilityConfig)
    # Call ``capabilities: list[CapabilitySpec] = Field``.
    capabilities: list[CapabilitySpec] = Field(default_factory=list)
    # Call ``skills: list[SkillSpec] = Field``.
    skills: list[SkillSpec] = Field(default_factory=list)
    # Call ``memory: MemoryConfig = Field``.
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    # Call ``observability: ObservabilityConfig = Field``.
    observability: ObservabilityConfig = Field(default_factory=ObservabilityConfig)
    # Call ``deployment: DeploymentConfig = Field``.
    deployment: DeploymentConfig = Field(default_factory=DeploymentConfig)


# ---------------------------------------------------------------------------
# Health response
# ---------------------------------------------------------------------------

class AgentHealth(BaseModel):
    """``AgentHealth`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
    agent_id: str
    status: Literal["healthy", "unhealthy", "starting", "busy"] = "healthy"
    busy: bool = False
    # Call ``capabilities: list[str] = Field``.
    capabilities: list[str] = Field(default_factory=list)
    reliability: Optional[ReliabilityConfig] = None


# ---------------------------------------------------------------------------
# Backwards-compatible aliases
# ---------------------------------------------------------------------------
TaskRequest = AgentTaskRequest
# Local ``TaskResult`` ← AgentTaskResult.
TaskResult = AgentTaskResult
