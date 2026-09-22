# packages/

Shared first-party libraries for the **agent_fleet** monorepo. Every Python
service, agent container, and dashboard build imports configuration, wire
contracts, SDKs, memory, and messaging from this tree once `agent_fleet` is on
`PYTHONPATH`.

This directory is **not** application code. It is the cross-cutting platform
layer that keeps ports, protos, and client contracts identical across
`fleet_server`, the Gateway BFF, telemetry ingest, agent task servers, and
`dashboard-web`.

## Purpose

| Concern | Where it lives | Who consumes it |
|---------|----------------|-----------------|
| Hosts, ports, DSNs, memory backends | `config.py`, `platform_config.py` | All services at import time |
| Async operation timing metrics | `metrics.py` | `fleet_server`, Gateway |
| gRPC wire schema | `proto/` | `fleet_server`, `fleet_sdk`, telemetry |
| Fleet ORM + gRPC client + registry | `fleet_sdk/` | `fleet_server`, Gateway gRPC bridge |
| Per-agent HTTP server / runtime | `agent_sdk/` | Agent Docker images (documented separately) |
| Silicon memory plane | `memory/` | Domain `EngineeringMemory`, agents |
| Durable pub/sub | `message_bus/` | Telemetry projection, memory NATS copies |
| Gateway HTTP/WebSocket clients | `client_sdk/` | Dashboard, CLIs, scripts |

Authoritative platform numbers live in `agent_fleet/config/platform.yaml`.
`packages.platform_config` loads and validates that file; `packages.config`
re-exports typed constants (`GATEWAY_URL`, `NATS_URL`, `MEMORY_*`, …) with
environment overrides for Compose and local dev.

## Top-level file inventory

| File | Role |
|------|------|
| `__init__.py` | Package marker; documents import paths (`from packages.config import …`) |
| `config.py` | Single source of truth for service URLs, DB, heartbeat tuning, memory-plane URLs |
| `platform_config.py` | YAML loader, host/Compose/agent env builders, Compose template renderer |
| `metrics.py` | `track_operation` async context manager for fire-and-forget latency metrics |

Subpackages each have their own README with module-level inventories.

## Architecture planes

The monorepo is organized around a few durable **planes**. They intersect in
`packages/` but deploy as separate processes:

```
  dashboard-web / CLI
        │  HTTP + WS (client_sdk)
        ▼
   Gateway BFF ──gRPC──► fleet_server (fleet_sdk + proto)
        │                      │
        │                      ├──► Postgres (registry ORM)
        │                      └──► agent HTTP task servers (agent_sdk)
        │
        ├──► telemetry HTTP/gRPC (proto/telemetry.proto)
        │
        └──► WebSocket invalidate / tasks_update

  agents ──gRPC/HTTP──► telemetry ingest
       ──writes──► memory plane (memory/ + config MEMORY_*)
       ──publish──► NATS (message_bus/)
```

### Configuration plane

`config.py` + `platform_config.py`. No service should hard-code a port. Grep
`PORT` or `URL` in `config.py` when wiring a new binary.

### Memory plane

`memory/` implements write policy, context assembly, and store adapters.
Agents and domain services call `assemble_copies` / `MemoryPlane.apply_copies`;
stores treat `scope_segments` as opaque. See `memory/README.md`.

### Fleet gRPC control plane

`proto/fleet_manager.proto` defines `FleetManager` RPCs. `fleet_sdk` maps
those messages to SQLAlchemy rows and exposes `FleetManagerClient` for sync
callers (Gateway bridge, scripts).

### Telemetry plane

`proto/telemetry.proto` defines `TelemetryEvent` ordering (`step_index`,
`sequence_id`) and the `TelemetryIngestion` service. Agent publishers live
under `agent_sdk/src/telemetry/`; browser viewers use `client_sdk` realtime
helpers.

### Client SDK plane

`client_sdk/` is the **only** supported surface for external UIs and scripts
talking to the Gateway. It does not speak gRPC to `fleet_server` directly.

### Message bus plane

`message_bus/` abstracts JetStream (default: `NatsJetStreamBus`) so telemetry
and memory event writers stay transport-agnostic.

## How major components use this tree

### Gateway (BFF)

- Imports `packages.config` for upstream URLs and CORS.
- Uses `fleet_sdk.src.grpc_client.FleetManagerClient` (or an async bridge) for
  control-plane mutations exposed as REST.
- Pushes realtime events that match `client_sdk/contract/events.schema.json`.
- May call `packages.metrics.track_operation` when recording BFF latency.

### fleet_server

- Owns the `FleetManager` gRPC servicer; persists via
  `fleet_sdk.src.instance_registry.AgentInstanceRegistry`.
- ORM models and proto converters in `fleet_sdk/src/models.py`.
- Reads `DATABASE_URL`, heartbeat thresholds, planner paths from `config.py`.

### Agents (task servers)

- Built on `agent_sdk` (server, runtime, skills) — see `agent_sdk/README.md`.
- Environment injected from `platform_config.agent_environment()` includes
  `MEMORY_*`, `NATS_URL`, `TELEMETRY_*` from the same YAML as `config.py`.
- Memory writes go through domain code into `packages.memory`; telemetry uses
  generated stubs from `packages/proto`.

### dashboard-web

- Depends on `@agent-fleet/client-sdk` (`client_sdk/typescript`) via `file:`.
- Never imports Python packages; contract alignment is TS types + JSON Schema.

## Subpackage index

| Path | README | Start here if… |
|------|--------|----------------|
| `proto/` | `proto/README.md` | Changing RPCs or event fields |
| `fleet_sdk/` | `fleet_sdk/README.md` | Registry, gRPC client, ORM |
| `memory/` | `memory/README.md` | Writes, context assembly, stores |
| `message_bus/` | `message_bus/README.md` | NATS subjects, consumers |
| `client_sdk/` | `client_sdk/README.md` | REST/WS client features |
| `agent_sdk/` | `agent_sdk/README.md` | Agent server/runtime (other task) |

## Related documentation

- `agent_fleet/config/platform.yaml` — authored ports and infrastructure map
- `agent_fleet/README.md` — monorepo-wide startup and Compose
- `services/fleet_server/` — FleetManager servicer implementation
- `services/gateway/` — REST + WebSocket BFF (names may vary; search for Gateway)
- `etched_agentic_chip_design_system_v3.md` — memory-plane physical storage table

## Recommended reading order

1. **`config.py`** (skim assignments) and **`config/platform.yaml`** (structure).
2. **`proto/README.md`** then skim `fleet_manager.proto` / `telemetry.proto`.
3. **`fleet_sdk/README.md`** — how RPCs become Postgres rows.
4. **`client_sdk/README.md`** — external API surface for UIs.
5. **`memory/README.md`** — if you touch agent memory or EngineeringMemory.
6. **`message_bus/README.md`** — if you add consumers or new subjects.
7. **`agent_sdk/`** — when implementing or debugging an agent container.

## Conventions

- Import as `from packages.<module> import …` with repo root `agent_fleet` on
  `PYTHONPATH` (Compose and local scripts set this consistently).
- Do not hand-edit `*_pb2.py` / `*_pb2_grpc.py`; regenerate from `.proto`.
- JSON under `client_sdk/contract/` has no inline comments — document in
  adjacent READMEs.
- `agent_sdk/` documentation is maintained by a separate task; this root README
  only indexes it.
