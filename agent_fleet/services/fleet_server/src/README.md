# Fleet Server (`src`)

Core orchestration service for multi-agent **planning**, **allocation**, and **execution**. Exposes gRPC **FleetManager** on port **50051** (default via `__main__.py`).

## Layout

| Module / package | Purpose |
|------------------|---------|
| `__main__.py` | CLI: port, `--reset-db`, `-v`, `--sql-debug`, graceful shutdown |
| `service.py` | `FleetManagerService` servicer + `serve()` |
| `events.py` | Gateway `emit_*` helpers (task/plan/agent changed) |
| `world_state.py` | `ExecutionContext` snapshots for agent task payloads |
| `formats/` | Pydantic Plan / DAG / Allocation schemas |
| `planners/` | Base + monolithic / dag / big_dag / replanner |
| `allocators/` | Base + lp / llm / cost_based |
| `executor/` | DAG scheduler, reliability, optional NATS dispatch |

## End-to-end lifecycle

```text
RegisterAgent / CreateGoal / CreateTask (optional manual tasks)
        │
        ▼
   CreatePlan ──► planner (optional) ──► tasks in DB
        │              │
        │              └── MANUAL / TESTING shortcuts
        ▼
   allocator (if strategy != NONE)
        │
        ▼
   StartPlan ──► Executor (background)
```

Operators can insert **`AllocatePlan`** between create and start when the first CreatePlan used `allocation_strategy=NONE`.

## CreatePlan (detailed)

Implementation: `FleetManagerService.CreatePlan` in `service.py`.

1. Read `planning_strategy`, `allocation_strategy`, `goal_ids`, name/description.
2. **`MANUAL_PLAN`** → `registry.create_plan(..., task_ids=[])`; emit event; return.
3. Auto-plan without goals → gRPC `INVALID_ARGUMENT`.
4. **`TESTING`** truthy → empty plan shell (no LLM).
5. **`get_planner(strategy)`** → `MonolithicPlanner` | `DAGPlanner` | `BigDAGPlanner`.
6. `plan_json = await planner.plan(goal_ids)`.
7. `plan_id = await planner.save_plan_to_db(...)` with prompts/artifacts/logs.
8. If **`allocation_strategy != NONE`**:
   - `get_allocator(strategy)` → LP | LLM | CostBased
   - `await allocator.allocate(plan_id)`
   - `update_plan` with allocation prompts/artifacts/logs
9. Return `get_plan(plan_id)` proto.

**Not in CreatePlan:** `Replanner` (Executor-only).

### Planning strategy picker

| Enum | Class | Pick when |
|------|-------|-----------|
| `MONOLITHIC` | `MonolithicPlanner` | Global sequential ordering |
| `DAG` | `DAGPlanner` | Isolated per-goal DAGs, internal parallelism |
| `BIG_DAG` | `BigDAGPlanner` | Cross-goal dependencies in one graph |
| `MANUAL_PLAN` | — | Human-authored task graph |

See `planners/types/*/README.md`.

### Allocation strategy picker (same RPC)

| Enum | Class | Pick when |
|------|-------|-----------|
| `NONE` | — | Defer to AllocatePlan or manual |
| `MANUAL_ALLOCATION` | — | Per-task UI assignment |
| `LP` | `LPAllocator` | Min-max load, explicit caps/types |
| `LLM` | `LLMAllocator` | One-shot semantic assignment |
| `COST_BASED` | `CostBasedAllocator` | Frontier-aware, switching-cost bias |

See `allocators/types/*/README.md`.

## AllocatePlan (detailed)

1. Load plan by id → `NOT_FOUND` if missing.
2. Require non-empty `task_ids` → else `FAILED_PRECONDITION`.
3. `get_allocator(request.allocation_strategy)`.
4. `allocate(plan_id)` mutates task rows.
5. Update plan metadata (strategy, prompts, artifacts).
6. Return refreshed plan proto.

Does **not** change `planning_strategy` or regenerate tasks.

## StartPlan

- Verifies **full allocation** (every task has `agent_id`).
- Spawns `Executor.execute()` asyncio task.
- Replanner may replace `plan_id` mid-run on configured failures.

## gRPC surface (selected)

- **Agents:** `RegisterAgent`, `UnregisterAgent`, `ListAgents`, `GetAgent`, `GetAgentStatus`
- **Goals / Tasks / Plans:** CRUD helpers used by CLI and dashboard
- **Plans:** `CreatePlan`, `AllocatePlan`, `GetPlan`, `ListPlans`, `StartPlan`, …

Deploy/Undeploy agent RPCs may be stubbed `UNIMPLEMENTED` depending on branch state — check `service.py`.

## Running

```bash
cd agent_fleet && python -m services.fleet_server.src -v

# Docker Compose (from agent_fleet/)
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | see `packages/config.py` | PostgreSQL connection string |
| `OPENAI_API_KEY` | (from `.env`) | LLM planners + LLM/cost_based allocators |
| `GATEWAY_EVENT_URL` | `http://localhost:8000/internal/events` | State-change event POSTs |
| `DEFAULT_AGENT_HOST` | `localhost` | Reach agent task servers |
| `DURABLE_TASK_DISPATCH` | `false` | NATS JetStream durable delivery |
| `NATS_URL` | `nats://localhost:4222` | JetStream when durable dispatch on |
| `TESTING` | unset | Truthy → CreatePlan skips LLM planners |

## Suggested strategy pairings

| Scenario | Planning | Allocation |
|----------|----------|------------|
| Linear demo / strict order | Monolithic | LP |
| Independent goals | DAG | LLM or LP |
| Chip-style staged flow | Big DAG | LLM or cost_based |
| Plan now, assign in UI | Any | NONE → manual or AllocatePlan later |
| Minimize agent thrash on DAG | DAG / Big DAG | cost_based |

Pairings are API-valid even when not listed — match planner graph shape to allocator strengths.

## Parent package

Service packaging and Docker: `../README.md`.
