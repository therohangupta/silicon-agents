"""
Robot SDK telemetry module.

Provides TelemetryPublisher for streaming canonical telemetry events
to the ingestion service via gRPC.
"""

from .publisher import TelemetryPublisher

__all__ = ["TelemetryPublisher"]
