# Telemetry `src` package

Python implementation of the telemetry service: FastAPI HTTP surface, optional
gRPC ingestion, in-memory heartbeat state, blob storage, and NATS publishing.
Import the ASGI app as `services.telemetry.src.main:app` or run the module
CLI (`python -m services.telemetry.src`).

## Process architecture

On startup (`app.lifespan`), the service wires four cooperating subsystems in
order:

1. **Health-changed publisher** — `GatewayHealthChangedPublisher` posts JSON
   `HealthChangedEvent` bodies to `GATEWAY_EVENT_URL` (default gateway internal
   events route). Used when ingest or the timeout scanner detects an effective
   reachability change.
2. **Timeout scanner** — asyncio task sleeping `HEARTBEAT_SCANNER_INTERVAL_SECS`,
   calling `HeartbeatStore.check_timeouts()` and publishing when agents go stale
   relative to `HEARTBEAT_REACHABLE_THRESHOLD_SECS`.
3. **Message bus** — `NatsJetStreamBus.connect()` and `ensure_stream("TELEMETRY", ["telemetry.>"])`.
   Failures are logged as warnings; HTTP heartbeats continue without JetStream.
4. **gRPC server** — `start_grpc_server(bus, TELEMETRY_GRPC_PORT)` registers
   `TelemetryIngestionServicer` (`StreamTelemetry`, `IngestBatch`).

Shutdown cancels the scanner, stops gRPC with a short grace period, closes NATS,
and closes the httpx client inside the publisher.

`app.state` holds `health_changed_publisher` and `message_bus` for FastAPI
`Depends` helpers in `dependencies.py`.

## Module reference

| Module | Responsibility |
|--------|----------------|
| `app.py` | FastAPI app, CORS, router mounts, `/healthz`, lifespan |
| `main.py` | Re-exports `app` for uvicorn |
| `__main__.py` | CLI entry: host/port flags → uvicorn |
| `config.py` | Re-exports shared `packages.config` constants (ports, NATS, CORS, thresholds) |
| `dependencies.py` | `get_publisher()` reads `app.state.health_changed_publisher` |
| `heartbeat_store.py` | Thread-safe singleton ring buffers; effective reachable; host:port index |
| `events.py` | `HealthChangedEvent` model + `HealthChangedPublisher` protocol |
| `publishing.py` | `GatewayHealthChangedPublisher` (httpx POST, non-fatal errors) |
| `validation.py` | Shared protobuf validation for HTTP and gRPC ingest |
| `dedup.py` | Process-wide LRU on `event_id` (HTTP + gRPC share one cache) |
| `grpc_server.py` | aio gRPC servicer; same publish subjects as HTTP ingest |
| `blob_store.py` | Local filesystem or S3 backend; singleton via `get_blob_store()` |
| `routers/` | HTTP route modules (see [`routers/README.md`](routers/README.md)) |

## Heartbeat semantics

Identity is always **`host:port`** string keys — there is no separate
`agent_id` field on the heartbeat payload. The store keeps the last
`MAX_HEARTBEATS_PER_AGENT` samples per key and computes **effective reachable**
from both the latest agent-reported `reachable` flag and freshness of `last_seen`.

Ingest coalesces concurrent POSTs: a pending map under `asyncio.Lock` keeps
only the newest payload per key before applying to the store, which reduces
lock contention when agents spam heartbeats.

When `record_heartbeat` detects an effective-reachable transition, the ingest
router publishes to the gateway. The background scanner covers the case where
heartbeats stop entirely.

## Telemetry event ingest (HTTP + gRPC)

Both paths share validation, deduplication, sequence warnings, and publishing:

- Valid events receive `ingest_time_ns = time.time_ns()` server-side.
- Publish subject: `telemetry.{modality}.{agent_id}` where modality is one of
  `state`, `action`, `vision`, `event`.
- Payload on the wire is **serialized protobuf** (`TelemetryEvent`), not JSON.

HTTP ingest accepts flexible JSON (list, `{events: [...]}`, or single object)
and returns aggregate accept/reject counts. gRPC exposes streaming for
high-volume agent producers.

Downstream **storage_writer** only persists rows when `tags["persist"] == "true"`;
telemetry does not filter on that tag — it publishes everything accepted.

## Blob storage

Vision frames are too large for JetStream payloads. Agents upload bytes via
`POST /telemetry/blob`, receive a `uri`, and reference that URI inside
`VisionPayload` on subsequent telemetry events. The gateway later reads blobs
from the same backend root or S3 bucket configured via `BLOB_STORAGE_*` env vars.

## Relationship to the gateway

Telemetry is **not** a user-facing API. The gateway:

- Proxies health queries to this service’s `/health/*` routes.
- Receives `telemetry.health_changed` pushes for WebSocket invalidation.
- May subscribe to the same NATS subjects for live charts.

Agents should be configured with `TELEMETRY_URL` and gRPC target pointing here,
not at the gateway, so ingest load and heartbeat state stay isolated from REST
traffic.

## Running and testing

```bash
# From  with editable install
python -m services.telemetry.src --port 9000

# Uvicorn reload during router work
cd services/telemetry && uvicorn src.main:app --reload --port 9000
```

Integration tests under `tests/` exercise heartbeat and ingest
behaviour against in-process or containerized NATS where applicable. When
developing routers, prefer hitting `/healthz` for liveness — it intentionally
does not touch NATS or the heartbeat store.

## Package boundaries

- **In scope here**: ingest validation, ephemeral health state, bus publish, blob write.
- **Out of scope**: fleet planning, Parquet durability (storage_writer), dashboard auth,
  long-term agent registration (fleet-server + gateway).

Keep new HTTP routes in `routers/` as separate `APIRouter` modules and mount
them from `app.py` so OpenAPI tags stay grouped by concern.
