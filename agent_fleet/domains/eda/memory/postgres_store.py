"""EDA binding for the generic Postgres store.

Wraps ``packages.memory.stores.postgres.PostgresStore`` so the default record
class is the EDA ``MemoryRecord``. Selected when ``open_memory`` sees
``MEMORY_BACKEND=postgres``. The DSN comes from the generic store's own
environment handling (e.g. ``DATABASE_URL`` / ``MEMORY_DATABASE_URL``) when
``dsn`` is omitted.

Postgres holds the envelope and decision projections; multi-store copies
still require the memory plane backend.
"""

# Generic Postgres-backed store from the memory kit.
from packages.memory.stores.postgres import PostgresStore as _PostgresStore

# EDA envelope model injected as the default record class.
from ..schemas.memory import MemoryRecord


class PostgresStore(_PostgresStore):
    """Postgres store that deserializes EDA ``MemoryRecord`` envelopes.

    Suitable when only the envelope store is needed. Writing non-Postgres
    copies through ``EngineeringMemory`` against this backend raises
    ``MemoryPolicyError`` unless the store exposes ``apply_copies``.
    """

    def __init__(self, dsn: str | None = None, *, record_cls: type = MemoryRecord) -> None:
        """Open a Postgres store for EDA memory records.

        Args:
            dsn: Optional database URL. When ``None``, the base class reads
                its configured environment variables.
            record_cls: Record model class; defaults to ``MemoryRecord``.

        Returns:
            None. Initializes the generic Postgres store.

        Side effects:
            May open a database connection pool.

        Failures:
            Propagates connection and configuration errors from the base class.
        """
        # Delegate construction with the EDA record class bound in.
        super().__init__(dsn, record_cls=record_cls)
