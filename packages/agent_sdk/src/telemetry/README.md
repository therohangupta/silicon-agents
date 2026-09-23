# Agent SDK — telemetry (`packages/agent_sdk/src/telemetry/`)

Agent-side observability: **HTTP heartbeats and event ingest** plus an optional **gRPC publisher** for high-frequency streams (video-like telemetry, dense progress) when an agent supplies `telemetry_adapter.py`.

Wire format aligns with [`packages/proto/telemetry.proto`](../../../proto/telemetry.proto) (`TelemetryEvent` messages).

---

## Purpose in the fleet

Operators and the control plane need to know:

- Which agents are alive and busy
- When tasks start, complete, or fail
- Which skills ran, with args summaries and duration
- Optional artifact and custom stream payloads

This directory implements the **emit path from the agent process** toward the fleet telemetry ingest service (HTTP POST and gRPC stub).

---

## Placement in architecture

```text
AgentServer lifespan
        │
        ├── TelemetryClient  ──► POST /telemetry/ingest (heartbeats, events)
        │         ▲
        │         │ emit on task lifecycle, skill_call hook, traces
        │
        └── TelemetryPublisher (optional) ◄── telemetry_adapter.py
                  │
                  gRPC TelemetryIngestion ──► stream_idle / stream_task
                  blob upload URL ──► HTTP /telemetry/blob
```

[`AgentServer`](../server/agent_server.py) constructs `TelemetryClient` in `_setup_telemetry` and optionally connects `TelemetryPublisher` when an adapter module exists.

---

## Files in this directory

| File | Role |
|------|------|
| [`client.py`](client.py) | `TelemetryClient` — async HTTP, heartbeats, `emit()` building protobuf JSON |
| [`publisher.py`](publisher.py) | `TelemetryPublisher` — gRPC connect, ingest, blob helpers for adapters |
| [`__init__.py`](__init__.py) | Package marker |
| [`README.md`](README.md) | This document |

Public package re-export: `from packages.agent_sdk import TelemetryClient`.

---

## TelemetryClient (`client.py`)

**Construction** (from server):

- `agent_id`, `agent_type` — usually `config.metadata.name`
- `endpoint` — from `observability.telemetry.endpoint`, expanded env, default `TELEMETRY_URL` from platform config
- `heartbeat_interval_secs` — from observability or `AGENT_HEARTBEAT_INTERVAL_SECS`
- `host`, `port` — agent connection info included in heartbeat payload

**Key methods:**

| Method | Purpose |
|--------|---------|
| `start_heartbeat()` / `stop_heartbeat()` | Background asyncio task posting periodic heartbeats |
| `set_busy(busy)` | Reflect task execution in heartbeat status |
| `emit(event_type, payload, stream_name=..., task_id=..., severity=...)` | Build `TelemetryEvent`, POST to ingest |
| `close()` | Stop heartbeat, close httpx client |

**Event types** commonly used by server: `task_started`, `task_completed`, `task_failed`, `task_artifacts`, `skill_call` (stream `skill_calls`).

Severity maps string labels to protobuf enum values.

---

## TelemetryPublisher (`publisher.py`)

**Construction:**

- `agent_id`, `agent_type`
- `grpc_target` — from `TELEMETRY_GRPC_TARGET` env or host/port derived from telemetry URL + platform settings
- `blob_upload_url` — typically `{telemetry_http}/telemetry/blob`

**Key methods:**

| Method | Purpose |
|--------|---------|
| `connect()` / `close()` | gRPC aio channel and stub lifecycle |
| `_base_event(...)` | Shared metadata (sequence_id, schema_version v1, source_id) |
| `_ingest(event)` | Send event on stub |
| Higher-level helpers | Used by adapters for chunked/streaming modalities (see module body) |

Adapters implement **`stream_idle(publisher)`** and **`stream_task(publisher, task_id, ...)`** coroutines; server manages task cancellation around execute.

---

## Data and control flow

1. **Startup** — Heartbeat loop begins; optional gRPC connect + idle stream.
2. **Task** — `task_started` HTTP emit; adapter task stream if configured; runtime executes.
3. **Skills** — Registry hook fires async `skill_call` emits; result traces may emit again post-task.
4. **Completion** — `task_completed` / artifacts; idle stream resumes.
5. **Shutdown** — Cancel streams, close gRPC and HTTP clients.

Events carry monotonic `sequence_id` per client/publisher instance for ordering on the consumer side.

---


---

## Related paths

| Path | Notes |
|------|--------|
| [`../server/agent_server.py`](../server/agent_server.py) | Wiring and lifecycle |
| [`../../../proto/telemetry.proto`](../../../proto/telemetry.proto) | Event schema |
| [`../../../packages/platform_config/`](../../../packages/platform_config/) | Default URLs and intervals |
| [`../../../agents/TELEMETRY.md`](../../../agents/TELEMETRY.md) | Adapter contract |

---

## Newcomer reading order

1. [`../../../agents/TELEMETRY.md`](../../../agents/TELEMETRY.md) — operator view
2. [`client.py`](client.py) — HTTP path
3. [`../server/agent_server.py`](../server/agent_server.py) — when emits fire
4. [`publisher.py`](publisher.py) — only if authoring an adapter

---

## Operational notes

- **Network** — HTTP client timeout 10s; failed emits should be logged, not crash tasks (see try/except in client).
- **gRPC optional** — Publisher connection failure logs warning; agent still runs on HTTP telemetry only.
- **Env vars** — `TELEMETRY_URL`, `TELEMETRY_GRPC_TARGET`, `TELEMETRY_GRPC_PORT`, `TASK_DURATION`.
- **Protobuf** — Generated code under `packages.proto`; keep schema in sync with ingest service version.
- **PII** — Payloads may contain task descriptions; scrub at ingest if exporting logs externally.

No subdirectories under `telemetry/`.
