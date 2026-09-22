"""
Gateway message-bus consumers package.

Submodules here attach the FastAPI gateway to asynchronous buses (today:
NATS JetStream). Consumers run as background asyncio tasks started from
``app.lifespan`` and push data into in-process caches and WebSocket fan-out
structures owned by the same process.

This ``__init__`` module is intentionally import-light so importing
``consumers`` does not start a bus connection; callers import
``telemetry_consumer`` symbols explicitly.
"""
