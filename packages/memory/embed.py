"""Local embedding used when no model endpoint is configured.

Token hashes land in a fixed 256-d vector. Shared words raise cosine
similarity, which is enough to test the pgvector index and MemoryPlane
semantic search without standing up a model service.

Set ``MEMORY_EMBEDDING_URL`` (consumed by ``MemoryPlane._vector``) to
replace this bag-of-hashes embedding with a real embedding endpoint. This
module itself always produces the local deterministic vector.
"""

from __future__ import annotations

# hashlib.sha256 maps tokens into stable bucket indices and signs.
import hashlib
# math.sqrt normalizes the sparse vector to unit length.
import math

# Default dimensionality must match Postgres ``vector(256)`` in stores/postgres.py.
DIMS = 256


def embed_text(text: str, dims: int = DIMS) -> list[float]:
    """Hash-bag embed ``text`` into a unit-length ``dims``-dimensional vector.

    Each whitespace token contributes +1 or -1 into one hashed bucket. The
    resulting sparse vector is L2-normalized so cosine distance in pgvector
    behaves like a similarity over shared tokens. Empty text yields the
    zero vector normalized with a floor of 1.0 to avoid division by zero.
    """
    # Start with an all-zero dense vector of the requested width.
    vector = [0.0] * dims
    # Lowercase and split so "Foo" and "foo" share a bucket.
    for token in text.lower().split():
        # SHA-256 digest gives stable pseudo-random bytes per token.
        digest = hashlib.sha256(token.encode()).digest()
        # First four bytes choose the bucket index modulo dims.
        index = int.from_bytes(digest[:4], "little") % dims
        # Fifth byte chooses the sign so collisions can cancel or reinforce.
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        # Accumulate the signed contribution into the chosen bucket.
        vector[index] += sign
    # L2 norm; use 1.0 when the vector is all zeros (empty input).
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    # Return the unit vector expected by cosine-distance indexes.
    return [value / norm for value in vector]
