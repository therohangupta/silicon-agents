"""
Fleet Server ``src`` package.

This package contains the runnable Fleet Manager service implementation:

  - ``service.py`` — gRPC ``FleetManagerServicer`` and ``serve()`` entry.
  - ``__main__.py`` — CLI bootstrap (port, DB reset, signal handling).
  - ``events.py`` — Gateway fire-and-forget mutation notifications.
  - ``world_state.py`` — per-plan execution context snapshots for agents.
  - ``planners/`` — planning strategies (monolithic, DAG, big DAG, replanner).
  - ``allocators/`` — allocation strategies (LP, LLM, cost-based).
  - ``executor/`` — dependency-aware task dispatch and reliability.
  - ``formats/`` — Pydantic schemas shared by planners and allocators.

Running ``python -m services.fleet_server.src`` executes ``__main__.main``.
"""
