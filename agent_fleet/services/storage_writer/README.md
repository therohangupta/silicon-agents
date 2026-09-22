# Storage Writer Service

Long-running **consumer** that turns NATS JetStream telemetry messages into
partitioned Snappy Parquet on disk (or a mounted volume). It exposes no HTTP
API — operators interact with it through logs, metrics hooks (future), and
the files it writes under `PARQUET_STORAGE_ROOT`.

## Role in the pipeline

Telemetry validates agent events and **publishes** protobuf bytes to subjects
`telemetry.{modality}.{agent_id}` on stream `TELEMETRY` (`telemetry.>` wildcard).
The gateway may **subscribe** to the same stream for live UI updates. Storage
writer is the **durable analytics leg**: it pull-consumes every message, acks
promptly, and only materializes rows when the producer set
`tags["persist"] = "true"`.

Ephemeral or high-volume debug streams can therefore flow through NATS without
filling disk — they are acked and dropped at the worker filter.

```
Agent → telemetry (validate) → NATS telemetry.>
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
              storage-writer    gateway WS     (other consumers)
                    │
                    ▼
         Parquet + _manifest.json
```

## Consumer semantics

Implemented in `src/worker.py`:

| Setting | Value | Rationale |
|---------|-------|-----------|
| Subject | `telemetry.>` | All modalities and agents |
| Durable name | `storage-writers` | Survives writer restarts |
| Queue group | `storage-writers` | Horizontal scale without duplicate writes |
| Deliver policy | `all` | Backfill when writer was down |

Each message is parsed as `TelemetryEvent`, acked, then optionally ingested into
`ParquetSink`. Parse failures are logged; JetStream may redeliver if ack did not
occur.

## Parquet layout

`ParquetSink` (`src/parquet_sink.py`) maintains separate long-format schemas for
modalities `state`, `action`, `vision`, and `event`. Shared envelope columns
include `timestamp_ns`, `agent_id`, `task_id`, `step_index`, `sequence_id`,
`source_id`, `completeness`, `done`, and `sync_group`.

On-disk hierarchy (Hive-style):

```text
{PARQUET_STORAGE_ROOT}/{modality}/agent_id={X}/task_id={Y}/date={Z}/part-{ts}_{uuid}.parquet
```

**Flush policy:** flush when buffered row count across modalities reaches
`FLUSH_ROW_THRESHOLD` (10_000) **or** `FLUSH_TIME_SECS` (60) elapses since the
last flush, whichever comes first. Idle periods still trigger timed flushes via
the pull loop’s `FETCH_TIMEOUT` branch.

When flushed rows include `done=true`, the worker marks the partition’s
`_manifest.json` with `episode_complete=true`.

## Manifest sidecars

`src/manifest.py` writes `{partition_dir}/_manifest.json` using **footer-only**
Parquet reads (row counts, min/max `step_index`, file list). Updates are atomic
(rename from `.json.tmp`). Downstream training or replay tools can discover
partitions without scanning every row group.

## Compaction

`src/compactor.py` runs a background loop (default every 300 seconds) over the
Parquet root. For each partition directory with multiple `part-*.parquet` files,
it concatenates tables, sorts by `(step_index, sequence_id)` when present,
writes `compacted-{ts}_{uuid}.parquet`, deletes old parts, and refreshes the
manifest. Target combined size is about **128 MB** per file to balance object
store efficiency and query parallelism.

Compaction and the pull worker run concurrently under `src/main.py`; both cancel
cleanly on SIGINT/SIGTERM after a final flush.

## Layout

| Path | Role |
|------|------|
| `src/main.py` | CLI, signal handling, bus connect, task supervision |
| `src/worker.py` | Pull loop, ack, persist filter, flush triggers |
| `src/parquet_sink.py` | Modality buffers, schema mapping, partitioned writes |
| `src/manifest.py` | Build/atomic write `_manifest.json` |
| `src/compactor.py` | Periodic merge/sort of small parts |
| `Dockerfile` | Container image for Compose `storage-writer` service |

## Run

```bash
# From agent_fleet/ (editable install)
python -m services.storage_writer.src.main [--nats-url URL]

# Docker
docker build -f services/storage_writer/Dockerfile -t storage-writer .
```

In Compose (`docker-compose.yml`), the service depends on `nats`, shares
`./.data/telemetry:/data` with telemetry and gateway, and sets
`PARQUET_STORAGE_ROOT` / `NATS_URL` from `packages.config`.

## Configuration

| Variable | Purpose |
|----------|---------|
| `NATS_URL` | JetStream connection (overridable via `--nats-url`) |
| `PARQUET_STORAGE_ROOT` | Root directory for modality trees |

`BLOB_STORAGE_ROOT` appears in Compose for mount consistency; blob bytes are
written by telemetry, not this service. Vision Parquet rows store **URIs** only.

## Operations notes

**Scaling:** Run multiple storage-writer containers with the same queue group.
JetStream delivers each message to one consumer instance.

**Disk pressure:** Compaction reduces file count but does not delete old
partitions — lifecycle policies belong in ops tooling.

**Ordering:** Sort keys in compaction aid range reads; global total order across
agents is not guaranteed.

**Failure modes:** If NATS is unavailable, the process fails at startup (unlike
telemetry’s soft-fail). If disk fills, flush logs errors — monitor free space on
the shared telemetry data volume in dev.

## Related reading

- [`../telemetry/README.md`](../telemetry/README.md) — ingest and publish path
- [`../README.md`](../README.md) — telemetry vs gateway vs storage_writer
- [`src/README.md`](src/README.md) — module-level implementation map
