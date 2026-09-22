# fleet_sdk

Python SDK for the **fleet control plane**: SQLAlchemy models that mirror
`fleet_manager.proto`, synchronous gRPC client wrappers, and the async
Postgres registry used by `fleet_server`.

## Purpose

`fleet_server` implements the `FleetManager` gRPC service. Callers inside the
monorepo need three things without duplicating schema knowledge:

1. **Durable rows** — agents, goals, plans, tasks, executions, metrics
2. **Proto interchange** — convert ORM ↔ `fleet_manager_pb2` messages
3. **Client access** — sync `FleetManagerClient` for Gateway bridge and scripts

This package is the fleet gRPC **control plane** library. It does not serve HTTP
to browsers; see `client_sdk` for that.

## Package layout

```
fleet_sdk/
├── __init__.py          ← package docstring; minimal re-exports
├── README.md            ← you are here
└── src/
    ├── README.md        ← module-level detail
    ├── models.py        ← ORM + *_model_to_proto / *_proto_to_model
    ├── grpc_client.py   ← FleetManagerClient (sync stub wrapper)
    └── instance_registry.py ← AgentInstanceRegistry (async CRUD)
```

Generated stubs live in `packages/proto/`, not under `fleet_sdk/`.

## Control-plane flow

```
Operator / Gateway bridge
        │
        ▼
FleetManagerClient (grpc_client.py)
        │  insecure channel → GRPC_SERVER_ADDRESS
        ▼
fleet_server FleetManager servicer
        │
        ▼
AgentInstanceRegistry (instance_registry.py)
        │  async SQLAlchemy
        ▼
Postgres (AgentModel, PlanModel, TaskModel, …)
        │
        ▼
*_model_to_proto → gRPC response messages
```

Registration example path:

1. Agent process starts; calls `RegisterAgent` (or Gateway POST
   `/api/agents/register` which forwards to gRPC).
2. Servicer writes `AgentModel` with JSON columns for nested proto messages
   (`TaskServerInfo`, `ContainerInfo`, …).
3. `ListAgents` / `GetAgent` read rows and convert via `agent_model_to_proto`.

Planning and execution:

- `CreatePlan` / `AllocatePlan` / `StartPlan` mutate `PlanModel` and related
  `TaskModel` rows; planners live under `fleet_server` but persist through
  registry methods.
- Heartbeat scanners and metric writers call registry helpers; optional
  `packages.metrics.track_operation` wraps long operations.

## Module responsibilities

| Module | Sync/async | Primary consumers |
|--------|------------|-------------------|
| `models.py` | N/A (types) | Registry, servicer, tests |
| `grpc_client.py` | Sync gRPC | Gateway bridge, CLIs |
| `instance_registry.py` | Async DB | `fleet_server` servicer |

`models.py` defines `Base`, table classes, and conversion helpers using
`google.protobuf.json_format` for nested JSON columns. Relationships use
SQLAlchemy `selectinload` where task lists must be eager-loaded before proto
conversion.

`grpc_client.py` exposes one Python method per RPC (`register_agent`,
`create_plan`, `start_plan`, …). No business logic — only request assembly.

`instance_registry.py` is large by design: it owns engine creation, schema
bootstrap, CRUD, heartbeat updates, metric event inserts, and `db_retry`
decorator (retries transient errors, never retries `IntegrityError`).

## Configuration dependencies

Registry and client default to `packages.config`:

- `DATABASE_URL` — async SQLAlchemy URL for registry
- `GRPC_SERVER_ADDRESS` — host:port for `FleetManagerClient`

Never duplicate these constants in `fleet_sdk`; import from `packages.config`.

## How Gateway, fleet, and agents use fleet_sdk

| Actor | Usage |
|-------|--------|
| **fleet_server** | Instantiates `AgentInstanceRegistry`; servicer methods delegate to it |
| **Gateway** | Uses `FleetManagerClient` (or async equivalent) to implement REST |
| **Agents** | Do not import `fleet_sdk`; they register via gRPC/HTTP and receive tasks |
| **dashboard-web** | Indirect via Gateway + `client_sdk` only |

Agents appear in the registry as `AgentModel` rows with `task_server_info`
host/port pointing at the agent SDK HTTP server.

## Proto source of truth

All message and RPC names are defined in `packages/proto/fleet_manager.proto`.
When changing the wire contract:

1. Edit `.proto` and regenerate Python stubs.
2. Update ORM columns and converters in `models.py`.
3. Add matching methods to `grpc_client.py` and registry.
4. Update Gateway REST mapping and `client_sdk` if externally visible.

## Related documentation

- `packages/proto/README.md` — RPC and message catalog
- `packages/proto/fleet_manager.proto` — inline field comments
- `fleet_sdk/src/README.md` — per-file API notes
- `packages/README.md` — platform planes overview
- `packages/config.py` — `GRPC_SERVER_*`, `DATABASE_URL`

## Reading order

1. Skim **`fleet_manager.proto`** service block and core messages (`Agent`,
   `Plan`, `Task`, `Goal`).
2. Read **`src/models.py`** table definitions matching those messages.
3. Read **`src/grpc_client.py`** for available RPC wrappers.
4. Search **`src/instance_registry.py`** for the servicer method you are
   implementing (e.g. `create_plan`, `record_heartbeat`).
5. Trace Gateway route → gRPC method → registry method in the Gateway service.

## Testing notes

Unit tests often mock the registry or use in-memory SQLite if configured;
integration tests hit Postgres from `platform.yaml`. Proto round-trip tests
belong next to `models.py` converters to catch JSON column drift.
