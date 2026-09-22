"""Shared memory toolkit: write copies, store adapters, and context assembly.

A record is an envelope plus a payload. ``assemble_copies`` checks a list of
store destinations against the write-policy rules (keyed stores need keys,
vault payloads stay isolated, ClickHouse needs numeric metrics). Store
adapters persist ``scope_segments`` and ``scope_key`` as opaque values —
they never interpret domain-specific scope trees. ``assemble`` ranks and
budget-trims records the caller already selected; it does not fetch.

This package is the memory plane used by domain EngineeringMemory services:
policy and context stay domain-agnostic, while ``stores`` provide File,
InMemory, Postgres, and the multi-backend ``MemoryPlane`` façade.

Public re-exports below are the symbols domain code should import from
``packages.memory`` rather than reaching into submodules.
"""

# Context assembly types and the ranking/budget function.
from .context import AssembledContext, AssembledConflict, ContextPolicy, assemble
# Write-policy types and the copy-assembly / validation entry point.
from .policy import Placement, PolicyError, StoreCopy, StoredCopy, WritePolicy, assemble_copies

# Explicit public API so ``from packages.memory import *`` stays intentional.
__all__ = [
    "AssembledConflict",
    "AssembledContext",
    "ContextPolicy",
    "Placement",
    "PolicyError",
    "StoreCopy",
    "StoredCopy",
    "WritePolicy",
    "assemble",
    "assemble_copies",
]
