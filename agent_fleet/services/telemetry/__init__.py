"""Telemetry service top-level package marker.

This file marks ``services.telemetry`` as an importable package so that
``python -m services.telemetry.src`` and uvicorn target
``services.telemetry.src.main:app`` resolve correctly after an editable
install. Runtime logic lives under ``src/``; operators should start from
``README.md`` in this directory for ports, env vars, and HTTP/gRPC surfaces.
"""
