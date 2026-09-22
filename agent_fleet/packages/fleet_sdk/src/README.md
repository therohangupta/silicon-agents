# fleet_sdk/src/

Implementation modules for the fleet control-plane SDK. Wire schema source of
truth: **`packages/proto/fleet_manager.proto`**. Generated stubs:
**`packages/proto/fleet_manager_pb2*.py`**.

## Purpose

This directory holds the three pillars used by `fleet_server` and sync clients:

1. **Persistence shape** — SQLAlchemy models matching proto messages
2. **Wire client** — thin `FleetManagerClient` over gRPC
3. **Runtime registry** — async Postgres façade with retries and metrics hooks

Import paths used in the monorepo:

```python
from packages.fleet_sdk.src.models import AgentModel, agent_model_to_proto
from packages.fleet_sdk.src.grpc_client import FleetManagerClient
from packages.fleet_sdk.src.instance_registry import AgentInstanceRegistry
```

## File inventory

| File | Approx. responsibility |
|------|-------------------------|
| `models.py` | `Base`, `AgentModel`, `GoalModel`, `PlanModel`, `TaskModel`, `TaskExecutionModel`, `MetricEvent`; proto ↔ ORM converters |
| `grpc_client.py` | Sync `FleetManagerClient` — one method per RPC |
| `instance_registry.py` | `AgentInstanceRegistry` — async CRUD, heartbeats, plan execution state |
| `__init__.py` | Submodule marker |
| `README.md` | you are here |

## models.py — ORM and converters

Tables mirror `fleet_manager_pb2` messages. Nested proto structures
(`TaskServerInfo`, `ContainerInfo`, `DeploymentInfo`) serialize to **JSON
columns** so the relational schema stays flat.

Converter naming convention:

- `agent_model_to_proto(model) -> fleet_manager_pb2.Agent`
- `agent_proto_to_model(msg) -> AgentModel` (where applicable)
- Same pattern for `task`, `plan`, `goal`

**Eager loading:** converters that populate repeated fields (e.g. task ids on
plans) require `selectinload` on relationships before conversion — documented in
module docstring.

Enums (`AgentStatus`, planning/allocation strategies) store as integers compatible
with proto enum numeric values.

## grpc_client.py — FleetManagerClient

- Opens **`grpc.insecure_channel(server_address)`** defaulting to
  `packages.config.GRPC_SERVER_ADDRESS`
- Binds **`FleetManagerStub`**
- Context manager **`with FleetManagerClient() as c:`** ensures channel close

Each public method builds the request message type from `fleet_manager_pb2` and
returns the response object (or nested messages like `Agent`). No retry logic —
callers handle `grpc.RpcError`.

Methods cover the full service surface: agent registration and deploy,
plan CRUD, task CRUD, goal CRUD, `start_plan`, `allocate_plan`, etc. Grep the
class for the authoritative list when adding Gateway routes.

## instance_registry.py — AgentInstanceRegistry

The durable heart of `fleet_server`:

- Creates async engine / session factory from `DATABASE_URL`
- **`create_tables`** / schema bootstrap on startup
- Agent registration, heartbeat recording, stale agent scanning support data
- Plan creation, allocation artifacts, execution status transitions
- Task assignment, dependency updates, deletion cascades
- **`record_metric`** integration for `packages.metrics.track_operation`

**`db_retry` decorator:** retries generic exceptions up to N times with delay;
**never** retries `IntegrityError` (permanent constraint violations).

Return types are **`fleet_manager_pb2` messages** — servicer layer stays proto-
native while storage stays ORM-native.

Logging: `configure_registry_logging(verbose=True)` for debug SQL-adjacent traces;
SQLAlchemy loggers default to ERROR to reduce noise.

## Data flow through src modules

```
gRPC request bytes
    ▼
Servicer parses fleet_manager_pb2 message
    ▼
Registry method (async) loads/updates ORM via session
    ▼
models.*_model_to_proto(row) → response message
```

Gateway sync path:

```
REST handler
    ▼
FleetManagerClient.register_agent(...)  [grpc_client.py]
    ▼
Same servicer + registry as above
```

## How Gateway, fleet, and agents relate

| Module | fleet_server | Gateway | Agents |
|--------|--------------|---------|--------|
| `models.py` | Direct | Indirect via gRPC responses | No |
| `grpc_client.py` | Rarely | Bridge / scripts | No |
| `instance_registry.py` | Direct | No | Heartbeats/tasks via server |

Agents never import this directory; they expose HTTP task servers referenced in
`AgentModel.task_server_info`.

## Related documentation

- `../README.md` — fleet_sdk package overview
- `../../proto/fleet_manager.proto` — RPC and field reference
- `../../proto/README.md` — wire contract maintenance
- `../../config.py` — connection defaults

## Reading order

1. **`models.py`** — table columns for the entity you are changing.
2. **`instance_registry.py`** — search async method name matching servicer RPC.
3. **`grpc_client.py`** — mirror new RPCs for operator scripts.
4. Servicer in **`services/fleet_server`** — glue between gRPC and registry.

## Extension checklist (new RPC)

1. Add RPC + messages to `fleet_manager.proto`; regenerate stubs.
2. Add/alter ORM models and converters in `models.py`.
3. Implement registry method with transactions and proto return type.
4. Wire servicer method to registry.
5. Add `FleetManagerClient` wrapper method.
6. Expose Gateway REST + `client_sdk` if user-facing.
