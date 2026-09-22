# proto

gRPC and Protocol Buffers **wire contracts** for the agent fleet platform.
Source `.proto` files are authoritative; generated `*_pb2.py` and
`*_pb2_grpc.py` stubs must not be hand-edited.

## Purpose

Two services span the control and observability planes:

| Proto file | Service / package | Role |
|------------|-------------------|------|
| `fleet_manager.proto` | `agent_fleet.FleetManager` | Agents, goals, plans, tasks, execution |
| `telemetry.proto` | `agent_fleet.telemetry.TelemetryIngestion` | Agent telemetry envelopes and ingest |

Python generated modules live beside the sources under `packages/proto/` and are
imported as `from packages.proto import fleet_manager_pb2`, etc.

## File inventory

| File | Kind | Notes |
|------|------|-------|
| `fleet_manager.proto` | Source | RPC + message definitions with block comments |
| `telemetry.proto` | Source | Event envelope, modalities, ordering contract |
| `fleet_manager_pb2.py` | Generated | Message classes |
| `fleet_manager_pb2_grpc.py` | Generated | `FleetManagerStub` / servicer base |
| `telemetry_pb2.py` | Generated | Telemetry messages |
| `telemetry_pb2_grpc.py` | Generated | Ingest stub / servicer |
| `__init__.py` | Hand-written | Package marker |

Regenerate after `.proto` edits using the repo’s protobuf toolchain (see
monorepo README or Makefile target if present).

## FleetManager control plane (`fleet_manager.proto`)

**Consumers:** `fleet_server` servicer, `fleet_sdk` ORM converters and
`FleetManagerClient`, Gateway gRPC bridge.

Core RPC groups:

- **Agent lifecycle** — `RegisterAgent`, `UnregisterAgent`, `DeployAgent`,
  `UndeployAgent`, `ListAgents`, `GetAgent`, `GetAgentStatus`
- **Planning** — `CreatePlan`, `GetPlan`, `ListPlans`, `DeletePlan`,
  `AllocatePlan`, `StartPlan`
- **Tasks & goals** — CRUD + list filters on plan/goal/agent ids

Important nested messages:

- `TaskServerInfo` — host/port for agent SDK HTTP task server
- `DeploymentInfo` / `ContainerConfig` — Docker deploy hints
- `PlanningStrategy` / `AllocationStrategy` enums — planner/allocator plugins
- `Plan`, `Task`, `Goal` — primary persisted aggregates

JSON columns in `fleet_sdk/src/models.py` store nested proto fragments via
`MessageToDict` / `ParseDict`.

### Control-plane flow (conceptual)

```
Client (Gateway / CLI)
    │  FleetManagerStub.*
    ▼
fleet_server gRPC servicer
    │  fleet_manager_pb2 requests/responses
    ▼
AgentInstanceRegistry + Postgres
    │  agent_model_to_proto / …
    ▼
Response Plan/Task/Agent messages on wire
```

## Telemetry ingest (`telemetry.proto`)

**Producers:** agent processes via `agent_sdk` telemetry publisher (gRPC or
HTTP paths depending on deployment).

**Consumers:** telemetry service, Parquet partitioners, dashboard viewers
(often via Gateway + `client_sdk` TypeScript helpers, not raw gRPC in browser).

### Ordering contract (critical)

Events within a task episode sort by:

1. **`step_index`** — primary alignment key; one control tick per index
2. **`sequence_id`** — per (agent, task, modality, stream_name) dedup/gap detect

Consumers reconstruct trajectories with `ORDER BY step_index, sequence_id`.

### Stream name stability

`stream_name` (e.g. `joint_states`, `front_camera`) must stay stable per
`agent_type` — renaming breaks Parquet bindings and dashboard panels.

### Envelope

`TelemetryEvent` carries identity (`event_id`, `agent_id`, `task_id`, …),
timestamps (`event_time_ns`, `ingest_time_ns`), modality metadata, and typed
payload oneofs (vision, scalar series, text, …). See proto for full variant list.

## Generated code policy

- Do **not** add line comments inside `*_pb2.py` — breaks descriptor integrity.
- Document field semantics in `.proto` comments or this README.
- Servicer implementations belong in services (`fleet_server`, telemetry), not
  in `proto/`.

## How Gateway, fleet, and agents use proto

| Actor | Proto usage |
|-------|-------------|
| **fleet_server** | Implements `FleetManager`; imports `fleet_manager_pb2_grpc` |
| **Gateway** | Translates REST ↔ gRPC messages via `fleet_sdk` |
| **Agents** | Publish `TelemetryEvent`; register agents through fleet API (proto-shaped) |
| **client_sdk** | No generated stubs — JSON only at Gateway edge |
| **fleet_sdk** | Primary Python consumer of `fleet_manager_pb2` |

## Related documentation

- `packages/fleet_sdk/README.md` — ORM mapping and client wrappers
- `packages/config.py` — `GRPC_SERVER_ADDRESS`, `TELEMETRY_GRPC_PORT`
- `packages/agent_sdk/src/telemetry/` — publisher implementation
- `packages/client_sdk/…/telemetryClient.ts` — browser-side viewing

## Reading order

1. Read **`fleet_manager.proto`** service and `Agent` / `Plan` / `Task` messages.
2. Skim **`fleet_sdk/src/models.py`** for table ↔ message correspondence.
3. Read **`telemetry.proto`** ordering section and `TelemetryEvent` fields.
4. Open generated **`fleet_manager_pb2_grpc.py`** only to find stub method names.
5. Trace one RPC end-to-end in `fleet_server` servicer source.

## Versioning and compatibility

- Prefer additive proto changes (new fields, new RPCs) with default values.
- Breaking renames require coordinated deploy of server, agents, and SDKs.
- Gateway REST DTOs may lag proto — track both when shipping features.
