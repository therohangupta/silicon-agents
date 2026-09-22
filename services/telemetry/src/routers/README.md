# Telemetry HTTP routers

FastAPI `APIRouter` modules mounted by `app.py`. Each file owns a URL prefix
and OpenAPI tag; the package `__init__.py` does not re-export routers — `app`
imports submodules by name to keep dependency direction one-way (routers → store
/ publishing / bus, never the reverse).

## Mount order in `app.py`

Routers are included without a global prefix:

```text
ingest.router      → /ingest/*
health.router      → /health/*
telemetry_ingest   → /telemetry/*
blob_upload        → /telemetry/*   (same prefix, different paths)
```

`/healthz` is defined directly on the app object for cheap orchestrator probes.

## `ingest.py` — agent heartbeats

**Route:** `POST /ingest/heartbeat`

**Body (`HeartbeatPayload`):**

| Field | Type | Notes |
|-------|------|-------|
| `host` | string | Required; part of identity key |
| `port` | int | Required; part of identity key |
| `reachable` | bool | Default `true`; agent-reported liveness |
| `busy` | bool, optional | Workload hint for UI |
| `ts` | float, optional | Producer time; server uses `time.time()` if omitted |

**Behaviour:**

- Builds agent key `f"{host}:{port}"`.
- Coalesces bursts: pending map + lock keeps latest payload per key before
  `HeartbeatStore.record_heartbeat`.
- On effective-reachable change, `await publisher.publish(HealthChangedEvent(...))`.
- Always returns `{"ok": true}` on the success path (including coalescing races).

**Dependencies:** `HealthChangedPublisher` via `Depends(get_publisher)`.

Agents typically call this on a fixed interval from the task server process.
The gateway never POSTs here — it only reads derived health.

## `health.py` — read API for operators

**Routes:**

| Method | Path | Response |
|--------|------|----------|
| GET | `/health/summary` | Dict keyed by agent id (and `host:port` aliases when indexed) |
| GET | `/health/{agent_id}` | Single summary or **404** if never seen |

Summaries expose fields such as `last_seen`, effective `reachable`, and `busy`
as maintained by `HeartbeatStore`. These endpoints are the backing store for
`gateway`’s `TelemetryClient` health proxy.

There is no mutation API on this router — all state changes arrive through
heartbeats or the internal timeout scanner in `app.py`.

## `telemetry_ingest.py` — batch JSON ingest

**Route:** `POST /telemetry/ingest`

**Request body:** JSON array of telemetry event objects, or `{ "events": [ ... ] }`,
or a single event object. Each object is converted with `google.protobuf.json_format.ParseDict`
into `TelemetryEvent`.

**Response (`IngestResponse`):**

| Field | Meaning |
|-------|---------|
| `ok` | `true` only when `rejected == 0` |
| `accepted` | Count published to NATS |
| `rejected` | Validation/parse failures |
| `errors` | Human-readable messages (truncated to 20 in response) |
| `rejected_event_ids` | Ids that failed |

**Pipeline per event:**

1. Skip if `dedup.is_duplicate(event_id)` (not counted as rejected).
2. `validate_event` — hard failure increments rejected.
3. `check_sequence` — logs warning only.
4. Set `ingest_time_ns`, publish to `telemetry.{modality}.{agent_id}`.

**Dependencies:** `request.app.state.message_bus` (must be connected for accepts).

Use this path for tools and agents that prefer HTTP over gRPC. High-throughput
agents should prefer `TelemetryIngestion.StreamTelemetry` on the gRPC port.

## `blob_upload.py` — vision binary upload

**Route:** `POST /telemetry/blob` (multipart form)

| Form field | Required | Purpose |
|------------|----------|---------|
| `agent_id` | yes | Namespace for stored object |
| `stream_name` | yes | Camera or stream identifier |
| `file` | yes | Raw bytes (frame, clip, etc.) |
| `task_id` | no | Sub-directory scope when set |

**Response:** `{ "uri": "<backend-specific URI>", "size": <bytes> }`

The returned URI is embedded in protobuf vision events as `BlobRef.uri` so
NATS messages stay small. Storage backend is selected by `BLOB_STORAGE_BACKEND`
(local path under `BLOB_STORAGE_ROOT` or S3).

## Cross-cutting concerns

**Authentication:** Routers do not implement auth today; network placement
(Compose internal network) is the primary boundary. If exposing telemetry HTTP
beyond the cluster, terminate TLS and add auth at an ingress layer.

**CORS:** Configured at the app level from `CORS_ORIGINS`, not per router.

**Error handling:** Ingest and blob routes log and continue where possible;
health routes use explicit `HTTPException(404)` for unknown agents.

## Adding a new router

1. Create `routers/my_feature.py` with `router = APIRouter(prefix=..., tags=[...])`.
2. Mount in `app.py` via `app.include_router(...)`.
3. Put shared state on `app.state` during lifespan if the route needs NATS or
   publishers — avoid module-level mutable singletons beyond existing stores.
4. Document new env vars in [`../../README.md`](../../README.md) configuration table.

Keep routers thin: parse/validate in the route handler or small helpers, delegate
persistence to `heartbeat_store`, `blob_store`, or the message bus.
