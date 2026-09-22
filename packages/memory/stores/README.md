# memory/stores/

**Durable adapters** for memory envelopes implementing the async `MemoryStore`
protocol in `protocol.py`. Domain records must satisfy `StoredRecord` in
`../envelope.py`.

## Purpose

The memory plane separates **what to write** (`policy.py`) from **where it
lands** (this directory). Each adapter implements the same CRUD + baseline CAS
contract so tests can swap `InMemoryStore` for `PostgresStore` or the full
`MemoryPlane` without changing domain services.

## File inventory

| File | Class / symbol | Role |
|------|----------------|------|
| `protocol.py` | `MemoryStore` | Async Protocol: insert, get, find_idempotency, scan, update, baseline CAS |
| `memory.py` | `InMemoryStore` | Process-local dict for unit tests |
| `file.py` | `FileStore` | JSONL + file locking; single-host durability |
| `postgres.py` | `PostgresStore` | Transactional envelopes, pgvector hooks, baselines |
| `plane.py` | `MemoryPlane` | Facade: Postgres + multi-backend `apply_copies` fan-out |
| `__init__.py` | re-exports | Public store symbols |
| `README.md` | you are here | |

Supporting modules at package root (not in `stores/`):

- `../embed.py` — hash embedding for vector rows when no external model URL
- `../values.py` — placement label strings for secondary indexes

## MemoryStore protocol (summary)

| Method | Behavior |
|--------|----------|
| `insert(record)` | Persist new envelope; respect `idempotency_key` dedup |
| `get(memory_id)` | Load by primary key |
| `find_idempotency(key)` | Return prior write for retry safety |
| `scan()` | Full table scan (rebuild/debug) |
| `update(record)` | Overwrite validation state, summary, payload |
| `get_baseline(scope_path)` | Canonical memory_id pointer for scope |
| `compare_and_set_baseline(scope_path, expected, new_value)` | Atomic baseline promotion |

Baseline CAS supports golden-record promotion without double-writer races.

## Adapter selection guide

| Adapter | When to use |
|---------|-------------|
| `InMemoryStore` | Fast tests, no I/O |
| `FileStore` | Local dev, single machine, JSONL audit trail |
| `PostgresStore` | Production envelope authority, vectors, leases |
| `MemoryPlane` | Full design table: Cassandra, S3, OpenSearch, ClickHouse, Vault, git, NATS |

Construct backend from `packages.config.MEMORY_BACKEND` in domain wiring code;
Compose agents often receive `MEMORY_BACKEND` via `agent_environment()`.

## MemoryPlane fan-out flow

```
Domain calls MemoryPlane.insert / apply_copies
        │
        ├── PostgresStore.insert (when POSTGRES copy present)
        ├── Cassandra journal append (CASSANDRA_JOURNAL)
        ├── Cassandra KV put (CASSANDRA_KV + key)
        ├── S3 put_object (OBJECT + key)
        ├── OpenSearch index (OPENSEARCH)
        ├── ClickHouse insert (CLICKHOUSE numeric payload)
        ├── git commit (GIT)
        ├── Vault write (VAULT — isolated payload)
        ├── embed_text → vector row (VECTOR)
        └── MessageBus publish (NATS placement)
```

`plane.py` uses `asyncio.to_thread` for blocking drivers (Cassandra, S3, git).
Configuration is read via `_env()` helper — missing vars raise
`PlatformConfigError`, not silent defaults.

`refresh_copies` from `policy.py` lists inherited projections that must rewrite
when the Postgres envelope changes.

## Idempotency and scope opacity

- Stores persist `scope_segments` and `scope_key` as JSON/text **without**
  parsing domain hierarchy.
- Duplicate inserts with same `idempotency_key` should return the existing row
  (Postgres + InMemory implement this pattern).

## How Gateway, fleet, and agents use stores

| Component | Usage |
|-----------|--------|
| **Agents** | Domain memory service selects adapter from env; writes on task progress |
| **fleet_server** | Uses fleet Postgres for control plane, not necessarily memory envelopes |
| **Gateway** | May query memory via REST if exposed; no direct import of stores in typical BFF |
| **Tests** | `InMemoryStore` / temp `FileStore` |

Agent SDK file/redis memory backends are separate from this shared plane — see
`agent_sdk/src/memory/`.

## Related documentation

- `../README.md` — write policy and context assembly
- `../policy.py` — `Placement`, `StoreCopy`, validation
- `../envelope.py` — `StoredRecord` fields
- `../../message_bus/README.md` — NATS copy inside `MemoryPlane`
- `../../config.py` — `MEMORY_*` URLs and credentials

## Reading order

1. **`protocol.py`** — contract all adapters must satisfy.
2. **`memory.py`** or **`file.py`** — simplest implementations to learn behavior.
3. **`postgres.py`** — production envelope schema assumptions.
4. **`plane.py`** — only when operating multi-store production deployments.
5. Domain **`EngineeringMemory`** (or equivalent) — how envelopes are built.

## Troubleshooting

| Symptom | Check |
|---------|--------|
| `PolicyError` before store | `assemble_copies` — keys, vault isolation |
| Postgres connection errors | `MEMORY_DATABASE_URL` / `DATABASE_URL` |
| Missing S3 object | `MEMORY_S3_*` endpoint and bucket |
| Empty vector search | `MEMORY_EMBEDDING_URL` or local `embed_text` fallback |
| NATS copy not arriving | `message_bus` connectivity and stream subjects |
