"""EDA re-export of the generic memory store protocol.

``MemoryStore`` is the structural protocol (or ABC) implemented by file,
Postgres, in-memory, and plane backends. Domain code that type-hints a raw
store can import it from here alongside ``EngineeringMemory``.
"""

# Generic store protocol from the memory kit.
from packages.memory.stores.protocol import MemoryStore

# Re-export as the sole public symbol.
__all__ = ["MemoryStore"]
