"""
FastAPI dependency injection helpers for the gateway.

This module owns the process-wide singleton ``GRPCBridge`` that every REST
and WebSocket handler uses to talk to the fleet manager. Lifecycle is tied to
the FastAPI lifespan in ``app.py``: ``init_bridge()`` runs on startup and
``close_bridge()`` on shutdown.

Using ``Depends(get_bridge)`` in route signatures ensures handlers receive a
ready bridge and fail loudly with ``RuntimeError`` if a request arrives before
startup completed (or after teardown). That failure is intentional — it
surfaces mis-ordered lifespan or tests that forgot to call ``init_bridge``.

Side effects: constructing the bridge opens a gRPC channel to
``GRPC_SERVER_ADDRESS`` (or host/port fallbacks) and initializes
``AgentInstanceRegistry`` against ``DATABASE_URL``. Closing the bridge closes
the gRPC client; the module-level ``_bridge`` is then cleared so subsequent
``get_bridge()`` calls raise until re-init.
"""

from typing import Optional

# Pull address pieces and DB URL from gateway config re-exports.
from .config import GRPC_SERVER_ADDRESS, GRPC_SERVER_PORT, DATABASE_URL

# Concrete bridge type injected into route handlers.
from .grpc_bridge import GRPCBridge

# =============================================================================
# Global Instances
# =============================================================================

# Singleton gRPC bridge — None until init_bridge() succeeds during lifespan startup.
_bridge: Optional[GRPCBridge] = None


def get_bridge() -> GRPCBridge:
    """
    Return the process-wide ``GRPCBridge`` for FastAPI dependency injection.

    Purpose:
        Provide a single shared client/registry to all route handlers so they
        do not open per-request gRPC channels.

    Args:
        None. FastAPI invokes this with no parameters when used as ``Depends(get_bridge)``.

    Returns:
        The initialized ``GRPCBridge`` instance.

    Side effects:
        None on success. Does not create the bridge.

    Failure behavior:
        Raises ``RuntimeError`` if ``_bridge`` is still ``None`` (app not started
        or already shut down). That exception becomes a 500 if it escapes a
        request handler unless callers catch it.
    """
    # Refuse to hand out a half-initialized client; forces correct lifespan wiring.
    if _bridge is None:
        raise RuntimeError("GRPCBridge not initialized. App may not have started properly.")
    # Hand the singleton to the caller / Depends machinery.
    return _bridge


def init_bridge() -> GRPCBridge:
    """
    Construct and store the global ``GRPCBridge`` during application startup.

    Purpose:
        Parse ``GRPC_SERVER_ADDRESS`` into host/port (or fall back to
        ``GRPC_SERVER_PORT``) and build a bridge bound to ``DATABASE_URL``.

    Args:
        None. Reads host/port/DB URL from module-level config imports.

    Returns:
        The newly created ``GRPCBridge``, also stored in ``_bridge``.

    Side effects:
        Overwrites any previous ``_bridge``. Opens gRPC and registry resources
        inside ``GRPCBridge.__init__``.

    Failure behavior:
        Propagates exceptions from address parsing (``int`` on bad port) or
        from ``GRPCBridge`` construction; lifespan will fail to start the app.
    """
    # Allow assignment to the module-level singleton.
    global _bridge
    # Prefer the full address string from env (e.g. "fleet-server:50051").
    addr = GRPC_SERVER_ADDRESS.strip()
    # Split on the last colon so IPv6-style or host:port forms still work for host:port.
    if ":" in addr:
        # host may contain colons in rare cases; rsplit isolates the port.
        host, port_str = addr.rsplit(":", 1)
        # Convert port text to int; ValueError if misconfigured.
        port = int(port_str, 10)
    else:
        # Address was host-only; use configured default gRPC port.
        host, port = addr, GRPC_SERVER_PORT
    # Construct bridge with parsed endpoint and shared DB URL for registry extras.
    _bridge = GRPCBridge(host=host, port=port, db_url=DATABASE_URL)
    # Return for callers that want the instance without calling get_bridge().
    return _bridge


def close_bridge() -> None:
    """
    Tear down the global ``GRPCBridge`` during application shutdown.

    Purpose:
        Close the underlying gRPC client and clear the singleton so no handler
        reuses a dead channel after lifespan exit.

    Args:
        None.

    Returns:
        None.

    Side effects:
        Calls ``GRPCBridge.close()`` when ``_bridge`` is set, then sets
        ``_bridge`` to ``None``.

    Failure behavior:
        Propagates exceptions raised by ``close()`` if the client fails to shut
        down cleanly; typically logged by the ASGI server during shutdown.
    """
    # Need write access to clear the singleton after close.
    global _bridge
    # Only close if startup previously succeeded.
    if _bridge:
        # Release gRPC channel / stubs held by FleetManagerClient.
        _bridge.close()
        # Ensure get_bridge() fails after shutdown rather than returning a closed client.
        _bridge = None
