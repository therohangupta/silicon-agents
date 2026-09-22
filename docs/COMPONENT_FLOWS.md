# Who Talks to Whom: Gateway, Fleet Server, Telemetry, Agents

Clear picture of the main backend services and how data flows. Paths below are relative to the `` directory (Python package root).

---

## The main components

| Component | What it is | Typical port |
|-----------|------------|--------------|
| **Fleet server** | Central control plane. Owns the database (plans, tasks, agents, goals). Runs plan execution (sends tasks to agents). Exposes **gRPC** only. | 50051 |
| **Gateway** | Single entry point for **all clients** (browser, mobile, CLI). Exposes **REST + WebSockets**. Proxies control and DB-backed reads to the fleet via gRPC; queries the **Telemetry** service over HTTP for heartbeat-derived health. | 8000 |
| **Telemetry** | Separate service for **agent push** ingest (heartbeats today; room for streams later) and **health read APIs** the Gateway calls. Does not own fleet control data. | 9000 |
| **Agent** | One per physical/digital agent. AgentServer: `/tasks/execute`, `/health`, heartbeats **to Telemetry**. | 8001, 8002, … |

---

## Rule of thumb

- **Clients (e.g. browser)** → talk **only** to the **Gateway** (except the one-off “Send Task” shortcut below).
- **Gateway** → talks to the **Fleet server** (gRPC) for control and DB-backed lists; talks to **Telemetry** (HTTP) for ingest-derived health and related reads.
- **Fleet server** → talks to **Agents** (to send tasks: “do this”).
- **Agents** → talk to the **Telemetry service** (heartbeats). They do **not** send heartbeats to the Fleet server for that path.

Realtime UI invalidation: after mutations, the **Fleet server** POSTs events to the Gateway (`POST /internal/events`); the Gateway’s WebSocket handlers notify clients. **Telemetry** can also POST health-changed events to the same endpoint so the UI refreshes agent health without polling.

So: nothing in the fleet **control plane** is bypassed for normal API usage; **Telemetry** sits beside the Gateway for observation data from agents.

---

## Flow diagrams

### 1) Control: “Do something” (create plan, run task, register agent, …)

```
  Browser (or other client)
         │
         │  HTTP: POST /api/plans, /api/plans/123/start, /api/agents/register, etc.
         ▼
  ┌──────────────┐
  │   Gateway    │
  └──────────────┘
         │
         │  gRPC: CreatePlan, StartExecution, RegisterAgent, etc.  (via grpc bridge)
         ▼
  ┌──────────────┐
  │ Fleet Server │ ──────►  Database (Postgres): plans, tasks, agents, goals
  └──────────────┘
         │
         │  When executing a plan: HTTP POST to each agent’s /do_task
         ▼
  ┌──────────────┐
  │    Agent     │  (one per agent; Fleet calls them)
  └──────────────┘
```

- **Request flow:** Client → Gateway → Fleet server. Fleet server may then call Agents.
- **Data flow:** Client sends intent; Gateway forwards; Fleet updates DB and commands agents; Agent returns task result to **Fleet**; Fleet updates DB again.

---

### 2) Observe: “See what’s happening” (list plans, task status, agent list, …)

```
  Browser (or other client)
         │
         │  HTTP: GET /api/plans, /api/tasks, /api/agents, etc.
         │  WebSocket: /ws/global-updates, /ws/execution/123
         ▼
  ┌──────────────┐
  │   Gateway    │
  └──────────────┘
         │
         │  gRPC: ListPlans, ListTasks, ListAgents, GetPlan, …  (via grpc bridge)
         ▼
  ┌──────────────┐
  │ Fleet Server │ ──────►  Database: read plans, tasks, agents, goals
  └──────────────┘
```

- **Request flow:** Client → Gateway → Fleet server (which reads from DB).
- **Data flow:** Fleet returns data to Gateway; Gateway returns it to the client. **Agents are not in this path** for “list plans / tasks / agents.”
- **Agent health in the UI:** Gateway aggregates fleet agent records with **Telemetry** health (`GET /health/...` on the Telemetry service). Heartbeats are **not** stored inside the Gateway process.
- **WebSockets:** The fleet server emits mutation events (`services/fleet_server/src/events.py`); the Gateway receives them on `POST /internal/events` and fans out invalidation over `/ws/global-updates` (see `services/gateway/src/routers/websocket.py`). Telemetry may POST `telemetry.health_changed` to the same internal endpoint when heartbeat-derived status changes.

---

### 3) Agent → Telemetry: heartbeats (and future telemetry)

```
  ┌──────────────┐
  │    Agent     │
  └──────────────┘
         │
         │  HTTP POST: /ingest/heartbeat  (Telemetry service; identity is host:port)
         │  (every N seconds; no one polls the agent)
         ▼
  ┌──────────────┐
  │  Telemetry   │  stores last heartbeat; exposes GET /health/summary, /health/{id}
  └──────────────┘
         │
         │  optional: POST /internal/events on Gateway (health_changed) for WS clients
         ▼
  ┌──────────────┐
  │   Gateway    │  browser calls GET /api/agents/health/* → Gateway queries Telemetry
  └──────────────┘
```

- **Request flow:** Agent → Telemetry for ingest; Browser → Gateway → Telemetry for displayed health.
- **Data flow:** Agent pushes “I’m alive, busy/idle” to Telemetry. Gateway reads that state when the UI asks. Fleet server is **not** in the heartbeat ingest path.

---

### 4) “Send Task” from the UI to one agent (special case)

Today, the **browser** can send a single task directly to a agent (agent card → “Send Task”):

```
  Browser
     │
     │  HTTP POST to http://<agent_host>:<agent_port>/tasks/execute
     │  (Browser uses agent’s host/port from GET /api/agents)
     ▼
  ┌──────────────┐
  │    Agent     │  returns { success, message, replan }
  └──────────────┘
```

- Here the browser talks **directly** to the agent (one-off). The Gateway is only used to get the agent’s address (from the list). This is the only case where the client skips the Gateway for the actual request.

---

## Summary table

| Who | Talks to Fleet server? | Talks to Gateway? | Talks to Telemetry? | Talks to Agent? |
|-----|------------------------|-------------------|---------------------|-----------------|
| **Browser** | No | Yes (all API + WS) | No (only via Gateway) | Yes, only “Send Task” |
| **Gateway** | Yes (gRPC) | — | Yes (HTTP read + receives internal events) | No |
| **Fleet server** | — | Yes (outbound: POST mutation events to Gateway) | No | Yes (during execution) |
| **Telemetry** | No | Yes (POST /internal/events for health fan-out) | — | No |
| **Agent** | No | No | Yes (heartbeat ingest) | — |

So:

- **Gateway** talks to **Fleet server** (gRPC) and **Telemetry** (HTTP), and receives **internal event POSTs** from Fleet and Telemetry.
- **Fleet server** talks to **Agents** (and DB).
- **Agents** push heartbeats to **Telemetry**; they respond to **Fleet server** (and optionally the browser) for `/tasks/execute`.

---

## Where this lives in the repo

| Area | Path |
|------|------|
| Gateway HTTP routers (plans, agents, tasks, goals, telemetry proxy, etc.) | `services/gateway/src/routers/` (`plans.py`, `agents.py`, `tasks.py`, `goals.py`, `telemetry.py`, …) |
| Gateway ↔ Fleet gRPC bridge | `services/gateway/src/grpc_bridge.py` |
| Gateway WebSockets + `POST /internal/events` | `services/gateway/src/routers/websocket.py` |
| Fleet gRPC service implementation | `services/fleet_server/src/service.py` |
| Plan / task execution loop | `services/fleet_server/src/executor/executor.py` |
| Fleet → Gateway event emission | `services/fleet_server/src/events.py` |
| Planners | `services/fleet_server/src/planners/` |
| Allocators | `services/fleet_server/src/allocators/` |
| DB / instance registry (fleet_sdk) | `packages/fleet_sdk/src/instance_registry.py` |
| Shared ports and URLs | `packages/config.py` |
| Telemetry FastAPI app, heartbeat store, publishing | `services/telemetry/src/` (`app.py`, `heartbeat_store.py`, `publishing.py`, …) |
| Dashboard API client and helpers | `services/dashboard-web/src/lib/` (`api.ts`, `utils.ts`) |
| Dashboard pages | `services/dashboard-web/src/pages/` |
