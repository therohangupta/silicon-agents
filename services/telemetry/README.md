# Telemetry Service

Minimal telemetry server for heartbeat ingest, derived health, batch/stream
telemetry ingest, and vision blob upload. **Agent task servers** are the primary
writers; the **gateway** reads health and receives push notifications but does
not replace this service for ingest. NATS JetStream fans out validated events to
the storage_writer (durable Parquet) and optionally to the gateway (live UI).

## Telemetry vs gateway (quick reference)

| | Telemetry (this service) | Gateway |
|---|--------------------------|---------|
| Port (typical) | 9000 HTTP, 9001 gRPC | 8000 HTTP/WS |
| Writes heartbeats | Yes — in-memory store | No — proxies `GET /health/*` here |
| Publishes `telemetry.>` | Yes — after validate/dedupe | May subscribe for WebSocket fan-out |
| Fleet plans / tasks | No | Yes — gRPC to fleet-server |
| Blob upload | Yes — `POST /telemetry/blob` | Read/serve for dashboard |
| Health push to UI | POST `telemetry.health_changed` → gateway | Dispatches to WebSocket clients |

Configure agents with `TELEMETRY_URL` / gRPC target pointing **here**, not at the
gateway.

## Responsibilities

- **Ingest**: Agents POST heartbeats to `POST /ingest/heartbeat` (identity is
  `host:port`; latest-wins coalescing under a pending lock).
- **Store**: Keeps last N heartbeats per agent in memory (configurable via
  `MAX_HEARTBEATS_PER_AGENT` / historically `MAX_HEARTBEATS_PER_ROBOT`).
- **Health read API**: Gateway queries `GET /health/summary` or
  `GET /health/{agent_id}` for derived health (reachable / busy / last_seen).
- **Event push**: When effective "reachable" changes (on heartbeat or via the
  timeout scanner), sends `telemetry.health_changed` to the gateway so the UI
  updates without polling.
- **Telemetry ingest**: HTTP `POST /telemetry/ingest` and gRPC
  `TelemetryIngestion.StreamTelemetry` / `IngestBatch` validate, dedupe,
  stamp `ingest_time_ns`, and publish to NATS subjects
  `telemetry.{modality}.{agent_id}`.
- **Blobs**: `POST /telemetry/blob` stores vision frames (local disk or S3)
  and returns a URI for `VisionPayload.BlobRef`.

## Layout

| Path | Role |
|------|------|
| `src/app.py` | FastAPI app, lifespan (publisher, NATS, gRPC, timeout scanner) |
| `src/main.py` | uvicorn entry (`app` export) |
| `src/__main__.py` | `python -m services.telemetry.src` CLI |
| `src/config.py` | Re-exports shared `packages.config` values |
| `src/heartbeat_store.py` | In-memory ring buffers + effective reachable |
| `src/routers/` | HTTP routes (ingest, health, telemetry, blob) |
| `src/grpc_server.py` | TelemetryIngestion gRPC servicer |
| `src/validation.py` / `dedup.py` | Shared event checks and LRU event_id cache |
| `src/blob_store.py` | Local / S3 blob backend |
| `src/publishing.py` / `events.py` | Health-changed publisher protocol + HTTP impl |

## Running locally (bare metal)

From repo root:

```bash
pip install -e .
python -m services.telemetry.src --port 9000
```

Or with uvicorn directly:

```bash
cd services/telemetry
uvicorn src.main:app --reload --port 9000
```

## Running in Docker

From repo root:

```bash
docker compose up --build
```

The `telemetry` service is defined in `docker-compose.yml`. Build standalone:

```bash
docker build -f services/telemetry/Dockerfile -t telemetry .
```

## Configuration (env vars)

| Variable | Default | Description |
|----------|---------|-------------|
| `GATEWAY_EVENT_URL` | `http://localhost:8000/internal/events` | Where to POST health_changed events |
| `TELEMETRY_PORT` | `9000` | Port for the Telemetry HTTP service |
| `TELEMETRY_GRPC_PORT` | (from `packages.config`) | Port for TelemetryIngestion gRPC |
| `NATS_URL` | (from `packages.config`) | JetStream URL; heartbeat-only mode if unavailable |
| `MAX_HEARTBEATS_PER_AGENT` | `20` | Ring buffer size per agent |
| `HEARTBEAT_REACHABLE_THRESHOLD_SECS` | `45.0` | Seconds since last heartbeat before "unreachable" |
| `HEARTBEAT_SCANNER_INTERVAL_SECS` | (from `packages.config`) | Background timeout scan period |
| `BLOB_STORAGE_BACKEND` / `BLOB_STORAGE_ROOT` | local path | Filesystem blob root |
| `S3_BUCKET` / `S3_REGION` | — | Used when backend is `s3` |
| `CORS_ORIGINS` | (from `packages.config`) | Allowed browser origins |

## API

- `POST /ingest/heartbeat` — agent heartbeat ingest (`host`, `port`, optional `reachable` / `busy` / `ts`)
- `GET /health/summary` — all agents' health (also keyed by `host:port` when known)
- `GET /health/{agent_id}` — single agent's health (404 if never seen)
- `POST /telemetry/ingest` — HTTP batch telemetry ingest (JSON list or `{events: [...]}`)
- `POST /telemetry/blob` — multipart blob upload (`agent_id`, `stream_name`, `file`, optional `task_id`)
- `GET /healthz` — liveness probe
- gRPC `TelemetryIngestion` on `TELEMETRY_GRPC_PORT` — `StreamTelemetry`, `IngestBatch`
