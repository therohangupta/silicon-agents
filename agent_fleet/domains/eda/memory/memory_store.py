"""EDA import path for the generic in-memory store.

Re-exports ``packages.memory.stores.memory.InMemoryStore`` so domain code and
tests can ``from domains.eda.memory import InMemoryStore`` without depending on
the packages layout. Selected when ``open_memory`` sees
``MEMORY_BACKEND=memory`` (or ``MEMORY_BACKEND=memory``).

The in-memory store is process-local: agent containers do not share it unless
they inject a single shared instance in tests.
"""

# Generic process-local store used for unit tests and ephemeral runs.
from packages.memory.stores.memory import InMemoryStore

# Re-export as the sole public symbol of this binding module.
__all__ = ["InMemoryStore"]
