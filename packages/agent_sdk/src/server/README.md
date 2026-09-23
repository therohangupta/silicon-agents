# Agent SDK — task server (`packages/agent_sdk/src/server/`)

Hosts **`AgentServer`**, the FastAPI application factory that wires validated config, skills, memory, runtime, and telemetry, then serves health and task endpoints on the agent’s **`connection.port`**.

Generic SDK agents run `AgentServer.from_yaml("config.yaml").run()`. Domain agents often use [`domains/server.AgentService`](../../../domains/server.py) instead, which reuses the same models and patterns; this module is the reference HTTP stack.

---

## Purpose in the fleet

Each agent container exposes a **task server** the executor calls:

- Prove liveness and capability set (`GET /health`)
- Accept work units (`POST /tasks/execute`)
- Optional introspection (`GET /skills`, `GET /memory/state`)

`AgentServer` is the **composition root** for in-process SDK subsystems.

---

## Placement in architecture

```text
config.yaml ──► load_agent_config ──► AgentConfig
                                              │
                                              ▼
                                        AgentServer.__init__
                    ┌─────────────────────────┼─────────────────────────┐
                    ▼                         ▼                         ▼
            TelemetryClient            SkillRegistry              MemoryManager
            (+ Publisher?)                  │                         │
                    │                         └──────────┬──────────────┘
                    │                                    ▼
                    │                            AgentRuntime
                    ▼                                    │
            FastAPI routes ◄─────────────────────────────┘
                    │
        GET /health, POST /tasks/execute, …
```

Optional **`telemetry_adapter.py`** beside the agent enables gRPC streaming via [`TelemetryPublisher`](../telemetry/publisher.py).

---

## Files in this directory

| File | Role |
|------|------|
| [`agent_server.py`](agent_server.py) | `AgentServer` — full wiring, routes, lifespan, uvicorn `run()` |
| [`__init__.py`](__init__.py) | Package marker |
| [`README.md`](README.md) | This document |

---

## Construction and factories

| Entry | Behavior |
|-------|----------|
| `AgentServer(config, config_path=None)` | Build from in-memory `AgentConfig` |
| `AgentServer.from_yaml(path)` / `from_config(path)` | Validate file, pass path for tools/adapter loading |

**Init sequence:**

1. `_setup_telemetry()` — `TelemetryClient`, skill call hook → async emit
2. `_load_skills()` — agent dir on `sys.path`, import `tools.py`, register YAML skills + memory skills
3. `_load_telemetry_adapter()` — optional `telemetry_adapter.py` dynamic import
4. `_make_runtime()` — from `execution.mode`
5. Semaphore from `execution.concurrency.max_tasks`
6. FastAPI app + `_install_routes()`

---

## HTTP routes

Default paths from `connection.endpoints` (overridable in YAML):

| Route | Method | Response |
|-------|--------|----------|
| `/health` (configurable) | GET | `AgentHealth` — agent_id, status, busy, capabilities, reliability |
| `/tasks/execute` | POST | `AgentTaskRequest` → `AgentTaskResult` |
| `/skills` | GET | List of registered `SkillSpec` JSON |
| `/memory/state` | GET | `MemoryManager.dump()` |

**Execute path behavior:**

- Acquire concurrency semaphore; set busy; telemetry `set_busy(True)`
- Start optional task stream from adapter (`stream_task`)
- Merge capability skill params into registry
- Emit `task_started` telemetry
- `await self._runtime.execute(request)`
- Emit completion, artifacts, skill_call traces
- On failure: log, `task_failed` telemetry, HTTP 500
- Finally: stop task stream, restart idle stream, clear busy

---

## Skill and module loading

- Agent directory = parent of `config.yaml`.
- `tools.py` loaded as `_agent_{metadata.name}_tools` to avoid collisions.
- Each `SkillSpec`: import module (default `tools`), `getattr(module, callable)`, `skills.register`.
- Auto-registers `memory_read`, `memory_write`, `memory_search`, `memory_clear`.
- Best-effort import of sibling `telemetry.py` if present (debug).

---

## Telemetry integration

- HTTP: heartbeats on lifespan start; events via `TelemetryClient.emit`.
- gRPC: if adapter exists, `_start_stream_publisher()` connects `TelemetryPublisher` to `TELEMETRY_GRPC_TARGET` / platform settings; blob upload URL `{telemetry_endpoint}/telemetry/blob`.
- Idle vs task streams: adapter may implement `stream_idle` / `stream_task`; server cancels idle during tasks.

Skill calls also emit on registry hook (`_on_skill_call`) in addition to trace replay after task completion.

---

## Lifespan

On startup: start heartbeat, connect stream publisher, start idle stream.

On shutdown: stop idle stream, close publisher, close telemetry client, `await memory.close()`.

---

## Data and control flow

**Inbound** — Executor POST mirrors [`AgentTaskRequest`](../contracts/): task id, description, plan/workspace fields, context snapshot, inputs, required capabilities, `record_episode` for telemetry persistence.

**Outbound** — [`AgentTaskResult`](../contracts/) with structured outcomes for replanning (`replan`, `outcome`, `reason_code`).

**Capability params** — `_capability_skill_params` merges `config.capabilities[].skill_params` for ids listed in `request.required_capabilities`.

---


---

## Related paths

| Path | Notes |
|------|--------|
| [`../runtime/README.md`](../runtime/README.md) | Runtime selection |
| [`../skills/README.md`](../skills/README.md) | Registry behavior |
| [`../telemetry/README.md`](../telemetry/README.md) | Client and publisher |
| [`../../../agents/TELEMETRY.md`](../../../agents/TELEMETRY.md) | Adapter authoring |

---

## Newcomer reading order

1. [`../schema/README.md`](../schema/README.md) — config shape
2. This README + skim [`agent_server.py`](agent_server.py) `_install_routes`
3. [`../runtime/README.md`](../runtime/README.md)
4. One agent `server.py` under `agents/backend/`

---

## Operational notes

- **Port binding** — `run(host="0.0.0.0", port=...)` defaults to config connection port.
- **503** — Runtime missing → should not occur after successful init.
- **500** — Uncaught exception in runtime; message in HTTP detail; check agent logs.
- **Concurrency** — Extra tasks block on semaphore until slot frees; health shows busy.
- **Security** — Routes are unauthenticated by default; restrict at network policy or add middleware in fork.
- **Env** — `TASK_DURATION` overrides task stream duration; `TELEMETRY_GRPC_TARGET` for gRPC.

No subdirectories under `server/` beyond this module.
