"""Load a domain-neutral ``AgentConfig`` from ``config.yaml``."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from packages.platform_config import host_settings

from .agent import AgentConfig

_ENV_DEFAULT_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-([^}]*))?\}")


class AgentConfigError(ValueError):
    """A config file is missing, unreadable, or is not a valid ``AgentConfig``."""


def expand_env_string(value: str) -> str:
    """Expand ``$VAR``, ``${VAR}``, and ``${VAR:-default}`` placeholders."""

    def replace(match: re.Match[str]) -> str:
        name = match.group(1)
        default = match.group(2)
        env_value = os.environ.get(name)
        if env_value not in (None, ""):
            return env_value
        if default is not None:
            return default
        values = host_settings()
        if name in values and values[name]:
            return values[name]
        return ""

    return _ENV_DEFAULT_PATTERN.sub(replace, os.path.expandvars(value))


def expand_env(value: Any) -> Any:
    """Expand environment placeholders in strings, lists, and mappings."""
    if isinstance(value, str):
        return expand_env_string(value)
    if isinstance(value, list):
        return [expand_env(item) for item in value]
    if isinstance(value, dict):
        return {key: expand_env(item) for key, item in value.items()}
    return value


def load_agent_document(path: str | Path) -> dict[str, Any]:
    """Read one YAML file and expand environment placeholders.

    ``path`` may be a ``config.yaml`` file or a directory containing one.
    """
    config_path = _config_path(path)
    try:
        document = yaml.safe_load(config_path.read_text()) or {}
    except OSError as exc:
        raise AgentConfigError(f"Cannot read {config_path}") from exc
    except yaml.YAMLError as exc:
        raise AgentConfigError(f"Invalid YAML in {config_path}") from exc
    if not isinstance(document, dict):
        raise AgentConfigError(f"{config_path} must contain a mapping")
    expanded = expand_env(document)
    if not isinstance(expanded, dict):
        raise AgentConfigError(f"{config_path} must contain a mapping")
    return expanded


def load_agent_config(path: str | Path, document: dict[str, Any] | None = None) -> AgentConfig:
    """Validate ``config.yaml`` as a generic ``AgentConfig``.

    Domain loaders call this first, then add their own fields from the same
    document. Pass ``document`` when the caller already read it.
    """
    config_path = _config_path(path)
    payload = load_agent_document(config_path) if document is None else document
    try:
        return AgentConfig.model_validate(payload)
    except ValidationError as exc:
        raise AgentConfigError(f"Invalid agent config {config_path}: {exc}") from exc


def load_agent_config_dict(path: str | Path) -> dict[str, Any]:
    """Return the validated config as a JSON-compatible mapping."""
    return load_agent_config(path).model_dump(mode="json")


def _config_path(path: str | Path) -> Path:
    candidate = Path(path)
    if candidate.is_dir():
        candidate = candidate / "config.yaml"
    if not candidate.is_file():
        raise AgentConfigError(f"Config file not found: {candidate}")
    return candidate
