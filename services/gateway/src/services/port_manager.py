"""
Port allocation helpers for locally hosted agent instances.

When many "fake" or local agents share ``localhost``, the dashboard must avoid
assigning the same task-server port twice. This module queries the fleet
registry (via ``get_bridge().list_agents``) for ports already claimed and can
suggest the next free integer starting at ``DEFAULT_AGENT_BASE_PORT``.

``is_localhost`` centralizes the host strings treated as loopback so the
agents router can enforce uniqueness only when binding would collide on the
same machine. Remote hosts skip the used-port check because collisions are
not knowable from the gateway alone.
"""

from typing import Set

# Default starting port when suggesting the next free value.
from ..config import DEFAULT_AGENT_BASE_PORT
# Bridge singleton supplies the current agent list (must be initialized).
from ..dependencies import get_bridge


def is_localhost(host: str) -> bool:
    """
    Return True if ``host`` refers to the local loopback interface family.

    Purpose:
        Gate localhost-only port collision checks during agent registration.

    Args:
        host: Hostname or IP string from the registration request.

    Returns:
        True for localhost / 127.0.0.1 / 0.0.0.0 / ::1 (case-insensitive host).

    Side effects:
        None.

    Failure behavior:
        Never raises; unknown hosts return False.
    """
    # Normalize case so "LocalHost" still matches.
    return host.lower() in ('localhost', '127.0.0.1', '0.0.0.0', '::1')


def get_used_ports() -> Set[int]:
    """
    Collect TCP ports already assigned to registered agents' task servers.

    Purpose:
        Feed registration validation and ``suggest_next_port``.

    Args:
        None (reads live fleet state via gRPC bridge).

    Returns:
        Set of integer ports currently recorded on agents.

    Side effects:
        Calls ``get_bridge().list_agents("all")`` (gRPC).

    Failure behavior:
        Propagates RuntimeError if bridge uninitialized, or client errors from
        list_agents. Agents without task_server_info/port are skipped.
    """
    # Resolve the process-wide bridge (raises if lifespan did not init).
    bridge = get_bridge()
    # Ask fleet for every known agent regardless of deploy filter.
    agents = bridge.list_agents("all")
    
    # Build the occupancy set incrementally.
    used = set()
    for agent in agents:
        # Nested dict may be None when agent has no task server info yet.
        task_server = agent.get("task_server_info")
        if task_server and task_server.get("port"):
            # Record the claimed port number.
            used.add(task_server["port"])
    
    return used


def suggest_next_port(base_port: int = DEFAULT_AGENT_BASE_PORT) -> int:
    """
    Find the lowest available port at or above ``base_port``.

    Purpose:
        Help the UI pre-fill a free port when creating a local agent instance.

    Args:
        base_port: Inclusive start of the search (default from config).

    Returns:
        First integer ``>= base_port`` not present in ``get_used_ports()``.

    Side effects:
        Indirectly lists agents via ``get_used_ports``.

    Failure behavior:
        Propagates errors from ``get_used_ports``. Infinite loop is avoided
        practically because ports are finite in use; theoretically increments forever.
    """
    # Snapshot currently claimed ports.
    used = get_used_ports()
    # Start searching at the requested base.
    port = base_port
    # Walk upward until a free port is found.
    while port in used:
        port += 1
    return port
