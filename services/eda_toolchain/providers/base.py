"""Typed contract implemented by configurable tool providers."""

from __future__ import annotations

from typing import Any, Mapping, Protocol


class ToolRequestLike(Protocol):
    """The validated request shape supplied by the provider host."""

    operation: str
    params: dict[str, Any]
    agent_id: str


class Provider(Protocol):
    """Contract for a provider loaded by the generic HTTP host."""

    def __init__(self, config: Mapping[str, Any]) -> None: ...

    def health(self) -> dict[str, Any]: ...

    def capabilities(self) -> dict[str, Any]: ...

    def run(self, request: ToolRequestLike) -> dict[str, Any]: ...
