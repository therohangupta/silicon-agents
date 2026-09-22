"""Write-policy building blocks that do not name a domain's record types.

A domain chooses the default copies for its own record types, then calls
``assemble_copies`` to check keys, vault isolation, and measurement payloads.

This module is the write half of the memory plane:

* ``StoreCopy`` / ``WritePolicy`` describe where a write should land.
* ``StoredCopy`` records what was requested (payloads stay in the destination).
* ``Placement`` enumerates the physical stores from the design table.
* ``assemble_copies`` validates and compiles a write into a ``CompiledWrite``.
* ``refresh_copies`` lists inherited projections that must be rewritten when
  the Postgres envelope changes.
"""

from __future__ import annotations

# frozen dataclass for the compiled write result.
from dataclasses import dataclass
# Enum for the closed set of physical store names.
from enum import Enum
# Any/Optional for payload typing.
from typing import Any, Optional

# Pydantic models for validated copy/policy JSON shapes.
from pydantic import BaseModel, Field


class StoreCopy(BaseModel):
    """One payload sent to one store.

    ``payload`` omitted means this copy uses the write's primary payload.
    A write policy holds as many copies as the caller needs, including several
    copies of the same store under different keys (e.g. multiple Cassandra KV
    lookup keys for one envelope).
    """

    # Placement name: must match a Placement enum value.
    store: str
    # Object / KV / git / vault / clickhouse key when the store is keyed.
    key: str = ""
    # Optional override body; None means inherit the write's primary payload.
    payload: Optional[dict[str, Any]] = None


class WritePolicy(BaseModel):
    """Which payload goes to which store for a single write."""

    # Ordered list of store copies that constitute this write.
    copies: list[StoreCopy] = Field(default_factory=list)


class StoredCopy(BaseModel):
    """Record of a copy that was requested. Payloads stay in the destination store."""

    # Placement name that received (or should receive) this copy.
    store: str
    # Key used for keyed stores; empty for unkeyed projections.
    key: str = ""
    # True when the copy inherited the primary payload (no override body).
    inherited: bool = True


class Placement(str, Enum):
    """Physical stores named in the shared memory-plane design table."""

    # Transactional envelope + leases, approvals, pointers, decisions, vectors.
    POSTGRES = "postgres"
    # Append-only journal keyed by (project_id, task_id).
    CASSANDRA_JOURNAL = "cassandra_journal"
    # Dictionary lookup keyed by (project_id, lookup_key).
    CASSANDRA_KV = "cassandra_kv"
    # Full-text search index (OpenSearch ``memory`` index).
    OPENSEARCH = "opensearch"
    # pgvector embedding row linked to memory_id.
    VECTOR = "vector"
    # Durable NATS JetStream event on ``memory.>``.
    NATS = "nats"
    # Large artifact in MinIO/S3.
    OBJECT = "object"
    # Numeric experiment measurement in ClickHouse.
    CLICKHOUSE = "clickhouse"
    # Versioned source file in the shared git working tree.
    GIT = "git"
    # Secret in Vault; never duplicated into other stores.
    VAULT = "vault"


# Stores that require a non-empty key on every copy.
_KEYED = {
    Placement.CASSANDRA_KV.value,
    Placement.OBJECT.value,
    Placement.GIT.value,
    Placement.VAULT.value,
    Placement.CLICKHOUSE.value,
}
# Inherited copies that must be rewritten when the envelope is updated.
_REFRESHABLE = {
    Placement.CASSANDRA_JOURNAL.value,
    Placement.CASSANDRA_KV.value,
    Placement.OPENSEARCH.value,
    Placement.VECTOR.value,
    Placement.NATS.value,
}


class PolicyError(ValueError):
    """Raised when a write policy violates placement rules."""

    pass


@dataclass(frozen=True)
class CompiledWrite:
    """Validated write ready for MemoryPlane / store adapters to execute."""

    # Normalized WritePolicy after store/key/payload checks.
    policy: WritePolicy
    # Single payload that Postgres should keep as the envelope body.
    envelope_payload: dict
    # Provenance list persisted on the record (no inline payloads).
    copies: list[StoredCopy]
    # Sorted unique placement names touched by this write.
    placements: list[str]
    # Cassandra KV keys registered for dictionary lookup.
    lookup_keys: list[str]


def assemble_copies(
    copies: list[StoreCopy],
    primary: dict,
    *,
    also_stores: list[str] | None = None,
    lookup_keys: list[str] | None = None,
) -> CompiledWrite:
    """Check a caller-supplied list of copies and record where each one goes.

    Extra store names in ``also_stores`` are appended as inherited copies.
    ``lookup_keys`` ensure Cassandra KV entries exist for each key. Raises
    ``PolicyError`` when the resulting policy is empty, references an unknown
    store, violates key/payload rules, duplicates vault bodies elsewhere, or
    asks Postgres for conflicting envelope payloads.
    """
    # Start from the caller-supplied copies (mutate a new list).
    assembled = list(copies)
    # Append any additional unkeyed store names the domain requested.
    for name in also_stores or []:
        # Call ``assembled.append``.
        assembled.append(StoreCopy(store=_check_store(name)))
    # Ensure each lookup key has a Cassandra KV copy.
    for key in lookup_keys or []:
        # Skip if this exact KV key is already present.
        if any(copy.store == Placement.CASSANDRA_KV.value and copy.key == key for copy in assembled):
            continue
        # Add an inherited KV copy for the missing lookup key.
        assembled.append(StoreCopy(store=Placement.CASSANDRA_KV.value, key=key))
    # A write must touch at least one store.
    if not assembled:
        # Raise ``PolicyError`` to signal this failure mode to callers.
        raise PolicyError("A write policy needs at least one store copy")

    # Normalize store names and strip keys.
    normalized: list[StoreCopy] = []
    # Loop: for copy in assembled.
    for copy in assembled:
        # Validate / canonicalize the placement name.
        store = _check_store(copy.store)
        # Preserve payload override; strip whitespace-only issues later via checks.
        normalized.append(StoreCopy(store=store, key=copy.key.strip(), payload=copy.payload))
    # Per-copy key and payload validation against the primary body.
    for copy in normalized:
        # Call ``_check_copy``.
        _check_copy(copy, primary)
    # Vault bodies must never also appear on another store.
    _check_vault(normalized, primary)

    # Build the persisted provenance list (no payloads inline).
    stored = [
        # Call ``StoredCopy``.
        StoredCopy(store=copy.store, key=copy.key, inherited=copy.payload is None)
        # Loop: for copy in normalized.
        for copy in normalized
    ]
    # Compile the validated write for the caller / plane.
    return CompiledWrite(
        # Local ``policy`` ← WritePolicy(copies=normalized),.
        policy=WritePolicy(copies=normalized),
        # Local ``envelope_payload`` ← _envelope_payload(normalized, primary),.
        envelope_payload=_envelope_payload(normalized, primary),
        # Local ``copies`` ← stored,.
        copies=stored,
        # Local ``placements`` ← sorted({copy.store for copy in normalized}),.
        placements=sorted({copy.store for copy in normalized}),
        # Local ``lookup_keys`` ← [copy.key for copy in normalized if copy.store == Placement.CASSA….
        lookup_keys=[copy.key for copy in normalized if copy.store == Placement.CASSANDRA_KV.value],
    )


def refresh_copies(record_copies: list[StoredCopy]) -> list[StoreCopy]:
    """Copies that should be rewritten when the envelope changes.

    Only inherited projections in ``_REFRESHABLE`` stores are returned —
    object/git/vault/clickhouse bodies are not automatically refreshed.
    """
    return [
        # Call ``StoreCopy``.
        StoreCopy(store=item.store, key=item.key)
        # Loop: for item in record_copies.
        for item in record_copies
        # Only when (item.inherited and item.store in _REFRESHABLE).
        if item.inherited and item.store in _REFRESHABLE
    ]


def _check_store(name: str) -> str:
    """Return the canonical Placement value or raise PolicyError."""
    try:
        # Round-trip through the enum to reject unknown names.
        return Placement(name).value
    # On except ValueError as exc: recover or re-raise as appropriate.
    except ValueError as exc:
        # List allowed values in the error for operator debugging.
        allowed = ", ".join(item.value for item in Placement)
        # Raise ``PolicyError`` to signal this failure mode to callers.
        raise PolicyError(f"Unknown store {name}. Choose from {allowed}.") from exc


def _check_copy(copy: StoreCopy, primary: dict) -> None:
    """Validate key presence/shape and store-specific payload constraints."""
    # Keys must be single tokens — whitespace breaks object/KV addressing.
    if copy.key and any(character.isspace() for character in copy.key):
        # Raise ``PolicyError`` to signal this failure mode to callers.
        raise PolicyError(f"{copy.store} key {copy.key!r} cannot contain spaces")
    # Keyed placements require a non-empty key.
    if copy.store in _KEYED and not copy.key:
        # Raise ``PolicyError`` to signal this failure mode to callers.
        raise PolicyError(f"A {copy.store} copy needs a key")
    # Resolve the effective payload for store-specific checks.
    payload = primary if copy.payload is None else copy.payload
    # Vault: must carry its own payload with a secret value field.
    if copy.store == Placement.VAULT.value:
        # Only when (copy.payload is None or "value" not in copy.payload).
        if copy.payload is None or "value" not in copy.payload:
            # Raise ``PolicyError`` to signal this failure mode to callers.
            raise PolicyError("A vault copy needs its own payload with a value, and that payload is not written elsewhere")
        return
    # ClickHouse: metric name, numeric value, and experiment id required.
    if copy.store == Placement.CLICKHOUSE.value:
        # Local ``metric`` ← payload.get("metric").
        metric = payload.get("metric")
        # Local ``value`` ← payload.get("value").
        value = payload.get("value")
        # Local ``experiment`` ← payload.get("experiment_id") or copy.key.
        experiment = payload.get("experiment_id") or copy.key
        # Only when (not isinstance(metric, str) or not metric.strip()).
        if not isinstance(metric, str) or not metric.strip():
            # Raise ``PolicyError`` to signal this failure mode to callers.
            raise PolicyError("A ClickHouse copy needs a metric name")
        # Reject bool (subclass of int) and non-numeric values.
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            # Raise ``PolicyError`` to signal this failure mode to callers.
            raise PolicyError("A ClickHouse copy needs a numeric value")
        # Only when (not experiment or any(character.isspace() for character in str(experiment))).
        if not experiment or any(character.isspace() for character in str(experiment)):
            # Raise ``PolicyError`` to signal this failure mode to callers.
            raise PolicyError("A ClickHouse copy needs an experiment id")
        # Quotes would break the simple string-interpolated SELECT path.
        if "'" in str(experiment) or "'" in metric:
            # Raise ``PolicyError`` to signal this failure mode to callers.
            raise PolicyError("ClickHouse identifiers cannot contain quotes")


def _check_vault(copies: list[StoreCopy], primary: dict) -> None:
    """Ensure no non-vault copy carries the same body as a vault secret."""
    # Collect every vault override payload.
    secret_payloads = [copy.payload for copy in copies if copy.store == Placement.VAULT.value]
    # Loop: for secret in secret_payloads.
    for secret in secret_payloads:
        # Loop: for copy in copies.
        for copy in copies:
            # Vault copies are allowed to hold the secret.
            if copy.store == Placement.VAULT.value:
                continue
            # Compare against the other copy's effective payload.
            other = primary if copy.payload is None else copy.payload
            # Only when (other == secret).
            if other == secret:
                # Raise ``PolicyError`` to signal this failure mode to callers.
                raise PolicyError("A vault payload cannot also be written to another store")


def _envelope_payload(copies: list[StoreCopy], primary: dict) -> dict:
    """Pick the single Postgres envelope payload or return ``{}`` if none."""
    chosen: dict | None = None
    # Loop: for copy in copies.
    for copy in copies:
        # Only postgres copies contribute to the envelope body.
        if copy.store != Placement.POSTGRES.value:
            continue
        # Local ``payload`` ← primary if copy.payload is None else copy.payload.
        payload = primary if copy.payload is None else copy.payload
        # Only when (chosen is None).
        if chosen is None:
            # Local ``chosen`` ← payload.
            chosen = payload
        elif payload != chosen:
            # Conflicting postgres bodies would corrupt the single envelope row.
            raise PolicyError("Postgres keeps one envelope payload per write")
    # No postgres copy means the envelope payload is empty (projections only).
    if chosen is None:
        # Hand ``{}`` back to the caller.
        return {}
    # Hand ``chosen`` back to the caller.
    return chosen
