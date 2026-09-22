# Fleet Server Service

Top-level Python package for the **Fleet Manager** gRPC orchestration service: agent registry, goals/tasks/plans CRUD, automated planning and allocation, and background plan execution.

Nested runnable code lives in `src/`; this directory holds packaging (`Dockerfile`, namespace `__init__.py`) and service-level documentation.

## What lives here

| Path | Role |
|------|------|
| `Dockerfile` | Container image: editable install of the workspace, exposes gRPC `:50051` |
| `__init__.py` | Package docstring / namespace marker (`services.fleet_server`) |
| `src/` | Implementation — see `src/README.md` |

## Runtime entrypoints

```bash
# From agent_fleet/ (workspace root on PYTHONPATH)
python -m services.fleet_server.src -v

# Container (build context = agent_fleet/)
docker build -f services/fleet_server/Dockerfile -t fleet-server .
```

Compose stacks under `agent_fleet/` typically wire PostgreSQL, Gateway, and this service together.

## Architecture overview

```text
Clients / CLI / Dashboard
         │ gRPC (FleetManager)
         ▼
   src/service.py  (FleetManagerService)
         │
    ┌────┴────┬────────────┬──────────┐
    ▼         ▼            ▼          ▼
 planners  allocators   executor   events.py
    │         │            │          │
    └────┬────┴────────────┴──────────┘
         ▼
 AgentInstanceRegistry (PostgreSQL)
         │
         ▼
 Agent HTTP task servers (+ optional NATS)
```

1. **gRPC FleetManager** — agents, goals, tasks, plans; `CreatePlan`, `AllocatePlan`, `StartPlan`.
2. **Planners** — Monolithic, DAG, Big DAG (+ Replanner on failure).
3. **Allocators** — LP, LLM, cost_based assign `agent_id`.
4. **Executor** — Kahn scheduling, parallel dispatch, replan/abort.
5. **Events** — fire-and-forget POSTs to Gateway for UI invalidation.

## CreatePlan — when each strategy runs

`CreatePlan` (`src/service.py`) branches on `planning_strategy` and `allocation_strategy` protobuf enums:

| Planning enum | Behavior |
|---------------|----------|
| `MANUAL_PLAN` | Empty plan shell; no LLM; tasks added separately |
| `MONOLITHIC` / `DAG` / `BIG_DAG` | `get_planner(...).plan(goal_ids)` → `save_plan_to_db` |
| (auto + no goals) | `INVALID_ARGUMENT` |

Bypasses:

- **`TESTING` env** — empty plan, skips planner (tests).

After tasks exist:

| Allocation enum | Behavior |
|-----------------|----------|
| `NONE` | Skip allocation; use `AllocatePlan` later |
| `MANUAL_ALLOCATION` | Skip automatic allocator |
| `LP` / `LLM` / `COST_BASED` | `get_allocator(...).allocate(plan_id)` |

Detailed guides: `src/planners/types/*/README.md`, `src/allocators/types/*/README.md`.

## AllocatePlan

Runs **only** allocation on an existing plan with tasks — common when CreatePlan used `NONE`, or when changing strategy after edits. Does not re-run planners.

## StartPlan

Spawns `Executor` in the background if allocation is complete. See `src/executor/README.md`.

## Configuration (service-level)

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | PostgreSQL for registry |
| `OPENAI_API_KEY` | LLM planners and LLM/cost_based allocators |
| `GATEWAY_EVENT_URL` | Dashboard event POST target |
| `TESTING` | Bypass LLM planning in CreatePlan |
| `DURABLE_TASK_DISPATCH` / `NATS_URL` | Optional durable task delivery |

Full table: `src/README.md`.

## Documentation map

| Topic | Path |
|-------|------|
| Source layout & RPC summary | `src/README.md` |
| Plan/DAG schemas | `src/formats/README.md` |
| Planner factory | `src/planners/README.md` |
| Allocator factory | `src/allocators/README.md` |
| Execution loop | `src/executor/README.md` |

## Related workspace packages

- `packages/proto` — `fleet_manager_pb2` enums for strategies
- `packages/fleet_sdk` — `AgentInstanceRegistry`, models
- `packages/agent_sdk` — agent HTTP client and task request models
- `services/gateway` — event consumer for dashboard
