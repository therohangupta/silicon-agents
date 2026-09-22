"""Fleet SDK package root.

Re-exports are intentionally minimal here — import from
``packages.fleet_sdk.src`` modules (``models``, ``grpc_client``,
``instance_registry``) or from the service that wires them. This file
exists so ``fleet_sdk`` is a proper Python package documenting the
fleet control-plane SDK layer (SQLAlchemy models, gRPC client, registry).
"""
