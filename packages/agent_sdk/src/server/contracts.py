"""HTTP server response contracts."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

from ..config import ReliabilityConfig


class AgentHealth(BaseModel):
    """Health state returned by an agent process."""

    agent_id: str
    status: Literal["healthy", "unhealthy", "starting", "busy"] = "healthy"
    busy: bool = False
    capabilities: list[str] = Field(default_factory=list)
    reliability: Optional[ReliabilityConfig] = None
