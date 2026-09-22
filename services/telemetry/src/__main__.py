#!/usr/bin/env python3
"""
CLI entrypoint for the Telemetry service.

Invoked as ``python -m services.telemetry.src`` (this module is loaded as
``__main__``). Parses an optional ``--port`` override, then hands control to
uvicorn with the ASGI app at ``services.telemetry.src.main:app``. Binding to
``0.0.0.0`` matches Docker Compose expectations so containers are reachable
from the gateway and sibling agents on the shared network.

The default port comes from ``TELEMETRY_PORT`` in shared config so bare-metal
and container runs stay aligned with ``packages.config`` without duplicating
magic numbers here.
"""

# argparse builds the small CLI surface without pulling in Click/typer.
import argparse
# uvicorn is the ASGI server that actually serves the FastAPI app.
import uvicorn

# Shared default port (env-overridable via packages.config).
from .config import TELEMETRY_PORT


def main():
    """Parse CLI flags and start uvicorn against the telemetry ASGI app.

    Creates an ArgumentParser whose only flag is ``--port``, defaulting to
    ``TELEMETRY_PORT`` so operators can override without editing config.
    Then calls ``uvicorn.run`` with the import string for ``main:app``, host
    ``0.0.0.0`` (all interfaces), and info-level logging suitable for local
    and container logs. Does not return under normal operation; the process
    exits when uvicorn shuts down.
    """
    # Describe the process for ``--help`` users.
    parser = argparse.ArgumentParser(description="Start the Telemetry service")
    # Allow ``--port 9001`` without changing env; type=int rejects non-ints.
    parser.add_argument("--port", type=int, default=TELEMETRY_PORT, help="Port to listen on")
    # Materialize Namespace with resolved defaults.
    args = parser.parse_args()

    # Import-string form lets uvicorn reload/worker modes re-import cleanly.
    uvicorn.run(
        "services.telemetry.src.main:app",
        # Listen on all interfaces so Docker publish and LAN access work.
        host="0.0.0.0",
        # Use CLI-resolved port (env default or --port).
        port=args.port,
        # Keep container/local logs readable without debug noise by default.
        log_level="info",
    )


# Standard script guard: only start the server when executed as main.
if __name__ == "__main__":
    # Delegate to main() so tests can import this module without binding a port.
    main()
