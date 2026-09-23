"""
Fleet Server ``src`` package.

Runnable gRPC service only:

  - ``service.py`` — ``FleetManagerServicer`` and ``serve()``
  - ``__main__.py`` — CLI bootstrap
  - ``events.py`` — re-exports SDK gateway emit helpers

Planning, allocation, formats, execution, and execution context live under
``packages/fleet_sdk/src/``.
"""
