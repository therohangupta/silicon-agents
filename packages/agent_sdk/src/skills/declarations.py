"""Domain-neutral declarations for agent capabilities and skills."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class CapabilityDeclaration(BaseModel):
    """An advertised capability with optional skill arguments."""

    model_config = {"extra": "allow"}

    id: str
    description: str
    skill_params: dict[str, Any] = Field(default_factory=dict)


class ParameterDeclaration(BaseModel):
    """A documented input accepted by a skill."""

    name: str
    description: str = ""


class RoleDeclaration(BaseModel):
    """A domain-defined role without imposed role categories."""

    id: str
    description: str = ""


class OperationDeclaration(BaseModel):
    """A domain-defined operation without imposed operation semantics."""

    id: str
    description: str = ""


class SkillDeclaration(BaseModel):
    """A callable skill exposed by an agent."""

    id: str
    description: str = ""
    module: str = "tools"
    callable: str
    timeout_secs: Optional[float] = None
    args_defaults: dict[str, Any] = Field(default_factory=dict)
    parameters: list[ParameterDeclaration] = Field(default_factory=list, alias="params")

    @property
    def name(self) -> str:
        """Callable identifier used by the runtime."""

        return self.callable
