# Agent SDK — memory backends (`packages/agent_sdk/src/memory/backends/`)

Concrete **`MemoryBackend`** implementations selected by [`MemoryManager`](../loader.py) from each store’s `persistence` field in `config.yaml`. All backends share the async API defined in [`../base.py`](../base.py).

---

## Purpose in the fleet

Agent containers need predictable storage semantics for **named stores** without each agent reimplementing Redis or Postgres access. Backends map `MemoryStoreConfig.type` (`key_value`, `list`, `queue`, `vector`) to appropriate data structures while honoring read/write/search/clear/dump for skills and runtimes.

Production deployments often use **file** (volume-mounted) or **redis** for multi-replica agents; **ephemeral** dict is the default for dev and stateless tools.

---

## Placement in architecture

```text
MemoryStoreConfig.persistence
        │
        ├── ephemeral ──► DictMemoryBackend
        ├── file      ──► FileMemoryBackend
        ├── redis     ──► RedisMemoryBackend
        └── postgres  ──► PostgresMemoryBackend
```

[`loader.py`](../loader.py) `_make_backend()` performs lazy import of optional dependencies (Redis, asyncpg) so agents without those extras still start.

---

## Files in this directory

| File | Class | When used |
|------|-------|-----------|
| [`dict_backend.py`](dict_backend.py) | `DictMemoryBackend` | `persistence: ephemeral` — in-process dict/list per store |
| [`file_backend.py`](file_backend.py) | `FileMemoryBackend` | `persistence: file` — one JSON file per store under configurable root |
| [`redis_backend.py`](redis_backend.py) | `RedisMemoryBackend` | `persistence: redis` — hashes/lists; production shared memory |
| [`postgres_backend.py`](postgres_backend.py) | `PostgresMemoryBackend` | `persistence: postgres` — JSONB rows in `agent_memory` table |
| [`__init__.py`](__init__.py) | Package marker | |
| [`README.md`](README.md) | This document | |

---

## Backend comparison

| Backend | Durability | Typical config keys | Dependencies |
|---------|------------|---------------------|--------------|
| Dict | Process lifetime | `{}` | none |
| File | Container volume | `path` (default `/data/agent_memory`) | stdlib json |
| Redis | External service | `url`, `prefix`, connection pool options | `redis>=5.0` |
| Postgres | External DB | `dsn` / `url`, or env `AGENT_MEMORY_DATABASE_URL` | async DB driver (see module) |

---

## DictMemoryBackend (`dict_backend.py`)

- Holds `_data[store.id]` as dict or list depending on `store.type`.
- **read** — Key lookup; list stores interpret key as index.
- **write** — Upsert key or append for lists/queues.
- **search** — Simple scan/filter over in-memory values.
- **dump** — Returns serializable snapshot of all stores in this backend instance.

Use for unit tests and agents with no cross-restart state requirement.

---

## FileMemoryBackend (`file_backend.py`)

- Root directory: `config.path` or `/data/agent_memory` (created at init).
- Each store persisted as `{store.id}.json`.
- Load/save on each operation (simple, not high-QPS).
- Suitable for **single-replica** Domain agents with Docker volume mounts.

Operational tip: backup the volume path before agent upgrades if stores hold non-reproducible tuning state.

---

## RedisMemoryBackend (`redis_backend.py`)

Documented mapping:

| Store type | Redis structure |
|------------|-----------------|
| `key_value` | Hash — HSET / HGET / HDEL |
| `list` | List — LPUSH / LRANGE / LTRIM |
| `queue` | List — RPUSH / LPOP |
| `vector` | Falls back to hash behavior; RediSearch not built-in |

- Async client via `redis.asyncio`.
- Keys namespaced with configurable prefix to avoid collisions in shared Redis.
- Implements `close()` for connection cleanup on server shutdown.

Configure URL in store `config` or environment consistent with fleet compose.

---

## PostgresMemoryBackend (`postgres_backend.py`)

- Schema: table `agent_memory (store_id, entry_key, value JSONB, updated_at)`.
- Creates table on first use if missing (`_SCHEMA` in module).
- DSN resolution: store config `dsn` / `url`, then `AGENT_MEMORY_DATABASE_URL`.
- Good for **auditable** agent state and SQL tooling; heavier than Redis for hot paths.

---

## Data and control flow

1. `MemoryManager.read(store_id, key)` resolves store config + backend instance.
2. Backend receives `MemoryStoreConfig` on each call for type-specific behavior.
3. `dump()` aggregates per backend for `/memory/state` HTTP route.
4. `close()` — Redis/Postgres release connections; dict/file no-op.

Search APIs accept a string query; non-vector backends implement pragmatic text matching — do not assume embedding search unless you add a dedicated backend later.

---


---

## Related paths

| Path | Notes |
|------|--------|
| [`../README.md`](../README.md) | MemoryManager and skills |
| [`../base.py`](../base.py) | Abstract interface |
| [`../../contracts/`](../../contracts/) and [`../../config/`](../../config/) | `MemoryStoreConfig` |
| [`../../config/load.py`](../../config/load.py) | `load_agent_config` and environment expansion |

---

## Newcomer reading order

1. [`../base.py`](../base.py) — method contracts
2. [`../loader.py`](../loader.py) — selection logic
3. This README — pick a backend
4. Read the single backend module you enable in YAML
5. [`../../server/README.md`](../../server/README.md) — shutdown `close()`

---

## Operational notes

- **Import errors** — Redis/Postgres backends import optional deps at runtime; missing packages raise clear errors on first use.
- **Migration** — Legacy configs with global `memory.backend.type` are upgraded to per-store `persistence` during validation.
- **Security** — Postgres DSN and Redis URLs belong in secrets/env, not committed YAML.
- **Performance** — File backend rewrites whole JSON per write; not for high-frequency telemetry-sized writes.
- **Testing** — Use `DictMemoryBackend` via ephemeral persistence in pytest.

No nested subdirectories under `backends/`; all drivers are flat modules listed above.
