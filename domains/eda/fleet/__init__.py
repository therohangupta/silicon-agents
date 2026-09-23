"""Fleet registry, Docker compose selection, and workflow intake."""

from .compose import FleetSelectionError, SelectedAgent, render_compose, select_agents
from .registry import (
    EDARegistryError,
    all_configs,
    fleet_capability_index,
    get_config,
    validate_eda_registry,
)
from .workflow import (
    plan_and_allocate_eda_workflow,
    plan_eda_workflow,
    to_fleet_workflow,
)

__all__ = [
    "EDARegistryError",
    "FleetSelectionError",
    "SelectedAgent",
    "all_configs",
    "fleet_capability_index",
    "get_config",
    "plan_and_allocate_eda_workflow",
    "plan_eda_workflow",
    "render_compose",
    "select_agents",
    "to_fleet_workflow",
    "validate_eda_registry",
]
