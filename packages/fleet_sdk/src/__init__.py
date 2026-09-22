"""fleet_sdk.src — control-plane models, gRPC client, and instance registry.

Submodules:

* ``models`` — SQLAlchemy ORM rows mirroring ``fleet_manager.proto`` plus
  model↔proto converters
* ``grpc_client`` — synchronous ``FleetManagerClient`` for Gateway/CLI
* ``instance_registry`` — async Postgres-backed ``AgentInstanceRegistry``
  used by fleet_server for agents, plans, tasks, goals, and metrics
"""
