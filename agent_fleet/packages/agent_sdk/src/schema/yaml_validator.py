from __future__ import annotations

"""Module ``agent_sdk/src/schema/yaml_validator.py``.

Agent SDK: HTTP task server, runtimes, skills, telemetry publisher, and workspace helpers for first-party agents.
Agent config.yaml / schema validation for agent packages.

Part of the agent SDK server/runtime stack: agents import these helpers to serve tasks over HTTP, run LLM/tool loops, publish telemetry, and persist plan workspaces.

Hand-written source for ``yaml_validator.py``. Behavior is unchanged; comments document control-plane / agent-runtime intent for maintainers.
"""


from .validator import AgentConfigValidator


class YAMLValidator:
    """``YAMLValidator`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
    def validate_file(self, path: str):
        """``YAMLValidator`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        return AgentConfigValidator().validate_file(path).model_dump(mode="json")
