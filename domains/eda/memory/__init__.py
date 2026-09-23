"""EDA engineering-memory package: stores, placements, plane, and service facade.

This subpackage binds the generic memory kit in ``packages.memory`` to the EDA
``MemoryRecord`` envelope and record-type placement defaults.

* ``EngineeringMemory`` (``service.py``) owns the envelope rules: append vs
  publish, idempotency, publish policy checks, query/search, baseline
  promotion, leases, artifacts, secrets, and QoR measurements.
* ``placements.py`` chooses default store copies per ``RecordType`` when the
  caller does not pass an explicit ``WritePolicy``.
* ``file_store.py``, ``postgres_store.py``, ``plane.py``, and
  ``memory_store.py`` are thin EDA bindings that inject ``MemoryRecord`` as
  the record class into the generic store implementations.
* ``protocol.py`` and ``embed.py`` re-export the generic store protocol and
  embedding helpers for convenient domain imports.
* ``open_memory`` selects the backend from ``MEMORY_BACKEND`` /
  ``MEMORY_BACKEND`` (memory, postgres, plane, or file).

Agents should talk to ``EngineeringMemory`` rather than raw stores so
envelope invariants stay centralized.
"""

# Write-policy types re-exported so callers can import from domains.eda.memory.
from ..schemas.memory import StoreCopy, WritePolicy
# File-backed store binding parameterized on MemoryRecord.
from .file_store import FileStore
# In-process store re-export for tests and MEMORY_BACKEND=memory.
from .memory_store import InMemoryStore
# Generic store protocol type alias.
from .protocol import MemoryStore
# Primary facade and factory used by EDAAgent and AgentService.
from .service import EngineeringMemory, MemoryPolicyError, open_memory

# Public surface for ``from domains.eda.memory import ...``.
__all__ = [
    "EngineeringMemory",
    "FileStore",
    "InMemoryStore",
    "MemoryPolicyError",
    "MemoryStore",
    "StoreCopy",
    "WritePolicy",
    "open_memory",
]
