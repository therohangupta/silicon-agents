# Telemetry, Data Flow, and Agent → Storage Pipeline

Telemetry is **not** just lightweight heartbeats. Long term it includes **execution data** for collection and training: video, images, joint positions, logs. The **Telemetry service** is a **separate HTTP server** that ingests from agents, holds (today: in-memory) state, and exposes **read APIs** so the **Gateway (BFF)** can query it and pass data to the frontend for display. The frontend never talks to the Telemetry service directly.

---

## 1. What handles telemetry today (v2)

### Telemetry service (canonical path)

The **Telemetry service** is a dedicated FastAPI app under **`services/telemetry/src/`**:

| Area | Files / behavior |
|------|------------------|
| App entry, lifespan, timeout scanner | `app.py` — background task calls `HeartbeatStore.check_timeouts()` and publishes when agents go stale |
| Store | `heartbeat_store.py` — thread-safe in-memory ring buffer (last **N** heartbeats per agent; **N** = `MAX_HEARTBEATS_PER_ROBOT` in `packages/config.py`) |
| Ingest | `routers/ingest.py` — **`POST /ingest/heartbeat`** |
| Read API | `routers/health.py` — **`GET /health/summary`**, **`GET /health/{agent_id}`** |
| Events | `events.py` — `HealthChangedEvent` with `type: "telemetry.health_changed"` |
| Publish to Gateway | `publishing.py` — HTTP **`POST`** to `GATEWAY_EVENT_URL` (default `{GATEWAY_URL}/internal/events`) |

**Agents** should POST heartbeats to **`{TELEMETRY_URL}/ingest/heartbeat`** (Compose exposes Telemetry on **port 9000** by default; `TELEMETRY_URL` / `TELEMETRY_PORT` come from `packages/config.py`).

**Ingest body** (see `routers/ingest.py`): `host`, `port`, `reachable`, optional `busy`, optional `ts`. The store’s primary key is **`host:port`** (task server address), so the Gateway can join Telemetry data with Fleet agents using each agent’s `task_server_info`.

**Joint positions, video, and rich logs** are still **not** implemented on this path; the target architecture below still applies for those.

### Gateway (consumer + real-time fan-out)

- **`services/gateway/src/services/telemetry_client.py`** — fetches **`GET {TELEMETRY_URL}/health/summary`** and **`GET {TELEMETRY_URL}/health/{agent_id}`** when serving Gateway APIs.
- **`services/gateway/src/routers/agents.py`** — agent health endpoints default to **`source=telemetry`**: they merge Fleet’s agent list with Telemetry’s summary keyed by **`host:port`**.
- **`services/gateway/src/routers/websocket.py`** — accepts **`POST /internal/events`** from Fleet **and** Telemetry; maps **`telemetry.health_changed`** → invalidates **`agent-health`** for WebSocket clients (same event bus as fleet mutations).

### Legacy route on the Gateway (optional / migration)

**`services/gateway/src/routers/telemetry.py`** still defines **`POST /api/telemetry/heartbeat`** with a **`agent_id`**-shaped payload and an in-memory **`_heartbeats`** dict on the Gateway. That path is **legacy**; with Telemetry deployed, agents should use **`POST …/ingest/heartbeat`** on the Telemetry service so the Gateway reads one source of truth via **`telemetry_client`**.

---

## 2. Frontend ↔ one agent: what actually happens

You have two ways the frontend interacts with a single agent:

### A) “Send Task” from the Agent detail (UI → agent **directly**)

1. Frontend gets the agent list from **Gateway** (`GET /api/agents`), which comes from Fleet/DB (includes `task_server_info.host` and `task_server_info.port`).
2. User opens a agent, goes to “Send Task”, enters a description, and submits.
3. Frontend **POSTs straight to the agent**:
   - URL: `http://<agent_host>:<agent_port>/tasks/execute`
   - Body: `{ "task_id", "description", "record_episode" }` (AgentTaskRequest)
4. Agent responds with:
   - `{ "success": bool, "message": string, "replan": bool }` (task result).

So for this flow: **frontend → agent directly**. No telemetry: only the one-off task result in the HTTP response. The gateway is not in the path for this request.

### B) Plan execution (UI → Gateway → Fleet → agent)

1. User creates/allocates a plan and clicks “Execute” (or “Start”).
2. Frontend calls **Gateway** `POST /api/plans/{plan_id}/start`.
3. Gateway calls **Fleet** (gRPC); Fleet’s **Executor** runs the plan:
   - For each ready task, Fleet’s `AgentClient` **POSTs to that agent’s `/tasks/execute`** (same contract as above, but from Fleet, not from the browser).
4. Agent returns the same `TaskResult` to Fleet; Fleet updates task status in the DB.
5. Frontend learns about progress by:
   - Polling (e.g. `GET /api/tasks?plan_id=...`) or
   - WebSocket `ws/execution/{plan_id}` (today still a 1s poll under the hood).

So for execution: **data “from the agent”** that the frontend sees is **task status and result text** stored in the DB and exposed via Gateway APIs/WS. No raw telemetry (joints, video) in this path.

---

## 3. Target: telemetry from agent → your storage (joints, video, etc.)

You want:

- **Each agent** to use its own stack (ROS1/2, Rust, etc.) to **read** joint positions, video, and other sensors.
- **Send** that data to a **central ingest** (no duplicate streams to many consumers).
- **Store** in a **place you specify** (e.g. object storage, time-series DB) for data collection and training.

A clean way to do that:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Agent                                                                      │
│  - Task server (FastAPI): /tasks/execute, /health, telemetry heartbeats       │
│  - Agent-specific collector: ROS1/2 or Rust → reads joints, camera, etc.  │
│  - Sends telemetry to central ingest (HTTP POST, WebSocket, or gRPC stream)│
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Central telemetry ingest                                                   │
│  **Today:** Telemetry service — heartbeats only (`POST /ingest/heartbeat`).  │
│  **Target:** same service (or additional routes) receives streams per      │
│    agent (tags: agent_id / host:port, plan_id, task_id, session_id).        │
│  - Normalizes / validates (e.g. canonical joint schema, chunked video).    │
│  - Forwards to storage you configure.                                       │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Your storage (you specify)                                                 │
│  - Time-series DB (e.g. Influx, Timescale, Prometheus): joint positions,    │
│    small sensor streams.                                                     │
│  - Object storage (S3, MinIO, GCS): video files, trajectory dumps, logs.   │
│  - Postgres (or existing DB): metadata, indexes (agent_id, plan_id, task_id,│
│    timestamps, pointers to blobs in object storage).                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Displaying telemetry in the UI:** The **Telemetry service** exposes **read APIs** (today: health summary derived from heartbeats). The **Gateway (BFF)** calls those APIs and passes the response to the frontend. So: **Browser → Gateway → Telemetry service (query) → Gateway → Browser**. The frontend never talks to the Telemetry service directly.

- **Who handles telemetry (heartbeats):** **`services/telemetry/src/`** — ingest, store, read API, and push **`telemetry.health_changed`** to the Gateway. The Gateway **queries** Telemetry on demand when serving health APIs and reacts to events for WebSocket invalidation (see `TELEMETRY_STORE_AND_EVENTS.md`).
- **Flow of data (ingest, heartbeats):** agent → **`POST {TELEMETRY_URL}/ingest/heartbeat`** → Telemetry store → (optional) event → Gateway → WS → UI refetch.
- **Flow of data (display):** Frontend → Gateway → **`GET {TELEMETRY_URL}/health/...`** → Gateway → Frontend.

Concretely (heartbeats **implemented**; streams **future**):

1. **Agent side (your responsibility per agent)**
   - Keep the task server for **control** (`/tasks/execute`, `/health`).
   - Send heartbeats to **`{TELEMETRY_URL}/ingest/heartbeat`** with **`host`/`port`** matching the task server Fleet knows about.
   - **Later:** add a **telemetry sender** (ROS node, Rust binary, etc.) that pushes structured streams to new ingest endpoints on the Telemetry service (or a sibling component).

2. **Central ingest (Telemetry service)**
   - **Implemented:** `POST /ingest/heartbeat`, read **`GET /health/summary`**, **`GET /health/{agent_id}`**, publish to Gateway **`POST /internal/events`**.
   - **Add later:** e.g. `POST /ingest/stream` (and/or WebSocket) for joints/logs; chunked or streaming video to object storage; metadata in Postgres.

3. **Storage you specify**
   - Configure the ingest (or media service) with time-series DB, object storage, and optional Postgres — **future** for high-volume telemetry; heartbeats today stay in-process on the Telemetry service unless you add Redis etc. (see `TELEMETRY_STORE_AND_EVENTS.md`).

4. **Frontend**
   - For **control**: unchanged (Send Task → agent; Execute Plan → Gateway → Fleet → agent).
   - For **telemetry**: no direct agent↔frontend telemetry. Frontend uses Gateway APIs; Gateway reads Telemetry and receives push invalidations over **`/ws/global-updates`**.

This keeps a single path for heartbeats: **agent → Telemetry → (events + read API) → Gateway → UI**, and leaves room to grow **agent → Telemetry → your storage** for training-scale data.

---

## 4. Summary

| Question | Answer |
|----------|--------|
| **What handles telemetry (heartbeats)?** | **Telemetry service** at `services/telemetry/src/`. Gateway **`telemetry_client`** reads **`/health/*`**; **`websocket`** handles **`telemetry.health_changed`**. Legacy **`routers/telemetry.py`** on the Gateway is optional. |
| **Frontend → one agent flow** | **Control:** (1) “Send Task” = frontend → agent `POST /tasks/execute`. (2) Execute plan = frontend → Gateway → Fleet → agent `/tasks/execute`; results via DB and Gateway APIs/WS. **Telemetry:** heartbeats + events → Telemetry; physical agents also stream joints/video via gRPC adapters. |
| **Joint / video / storage** | Target: agent collector → Telemetry (or media) ingest → **your** time-series DB and object storage. **Today:** only heartbeat ingest + in-memory store on Telemetry. |

For the event-driven health path and store patterns, see **`TELEMETRY_STORE_AND_EVENTS.md`**.
