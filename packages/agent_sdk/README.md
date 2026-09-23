# Agent SDK (`packages/agent_sdk/`)

The **Agent SDK** is the shared Python library for first-party agent task servers in the monorepo. It turns a directory containing `config.yaml`, `tools.py`, and `server.py` into a runnable **task server**: HTTP health checks, task execution, skill registration, optional LLM runtimes, telemetry, agent-local memory, and plan-workspace helpers.

Fleet orchestration (Gateway, executor, plan workspace on the control plane) lives outside this package. The SDK is the **in-process runtime** that agents import as `from packages.agent_sdk import AgentServer, tool, PlanWorkspace, …`.

---

## Purpose in the fleet

| Concern | Where it lives in the SDK |
|--------|---------------------------|
| Task HTTP API | [`src/server/`](src/server/README.md) — `AgentServer` (FastAPI + uvicorn) |
| Execution strategy | [`src/runtime/`](src/runtime/README.md) — direct function, tool loop, codegen |
| Callable tools | [`src/skills/`](src/skills/README.md) — `@tool`, `SkillRegistry` |
| `config.yaml` contract | [`src/contracts/`](src/contracts/) and [`src/config/`](src/config/), [`src/schema/`](src/schema/README.md) |
| Observability | [`src/telemetry/`](src/telemetry/README.md) — HTTP ingest + optional gRPC streams |
| Scratch / durable agent memory | [`src/memory/`](src/memory/README.md) — not fleet-wide `packages/memory` |
| Large plan artifacts | [`src/workspace/`](src/workspace/README.md) — `PlanWorkspace`, local/S3 backends |
| Agent-to-agent HTTP | [`src/client/`](src/client/README.md) — `AgentClient` |
| Domain lifecycle template | [`src/lifecycle.py`](src/lifecycle.py) — `TaskLifecycle` ABC |

Domain-specific wrappers may compose these modules under `domains/`; generic agents call `AgentServer.from_yaml("config.yaml")` directly.

---

## Placement in architecture

```text
                    Control plane / Gateway
                              │
                    POST AgentTaskRequest
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Agent container (this SDK)                                    │
│  AgentServer (or a domain-specific service wrapper)          │
│    ├─ load_agent_config ← config.yaml                        │
│    ├─ SkillRegistry ← tools.py + memory skills               │
│    ├─ MemoryManager ← memory.stores[]                        │
│    ├─ AgentRuntime ← execution.mode                          │
│    ├─ TelemetryClient (+ optional TelemetryPublisher)        │
│    └─ PlanWorkspace (from request.workspace_uri)             │
└─────────────────────────────────────────────────────────────┘
                              │
                    AgentTaskResult + ArtifactRef[]
                              ▼
                    Executor / downstream tasks
```

Distinction from **`client_sdk/`**: the Gateway BFF client talks to the fleet API. **`AgentClient`** in this package talks to **another agent’s task-server port** (`connection.port` in that agent’s YAML).

---

## Package layout

| Path | Role |
|------|------|
| [`__init__.py`](__init__.py) | Public re-exports: `AgentServer`, Pydantic models, `tool`, `TelemetryClient`, `PlanWorkspace` |
| [`src/`](src/README.md) | Implementation root (prefer `packages.agent_sdk` imports in agent code) |
| [`src/contracts/`](src/contracts/) and [`src/config/`](src/config/) | `AgentConfig`, `AgentTaskRequest` / `AgentTaskResult`, traces, memory/telemetry config |
| [`src/lifecycle.py`](src/lifecycle.py) | Domain-neutral `TaskLifecycle.handle()` hook pipeline |
| [`src/server/`](src/server/README.md) | `AgentServer` wiring and routes |
| [`src/runtime/`](src/runtime/README.md) | `AgentRuntime` implementations |
| [`src/skills/`](src/skills/README.md) | Tool decorator and registry |
| [`src/schema/`](src/schema/README.md) | YAML load, env expansion, legacy migration |
| [`src/memory/`](src/memory/README.md) | `MemoryManager` + backends |
| [`src/telemetry/`](src/telemetry/README.md) | Heartbeats and event ingest |
| [`src/workspace/`](src/workspace/README.md) | Plan-scoped blob storage |
| [`src/client/`](src/client/README.md) | Async HTTP client for peer agents |

There is no separate `pyproject.toml` in this folder; the package is consumed as part of the repository root Python path (`packages.*` imports).

---

## Public import surface

Agent `tools.py` and `server.py` typically use:

```python
from packages.agent_sdk import (
    AgentServer,
    AgentTaskRequest,
    AgentTaskResult,
    AgentConfig,
    tool,
    PlanWorkspace,
    TelemetryClient,
)
```

Deep imports (`from packages.agent_sdk.src.runtime...`) are reserved for SDK internals and fleet domain code.

---

## Data and control flow (one task)

1. **Ingress** — Executor POSTs JSON matching `AgentTaskRequest` to `connection.endpoints.execute` (default `/tasks/execute`).
2. **Concurrency** — `execution.concurrency.max_tasks` semaphore; health reports `busy` while held.
3. **Capability params** — `required_capabilities` merged into per-skill kwargs via `SkillRegistry.set_capability_params`.
4. **Runtime** — Selected by `execution.mode`: `direct_function` → `tools.execute(request)`; `tool_loop` → LangChain + tools; `codegen` → generated code + `CodeExecutionRunner`.
5. **Egress** — `AgentTaskResult` with `success`, `message`, inline `artifacts`, `artifact_refs`, structured `traces`, optional `replan` / `outcome` / `reason_code`.
6. **Side effects** — Telemetry events (`task_started`, `task_completed`, `skill_call`, …); memory ops via registered `memory_*` skills; workspace publishes collected as `ArtifactRef` list.

---

## Related paths

| Location | Relationship |
|----------|----------------|
| [`packages/proto/telemetry.proto`](../../packages/proto/telemetry.proto) | Event schema for telemetry client/publisher |
| [`packages/platform_config/`](../../packages/platform_config/) | Default hosts, ports, heartbeat intervals |
| [`config/platform.yaml`](../../config/platform.yaml) | Fleet-wide settings referenced by validators |
| [`agents/TELEMETRY.md`](../../agents/TELEMETRY.md) | Operator guide for agent telemetry adapters |

---

## Newcomer reading order

1. This README — fleet role and layout.
2. [`src/contracts/`](src/contracts/) and [`src/config/`](src/config/) — request/result and config shape (skim `AgentConfig` sections).
3. [`src/server/README.md`](src/server/README.md) — how a process starts and serves tasks.
4. [`src/skills/README.md`](src/skills/README.md) — how `tools.py` connects to YAML.
5. Pick one execution path: [`src/runtime/README.md`](src/runtime/README.md) for mode selection.
6. [`src/workspace/README.md`](src/workspace/README.md) if tasks exchange large artifacts.
7. [`src/telemetry/README.md`](src/telemetry/README.md) when debugging observability.

---

## Operational notes

- **Config path** — `AgentServer.from_yaml(path)` adds the agent directory to `sys.path` and loads `tools.py` from the same folder as `config.yaml`.
- **Environment** — Validators expand `${VAR}` and `${VAR:-default}` in YAML; telemetry URL defaults via `TELEMETRY_URL` and platform settings.
- **Ports** — Each agent YAML sets `connection.port`; fleet compose maps unique host ports per agent.
- **Health** — GET `/health` returns capability IDs and `ReliabilityConfig` for orchestrator routing.
- **Debugging** — GET `/skills` lists registered specs; GET `/memory/state` dumps configured stores (avoid in production without auth).
- **Custom runtimes** — `execution.mode: custom` currently maps to `DirectFunctionRuntime`; extend `AgentServer._make_runtime` only in forked SDK code.

For module-level detail, follow the README in each `src/*` subdirectory listed above.
