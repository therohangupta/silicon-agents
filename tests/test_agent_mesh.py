"""Prove the running fleet agents answer HTTP and can call each other.

Skipped unless MEMORY_PLANE_TEST=1. The agent set is whatever startup.sh last
selected, so the test follows the containers instead of a fixed pair.

Locks in: host /health for each silicon-agents Compose service, docker-exec
peer HTTP execute between two agents, fleet_server ListAgents gRPC readiness,
and gateway /health plus /api/agent-templates category alignment with the registry.
"""

from __future__ import annotations

# Parse docker inspect JSON and peer script stdout.
import json
# Gate the module on MEMORY_PLANE_TEST.
import os
# docker ps / inspect / exec.
import subprocess
# sys.path for domains imports.
import sys
from pathlib import Path

# Host-side HTTP to published agent/gateway ports.
import httpx
import pytest

# agent_fleet root.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Registry lookup for embodiment category assertions.
from domains.eda.fleet import get_config
# gRPC stubs for fleet_server smoke check.
from packages.proto import fleet_manager_pb2, fleet_manager_pb2_grpc

# Skip the whole module unless the live plane flag is set.
pytestmark = pytest.mark.skipif(
    os.environ.get("MEMORY_PLANE_TEST") != "1",
    reason="Set MEMORY_PLANE_TEST=1 when the agent containers are running",
)


def _running_agents() -> list[dict]:
    """Discover running silicon-agents Compose containers and their host ports.

    Uses ``docker ps`` filtered by project label, then ``docker inspect`` for
    service name, container name, and the first published port binding.
    Returns a list sorted by host_port for stable caller/callee pairing.
    """
    # List container ids for the silicon-agents Compose project.
    ids = subprocess.check_output(
        ["docker", "ps", "-q", "--filter", "label=com.docker.compose.project=silicon-agents"],
        text=True,
    ).split()
    agents = []
    for container_id in ids:
        # Inspect returns a one-element list of container objects.
        inspected = json.loads(subprocess.check_output(["docker", "inspect", container_id], text=True))[0]
        labels = inspected["Config"]["Labels"]
        host_port = None
        container_port = None
        # Take the first published port mapping (agents publish one HTTP port).
        for key, binding in inspected["NetworkSettings"]["Ports"].items():
            if not binding:
                continue
            # key like "8202/tcp" -> container port.
            container_port = int(key.split("/")[0])
            # Host side of the binding.
            host_port = int(binding[0]["HostPort"])
            break
        agents.append({
            "service": labels["com.docker.compose.service"],
            "name": inspected["Name"].lstrip("/"),
            "host_port": host_port,
            "port": container_port,
        })
    # Stable order so agents[0]/agents[1] is deterministic across runs.
    agents.sort(key=lambda item: item["host_port"])
    return agents


def test_running_agents_are_healthy_and_call_each_other():
    """Live mesh: health, peer execute, fleet gRPC, gateway embodiments."""
    agents = _running_agents()
    # Need at least two agents to exercise peer HTTP.
    assert len(agents) >= 2, "startup.sh needs a fleet file with at least two agents"

    for agent in agents:
        # Host-published health must succeed.
        from packages.platform_config import load_platform
        platform = load_platform()
        health = httpx.get(
            f"{platform['http_scheme']}://{platform['process_host']}:{agent['host_port']}/health",
            timeout=10.0,
        )
        assert health.status_code == 200
        body = health.json()
        # agent_id matches Compose service name.
        assert body["agent_id"] == agent["service"]
        assert body["status"] == "healthy"
        # Capabilities list is non-empty for registered agents.
        assert body["capabilities"]

    # First two agents by host_port act as caller/callee.
    caller, callee = agents[0], agents[1]
    # Inside the caller container, HTTP to callee via Compose DNS + container port.
    peer = subprocess.run(
        [
            "docker", "exec", caller["name"],
            "python", "-c",
            (
                "import httpx, json; "
                f"health = httpx.get('http://{callee['service']}:{callee['port']}/health', timeout=20.0); "
                "health.raise_for_status(); "
                f"task = httpx.post('http://{callee['service']}:{callee['port']}/tasks/execute', timeout=60.0, "
                "json={'task_id': 'mesh-peer', 'description': 'check the peer'}); "
                "task.raise_for_status(); "
                "print(json.dumps({'health': health.json()['agent_id'], 'outcome': task.json().get('outcome'), "
                "'success': task.json().get('success')}))"
            ),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    # Last stdout line is the JSON summary from the in-container script.
    body = json.loads(peer.stdout.strip().splitlines()[-1])
    # Peer health identity matches callee service.
    assert body["health"] == callee["service"]
    # Execute reported success.
    assert body["success"] is True
    # Framework-unbound agents may be PARTIALLY_COMPLETED; both are acceptable.
    assert body["outcome"] in {"PARTIALLY_COMPLETED", "COMPLETED"}

    import grpc

    # Use published host port — ``setting()`` may see Compose shell exports
    # (container DNS names) that are not reachable from the test process.
    from packages.platform_config import host_settings

    channel = grpc.insecure_channel(host_settings()["GRPC_SERVER_ADDRESS"])
    # Block until the channel is ready or 10s elapse.
    grpc.channel_ready_future(channel).result(timeout=10)
    stub = fleet_manager_pb2_grpc.FleetManagerStub(channel)
    # ListAgents must return a response object (agents may be empty).
    listed = stub.ListAgents(fleet_manager_pb2.ListAgentsRequest(), timeout=10)
    assert listed is not None

    gateway_url = host_settings()["GATEWAY_URL"]
    gateway = httpx.get(f"{gateway_url}/health", timeout=10.0)
    assert gateway.status_code == 200
    # Embodiment registry from the gateway.
    embodiments = httpx.get(f"{gateway_url}/api/agent-templates", timeout=20.0)
    assert embodiments.status_code == 200
    by_name = {item["name"]: item for item in embodiments.json()}
    for agent in agents:
        # Category in the API matches the registry spec for that agent id.
        assert by_name[agent["service"]]["category"] == get_config(agent["service"]).category
