"""Observability configuration owned by the telemetry subsystem."""

from __future__ import annotations

from pydantic import BaseModel, Field

from packages.platform_config import setting


def _agent_heartbeat_interval() -> float:
    return float(setting("AGENT_HEARTBEAT_INTERVAL_SECS"))


class TelemetryStreamConfig(BaseModel):
    """One telemetry stream emitted by an agent process."""

    name: str
    description: str = ""


class TelemetryConfig(BaseModel):
    """Telemetry destination and stream declarations."""

    endpoint: str = "${TELEMETRY_URL}"
    streams: list[TelemetryStreamConfig] = Field(default_factory=list)


class ObservabilityConfig(BaseModel):
    """Heartbeat and telemetry settings for an agent process."""

    heartbeat_interval_secs: float = Field(default_factory=_agent_heartbeat_interval)
    telemetry: TelemetryConfig = Field(default_factory=TelemetryConfig)
