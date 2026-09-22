"""First-party runtime services that make up the agent fleet control plane.

This package is the namespace root for every long-running process that is *not*
an individual silicon agent container. Sibling directories under ``services/``
host fleet orchestration (``fleet_server``), the HTTP/WebSocket edge
(``gateway``), heartbeat and telemetry ingest (``telemetry``), durable Parquet
persistence (``storage_writer``), the operator UI (``dashboard-web``), a
placeholder for a future service-side CLI image (``cli``), and the shared
silicon-agent container base image (``silicon_agent``).

Import paths such as ``services.telemetry.src.app`` and
``services.storage_writer.src.main`` rely on this package existing so that
editable installs and Docker images can treat the repo root as a single
Python distribution. The module intentionally exports nothing: each service
owns its own ``src`` package and is started via ``python -m`` or uvicorn, not
by importing symbols from this ``__init__``.

Operators and contributors should treat ``services/README.md`` as the
directory-level map of what each sibling tree does; this docstring only
establishes the Python package boundary so tooling can discover and import
service modules consistently.
"""
