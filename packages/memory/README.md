# memory

Domain-agnostic **silicon memory plane** toolkit: write policies that fan out
copies to physical stores, context assembly for LLM prompt packages, and async
store adapters from in-memory tests through full `MemoryPlane` production
facades.

## Purpose

Chip-design and EDA agents persist structured **envelopes** (metadata + JSON
payload) that must land in Postgres, journals, object storage, search indexes,
vectors, and event streams according to a design-table of placements. Domain
code (for example `EngineeringMemory` under `domains/eda/`) supplies record
types; this package supplies:

- **Write path** — `WritePolicy`, `assemble_copies`, placement validation
- **Read path for prompts** — `assemble` ranks and budget-trims already-selected
  records; it does not fetch from stores
- **Storage** — `MemoryStore` protocol and adapters in `stores/`

Stores treat `scope_segments` and `scope_key` as opaque; they never interpret
domain scope trees.

## Public API (`__init__.py`)

Import from `packages.memory` rather than deep modules when possible:

| Symbol | Module | Role |
|--------|--------|------|
| `WritePolicy`, `StoreCopy`, `StoredCopy`, `Placement` | `policy.py` | Describe multi-store writes |
| `assemble_copies`, `PolicyError` | `policy.py` | Validate and compile writes |
| `ContextPolicy`, `AssembledContext`, `AssembledConflict` | `context.py` | Prompt assembly policy |
| `assemble` | `context.py` | Rank, protect, trim, conflict-detect |

## Top-level file inventory

| File | Role |
|------|------|
| `policy.py` | Placements enum, copy models, `assemble_copies`, `refresh_copies` |
| `context.py` | `assemble()` with precedence, protect, drop_states, token budget |
| `envelope.py` | `StoredRecord` Protocol for store adapters |
| `embed.py` | Local hash embedding when no external embedding URL (tests/dev) |
| `values.py` | String labels for store columns / Cassandra keys |
| `stores/` | `MemoryStore` implementations — see `stores/README.md` |

## Write flow (policy → stores)

```
Domain service builds envelope (implements StoredRecord)
        │
        ▼
WritePolicy with StoreCopy list (postgres, cassandra_kv, object, …)
        │
        ▼
assemble_copies() → validates keys, vault isolation, ClickHouse metrics
        │
        ▼
MemoryPlane.apply_copies() or single-store adapter.insert()
        │
        ├── PostgresStore (transactional envelope, baselines, vectors)
        ├── Cassandra journal/KV, S3 object, OpenSearch, ClickHouse, …
        └── NATS JetStream copy (via message_bus publish inside plane)
```

Vault payloads must stay isolated — policy enforces that secrets never appear
in other placement bodies. Keyed stores require non-empty `key` on copies.

## Context assembly flow (prompt package)

```
Caller loads candidate records from stores (domain-specific query)
        │
        ▼
assemble(records, policy=ContextPolicy(...), token_budget=…,
         state_of=…, subject_of=…, claim_of=…, size_of=…)
        │
        ▼
AssembledContext { records, conflicts, omitted, token_estimate }
```

Conflicts: two kept records with same subject but different claims are reported
in `conflicts` but **not** auto-removed — the model or human resolves them.

## Physical placements (`Placement` enum)

Named stores match the architecture memory table (abbreviated):

| Placement | Typical use |
|-----------|-------------|
| `POSTGRES` | Canonical envelope, leases, approvals, pgvector row |
| `CASSANDRA_JOURNAL` | Append-only task journal |
| `CASSANDRA_KV` | Scope / lookup keys |
| `OPENSEARCH` | Full-text on summary/tags |
| `VECTOR` | Semantic search pointer |
| `NATS` | Durable `memory.>` event |
| `OBJECT` | Large artifact in MinIO/S3 |
| `CLICKHOUSE` | Numeric measurements |
| `GIT` | Source artifact commits |
| `VAULT` | Secrets only |

Full fan-out logic lives in `stores/plane.py`.

## Configuration

Memory backends read `packages.config` / env (`MEMORY_BACKEND`,
`MEMORY_DATABASE_URL`, `MEMORY_S3_*`, `MEMORY_CASSANDRA_*`, …) populated from
`config/platform.yaml` via `platform_config.host_settings()` and
`agent_environment()` for containers.

Default process backend is often `file` or `postgres` for dev; production uses
`MemoryPlane` with Postgres plus optional Cassandra, MinIO, etc.

## How Gateway, fleet, and agents use memory

| Component | Interaction |
|-----------|-------------|
| **Agents** | Write/read through domain memory services calling `assemble_copies` and store adapters; env vars from Compose |
| **fleet_server** | May read metrics or orchestration state from Postgres; not the primary memory API |
| **Gateway** | May expose memory queries if REST routes exist; typically proxies domain services |
| **client_sdk** | No direct memory plane — any UI goes through Gateway REST |

Agent SDK memory backends under `agent_sdk/src/memory/` are per-agent skill
storage; shared silicon plane is this `packages/memory` tree.

## Related documentation

- `memory/stores/README.md` — adapter catalog and `MemoryStore` protocol
- `packages/message_bus/README.md` — NATS abstraction used by NATS placement
- `packages/config.py` — `MEMORY_*` constants
- `domains/eda/` — EngineeringMemory integration (domain-specific)
- Design doc memory table in `etched_agentic_chip_design_system_v3.md`

## Reading order

1. **`envelope.py`** — fields every store expects on a record.
2. **`policy.py`** — `StoreCopy`, `assemble_copies`, placement rules.
3. **`stores/protocol.py`** — async CRUD + baseline CAS.
4. **`stores/README.md`** — pick adapter for your environment.
5. **`context.py`** — if building prompt packages from memory records.
6. **`stores/plane.py`** — when debugging multi-store fan-out in production.

## Testing strategy

- Unit tests: `InMemoryStore` or `FileStore` under `/tmp`.
- Policy tests: invalid copies (missing keys, vault leakage) must raise
  `PolicyError`.
- Integration: `PostgresStore` / `MemoryPlane` against Compose Postgres +
  MinIO from `platform.yaml`.
