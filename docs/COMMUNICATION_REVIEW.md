# Communication Architecture Review: Polling vs Event-Driven

> **Document status (April 2026):** This file is a **living reference**. It describes the current stack and what is still worth tightening. Paths below are under the `` tree unless noted.
>
> **Implemented since the original draft**
> - **Fleet → Gateway:** The fleet server POSTs mutation events to the gateway (`POST /internal/events`). See `services/fleet_server/src/events.py` and call sites in `service.py` / `executor/executor.py`.
> - **Gateway WebSocket (`ws/global-updates`):** **Event-driven.** An in-process `EventBus` holds per-subscriber `asyncio.Queue`s; the handler waits on the queue and only sends `invalidate` when an event arrives (plus optional `ping` on a 30s idle timeout). Implemented in `services/gateway/src/routers/websocket.py`.
> - **Gateway WebSocket (`ws/execution/{plan_id}`):** **Also event-driven** (same event bus): on notification it refetches tasks for that `plan_id` via the gRPC bridge and pushes `tasks_update`. It does **not** use a 1s `sleep` loop anymore. Caveat: any fleet/telemetry event currently wakes all execution subscribers, which then each refetch their plan (possible future optimization: filter by `plan_id` / event payload).
> - **Telemetry service:** Separate HTTP service on port **9000** (`TELEMETRY_PORT`). Agents POST heartbeats to **`/ingest/heartbeat`** (see `services/telemetry/src/routers/ingest.py`). Telemetry publishes **`telemetry.health_changed`** to the gateway’s `/internal/events` when health changes (see `services/telemetry/src/publishing.py`). The gateway reads aggregated health from Telemetry (`TELEMETRY_URL`, e.g. `services/gateway/src/services/telemetry_client.py`).
> - **Demo agents:** Push heartbeats to the Telemetry URL via AgentServer (e.g. `agents/physical/*/server.py`), not to the gateway.
>
> **Still open / incremental**
> - **Frontend:** Reduce remaining intentional polling (e.g. Execution page plan `refetchInterval` while `executing`) and align every “live” view with WS invalidation where possible.
> - **Execution WS:** Optionally narrow which events trigger `list_tasks` per connection.
> - **Gateway** still includes a legacy **`/api/telemetry/heartbeat`** router (`services/gateway/src/routers/telemetry.py`) for ingest experiments; production-style flow is **Telemetry :9000 → gateway reads `/health/*`**.

Revisit after many days: what’s done, what’s wasteful, and what’s left for the frontend, gateway, fleet server, and agent servers.

---

## 1. What’s Been Done and Changed

### Frontend ↔ Gateway (single UI boundary)
- **Done:** UI talks only to the gateway via `/api/*` and `/ws/*` (no direct calls to fleet or agents).
- **Done:** `useRealtimeUpdates()` exists and is used on Plans, PlanDetails, Agents, Goals, Dashboard, App shell, and Execution. It connects to `ws/global-updates` and invalidates React Query when it receives `type: "invalidate"` with the query keys the gateway derives from event types.
- **Done:** PlanDetails and Plans explicitly avoid `refetchInterval` and rely on WebSocket-driven invalidation (comments: “No refetchInterval - using WebSocket real-time updates”).
- **Done (default QueryClient):** `services/dashboard-web/src/main.tsx` sets **`staleTime: 2000`** only; there is **no** global `refetchInterval: 5000` anymore.

### Gateway WebSocket “real-time”
- **Current behavior (`services/gateway/src/routers/websocket.py`):**
  - **`POST /internal/events`:** Accepts JSON events from the fleet server and from Telemetry (e.g. `task.state_changed`, `plan.state_changed`, `agent.changed`, `telemetry.health_changed`). Each event maps to React Query key lists and calls `event_bus.notify(...)`.
  - **`ws/global-updates`:** Subscribes to a per-connection queue; **`await queue.get()`** with a 30s timeout for keepalive `ping`. **No polling loop** for “something changed.”
  - **`ws/execution/{plan_id}`:** Subscribes to the **same** event bus; when woken, calls `bridge.list_tasks(plan_ids=[plan_id])` and sends `tasks_update`. Again, **no 1s sleep loop**—traffic is driven by events (with the same 30s idle `ping` pattern).

### Where polling / refetch is still used (worth reviewing)
- **`services/dashboard-web/src/pages/Execution.tsx`**
  - Plan query: **`refetchInterval`** of **3s** while `execution_status === 'executing'` (HTTP refetch of plan metadata).
  - Tasks: primary display prefers **`ws/execution/{planId}`** (`GatewayRealtimeClient.connectPlanExecution`); initial/fallback load still uses `tasksApi.list`.
  - Agents list: no aggressive `refetchInterval` in the current file; `useRealtimeUpdates()` covers broader invalidation.

- **`services/dashboard-web/src/pages/Dashboard.tsx`**
  - Uses **`useRealtimeUpdates()`**; **`agent-health`** has **no** `refetchInterval`—updates follow gateway invalidation (including `telemetry.health_changed` → `agent-health`).

### Fleet server (central server)
- **Done:** Writes plan/task/agent truth to Postgres via the registry; executor updates task and plan execution status.
- **Done:** After mutations, the fleet server **notifies the gateway** by fire-and-forget HTTP POST to `GATEWAY_EVENT_URL` (default `http://localhost:8000/internal/events` in dev; `http://gateway:8000/internal/events` in Compose). See `services/fleet_server/src/events.py`.

### Agent servers (Docker / fake)
- **Done:** Agents expose HTTP (`/tasks/execute`, `/health`). Fleet executor calls agents via `AgentClient` (HTTP).
- **Done (heartbeats):** Demo agents **POST heartbeats to the Telemetry service** on an interval (AgentServer in each `agents/physical/*/server.py`). Identity in Telemetry is **`host:port`**; the gateway merges that with fleet `agent_id` when serving `/api/agents/health/all`.
- **Gap (optional):** “Task started / completed” pushes from agents to the fleet are still not a separate channel beyond normal executor HTTP; high-rate telemetry remains out of scope here.

---

## 2. Summary: What Is Wasteful Today

| Layer | What’s happening | Why it can still be wasteful |
|-------|------------------|------------------------------|
| **Gateway WS** | Event-driven invalidation + execution task snapshots | Execution connections may **refetch tasks on any** fleet/telemetry event, not only events for their `plan_id`. |
| **Frontend (Execution)** | Plan metadata **refetch every 3s** while executing | Could rely more on WS + targeted invalidation if plan fields are also event-driven. |
| **Telemetry** | Background **timeout scanner** loop (`services/telemetry/src/app.py`) | Intentional: detects missed heartbeats and emits `telemetry.health_changed`. Not UI polling. |

---

## 3. What’s Remaining for the Frontend

- **Execution page:** Consider dropping or lengthening the **3s plan `refetchInterval`** during execution if plan status can be inferred from tasks/WS alone, or invalidate `['plan', planId]` only when execution-related events fire.
- **Consistency:** Any page that should feel “live” should prefer **`useRealtimeUpdates()`** + gateway invalidation over ad hoc `refetchInterval`, and document any remaining intentional poll.

---

## 4. What’s Remaining for Gateway ↔ Fleet (Event-Driven)

- **Done:** Fleet → gateway HTTP events for task/plan/agent mutations.
- **Optional next steps:** If the gateway and fleet scale beyond one host each, replace in-process fan-out with a shared bus (Redis, NATS, etc.) while keeping the same event **types** and payloads. Optionally include **`plan_id` filtering** on execution WS handlers to avoid redundant `list_tasks` calls.

---

## 5. Agent Servers → Telemetry / Gateway / Fleet

- **Done:** Heartbeats to **Telemetry :9000** (`/ingest/heartbeat`); Telemetry notifies gateway for `agent-health` invalidations.
- **Done (read path):** Gateway **`/api/agents/health/*`** uses **`services/gateway/src/services/telemetry_client.py`** against Telemetry’s **`/health/summary`** and **`/health/{agent_id}`** (see `services/telemetry/src/routers/health.py`).
- **Recommended later:** Richer telemetry streams (logs, joint state) via dedicated channels; keep heartbeats low-rate HTTP as today.

---

## 6. Quick Reference: Current vs Desired

| Concern | Current | Desired / next |
|--------|--------|----------------|
| **UI → Gateway** | Only `/api` and `/ws`; single boundary | Keep as is. |
| **Live data (plans, tasks, agents)** | WS event-driven invalidation; Execution uses dedicated WS for tasks | Tighten remaining HTTP refetch (Execution plan poll). |
| **Default refetch** | No global `refetchInterval` in `main.tsx` | Keep; avoid reintroducing global polling. |
| **Execution page** | WS task stream + 3s plan poll while executing | Prefer event-only updates where possible. |
| **Agent health** | Telemetry heartbeats + gateway merge for UI | Keep; monitor timeout scanner interval vs UX. |
| **Fleet → Gateway** | HTTP `POST /internal/events` | Optional: external bus at scale. |
| **Agents → central** | Heartbeats → Telemetry → gateway events | Extend with richer telemetry when needed. |

---

## 7. Files to Touch (for “no polling unless necessary”)

- **Frontend:**  
  `services/dashboard-web/src/main.tsx` (default query options),  
  `services/dashboard-web/src/pages/Dashboard.tsx` (`agent-health` / aggregation),  
  `services/dashboard-web/src/pages/Execution.tsx` (plan `refetchInterval`; task WS already wired).
- **Gateway:**  
  `services/gateway/src/routers/websocket.py` (`/internal/events`, `ws/global-updates`, `ws/execution/{plan_id}`),  
  `services/gateway/src/services/telemetry_client.py`,  
  `services/gateway/src/app.py` / `main.py` (app wiring).  
  Optional legacy ingest: `services/gateway/src/routers/telemetry.py`.
- **Fleet:**  
  `services/fleet_server/src/events.py`,  
  `services/fleet_server/src/service.py`,  
  `services/fleet_server/src/executor/executor.py` (emit hooks).
- **Telemetry:**  
  `services/telemetry/src/app.py`,  
  `services/telemetry/src/routers/ingest.py`,  
  `services/telemetry/src/publishing.py`,  
  `services/telemetry/src/heartbeat_store.py`.
- **Agents:**  
  `agents/physical/*/server.py` (heartbeat URL / interval).

This keeps the architecture aligned with `DESIGN.md` and documents the move from gateway polling loops to **event-driven** WebSockets and a **standalone Telemetry** service on port **9000**.
