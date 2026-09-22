# DESIGN.md

### Goals
- **Prototype that scales**: keep production-shaped boundaries while staying lightweight.
- **Single UI boundary**: the browser should talk to exactly one service (the “Gateway/BFF”).
- **Control-plane correctness**: plan execution and task/plan truth must remain consistent and recoverable.
- **Data-plane scalability**: high-rate telemetry/video should not destabilize control-plane execution.

---

### Current repo reality (today)
- **Fleet control plane (gRPC server)**: `agent_fleet/services/fleet_server/src/service.py`
  - Execution orchestration: `agent_fleet/services/fleet_server/src/executor/executor.py`
  - DB access: `agent_fleet/packages/fleet_sdk/src/instance_registry.py` (`AgentInstanceRegistry`; also used by gateway gRPC bridge, planners, and allocators)
  - **Fleet → gateway event callback**: `agent_fleet/services/fleet_server/src/events.py` — fire-and-forget HTTP POST to `GATEWAY_EVENT_URL` (from `agent_fleet/packages/config.py`: same host/port as the gateway plus `/internal/events`; Docker Compose sets this explicitly, e.g. `http://gateway:8000/internal/events`)
- **Gateway/BFF (FastAPI)**: `agent_fleet/services/gateway/src/app.py`
  - gRPC to fleet: `agent_fleet/services/gateway/src/grpc_bridge.py`
  - HTTP API routers: `agent_fleet/services/gateway/src/routers/` — e.g. `plans.py`, `agents.py`, `tasks.py`, `goals.py`, `websocket.py`, `telemetry.py`, `metrics.py`, …
  - Agent health for the UI: HTTP client to the Telemetry service in `agent_fleet/services/gateway/src/services/telemetry_client.py` (used from `routers/agents.py` via `TELEMETRY_URL` in gateway config)
- **Telemetry service (FastAPI)**, separate from gateway: `agent_fleet/services/telemetry/src/`
  - App entry: `app.py`; heartbeat storage: `heartbeat_store.py`; notifying gateway on health changes: `publishing.py` (POSTs `telemetry.health_changed`-style events to the same gateway `/internal/events` path)
  - Routers: `routers/` (`ingest.py` for `/ingest/heartbeat`, `health.py` for summaries the gateway reads, …)
- **Frontend (Vite/React)**: `agent_fleet/services/dashboard-web/src/` — `pages/`, `components/`, `lib/`, …
  - Calls `/api/...` on the gateway (already aligned with “single UI boundary”)
- **Agent task servers**: `agent_fleet/agents/` — one directory per agent, each with `config.yaml`, `server.py`, and `tools.py`
- **Shared ports/URLs**: `agent_fleet/packages/config.py` (e.g. `DATABASE_URL`, `GATEWAY_EVENT_URL`; gateway and telemetry import their own `config` modules that align with these)

---

### Recommended architecture (production-shaped, prototype-friendly)

#### Components
- **Agents (many)**: execute tasks and report telemetry.
- **Fleet Server (Control Plane)**: orchestrates plans/tasks/allocations/execution; writes truth to DB; commands agents.
- **Gateway/BFF (Data Plane Edge for UI)**: the only browser-facing API; fans out realtime updates; proxies or composes reads from control plane and telemetry (video/ingress may stay separate or move behind gateway later).
- **Postgres (Truth Store)**: plans/tasks/agents/goals + execution outcomes + metadata.

Optional later (add only when needed):
- **Event stream** (NATS/Redis Streams/Kafka): decouples fleet events from UI fanout/analytics.
- **Time-series store** (Prometheus/Influx/Timescale): stores high-rate telemetry history.
- **Media service** (WebRTC SFU + recorder): scalable livestream + recording.
- **Object storage** (S3/MinIO): videos, trajectories, large artifacts; Postgres stores metadata/pointers only.

---

### Control path vs Observe path (the two paths)

#### 1) Control path (“do something”)

```text
UI → Gateway/BFF → Fleet Server → Agent(s)
                    ↓
                 Postgres
```

Examples:
- register/unregister agent
- create/update plan/task, allocate agents
- start/cancel execution

Key rule:
- **UI never calls agents or fleet directly** (except in local dev prototypes if you explicitly choose to).

#### 2) Observe path (“see what’s happening”)
This splits into two categories:

##### A) Control-plane observability (authoritative state)

```text
Postgres (truth) ← Fleet Server → Gateway/BFF → UI
```

Includes:
- plans/tasks/goals/allocations
- task status + final task results
- plan execution status

##### B) Data-plane observability (telemetry + media)

```text
Agent(s) → Telemetry service → Gateway/BFF → UI
```

(In the current repo, agents **push** heartbeats to Telemetry; the gateway **pulls** health summaries from Telemetry over HTTP for API responses, and Telemetry can **push** lightweight `telemetry.health_changed` notifications to the gateway so WebSocket subscribers invalidate/refetch without polling.)

Includes:
- agent health heartbeat streams (if treated as telemetry)
- joint states, sensor streams, rich logs
- camera/video livestream

Key rule:
- **Avoid duplicating full-rate streams** to multiple consumers. Prefer “send once → fan out”.
- Fleet should consume **summaries** needed for decisions, not raw high-rate streams.

---

### “Desired vs Observed” + reconciliation (why both fleet & agent status matter)
The fleet server maintains:
- **Desired/commanded state**: what it dispatched and what the DB says should be happening.
Agents maintain:
- **Observed state**: what is actually happening (heartbeat, faults, estop, reboot, busy/idle).

Fleet computes an **effective** status by reconciling both:
- If `last_heartbeat` is stale → agent is **offline**, even if DB says tasks are in progress.
- If agent reports `fault/estop` → agent is **unavailable** even if “idle”.
- If fleet thinks busy but agent reports idle → tasks may be stale; recover/reassign.

This keeps execution robust under crashes, partitions, and restarts.

---

### Realtime: event-driven updates (**implemented**)
Current behavior (no polling for invalidation):
- On control-plane mutations, the fleet server POSTs a small JSON event to the gateway (`GATEWAY_EVENT_URL`, handled in `agent_fleet/services/gateway/src/routers/websocket.py` as `POST /internal/events`).
- The gateway keeps an in-process **EventBus** with **per-subscriber `asyncio.Queue`s**; each notification delivers query-key hints so React Query (or similar) refetches only what changed.
- Telemetry can POST the same endpoint when agent health changes so the UI updates immediately.
- WebSocket clients are woken when there is a real change, not on a fixed poll timer.

---

### Suggested event schema (minimal set)
Use a small stable contract; the UI consumes:
- **snapshot** on connect
- **deltas/events** as they happen

Suggested event types:
- `task.state_changed`: `{ plan_id, task_id, status, agent_id, ts, result? }`
- `plan.state_changed`: `{ plan_id, status, ts }`
- `agent.heartbeat`: `{ agent_id, reachable, latency_ms?, battery?, faults?, ts }`
- `agent.state_changed` (effective): `{ agent_id, effective_state, reason?, ts }`
- `replan.occurred`: `{ old_plan_id, new_plan_id, failed_task_id?, reason, ts }`

Notes:
- Keep payloads small and stable.
- For heavy content (video/log blobs), send references/URLs and fetch/stream separately.

---

### Protocol recommendations (prototype → production)

#### Control plane
- **Fleet ⇄ Agents**: gRPC is ideal (or HTTP if needed).
- **Gateway ⇄ Fleet**: gRPC or HTTP; events via WS/SSE or streaming gRPC.
- **UI ⇄ Gateway**: REST for queries/mutations; WS/SSE for realtime.

#### Telemetry
- **Agent → Telemetry service** (current default for heartbeats):
  - low-rate: HTTP POST (e.g. `/ingest/heartbeat`)
  - high-rate: WS or gRPC streaming
  - logs: WS stream
- **Telemetry → Gateway**: HTTP for health summaries the BFF serves to the UI; optional HTTP callbacks to `/internal/events` for realtime invalidation (implemented).
- **Video**:
  - agent publishes RTSP/WebRTC internally
  - gateway/media layer exposes **WebRTC** (or HLS) to browsers

---

### Naming & class design recommendations (aspirational — not the current codebase)
These are **forward-looking** naming and layering suggestions. The repo still uses the prototype names; nothing here is a promise to rename immediately.

Current names work for a prototype, but clearer separation helps future growth.

#### Rename by responsibility (recommended)
- `FleetManagerService` → **`FleetControlService`**
  - communicates “this is the control plane”
- `Executor` → **`PlanExecutor`**
  - clearer that it executes a plan DAG, not a generic “executor”
- `AgentClient` → **`AgentTaskClient`**
  - clearer that this is task RPC, not telemetry/media
- `GRPCBridge` (gateway) → **`FleetGatewayClient`** or **`FleetControlClient`**
  - “bridge” is vague; “client” clarifies direction

#### Introduce explicit interfaces (even if implemented in one file today)
- **Control plane interfaces**:
  - `IAgentCommandClient`: send tasks/cancel/pause
  - `IPlanExecutor`: run plan execution loop
  - `IStateStore`: DB operations for plans/tasks/agents
- **Gateway interfaces**:
  - `IEventSubscriber`: subscribe to fleet events
  - `IEventBroadcaster`: broadcast to UI clients
  - `ITelemetryIngestor`: accept agent telemetry
  - `IMediaSessionManager`: negotiate video sessions (later)

#### Organize packages by plane (optional refactor later)
- `agent_fleet/control_plane/...`
- `agent_fleet/data_plane/...` (telemetry already lives in `services/telemetry/` today)
- `agent_fleet/storage/...` (DB models + registry)

---

### Concrete “best-practice” changes to make next (without breaking docker testing)
- Keep frontend calling `/api/*` (already true).
- Keep dashboard backend as Gateway/BFF (already exists).
- ~~Replace WS polling loops with event-driven updates~~ (done: fleet and telemetry → gateway `POST /internal/events` → per-subscriber queues → UI).
- Move agent health to a fleet-owned heartbeat/reconciliation model (avoid UI-driven constant probing).
- Add a documented event schema and keep it stable as features grow.
- Keep videos/trajectories out of Postgres; store metadata in Postgres and blobs in object storage later.

---

### Dev workflow (still works)
- You can continue using docker “fake agents” and the frontend.
- For faster iteration on agent server code, use bind mounts (dev runner script) and restart containers to reload code.

