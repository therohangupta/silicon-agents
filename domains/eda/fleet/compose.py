"""EDA entry points for fleet selection. Compose rendering lives in the fleet SDK."""

from __future__ import annotations

from packages.fleet_sdk.src.selection import (
    FleetSelectionError,
    RegisteredAgent,
    SelectedAgent,
    render_compose as render_selected_compose,
    select_agents as select_registered_agents,
)

from ..config.models import EDAAgentConfig
from .platform_config import merge_agent_environment
from .registry import all_configs

__all__ = [
    "FleetSelectionError",
    "SelectedAgent",
    "render_compose",
    "select_agents",
]


def select_agents(
    document: object,
    configs: list[EDAAgentConfig] | None = None,
) -> list[SelectedAgent]:
    """Select EDA agents with the generic fleet selector."""
    loaded = list(configs) if configs is not None else all_configs()
    registered = [
        RegisteredAgent(agent_id=cfg.agent_id, directory=cfg.fleet_path, port=cfg.port)
        for cfg in loaded
    ]
    return select_registered_agents(document, registered)


def render_compose(agents: list[SelectedAgent]) -> str:
    """Render Compose for the selection, including EDA toolchain environment."""
    return render_selected_compose(agents, merge_agent_environment())
