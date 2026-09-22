"""EDA re-export of generic embedding helpers for semantic search.

``DIMS`` is the embedding dimensionality and ``embed_text`` turns text into a
vector used by plane-backed semantic search. Re-exported here so EDA memory
callers do not import ``packages.memory.embed`` directly.
"""

# Embedding dimensionality constant and text→vector helper from the memory kit.
from packages.memory.embed import DIMS, embed_text

# Public symbols for semantic-search callers.
__all__ = ["DIMS", "embed_text"]
