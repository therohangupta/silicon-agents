# Agent SDK — implementation root (`packages/agent_sdk/src/`)

This directory is the **Python implementation** of the Agent SDK. Application code in agent containers should import from the package root ([`../README.md`](../README.md)) — `from packages.agent_sdk import AgentServer, …` — which re-exports the stable surface from here.

Internal SDK modules use relative imports (`from ..models import AgentTaskRequest`). Fleet domain code may import submodules directly when wiring custom servers.

---

## Purpose in the fleet

Everything under `src/` runs **inside the agent process** after the container starts:

- Parse and validate agent `config.yaml`
- Build FastAPI routes for health and task execution
- Register skills from `tools.py` and auto-register memory operations
- Execute tasks through a pluggable runtime
- Emit telemetry and optional streaming adapters
- Expose helpers for plan workspace I/O and peer-agent HTTP calls

The control plane sends **`AgentTaskRequest`** JSON; this tree turns it into domain work and returns **`AgentTaskResult`**.

---

## Placement in architecture

```text
packages/agent_sdk/__init__.py  (public re-exports)
        │
        ▼
packages/agent_sdk/src/
        ├── models.py          ← transport + config Pydantic models
        ├── lifecycle.py       ← optional domain lifecycle ABC
        ├── server/            ← AgentServer (HTTP entry)
        ├── runtime/           ← execute(request) strategies
        ├── skills/            ← @tool + SkillRegistry
        ├── schema/            ← YAML → AgentConfig
        ├── memory/            ← MemoryManager + backends
        ├── telemetry/         ← TelemetryClient, TelemetryPublisher
        ├── workspace/         ← PlanWorkspace + blob backends
        └── client/            ← AgentClient (peer HTTP)
```

[`domains/server.py`](../../../domains/server.py) composes many of the same pieces for Domain agents without always instantiating `AgentServer` directly.

---

## Complete file table

| File / directory | Responsibility |
|------------------|----------------|
| [`__init__.py`](__init__.py) | Subset re-export of models for `from packages.agent_sdk.src import …` |
| [`models.py`](models.py) | `AgentConfig`, task DTOs, execution traces, memory/telemetry/deployment config |
| [`lifecycle.py`](lifecycle.py) | `TaskLifecycle` — decode → context → journal → execute → encode |
| [`server/`](server/README.md) | `agent_server.py` — `AgentServer` |
| [`runtime/`](runtime/README.md) | `AgentRuntime` and mode-specific executors |
| [`skills/`](skills/README.md) | `@tool`, `SkillRegistry` |
| [`schema/`](schema/README.md) | `AgentConfigValidator`, env expansion, legacy YAML migration |
| [`memory/`](memory/README.md) | `MemoryManager`, memory skill factories, backends |
| [`telemetry/`](telemetry/README.md) | HTTP ingest client, gRPC publisher |
| [`workspace/`](workspace/README.md) | `PlanWorkspace`, local/S3 backends |
| [`client/`](client/README.md) | `AgentClient` |
| [`README.md`](README.md) | This document |

---

## Data and control flow

**Startup (typical `AgentServer`):**

1. `AgentConfigValidator.validate_file(config.yaml)` → `AgentConfig`
2. Construct `MemoryManager`, `SkillRegistry`, `TelemetryClient`
3. Load `tools.py`, register YAML `skills`, inject `memory_*` skills
4. Optionally load `telemetry_adapter.py` for gRPC streaming
5. `_make_runtime()` from `execution.mode`
6. Register FastAPI routes; uvicorn binds `connection.host` / `connection.port`

**Per task:**

1. Semaphore acquire → busy flag → optional task telemetry stream
2. `SkillRegistry.set_capability_params(...)` from request capabilities
3. `runtime.execute(request)` → `AgentTaskResult`
4. Telemetry flush of traces; release semaphore; resume idle stream

**Cross-cutting models** — `ExecutionContextSnapshot` on the request carries plan summary, completed tasks, and `ArtifactRef` list for downstream Domain agents. Results append `ExecutionTrace` entries for skill calls, memory ops, and code execution.

---


---

## Related paths

| Path | Notes |
|------|--------|
| [`../README.md`](../README.md) | Package-level overview |
| [`../../../agents/backend/*/config.yaml`](../../../agents/backend/) | Per-agent SDK config examples |
| [`../../proto/telemetry.proto`](../../proto/telemetry.proto) | Telemetry wire format |

---

## Newcomer reading order

1. [`models.py`](models.py) — especially `AgentTaskRequest`, `AgentTaskResult`, `AgentConfig`
2. [`server/README.md`](server/README.md)
3. [`skills/README.md`](skills/README.md)
4. [`runtime/README.md`](runtime/README.md) — match your agent’s `execution.mode`
5. Subsystems you touch: memory, workspace, telemetry, client

---

## Operational notes

- **Import path** — Monorepo expects `PYTHONPATH` including `agent_fleet` so `packages.agent_sdk` resolves.
- **lifecycle.py** — Use when building other domains that need journaling without copying executor logic; Domain agents often implement equivalent steps inside `domain handler`.
- **Testing** — Integration tests may construct validators and runtimes without HTTP; see fleet test layout outside this package.
- **Do not duplicate** — Fleet-wide memory and gateway clients live in other `packages/*` trees; agent-local persistence is only [`memory/`](memory/README.md).

Subdirectory READMEs document each module in depth (target 80–150+ lines per leaf).
