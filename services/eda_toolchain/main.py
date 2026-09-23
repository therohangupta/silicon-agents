"""Generic, configuration-driven HTTP host for tool providers."""

from __future__ import annotations

import importlib
import os
from pathlib import Path
from typing import Any, Mapping, cast

from fastapi import FastAPI
from pydantic import BaseModel, Field
import yaml

from .providers.base import Provider


CONFIG_PATH = Path(
    os.environ.get(
        "TOOLCHAIN_PROVIDER_CONFIG",
        Path(__file__).resolve().parents[2] / "domains" / "eda" / "toolchain.yaml",
    )
)


class ToolRequest(BaseModel):
    """Generic request validated before delegation to the configured provider."""

    operation: str
    params: dict[str, Any] = Field(default_factory=dict)
    agent_id: str = ""


def _load_provider() -> Provider:
    try:
        raw = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise RuntimeError(f"invalid provider configuration {CONFIG_PATH}: {error}") from error
    if not isinstance(raw, dict):
        raise RuntimeError(f"invalid provider configuration {CONFIG_PATH}: expected a mapping")
    provider = raw.get("provider")
    if not isinstance(provider, dict):
        raise RuntimeError(f"invalid provider configuration {CONFIG_PATH}: missing provider mapping")
    implementation = provider.get("implementation")
    config = provider.get("config")
    if not isinstance(implementation, str) or ":" not in implementation:
        raise RuntimeError("provider.implementation must be a 'module:attribute' string")
    if not isinstance(config, dict):
        raise RuntimeError("provider.config must be a mapping")
    module_name, attribute = implementation.split(":", maxsplit=1)
    try:
        factory = getattr(importlib.import_module(module_name), attribute)
    except (ImportError, AttributeError) as error:
        raise RuntimeError(f"unable to load provider {implementation}: {error}") from error
    instance = factory(cast(Mapping[str, Any], config))
    for method in ("health", "capabilities", "run"):
        if not callable(getattr(instance, method, None)):
            raise RuntimeError(f"provider {implementation} does not implement {method}()")
    return cast(Provider, instance)


PROVIDER = _load_provider()
app = FastAPI(title="Tool provider host")


@app.get("/healthz")
def health() -> dict[str, Any]:
    return PROVIDER.health()


@app.get("/capabilities")
def capabilities() -> dict[str, Any]:
    return PROVIDER.capabilities()


@app.post("/run")
def run(request: ToolRequest) -> dict[str, Any]:
    return PROVIDER.run(request)
