"""Contract tests for standard agent packages.

Parametrized over ``agents/*/*/config.yaml`` parents (two-level glob). Locks
in: config parse, ``/health`` + ``/tasks/execute`` via TestClient, and the
``tools.py`` callable surface declared by each agent configuration.
"""

from __future__ import annotations

from pathlib import Path

import pytest
# In-process ASGI client (no real network).
from fastapi.testclient import TestClient

# Server factory + request model.
from packages.agent_sdk import AgentServer, AgentTaskRequest
from packages.agent_sdk.src.schema.validator import AgentConfigValidator

# Agent dirs that match agents/<track-or-domain>/<name>/config.yaml.
AGENT_DIRS = list(Path(__file__).resolve().parents[2].glob("agents/*/*/config.yaml"))
# Convert config paths to package directories for parametrization.
AGENT_DIRS = [p.parent for p in AGENT_DIRS]


@pytest.mark.parametrize("agent_dir", AGENT_DIRS)
def test_config_parses(agent_dir: Path):
    """Each agent package config validates with named capabilities."""
    config_path = agent_dir / "config.yaml"
    # Historical fallback name if config.yaml missing.
    if not config_path.exists():
        config_path = agent_dir / "agent.yaml"
    config = AgentConfigValidator().validate_file(config_path)
    # metadata.name must be non-empty.
    assert config.metadata.name
    # At least one capability declared.
    assert config.capabilities
    for cap in config.capabilities:
        # Capability id and description are required fields.
        assert cap.id
        assert cap.description


@pytest.mark.parametrize("agent_dir", AGENT_DIRS)
def test_health_and_execute(agent_dir: Path):
    """AgentServer serves /health and accepts /tasks/execute for each package."""
    config_path = agent_dir / "config.yaml"
    if not config_path.exists():
        pytest.skip("no config.yaml")
    # Build ASGI app from the package config.
    server = AgentServer.from_config(config_path)
    client = TestClient(server.app)

    # Liveness/identity endpoint.
    health = client.get("/health")
    assert health.status_code == 200
    body = health.json()
    # agent_id matches metadata.name from config.
    assert body["agent_id"] == server.config.metadata.name

    # Minimal execute request.
    req = AgentTaskRequest(task_id="test-1", description="contract test task")
    resp = client.post("/tasks/execute", json=req.model_dump(mode="json"))
    assert resp.status_code == 200
    result = resp.json()
    # Result always includes success flag and traces list.
    assert "success" in result
    assert "traces" in result


@pytest.mark.parametrize("agent_dir", AGENT_DIRS)
def test_declared_tools_are_loadable(agent_dir: Path):
    """Every configured SDK skill resolves to a callable in ``tools.py``."""
    tools_path = agent_dir / "tools.py"
    assert tools_path.is_file()
    import importlib.util

    # Dynamic load matches AgentServer's local-tools registration path.
    spec = importlib.util.spec_from_file_location(f"_contract_tools_{agent_dir.name}", tools_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    config = AgentConfigValidator().validate_file(agent_dir / "config.yaml")
    for skill in config.skills:
        assert skill.module == "tools"
        assert callable(getattr(module, skill.callable))
