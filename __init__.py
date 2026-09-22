"""Silicon / EDA multi-agent control plane (repository root package).

Installing with ``pip install -e .`` from the repo root (see ``pyproject.toml``)
exposes:

* ``packages`` — shared config, SDKs, protobuf stubs
* ``services`` — fleet_server, gateway, telemetry, storage_writer, dashboard-web
* ``cli`` — ``agentctl`` operator CLI
* ``agents`` — one directory per agent (config.yaml + server.py + tools)
* ``domains`` — domain specializations (e.g. ``domains.eda`` fleet selection)

Runtime glue that is *not* imported as a Python package but lives beside this
module: ``docker-compose*.yml``, ``fleets/``, ``deploy/``, ``docs/``, ``scripts/``.

``scripts/startup.sh`` cds here and starts Compose + the dashboard.
"""
