"""
Event models and publisher protocol for telemetry fan-out.

Defines the stable ``HealthChangedEvent`` payload shape so the same JSON can
be POSTed to the gateway today or published on a message bus later without
changing ingest call sites. ``HealthChangedPublisher`` is a structural
Protocol: ingest only calls ``publish``; lifespan plugs in the HTTP
implementation (or a future Kafka/composite publisher).
"""

# Protocol enables duck-typed publishers without an ABC inheritance tax.
from typing import Protocol

# Pydantic BaseModel gives JSON-friendly serialization via model_dump().
from pydantic import BaseModel


class HealthChangedEvent(BaseModel):
    """Event emitted when effective reachable status changes for one or more agents.

    ``type`` is fixed to ``telemetry.health_changed`` so the gateway can route
    the payload among other internal events. ``agent_ids`` lists the keys that
    changed (usually ``host:port`` strings from heartbeat identity). ``ts`` is
    an optional Unix timestamp for UI freshness; publishers may leave it None
    and let the consumer stamp receive time instead.
    """

    # Discriminator string consumed by the gateway internal event router.
    type: str = "telemetry.health_changed"
    # One or more agent keys whose effective reachable flipped.
    agent_ids: list[str]
    # Optional event time; ingest usually sets time.time() when publishing.
    ts: float | None = None


class HealthChangedPublisher(Protocol):
    """Pluggable fan-out: implement with HTTP to gateway, Kafka, or both.

    Implementations must be async and should treat failures as non-fatal
    (log and continue) so a down gateway never blocks heartbeat ingest.
    """

    async def publish(self, event: HealthChangedEvent) -> None:
        """Publish a health_changed event. Fire-and-forget; log and ignore errors.

        Called after the heartbeat store reports an effective-reachable flip or
        after the timeout scanner marks agents unreachable. Empty ``agent_ids``
        should be a no-op in concrete implementations.
        """
        # Protocol body is ellipsis; concrete classes provide the real work.
        ...
