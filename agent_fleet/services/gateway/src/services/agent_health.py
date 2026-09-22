"""
Direct HTTP health-checking helpers for agent task servers.

This module implements the legacy/fallback path used when callers pass
``source=direct`` to agent health endpoints. It pings common HTTP paths
(``/health``, then ``/``) on the agent's host:port with ``httpx.AsyncClient``
and treats any non-5xx response as reachable.

Preferred production path is heartbeat-derived health from the Telemetry
service (see ``telemetry_client.py``). Direct probes remain useful for local
debugging when Telemetry has not yet received heartbeats.

Timeouts come from ``HEALTH_CHECK_TIMEOUT_SECS``. Failures never raise to
callers; they return ``reachable=False`` with an ``error`` string so routers
can always return 200 JSON bodies for probe results (404 only if the agent
id itself is unknown at the fleet layer).
"""

from typing import List, Dict, Any
import httpx

# Timeout and default host/port when agent dicts omit task_server_info.
from ..config import HEALTH_CHECK_TIMEOUT_SECS, DEFAULT_AGENT_HOST, DEFAULT_AGENT_BASE_PORT


async def check_agent_health(
    host: str, 
    port: int, 
    timeout: float = HEALTH_CHECK_TIMEOUT_SECS
) -> Dict[str, Any]:
    """
    Probe a single agent's HTTP endpoints for liveness.

    Purpose:
        Determine whether the task server accepts HTTP without relying on
        Telemetry heartbeats.

    Args:
        host: Agent hostname or IP.
        port: Agent HTTP listen port.
        timeout: Per-client timeout seconds for the AsyncClient.

    Returns:
        Dict with ``reachable`` True and ``latency_ms`` on success, or
        ``reachable`` False and ``error`` describing timeout/connect/other.

    Side effects:
        Issues one or more outbound HTTP GETs to ``http://{host}:{port}/...``.

    Failure behavior:
        Does not raise; maps httpx timeout/connect and generic exceptions into
        the error dict shape. Continues to the next endpoint on per-path errors.
    """
    try:
        # One shared client for both candidate endpoints within this call.
        async with httpx.AsyncClient(timeout=timeout) as client:
            # Try common health endpoints
            for endpoint in ["/health", "/"]:
                try:
                    # Build absolute URL for this candidate path.
                    url = f"http://{host}:{port}{endpoint}"
                    # Perform the GET; httpx records elapsed time on the response.
                    response = await client.get(url)
                    # Accept any non-5xx response as "alive"
                    if response.status_code < 500:
                        return {
                            "reachable": True, 
                            "latency_ms": response.elapsed.total_seconds() * 1000
                        }
                except Exception:
                    # Try the next endpoint path if this one fails.
                    continue
            # Both endpoints failed without a non-5xx response.
            return {"reachable": False, "error": "No valid endpoint responded"}
    except httpx.TimeoutException:
        # Client-level timeout (no timely TCP/HTTP completion).
        return {"reachable": False, "error": "Connection timeout"}
    except httpx.ConnectError:
        # Nothing listening / connection refused.
        return {"reachable": False, "error": "Connection refused"}
    except Exception as e:
        # Catch-all so routers always get a structured result.
        return {"reachable": False, "error": str(e)}


async def check_all_agents_health(agents: List[Dict]) -> List[Dict[str, Any]]:
    """
    Sequentially health-check many agent dicts from the fleet registry.

    Purpose:
        Power ``GET /api/agents/health/all?source=direct`` by probing each
        agent's task_server_info host/port.

    Args:
        agents: List of agent dicts; each should include ``agent_id`` and
            optionally ``task_server_info`` with host/port.

    Returns:
        List of result dicts merging agent_id/host/port with each probe result.

    Side effects:
        One ``check_agent_health`` call per agent (sequential awaits).

    Failure behavior:
        Individual probe failures appear as reachable=False entries; this
        function does not raise for probe failures. Missing keys use defaults.
    """
    # Accumulator returned to the router.
    results = []
    for agent in agents:
        # Fall back to configured defaults when registration omitted network info.
        host = agent.get("task_server_info", {}).get("host", DEFAULT_AGENT_HOST)
        port = agent.get("task_server_info", {}).get("port", DEFAULT_AGENT_BASE_PORT)
        # Await the probe for this agent before moving on.
        health = await check_agent_health(host, port)
        # Merge identity + network + probe fields into one row.
        results.append({
            "agent_id": agent["agent_id"],
            "host": host,
            "port": port,
            **health
        })
    return results
