"""Domain-neutral configuration contracts for named memory stores."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class MemoryStoreConfig(BaseModel):
    """Configuration of one named memory store."""

    model_config = {"extra": "allow"}

    id: str
    description: str = ""
    type: Literal["list", "key_value", "vector", "queue"] = "key_value"
    persistence: Literal["ephemeral", "redis", "file", "postgres"] = "ephemeral"
    config: dict[str, Any] = Field(default_factory=dict)
    schema_def: dict[str, Any] = Field(default_factory=dict, alias="schema")
    max_items: Optional[int] = None
    ttl_secs: Optional[int] = None


class MemoryConfig(BaseModel):
    """Configuration of the named stores available to a runtime."""

    stores: list[MemoryStoreConfig] = Field(default_factory=list)
