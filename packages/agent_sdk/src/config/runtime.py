"""Runtime connection, backend, execution, and reliability configuration."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

from packages.platform_config import setting


def _default_agent_host() -> str:
    return setting("DEFAULT_AGENT_HOST")


def _default_agent_port() -> int:
    return int(setting("DEFAULT_AGENT_BASE_PORT"))


class ConnectionConfig(BaseModel):
    """HTTP connection settings for an agent process."""

    host: str = Field(default_factory=_default_agent_host)
    port: int = Field(default_factory=_default_agent_port)
    endpoints: dict[str, str] = Field(
        default_factory=lambda: {
            "health": "/health",
            "execute": "/tasks/execute",
        }
    )


class BackendConfig(BaseModel):
    """Model or custom backend selected by an agent runtime."""

    type: Literal["langchain", "none", "custom"] = "none"
    provider: Optional[str] = None
    model: Optional[str] = None
    temperature: float = 0.2
    system_prompt: Optional[str] = None
    config: dict[str, Any] = Field(default_factory=dict)


class ConcurrencyConfig(BaseModel):
    """Concurrency cap for agent task execution."""

    max_tasks: int = 1


class ExecutionConfig(BaseModel):
    """Execution mode and runner settings for an agent runtime."""

    mode: Literal["codegen", "direct_function", "tool_loop", "custom"] = "direct_function"
    language: str = "python"
    runner: str = "subprocess"
    template_prefix: Optional[str] = None
    template_suffix: Optional[str] = None
    work_dir: str = "/tmp/agent_runs"
    concurrency: ConcurrencyConfig = Field(default_factory=ConcurrencyConfig)


class RetryBackoffConfig(BaseModel):
    """Retry delay policy."""

    strategy: Literal["fixed", "exponential"] = "exponential"
    base_secs: float = 2.0
    max_secs: float = 30.0


class ReliabilityConfig(BaseModel):
    """Timeout, retry, and failure policy for agent task execution."""

    task_timeout_secs: float = 120.0
    max_retries: int = 0
    retry_backoff: RetryBackoffConfig = Field(default_factory=RetryBackoffConfig)
    on_failure: Literal["replan", "abort", "skip", "dead_letter"] = "replan"
    retry_on: list[str] = Field(default_factory=lambda: ["timeout", "transient_error"])
    no_retry_on: list[str] = Field(default_factory=lambda: ["validation_error"])
