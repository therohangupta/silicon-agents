# message_bus

Swappable **pub/sub abstraction** for the agent fleet platform. The default
implementation is NATS JetStream (`NatsJetStreamBus` in `nats_jetstream.py`).

## Purpose

Telemetry publishers, memory-plane NATS placements, and future event projections
need durable publish/subscribe with replay, durable consumer names, and optional
queue groups — without locking call sites to a specific broker API.

This package defines:

- **`Message`** — subject, bytes payload, headers, optional stream sequence
- **`Subscription`** — `next_msg`, `ack`, `unsubscribe`
- **`MessageBus`** — connect, publish, subscribe, `ensure_stream`, close

Implementations must support deliver policies (`all`, `new`, `last`) and
idempotent stream creation.

## File inventory

| File | Role |
|------|------|
| `__init__.py` | ABCs, `Message` dataclass, interface documentation |
| `nats_jetstream.py` | `NatsJetStreamBus`, `_NatsSubscription` adapter |
| `README.md` | you are here |

Dependency: **`nats-py`** (`pip install nats-py`). Not all dev installs include
it until a service needs JetStream.

## NATS implementation highlights

`NatsJetStreamBus`:

- **`connect()`** — `nats.connect(url)` then `jetstream()` context
- **`publish(subject, data, headers=…, stream=…)`** — optional stream pin
- **`subscribe(...)`** — durable consumer; uses **pull** subscribe when
  `queue_group` set (load-balanced workers), else **push** subscribe
- **`ensure_stream(name, subjects, max_age, storage, replicas)`** — create or
  update LIMITS retention stream
- **`close()`** — drain connection

`_NatsSubscription.next_msg` maps NATS messages to `Message` and binds
`_ack_func` for explicit ack after processing.

Default URL comes from callers; typically `packages.config.NATS_URL` or
`MEMORY_NATS_URL` for memory-specific subjects.

## Typical flows

### Telemetry event fan-out

```
Agent telemetry publisher (agent_sdk)
        │  encode TelemetryEvent bytes
        ▼
MessageBus.publish("telemetry.agent.{id}", data)
        │
        ▼
JetStream stream (subjects telemetry.>)
        │
        ▼
Consumer worker(s) with queue_group → ingest / Parquet / dashboard projection
```

### Memory plane NATS copy

```
MemoryPlane.apply_copies → Placement.NATS
        │  JSON envelope notification
        ▼
publish on memory.> (or configured subject prefix)
        │
        ▼
Downstream indexer or audit projector (pull consumer, deliver_policy=new)
```

### Stream bootstrap at service startup

```
Service main()
    bus = NatsJetStreamBus(NATS_URL)
    await bus.connect()
    await bus.ensure_stream("TELEMETRY", ["telemetry.>"], max_age=7d)
    sub = await bus.subscribe("telemetry.>", "ingest-worker", queue_group="ingest")
```

## Interface vs implementation

Callers depend only on `MessageBus` methods. Tests may inject an in-memory fake
that records publishes without NATS. Production Compose stacks start NATS with
ports from `config/platform.yaml` (`nats.published_client_port` on host).

## How Gateway, fleet, and agents use message_bus

| Component | Usage |
|-----------|--------|
| **Agents** | Indirect — telemetry publisher may use bus configured via env; memory NATS copy from `MemoryPlane` |
| **fleet_server** | Typically Postgres-centric; may consume metrics events from DB rather than NATS directly |
| **Gateway** | Usually does not subscribe to JetStream; realtime WS uses internal events |
| **Telemetry service** | Likely subscriber and/or secondary publisher for derived topics |

Search the monorepo for `NatsJetStreamBus`, `MessageBus`, and `ensure_stream`
to find live wiring.

## Operational notes

- **Ack policy:** queue-group pull consumers use explicit ack; call
  `await sub.ack(msg)` after successful handling.
- **Timeouts:** `next_msg(timeout=5.0)` returns `None` on idle — loop accordingly.
- **Wildcards:** NATS subject filters like `telemetry.>` are valid in subscribe.
- **Replacements:** Kafka or Redis Streams would implement the same ABCs in a new
  module without changing telemetry/memory call sites.

## Related documentation

- `packages/config.py` — `NATS_URL`, `MEMORY_NATS_URL`
- `packages/memory/stores/plane.py` — NATS placement writer
- `packages/proto/telemetry.proto` — payload schema on the wire (often JSON or
  protobuf bytes depending on publisher)
- `packages/agent_sdk/src/telemetry/` — agent-side publish path

## Reading order

1. Read **`__init__.py`** — contract for `MessageBus` / `Subscription`.
2. Read **`nats_jetstream.py`** — deliver policy maps and pull vs push.
3. Grep services for `NatsJetStreamBus` to see stream names and subjects.
4. Cross-check **`config/platform.yaml`** NATS ports for local debugging with
   `nats` CLI.

## Debugging checklist

- Connection refused → wrong `NATS_URL` or NATS container not up.
- No messages → consumer `deliver_policy=new` after stream already had traffic;
  use `all` for replay tests.
- Slow consumers → increase pull batch or add queue group workers.
- Stream missing → call `ensure_stream` before first publish on new subjects.
