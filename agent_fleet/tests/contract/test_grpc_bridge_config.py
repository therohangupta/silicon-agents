"""Gateway registration must read agentfleet/v1 connection block.

Locks in ``services.gateway.src.grpc_bridge`` helpers that extract connection,
deployment, and capability ids from a validated agent config dict so gateway
registration stays aligned with the YAML schema.
"""

from __future__ import annotations

# Temporary directory for a synthetic config.yaml.
import tempfile
from pathlib import Path

# Helpers under contract.
from services.gateway.src.grpc_bridge import (
    _capabilities_from_config,
    _connection_from_config,
    _deployment_from_config,
)
# Validate then model_dump to the dict shape the bridge expects.
from packages.agent_sdk.src.schema.validator import AgentConfigValidator


def test_connection_from_v1_config():
    """v1 connection/deployment/capabilities round-trip through bridge helpers."""
    with tempfile.TemporaryDirectory() as tmp:
        # Write a minimal but valid agentfleet/v1 document.
        path = Path(tmp) / "config.yaml"
        path.write_text(
            """
apiVersion: agentfleet/v1
kind: Agent
metadata:
  name: test_agent
  description: test
connection:
  host: 10.0.0.5
  port: 8123
backend:
  type: none
execution:
  mode: direct_function
capabilities:
  - id: demo
    description: demo cap
skills: []
deployment:
  image: agentfleet/test:1.0
  environment:
    FOO: bar
"""
        )
        # Validate and dump to JSON-mode dict (bridge input shape).
        config = AgentConfigValidator().validate_file(path).model_dump(mode="json")
        # Connection host/port come from the connection block.
        conn = _connection_from_config(config)
        assert conn["host"] == "10.0.0.5"
        assert conn["port"] == 8123
        # Deployment image/env come from the deployment block.
        dep = _deployment_from_config(config)
        assert dep["image"] == "agentfleet/test:1.0"
        assert dep["environment"]["FOO"] == "bar"
        # Capabilities reduce to id strings.
        assert _capabilities_from_config(config) == ["demo"]
