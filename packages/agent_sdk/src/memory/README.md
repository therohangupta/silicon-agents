# Agent SDK — agent-local memory (`packages/agent_sdk/src/memory/`)

This package implements **per-agent memory**: named stores configured in `config.yaml`, accessed through `MemoryManager` and optional **`memory_*` skills** registered automatically on `AgentServer` startup.

It is **not** the silicon / fleet **`packages/memory`** data plane. Agent-local memory holds scratch state, short-lived queues, or container-persistent JSON/Redis/Postgres data scoped to one agent process.

---

## Purpose in the fleet

LLM and tool runtimes need a consistent way to:

- Read/write key-value or list stores across tasks in the same agent
- Expose memory to the model via skills (`memory_read`, `memory_write`, …)
- Dump state for debugging (`GET /memory/state` on the task server)
- Choose persistence per store (ephemeral vs file vs Redis vs Postgres)

EDA agents use memory for **session context** (last congestion report, pinned parameters) without pushing everything through the plan workspace.

---

## Placement in architecture

```text
config.yaml  memory.stores[]
        │
        ▼
MemoryManager  ──►  one MemoryBackend per store.id
        │
        ├── read / write / search / clear / dump
        │
        ▼
make_memory_skills()  ──►  SkillRegistry (memory_read, …)
        │
        ▼
LangChain / tool_loop runtimes  OR  direct @tool usage
```

[`AgentServer`](../server/agent_server.py) constructs `MemoryManager(config.memory)` before loading skills and closes backends on app shutdown.

---

## Files in this directory

| File | Role |
|------|------|
| [`base.py`](base.py) | `MemoryBackend` ABC — `read`, `write`, `search`, `clear`, `dump` |
| [`loader.py`](loader.py) | `MemoryManager` — routes ops to per-store backend; lazy ephemeral store |
| [`skills.py`](skills.py) | `make_memory_skills(memory)` → async skill callables |
| [`backends/`](backends/README.md) | Dict, file, Redis, Postgres implementations |
| [`__init__.py`](__init__.py) | Package marker |
| [`README.md`](README.md) | This document |

Configuration types live in [`../models.py`](../models.py): `MemoryConfig`, `MemoryStoreConfig` (`type`, `persistence`, `config`, `schema`, TTL, max_items).

---

## MemoryManager behavior

**Construction** — For each entry in `memory.stores`, `_make_backend(store)` selects:

| `persistence` | Backend class |
|---------------|---------------|
| `ephemeral` | `DictMemoryBackend` |
| `file` | `FileMemoryBackend` |
| `redis` | `RedisMemoryBackend` |
| `postgres` | `PostgresMemoryBackend` |

**Ad hoc stores** — If code references an unknown `store_id`, manager creates an ephemeral `MemoryStoreConfig` and `DictMemoryBackend` automatically.

**API** — `read(store_id, key)`, `write`, `search(store_id, query, top_k=5)`, `clear(store_id, key=None)`, `dump()` (all stores), `close()` (optional backend `close()` hooks).

**Store types** (`MemoryStoreConfig.type`) — `key_value`, `list`, `queue`, `vector` (vector search is backend-dependent; Redis notes RediSearch limitation in backend README).

---

## Memory skills (`skills.py`)

Registered on server startup without YAML entries:

| Skill ID | Behavior |
|----------|----------|
| `memory_read` | `(store_id, key)` → value |
| `memory_write` | `(store_id, key, value)` → `{"status": "ok"}` |
| `memory_search` | `(store_id, query, top_k=5)` → list |
| `memory_clear` | `(store_id, key=None)` → `{"status": "ok"}` |

Traces can record `MemoryOp` payloads on [`AgentTaskResult`](../models.py) when runtimes emit `trace_type: memory_op`.

---

## Data and control flow

1. YAML defines stores with persistence and optional `config` (paths, DSN, Redis URL).
2. Validator may migrate legacy `memory.backend.type` to per-store `persistence` ([`../schema/validator.py`](../schema/validator.py)).
3. Task execution reads/writes via skills or direct `server.memory` access in custom code.
4. Shutdown: `AgentServer` lifespan awaits `memory.close()` to release Redis/Postgres pools.

---

## How EDA agents use memory

- **config.yaml** — Declare stores like `placement_notes` with `persistence: file` and `config.path: /data/agent_memory` on a Docker volume.
- **tools.py** — Prefer workspace for **large** artifacts; memory for **small** structured state (metrics, last tool status).
- **LLM agents** — `tool_loop` mode exposes memory skills to the model alongside domain `@tool` functions.
- **Observability** — Operators inspect `/memory/state` in dev; avoid exposing in untrusted networks.

Do not store secrets in file-backed stores without volume permissions; use env-based DSN for Postgres.

---

## Related paths

| Path | Notes |
|------|--------|
| [`backends/README.md`](backends/README.md) | Backend-specific config and Redis/Postgres ops |
| [`../server/README.md`](../server/README.md) | Wiring and `/memory/state` route |
| [`../models.py`](../models.py) | `MemoryStoreConfig`, `MemoryOp` |
| [`../../../../packages/memory/`](../../../../packages/memory/) | Fleet silicon memory (separate system) |

---

## Newcomer reading order

1. `MemoryStoreConfig` in [`../models.py`](../models.py)
2. [`loader.py`](loader.py) — manager routing
3. [`backends/README.md`](backends/README.md) — pick persistence for your agent
4. [`skills.py`](skills.py) — how LLM sees memory
5. Sample agent `config.yaml` under [`../../../agents/`](../../../agents/)

---

## Operational notes

- **Ephemeral default** — Unconfigured or unknown stores are in-process dicts; lost on restart.
- **File backend** — Default root `/data/agent_memory`; one JSON file per store id.
- **Redis** — Requires `redis>=5.0`; async client; see backend README for key naming.
- **Postgres** — Auto-creates `agent_memory` table; DSN from config or `AGENT_MEMORY_DATABASE_URL`.
- **Search** — Semantic quality depends on backend; dict/file often use substring heuristics.
- **Concurrency** — `MemoryManager` does not global-lock; backends should be safe for asyncio concurrent tasks within one process.

For implementation details of each persistence driver, see [`backends/README.md`](backends/README.md).
