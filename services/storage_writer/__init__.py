"""Storage writer service top-level package marker.

Marks ``services.storage_writer`` as importable so
``python -m services.storage_writer.src.main`` resolves after an editable
install. Runtime logic lives under ``src/``; see ``README.md`` in this
directory for consumer group, Parquet layout, and compaction behavior.
"""
