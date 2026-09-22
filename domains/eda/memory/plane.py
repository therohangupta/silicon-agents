"""EDA binding for the generic memory plane.

The plane persists whatever record class it is given and fans writes out to
Postgres, Cassandra, OpenSearch, object storage, NATS, and related services
according to compiled copy policies. This binding supplies the EDA
``MemoryRecord``, whose ``scope_key`` and ``scope_segments`` properties define
how scope projections are keyed for this domain.

Selected when ``open_memory`` sees ``MEMORY_BACKEND=plane``. Fleet compose
renders ``MEMORY_BACKEND=plane`` for every silicon agent service so they share
the platform memory plane rather than per-container file directories.
"""

# Generic multi-store memory plane from the memory kit.
from packages.memory.stores.plane import MemoryPlane as _MemoryPlane

# EDA envelope whose scope_key/scope_segments the plane persists.
from ..schemas.memory import MemoryRecord


class MemoryPlane(_MemoryPlane):
    """Memory plane parameterized on the EDA ``MemoryRecord`` envelope.

    Inherits apply_copies, journals, artifacts, leases, and search from the
    generic plane. Only the default record class (and thus scope keying) is
    specialized here.
    """

    def __init__(self, *, record_cls: type = MemoryRecord) -> None:
        """Construct a plane that round-trips EDA memory records.

        Args:
            record_cls: Record model class; defaults to ``MemoryRecord``.

        Returns:
            None. Initializes the generic plane.

        Side effects:
            May connect to configured plane backends via environment variables
            when the base class eagerly initializes clients.

        Failures:
            Propagates base-class connection or configuration errors.
        """
        # Bind the EDA record class so scope_key comes from MemoryRecord.
        super().__init__(record_cls=record_cls)
