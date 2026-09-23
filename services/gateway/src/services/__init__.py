"""
Business-logic services used by gateway routers.

Routers stay transport-oriented (HTTP status codes, Depends injection). This
package holds reusable operations that may be shared across multiple routes:

- Direct agent HTTP health probes (legacy/fallback).
- Telemetry service HTTP client (preferred heartbeat-based health).
- YAML scanners for agent templates and planner/allocator method metadata.
- Localhost port occupancy helpers for agent registration.

Importing this package re-exports the common entry points listed in ``__all__``.
No network I/O occurs at import time; clients and scanners run when called.
``close_telemetry_client`` is invoked from app lifespan shutdown.
"""

# Legacy direct HTTP probes against agent task servers.
from .agent_health import check_agent_health, check_all_agents_health
# Filesystem discovery of agent packages and planner/allocator summaries.
from .yaml_scanner import (
    scan_agent_templates,
    scan_planner_types,
    scan_allocator_types,
    scan_all_method_types,
    load_planner_summary,
    find_yaml_for_agent,
    get_allocation_strategy_id,
    get_planning_strategy_id,
)
# Port uniqueness helpers for localhost agent instances.
from .port_manager import get_used_ports, suggest_next_port, is_localhost
# Preferred health path: query the dedicated Telemetry microservice.
from .telemetry_client import (
    get_health_summary as get_telemetry_health_summary,
    get_agent_health as get_telemetry_agent_health,
    close_client as close_telemetry_client,
)

# Public symbols re-exported for ``from ..services import ...`` in routers.
__all__ = [
    # Agent health (direct polling - legacy/fallback)
    "check_agent_health",
    "check_all_agents_health",
    # Agent health from Telemetry service (preferred)
    "get_telemetry_health_summary",
    "get_telemetry_agent_health",
    "close_telemetry_client",
    # YAML scanning
    "scan_agent_templates",
    "scan_planner_types",
    "scan_allocator_types",
    "scan_all_method_types",
    "load_planner_summary",
    "find_yaml_for_agent",
    "get_allocation_strategy_id",
    "get_planning_strategy_id",
    # Port management
    "get_used_ports",
    "suggest_next_port",
    "is_localhost",
]
