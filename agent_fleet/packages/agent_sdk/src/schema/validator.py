from __future__ import annotations

"""Module ``agent_sdk/src/schema/validator.py``.

Agent SDK: HTTP task server, runtimes, skills, telemetry publisher, and workspace helpers for first-party agents.
Agent config.yaml / schema validation for agent packages.

Part of the agent SDK server/runtime stack: agents import these helpers to serve tasks over HTTP, run LLM/tool loops, publish telemetry, and persist plan workspaces.

Hand-written source for ``validator.py``. Behavior is unchanged; comments document control-plane / agent-runtime intent for maintainers.
"""


import os
import re
from pathlib import Path
from typing import Any

import yaml

from ..models import AgentConfig


# Local ``_ENV_DEFAULT_PATTERN`` ← re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-([^}]*))?\}").
_ENV_DEFAULT_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-([^}]*))?\}")


def _expand_env_string(value: str) -> str:
    """Expand $VAR, ${VAR}, and shell-style ${VAR:-default} placeholders."""
    expanded = os.path.expandvars(value)

    def replace(match: re.Match[str]) -> str:
        """``_expand_env_string`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        name = match.group(1)
        # Local ``default`` ← match.group(2).
        default = match.group(2)
        # Local ``env_value`` ← os.environ.get(name).
        env_value = os.environ.get(name)
        # Only when (env_value not in (None, "")).
        if env_value not in (None, ""):
            return env_value
        if default is not None:
            return default
        from packages.platform_config import host_settings

        values = host_settings()
        if name in values and values[name]:
            return values[name]
        return ""

    # Hand ``_ENV_DEFAULT_PATTERN.sub(replace, expanded)`` back to the caller.
    return _ENV_DEFAULT_PATTERN.sub(replace, expanded)


def _expand_env(value: Any) -> Any:
    """``_expand_env`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
    if isinstance(value, str):
        # Hand ``_expand_env_string(value)`` back to the caller.
        return _expand_env_string(value)
    # Only when (isinstance(value, list)).
    if isinstance(value, list):
        # Hand ``[_expand_env(item) for item in value]`` back to the caller.
        return [_expand_env(item) for item in value]
    # Only when (isinstance(value, dict)).
    if isinstance(value, dict):
        # Hand ``{key: _expand_env(item) for key, item in value.items()}`` back to the caller.
        return {key: _expand_env(item) for key, item in value.items()}
    # Hand ``value`` back to the caller.
    return value


def _migrate_legacy_config(data: dict[str, Any]) -> dict[str, Any]:
    """Map old agent.yaml fields to the new config.yaml contract."""
    if "connection" in data:
        # Hand ``data`` back to the caller.
        return data

    # Local ``migrated`` ← dict(data).
    migrated = dict(data)

    # Only when ("runtime" in data and "connection" not in migrated).
    if "runtime" in data and "connection" not in migrated:
        # Local ``rt`` ← data["runtime"].
        rt = data["runtime"]
        migrated["connection"] = {
            "host": rt.get("host", "localhost"),
            "port": rt.get("port", 8001),
            "endpoints": rt.get("endpoints", {
                "health": "/health",
                "execute": "/tasks/execute",
            }),
        }
        # Only when ("concurrency" in rt).
        if "concurrency" in rt:
            # Call ``migrated.setdefault``.
            migrated.setdefault("execution", {})
            # Only when (isinstance(migrated["execution"], dict)).
            if isinstance(migrated["execution"], dict):
                migrated["execution"]["concurrency"] = rt["concurrency"]

    # Only when ("backend" in data).
    if "backend" in data:
        # Local ``bt`` ← data["backend"].get("type", "none").
        bt = data["backend"].get("type", "none")
        # Only when (bt == "python_function").
        if bt == "python_function":
            migrated["backend"] = {**data["backend"], "type": "none"}
            # Call ``migrated.setdefault``.
            migrated.setdefault("execution", {})
            # Only when (isinstance(migrated["execution"], dict)).
            if isinstance(migrated["execution"], dict):
                migrated["execution"]["mode"] = "direct_function"

    # Only when ("memory" in data and "stores" in data.get("memory", {})).
    if "memory" in data and "stores" in data.get("memory", {}):
        # Local ``mem`` ← data["memory"].
        mem = data["memory"]
        # Only when ("backend" in mem).
        if "backend" in mem:
            # Local ``global_type`` ← mem["backend"].get("type", "dict").
            global_type = mem["backend"].get("type", "dict")
            # Local ``persistence`` ← "redis" if global_type == "redis" else "ephemeral".
            persistence = "redis" if global_type == "redis" else "ephemeral"
            # Local ``stores`` ← [].
            stores = []
            # Loop: for store in mem.get("stores", []).
            for store in mem.get("stores", []):
                # Local ``s`` ← dict(store).
                s = dict(store)
                # Only when ("persistence" not in s).
                if "persistence" not in s:
                    s["persistence"] = persistence
                # Call ``stores.append``.
                stores.append(s)
            migrated["memory"] = {"stores": stores}

    # Only when ("observability" in data).
    if "observability" in data:
        # Local ``obs`` ← data["observability"].
        obs = data["observability"]
        # Only when ("telemetry_streams" in obs and "telemetry" not in obs).
        if "telemetry_streams" in obs and "telemetry" not in obs:
            # Call ``migrated.setdefault``.
            migrated.setdefault("observability", dict(obs))
            migrated["observability"]["telemetry"] = {
                "streams": obs["telemetry_streams"],
            }

    # Only when ("metadata" in data).
    if "metadata" in data:
        # Local ``meta`` ← data["metadata"].
        meta = data["metadata"]
        # Only when ("tags" in meta and "labels" not in meta).
        if "tags" in meta and "labels" not in meta:
            # Local ``labels`` ← {}.
            labels = {}
            # Loop: for tag in meta.get("tags", []).
            for tag in meta.get("tags", []):
                labels[tag] = tag
            # Call ``migrated.setdefault``.
            migrated.setdefault("metadata", dict(meta))
            migrated["metadata"]["labels"] = labels

    # Only when ("taskServer" in data).
    if "taskServer" in data:
        # Local ``ts`` ← data["taskServer"].
        ts = data["taskServer"]
        migrated["connection"] = {
            "host": ts.get("host", "localhost"),
            "port": ts.get("port", 8001),
            "endpoints": {"health": "/health", "execute": "/tasks/execute"},
        }
        # Call ``migrated.setdefault``.
        migrated.setdefault("metadata", {})
        # Only when ("name" not in migrated.get("metadata", {})).
        if "name" not in migrated.get("metadata", {}):
            # Call ``migrated["metadata"]["name"] = data.get``.
            migrated["metadata"]["name"] = data.get("name", data.get("agentType", "agent"))

    # Only when ("capabilities" in data).
    if "capabilities" in data:
        # Local ``caps`` ← [].
        caps = []
        # Loop: for cap in data["capabilities"].
        for cap in data["capabilities"]:
            # Only when (isinstance(cap, str)).
            if isinstance(cap, str):
                # Call ``caps.append``.
                caps.append({"id": cap.replace(" ", "_")[:64], "description": cap})
            else:
                # Call ``caps.append``.
                caps.append(cap)
        migrated["capabilities"] = caps

    # Call ``migrated.setdefault``.
    migrated.setdefault("apiVersion", "agentfleet/v1")
    # Call ``migrated.setdefault``.
    migrated.setdefault("kind", "Agent")

    # Hand ``migrated`` back to the caller.
    return migrated


class AgentConfigValidator:
    """``AgentConfigValidator`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
    def validate_file(self, path: str | Path) -> AgentConfig:
        """``AgentConfigValidator`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        path = Path(path)
        # Hold ``path.open()`` for the duration of the indented block.
        with path.open() as fh:
            # Local ``data`` ← yaml.safe_load(fh) or {}.
            data = yaml.safe_load(fh) or {}
        # Local ``data`` ← _expand_env(data).
        data = _expand_env(data)
        # Local ``data`` ← _migrate_legacy_config(data).
        data = _migrate_legacy_config(data)
        # Hand ``AgentConfig(**data)`` back to the caller.
        return AgentConfig(**data)

    def validate_dict(self, data: dict[str, Any]) -> AgentConfig:
        """``validate_dict`` — agent_fleet packages helper; see body comments for step-by-step behavior."""
        data = _expand_env(data)
        # Local ``data`` ← _migrate_legacy_config(data).
        data = _migrate_legacy_config(data)
        # Hand ``AgentConfig(**data)`` back to the caller.
        return AgentConfig(**data)
