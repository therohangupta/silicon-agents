"""
EDA domain configuration composed on top of generic ``config/platform.yaml``.

Generic platform code lives in ``packages/platform_config`` and must not
reference the toolchain. This module owns:

  - ``domains/eda/platform.yaml`` (host-runtime address, agent address, framework)
  - Agent environment ``EDA_TOOLCHAIN_URL`` and ``EDA_FRAMEWORK``

Wiring:

  1. ``load_platform()`` — shared HTTP scheme, fleet/gateway/postgres, etc.
  2. ``load_eda_platform()`` — toolchain section only
  3. ``eda_agent_environment()`` — merge (1)+(2) at the Docker deployment edge

Call sites (never ``packages/``):

  - ``domains/eda/fleet.py`` — agent compose ``environment:``
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from packages.platform_config import PlatformConfigError, load_platform

EDA_PLATFORM_PATH = Path(__file__).resolve().parent / "platform.yaml"

_TOOLCHAIN_REQUIRED: dict[str, type] = {
    "bind_host": str,
    "port": int,
    "agent_host": str,
    "framework": str,
}


class EdaPlatformConfigError(RuntimeError):
    """Raised when ``domains/eda/platform.yaml`` is missing or invalid."""


_CACHE: dict[str, Any] | None = None


def _check_toolchain(block: object, where: str) -> None:
    if not isinstance(block, dict):
        raise EdaPlatformConfigError(f"{where} must be a mapping")
    missing = sorted(set(_TOOLCHAIN_REQUIRED) - set(block))
    if missing:
        raise EdaPlatformConfigError(f"{where} is missing {missing[0]}")
    for key, typ in _TOOLCHAIN_REQUIRED.items():
        value = block[key]
        if typ is int and (isinstance(value, bool) or not isinstance(value, int)):
            raise EdaPlatformConfigError(f"{where}.{key} must be an integer")
        if typ is str and (not isinstance(value, str) or not value.strip()):
            raise EdaPlatformConfigError(f"{where}.{key} must be a non-empty string")


def load_eda_platform() -> dict[str, Any]:
    """Return the EDA platform document from ``domains/eda/platform.yaml``."""
    global _CACHE
    if _CACHE is not None:
        return _CACHE
    if not EDA_PLATFORM_PATH.is_file():
        raise EdaPlatformConfigError(f"EDA platform config not found: {EDA_PLATFORM_PATH}")
    document = yaml.safe_load(EDA_PLATFORM_PATH.read_text())
    if not isinstance(document, dict):
        raise EdaPlatformConfigError(f"{EDA_PLATFORM_PATH} must be a mapping")
    _check_toolchain(document.get("toolchain"), f"{EDA_PLATFORM_PATH}.toolchain")
    _CACHE = document
    return document


def _origin(scheme: str, host: str, port: int) -> str:
    return f"{scheme}://{host}:{port}"


def eda_compose_values(
    eda_document: dict[str, Any] | None = None,
    platform_document: dict[str, Any] | None = None,
) -> dict[str, str]:
    """Expose the host-runtime endpoint to deployment templates."""
    return {
        "EDA_TOOLCHAIN_AGENT_URL": eda_agent_environment(
            eda_document, platform_document
        )["EDA_TOOLCHAIN_URL"],
        "EDA_TOOLCHAIN_PORT": str(
            (eda_document if eda_document is not None else load_eda_platform())["toolchain"]["port"]
        ),
    }


def eda_agent_environment(
    eda_document: dict[str, Any] | None = None,
    platform_document: dict[str, Any] | None = None,
) -> dict[str, str]:
    """Extra agent container env vars for EDA toolchain HTTP access."""
    eda = eda_document if eda_document is not None else load_eda_platform()
    platform = platform_document if platform_document is not None else load_platform()
    toolchain = eda["toolchain"]
    scheme = str(platform["http_scheme"])
    return {
        "EDA_TOOLCHAIN_URL": _origin(
            scheme, toolchain["agent_host"], toolchain["port"]
        ),
        "EDA_FRAMEWORK": str(toolchain["framework"]),
    }


def extend_compose_values(
    base: dict[str, str],
    eda_document: dict[str, Any] | None = None,
    platform_document: dict[str, Any] | None = None,
) -> None:
    """Merge EDA host-runtime placeholders into a deployment template."""
    base.update(eda_compose_values(eda_document, platform_document))


def merge_agent_environment(
    base: dict[str, str] | None = None,
    eda_document: dict[str, Any] | None = None,
    platform_document: dict[str, Any] | None = None,
) -> dict[str, str]:
    """Generic ``agent_environment()`` plus EDA toolchain URLs."""
    from packages.platform_config import agent_environment

    merged = dict(base if base is not None else agent_environment(platform_document))
    merged.update(eda_agent_environment(eda_document, platform_document))
    return merged
