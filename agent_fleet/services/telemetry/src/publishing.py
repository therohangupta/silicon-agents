"""
Publisher implementations for telemetry events.

Default implementation posts ``HealthChangedEvent`` JSON to the gateway
internal events URL. The class is intentionally thin so a future Kafka or
composite publisher can share the same ``publish`` / ``close`` shape used by
app lifespan and ingest routes without changing call sites.
"""

# stdlib logging for non-fatal gateway failures.
import logging

# httpx provides the async HTTP client with explicit timeouts.
import httpx

# Shared gateway URL from packages.config via local re-export.
from .config import GATEWAY_EVENT_URL
# Event model serialized with model_dump() for the POST body.
from .events import HealthChangedEvent

# Module logger named after this file for structured service logs.
logger = logging.getLogger(__name__)


class GatewayHealthChangedPublisher:
    """Publish health_changed events to the gateway via HTTP (current behavior).

    Lazily creates a single ``httpx.AsyncClient`` with a short timeout so
    repeated publishes reuse connections. Failures are logged as warnings;
    they never raise into the heartbeat path. Call ``close`` from lifespan
    shutdown to release sockets cleanly.
    """

    def __init__(self, gateway_event_url: str | None = None):
        """Store the target URL and defer client construction until first publish.

        Args:
            gateway_event_url: Optional override; defaults to ``GATEWAY_EVENT_URL``
                so tests can point at a mock without patching config.
        """
        # Prefer explicit override, else shared config default.
        self._url = gateway_event_url or GATEWAY_EVENT_URL
        # Lazy client avoids opening sockets during import/tests that never publish.
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Return a shared AsyncClient, creating it on first use.

        Timeout is 2 seconds so a hung gateway cannot stall heartbeat handling
        for long. The client is stored on ``self._client`` for reuse across
        publishes until ``close`` clears it.
        """
        # Create once; subsequent publishes reuse the same client.
        if self._client is None:
            # Short timeout: fire-and-forget toward the gateway.
            self._client = httpx.AsyncClient(timeout=2.0)
        # Always return the live client instance.
        return self._client

    async def publish(self, event: HealthChangedEvent) -> None:
        """POST the event JSON to the gateway; log and swallow transport errors.

        Skips the network call when ``agent_ids`` is empty (nothing changed).
        On HTTP 4xx/5xx, logs status and a truncated body. On connection
        errors, logs the exception string. Never re-raises.
        """
        # Empty fan-out list is a deliberate no-op.
        if not event.agent_ids:
            return
        try:
            # Ensure we have a client before posting.
            client = await self._get_client()
            # Serialize Pydantic model to a JSON-compatible dict for httpx.
            resp = await client.post(self._url, json=event.model_dump())
            # Treat any 4xx/5xx as soft failure; ingest already applied the heartbeat.
            if resp.status_code >= 400:
                logger.warning(
                    "Gateway event POST returned %d: %s",
                    resp.status_code,
                    # Truncate body so log lines stay manageable.
                    resp.text[:200],
                )
        except Exception as e:
            # Network blips and DNS failures must not fail the heartbeat route.
            logger.warning("Failed to publish health_changed to gateway: %s", e)

    async def close(self) -> None:
        """Close the underlying httpx client if one was created.

        Safe to call multiple times. Lifespan shutdown always invokes this so
        open connections do not linger after process exit.
        """
        # Only close if we ever opened a client.
        if self._client is not None:
            # aclose releases the connection pool.
            await self._client.aclose()
            # Allow a future publish to recreate the client if needed.
            self._client = None
