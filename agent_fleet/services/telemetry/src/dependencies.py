"""
FastAPI dependencies for the telemetry service.

Centralizes Request-scoped lookups so route handlers stay free of
``request.app.state`` plumbing. Today only the health-changed publisher is
exposed; additional dependencies (message bus, blob store) can be added here
with the same pattern without changing router signatures beyond Depends().
"""

# FastAPI Request carries the app (and thus lifespan-populated state).
from fastapi import Request

# Protocol type so Depends annotations stay implementation-agnostic.
from .events import HealthChangedPublisher


def get_publisher(request: Request) -> HealthChangedPublisher:
    """Return the pluggable health_changed publisher installed during lifespan.

    Reads ``request.app.state.health_changed_publisher``, which ``app.lifespan``
    sets to a ``GatewayHealthChangedPublisher`` (or a future composite). Route
    handlers declare ``Depends(get_publisher)`` so tests can override the
    dependency without patching module globals. Raises AttributeError if the
    app was constructed without running lifespan (misconfigured test harness).
    """
    # Lifespan always assigns this attribute before yielding to request handling.
    return request.app.state.health_changed_publisher
