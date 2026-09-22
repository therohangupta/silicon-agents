# executor

Runs **fully allocated** plans: dependency-aware scheduling, parallel agent dispatch, reliability policies, optional durable NATS delivery, and Replanner integration on recoverable failures.

Started by `FleetManagerService.StartPlan` as `asyncio.create_task(Executor(...).execute())` after allocation checks pass.

## Preconditions (StartPlan)

`StartPlan` rejects execution unless every task has an `agent_id`:

- `unallocated` — no assignments; run `AllocatePlan` or CreatePlan with non-NONE allocation
- `partially_allocated` — lists missing task ids
- `fully allocated` — Executor allowed to start

Planning strategy (Monolithic/DAG/Big DAG) does not affect Executor entry — only task ids, deps, and agent assignments matter.

## Module layout

| File | Role |
|------|------|
| `executor.py` | Main `Executor` class: DAG build, Kahn sort, dispatch loop, replan/abort |
| `reliability.py` | Failure classification, retryability, exponential backoff |
| `task_delivery.py` | NATS JetStream durable dispatch + deferred ack when enabled |

## Execution pipeline

1. **Optional NATS** — if `DURABLE_TASK_DISPATCH=true`, connect `TaskDeliveryBus`; fall back to direct HTTP on failure.
2. **Status** — plan `execution_status=executing`; Gateway `emit_plan_changed`.
3. **DAG** — `_generate_dag()` builds `AllocatedDAGPlan` from registry tasks (int deps, agent ids).
4. **Partition** — `_get_agent_task_map()` topo-sorts (Kahn) and assigns ordered queues per agent.
5. **Loop** (~1s poll) — schedule ready tasks when deps complete and agent idle.
6. **Dispatch** — `AgentClient` or durable bus; attach `ExecutionContext` snapshot + artifact manifest.
7. **Success** — mark task completed, pop queue, accumulate world facts / artifacts.
8. **Failure** — honor per-agent `ReliabilityConfig.on_failure`:
   - `replan` → `Replanner.replan(...)` → new plan id, rebuild DAG
   - `skip` / retries / `dead_letter` / abort paths per `reliability.py`
9. **Terminal** — plan completed or failed; remaining tasks may be marked failed on abort.

## Parallelism model

- Global readiness follows **task dependency graph** (not planner string node ids).
- An agent runs one task at a time (`agent_to_idle_bool`).
- Independent branches (from DAG or Big DAG planning) can run concurrently on different agents.

Monolithic plans still execute correctly but expose little parallelism because deps form a chain.

## Replanner coupling

Executor imports `Replanner` directly — not via `get_planner` or CreatePlan.

On replan:

- New plan saved with original goal/strategy metadata
- `LLMAllocator` assigns agents (hard-coded in Replanner)
- Executor sets `self.replan = True` and switches `self.plan_id`

CreatePlan/AllocatePlan enums do not control recovery allocation today.

## World state and artifacts

- `ExecutionContext.snapshot()` feeds agent task requests.
- `_artifact_manifest` collects `ArtifactRef` from completed tasks for downstream context.
- Workspace URI from config (`WORKSPACE_*`) embedded in requests.

## Configuration

| Variable | Effect |
|----------|--------|
| `DURABLE_TASK_DISPATCH` | `true` → JetStream path in `task_delivery.py` |
| `NATS_URL` | Broker for durable mode |
| `DEFAULT_AGENT_HOST` | Host rewrite for agent HTTP endpoints |
| `DATABASE_URL` | Registry persistence |

## Reliability (`reliability.py`)

- `classify_failure` — maps exceptions/agent results to categories
- `is_retryable` / `backoff_delay` — bounded retries before terminal handling

Executor respects agent-configured reliability on each dispatch.

## Observability

- `execution_logs` appended and persisted on plan rows
- `emit_task_changed` / `emit_plan_changed` for Gateway dashboard invalidation
- Metrics spans via `packages.metrics.track_operation`

## Standalone harness

`executor.py` includes `__main__` for local debugging (ArgumentParser) — not used in production gRPC path.

## Related reading

- gRPC start: `../service.py` (`StartPlan`)
- Schemas: `../formats/README.md` (`AllocatedDAGPlan`)
- Recovery planner: `../planners/types/replanner/README.md`
- Planning/allocation upstream: `../README.md`
