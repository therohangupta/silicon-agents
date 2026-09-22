"""Contract tests for config expansion and codegen execution.

Locks in ``_expand_env_string`` default syntax and that ``execution.mode:
codegen`` can call a registered ``@tool`` skill and return traces.
"""

from __future__ import annotations

# Drive the async runtime from a sync test.
import asyncio
# Mutate env for expansion cases.
import os
# Temporary agent package tree for codegen.
import tempfile
from pathlib import Path

# AgentServer + request model for codegen execution.
from packages.agent_sdk import AgentServer, AgentTaskRequest
# Validator + env expansion helper under test.
from packages.agent_sdk.src.schema.validator import AgentConfigValidator, _expand_env_string


def test_expand_env_default_syntax():
    """``${VAR:-default}`` uses default when unset/empty and value when set."""
    # Empty string should still trigger the default branch.
    os.environ["TEST_AGENT_DB"] = ""
    assert _expand_env_string("${TEST_AGENT_DB:-sqlite:///tmp/test.db}") == "sqlite:///tmp/test.db"
    # Non-empty overrides the default.
    os.environ["TEST_AGENT_DB"] = "postgres://real"
    assert _expand_env_string("${TEST_AGENT_DB:-sqlite:///tmp/test.db}") == "postgres://real"
    # Clean up so later tests are not polluted.
    del os.environ["TEST_AGENT_DB"]


def test_config_yaml_parses_with_defaults():
    """Missing telemetry env var expands to the inline default endpoint."""
    with tempfile.TemporaryDirectory() as tmp:
        cfg_path = Path(tmp) / "config.yaml"
        # Observability.telemetry.endpoint uses ${MISSING_TELEMETRY:-...}.
        cfg_path.write_text(
            """
apiVersion: agentfleet/v1
kind: Agent
metadata:
  name: env_agent
  description: test
connection:
  host: localhost
  port: 9000
backend:
  type: none
execution:
  mode: direct_function
observability:
  telemetry:
    endpoint: "${MISSING_TELEMETRY:-http://telemetry:9000}"
capabilities:
  - id: demo
    description: demo capability
skills: []
"""
        )
        config = AgentConfigValidator().validate_file(cfg_path)
        # Default endpoint applied because MISSING_TELEMETRY is unset.
        assert config.observability.telemetry.endpoint == "http://telemetry:9000"


def test_codegen_executes_registered_skill():
    """Codegen mode executes supplied code that calls a registered add skill."""

    async def _run():
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # Minimal tools module with one @tool.
            (root / "tools.py").write_text(
                """
from packages.agent_sdk import tool

@tool(description="Add")
def add(a: int = 0, b: int = 0):
    return a + b
"""
            )
            # Agent config pointing skills at tools.add in codegen mode.
            (root / "config.yaml").write_text(
                f"""
apiVersion: agentfleet/v1
kind: Agent
metadata:
  name: codegen_test
  description: codegen
connection:
  host: localhost
  port: 9000
backend:
  type: none
execution:
  mode: codegen
  work_dir: {root / "runs"}
skills:
  - id: add
    module: tools
    callable: add
    description: add numbers
"""
            )
            # Build server from the temp package.
            server = AgentServer.from_config(root / "config.yaml")
            # Execute codegen that calls the skill and returns artifacts.
            result = await server._runtime.execute(
                AgentTaskRequest(
                    task_id="1",
                    description="add numbers",
                    inputs={
                        "code": (
                            'def _main():\n'
                            '    value = _call_skill("add", a=2, b=3)\n'
                            '    return {"success": True, "message": str(value), "artifacts": {"value": value}}\n'
                        ),
                    },
                )
            )
            # Skill result surfaced as success + artifact.
            assert result.success
            assert result.artifacts.get("value") == 5
            # Traces include both code execution and the skill call.
            assert any(t.trace_type == "code_execution" for t in result.traces)
            assert any(t.trace_type == "skill_call" for t in result.traces)

    # Drive the async body from pytest's sync world.
    asyncio.run(_run())
