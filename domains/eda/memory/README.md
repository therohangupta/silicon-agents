# memory

**Engineering memory** binds the generic memory kit in `packages/memory` to the EDA **`MemoryRecord`** envelope and default **placement** rules per **`RecordType`**. Every **`EDAAgent`** reads and writes through **`EngineeringMemory`**; bypassing the facade risks breaking publish policy, idempotency, and multi-store copies.

## Design split: envelope vs payload

| Layer | Owner | Contents |
|-------|--------|----------|
| **Envelope** | `EngineeringMemory` | `memory_id`, scope, record type, validation state, authorship, evidence refs, idempotency, placements |
| **Payload** | Writing agent | Arbitrary JSON dict (experiment metrics, workflow graph, checkpoint summary, …) |

The generic kit knows how to insert, scan, and replicate **copies** across stores. This package knows **which EDA record types** may be published, what evidence is required, and how baselines move.

## EngineeringMemory API (conceptual)

### Write paths

**`append`** — Provisional **task-local** journal entries. Used by **`EDAAgent.journal_started`** / **`journal_finished`**. Always **`ValidationState.PROVISIONAL`**, **`AuthorKind.AGENT`**, typically **`RecordType.TASK_CHECKPOINT`**. Does **not** run full publish policy (checkpoints are not promoted engineering facts).

**`publish`** / **`write`** — Records visible to other agents. Flow:

1. **`_check_publish`** — role/type rules (e.g. agents cannot publish **`HUMAN_INTENT`**; findings need evidence).
2. Idempotency lookup via **`store.find_idempotency`**.
3. **`compile_policy`** — merge default placements with optional **`WritePolicy`** / **`also_stores`**.
4. **`insert`** envelope; non-Postgres backends may **`apply_copies`** for secondary stores.
5. Special cases: decision projection, supersede older records on publish.

**`record_experiment`** — Convenience wrapper publishing **`ExperimentRecord`**-shaped payloads.

**Baseline rule:** Direct publishes of **`DESIGN_BASELINE`** are rejected. Canonical baselines move **only** through **`promote_candidate`** (compare-and-swap on scope path + validated gate checks).

### Read paths

| Method | Purpose |
|--------|---------|
| **`get`** | Fetch one record by id |
| **`query`** | Project + optional scope / type filters (context assembly) |
| **`search`** | Text/semantic search when backend supports it |
| **`get_lookup`** / **`read_copy`** | Resolve lookup keys and store-specific copies |

### Errors

**`MemoryPolicyError`** — Non-retryable policy violations (invalid lookup, forbidden type, placement failure). Distinct from transient store outages.

## open_memory backend factory

**`open_memory()`** selects a store implementation from environment:

| Backend | Typical use |
|---------|-------------|
| **`file`** | Default local dev; shared directory under configurable path |
| **`memory`** | In-process **`InMemoryStore`** for unit tests |
| **`postgres`** | Envelope-only Postgres binding |
| **`plane`** | **`MemoryPlane`**: multi-store plane (Postgres, OpenSearch, vector, Cassandra journal, NATS, …) |

Variables: **`MEMORY_BACKEND`** or **`SILICON_MEMORY_BACKEND`**. Fleet Compose sets **`MEMORY_BACKEND=plane`** so silicon agent containers share the platform plane services.

## placements.py

When the caller does not pass an explicit **`WritePolicy`**, **`compile_policy`** uses **`_BY_TYPE`** defaults:

| Family | Stores (conceptually) | Record types (examples) |
|--------|----------------------|-------------------------|
| **`_SEARCHABLE`** | Postgres + OpenSearch + vector + NATS | Requirements, findings, experiments, interface contracts |
| **`_JOURNAL`** | Postgres + Cassandra journal + NATS | Task checkpoints, workflow revisions |
| **`_CANONICAL`** | Postgres + NATS | Decisions, gates, waivers, human intent, artifact refs, baselines |

Unknown **`RecordType`** values fall back to **`_CANONICAL`**. **`PlacementError`** aliases the generic **`PolicyError`** for domain catch blocks.

## Store bindings in this package

| Module | Role |
|--------|------|
| **`service.py`** | **`EngineeringMemory`**, **`open_memory`**, **`MemoryPolicyError`** |
| **`placements.py`** | Default copies per **`RecordType`**, **`compile_policy`** |
| **`plane.py`** | **`MemoryPlane`** — inject **`MemoryRecord`** into generic multi-store plane |
| **`file_store.py`** | **`FileStore`** binding for directory backends |
| **`postgres_store.py`** | **`PostgresStore`** envelope binding |
| **`memory_store.py`** | Re-export in-process store |
| **`protocol.py`** | Re-export **`MemoryStore`** protocol |
| **`embed.py`** | Re-export **`DIMS`**, **`embed_text`** for semantic search helpers |

## Interaction with ContextService

**`ContextService.assemble`** calls **`EngineeringMemory.query`** with project id and expanded **`RecordType`** set from **`INCLUDE_TYPES`**, then filters by **`MemoryScope.contains`**, exclude rules, and rejected validation state. Assembly is **read-only** on the facade (aside from store scan semantics).

Rejected records never enter the package regardless of include lists.

## Testing notes

- Unit tests often inject a shared **`EngineeringMemory`** over **`InMemoryStore`** or file store.
- Live plane tests (`tests/test_memory_plane.py`, `tests/test_agent_mesh.py`) require **`SILICON_PLANE_TEST=1`** and a running Compose stack.

## Related

| Document | Topic |
|----------|--------|
| [`../schemas/memory.py`](../schemas/memory.py) | **`MemoryRecord`**, **`MemoryScope`**, **`ContextPackage`** models |
| [`../schemas/README.md`](../schemas/README.md) | Enums and message types |
| [`../agent.py`](../agent.py) | Journaling and publish calls from **`EDAAgent`** |
| [`../../docs/TELEMETRY_AND_DATA_FLOW.md`](../../docs/TELEMETRY_AND_DATA_FLOW.md) | Platform data movement |
