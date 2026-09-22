"""Storage writer implementation package (``services.storage_writer.src``).

Holds the async entrypoint, JetStream pull worker, Parquet sink with
per-modality schemas, partition manifest helpers, and the compaction loop.
This ``__init__`` intentionally exports nothing so importing a single
submodule does not start NATS consumers as a side effect.
"""
