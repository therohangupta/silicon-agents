"""Uniqueness rules shared by every agent registry."""

from __future__ import annotations

from .agent import AgentConfig


class AgentRegistryError(ValueError):
    """Registered agents collide on id, port, or class name."""


def agent_class_name(agent_id: str) -> str:
    """Build the conventional Python class name for an agent id."""
    return "".join(part.capitalize() for part in agent_id.split("_")) + "Agent"


def validate_agent_registry(configs: list[AgentConfig]) -> None:
    """Require unique agent ids, listen ports, and derived class names."""
    ids = [config.metadata.name for config in configs]
    if len(ids) != len(set(ids)):
        raise AgentRegistryError("Duplicate agent id")
    ports = [config.connection.port for config in configs]
    if len(ports) != len(set(ports)):
        raise AgentRegistryError("Duplicate agent port")
    names = [agent_class_name(agent_id) for agent_id in ids]
    if len(names) != len(set(names)):
        raise AgentRegistryError("Duplicate class name")
