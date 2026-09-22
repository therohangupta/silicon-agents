"""EDA binding for the generic file store.

The generic ``packages.memory.stores.file.FileStore`` persists whatever record
class it is given as JSON files under a root directory. This module supplies
the EDA ``MemoryRecord`` as the default ``record_cls`` so agent processes that
share ``MEMORY_ROOT`` (or ``/tmp/silicon_memory``) exchange typed
envelopes without each caller repeating the record class argument.

Use this backend when ``MEMORY_BACKEND`` / ``MEMORY_BACKEND`` is unset
or set to ``file`` (the ``open_memory`` default).
"""

# Generic file-backed store implementation from the memory kit.
from packages.memory.stores.file import FileStore as _FileStore

# EDA envelope model injected as the default record class.
from ..schemas.memory import MemoryRecord


class FileStore(_FileStore):
    """File-directory store that deserializes EDA ``MemoryRecord`` envelopes.

    Inherits all scan/get/insert/update/idempotency behavior from the generic
    file store. Only the default record class differs.
    """

    def __init__(self, root, *, record_cls: type = MemoryRecord) -> None:
        """Open a file store rooted at ``root`` for EDA memory records.

        Args:
            root: Filesystem directory where JSON record files are kept.
            record_cls: Record model class; defaults to ``MemoryRecord``.
                Override only in specialized tests.

        Returns:
            None. Initializes the generic base store.

        Side effects:
            May create the root directory depending on base-class behavior.

        Failures:
            Propagates base-class I/O errors.
        """
        # Delegate to the generic store with the EDA record class bound in.
        super().__init__(root, record_cls=record_cls)
