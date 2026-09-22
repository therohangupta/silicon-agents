# Storage writer `src` package

Async Python package that connects to NATS JetStream, consumes telemetry
protobuf messages, and writes Snappy Parquet with manifest sidecars. Entry:
`python -m services.storage_writer.src.main` (also `services.storage_writer.src.__main__`).

## Control flow

`main.py` orchestrates the process lifetime:

1. Parse optional `--nats-url` (defaults to `packages.config.NATS_URL`).
2. `asyncio.run(_run(url))`:
   - Construct `NatsJetStreamBus`, `connect()`, `ensure_stream("TELEMETRY", ["telemetry.>"])`.
   - Start `run_storage_writer(bus)` and `run_compaction_loop(PARQUET_STORAGE_ROOT)` as tasks.
   - Register SIGINT/SIGTERM handlers that set an `asyncio.Event`.
   - On stop: cancel both tasks, await cancellation, `bus.close()`.

There is no HTTP server or health endpoint — liveness is “process running and
consuming” as seen in container logs (`Storage writer started — consuming …`).

## `worker.py` — pull consumer

`run_storage_writer(bus)` is the hot loop:

- Instantiates `ParquetSink(root=PARQUET_STORAGE_ROOT)`.
- `bus.subscribe(...)` with durable + queue group `storage-writers`.
- `next_msg(timeout=FETCH_TIMEOUT)` where `FETCH_TIMEOUT = 1.0` seconds.
- On timeout with no message: if `sink.should_flush()`, flush and update manifests.
- On message: `TelemetryEvent.ParseFromString`, **ack**, skip unless
  `event.tags.get("persist") == "true"`, else `sink.ingest(event)`.
- After ingest: flush when thresholds met.
- On `CancelledError`: final `flush_all()`, manifest updates for `done` partitions,
  `unsubscribe()`.

The ack-before-process choice means a crash after ack but before durable write
could lose a row — acceptable for at-least-once telemetry; producers should
use idempotent `event_id` semantics upstream.

## `parquet_sink.py` — buffering and write

`ParquetSink` owns four modality buffers (`state`, `action`, `vision`, `event`).
`ingest(event)` expands protobuf oneofs into flat dict rows matching Arrow schemas
defined at module level (`STATE_SCHEMA`, `ACTION_SCHEMA`, etc.).

`flush_all()`:

- Writes each non-empty buffer to a new `part-{unix_ts}_{uuid}.parquet` under the
  computed partition path.
- Clears buffers and resets flush timers.
- Returns partition directories that contained at least one row with `done=true`.

Snappy compression is used via PyArrow defaults for CPU/density balance on
time-series workloads.

## `manifest.py` — partition catalog

Functions:

- `build_manifest(partition_dir, episode_complete=...)` — scan `*.parquet` footers,
  aggregate row counts and step ranges.
- `write_manifest(partition_dir, episode_complete=...)` — merge with existing JSON,
  stamp `updated_at` UTC ISO8601, atomic replace.

Corrupt manifests are rebuilt with a warning log — operators can delete
`_manifest.json` to force a footer rescan.

## `compactor.py` — background merge

`run_compaction_loop(root, interval=COMPACTION_INTERVAL_SECS)` sleeps in a loop
until cancelled, walking the tree for partition directories.

`_compact_partition(dir)`:

- Ignores dirs with ≤1 Parquet file.
- Reads all parts, `pa.concat_tables`, optional sort on `(step_index, sequence_id)`.
- Writes `compacted-{ts}_{uuid}.parquet`, deletes superseded parts.
- Calls `write_manifest` with `episode_complete` inferred from any `done` column.

Constants: `TARGET_FILE_BYTES = 128 * 1024 * 1024`, default interval 300 s.

## Dependencies

| Package / module | Usage |
|------------------|--------|
| `packages.message_bus.nats_jetstream.NatsJetStreamBus` | Connect, stream ensure, pull subscribe |
| `packages.proto.telemetry_pb2.TelemetryEvent` | Wire format |
| `packages.config` | `NATS_URL`, `PARQUET_STORAGE_ROOT` |
| `pyarrow` | Tables, Parquet IO, footer metadata |

## Extension points

**New modality:** Add schema + branch in `ParquetSink.ingest` and ensure
telemetry publishes the matching protobuf `Modality` enum (subject segment must
stay consistent with `telemetry.{name}.{agent_id}`).

**Alternate sinks:** The worker is intentionally narrow — swap `ParquetSink` for
another backend by keeping the same subscribe/ack/filter contract.

**Metrics:** Hook flush durations and lag (sequence vs consumer ack) inside
`_flush_and_update_manifests` or around `next_msg` without changing NATS
consumer names (changing durable identity resets delivery cursor).

## Testing locally

Run platform NATS (`docker compose up nats -d`), then:

```bash
export NATS_URL=nats://localhost:4222
export PARQUET_STORAGE_ROOT=/tmp/parquet-test
python -m services.storage_writer.src.main
```

Publish test events through telemetry HTTP/gRPC with `tags: {"persist": "true"}`
and inspect output under the root. Without the persist tag, messages should vanish
from the bus with no new files.

## Boundaries

This package does **not** validate events (telemetry already did), serve blobs,
or push WebSocket updates. It assumes JetStream retention and telemetry stream
configuration match production (`TELEMETRY` stream, `telemetry.>` subjects).
