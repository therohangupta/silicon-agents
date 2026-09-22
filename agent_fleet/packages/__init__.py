"""Shared, domain-neutral packages for the agent fleet control plane.

This package root is the import namespace for everything that multiple
services and agents share: configuration (``config``), observability
helpers (``metrics``), gRPC protobuf contracts (``proto``), the fleet
control-plane client and registry models (``fleet_sdk``), the per-agent
HTTP server / runtime / telemetry SDK (``agent_sdk``), the shared memory
plane (``memory``), the NATS JetStream message bus abstraction
(``message_bus``), and the Gateway-facing client SDKs (``client_sdk``).

Import paths used elsewhere in the monorepo typically look like
``from packages.config import GATEWAY_URL`` or
``from packages.memory.stores.plane import MemoryPlane`` once ``agent_fleet``
is on ``PYTHONPATH``. Nothing in this ``__init__`` re-exports symbols; it
exists so ``packages`` is a proper Python package, guarantees this checkout
wins over similarly named editable installations, and documents the shared
layer.
"""
