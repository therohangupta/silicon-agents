"""Top-level agent process configuration."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

from packages.memory.config import MemoryConfig

from ..skills.declarations import CapabilityDeclaration, SkillDeclaration
from ..telemetry.config import ObservabilityConfig
from .runtime import BackendConfig, ConnectionConfig, ExecutionConfig, ReliabilityConfig


class DeploymentConfig(BaseModel):
    """Container image and resource configuration for an agent process."""

    image: str = ""
    dockerfile: str = "Dockerfile"
    environment: dict[str, str] = Field(default_factory=dict)
    resources: dict[str, Any] = Field(default_factory=dict)


class AgentMetadata(BaseModel):
    """Human-readable identity and labels for an agent process."""

    name: str
    display_name: Optional[str] = None
    description: str = ""
    labels: dict[str, str] = Field(default_factory=dict)


class AgentConfig(BaseModel):
    """Complete configuration consumed by an agent process."""

    model_config = {"extra": "allow"}

    apiVersion: str = "agentfleet/v1"
    kind: Literal["Agent"] = "Agent"
    metadata: AgentMetadata
    connection: ConnectionConfig = Field(default_factory=ConnectionConfig)
    backend: BackendConfig = Field(default_factory=BackendConfig)
    execution: ExecutionConfig = Field(default_factory=ExecutionConfig)
    reliability: ReliabilityConfig = Field(default_factory=ReliabilityConfig)
    capabilities: list[CapabilityDeclaration] = Field(default_factory=list)
    skills: list[SkillDeclaration] = Field(default_factory=list)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    observability: ObservabilityConfig = Field(default_factory=ObservabilityConfig)
    deployment: DeploymentConfig = Field(default_factory=DeploymentConfig)
