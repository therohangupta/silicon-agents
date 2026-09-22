# planners

Turns registry **goals** into persisted **tasks** and dependency structure. Consumed by `FleetManagerService.CreatePlan` for automatic planning and by the **Executor** (via `Replanner`) for failure recovery.

## Package exports

From `__init__.py`:

- `BasePlanner`, `PlanningStrategy`, `get_planner`
- `MonolithicPlanner`, `DAGPlanner`, `BigDAGPlanner`, `Replanner`

## CreatePlan integration

High-level flow in `service.py`:

```text
MANUAL_PLAN → empty plan, return
no goal_ids → INVALID_ARGUMENT
TESTING → empty plan, return
planner = get_planner(planning_strategy)
plan_json = await planner.plan(goal_ids)
plan_id = await planner.save_plan_to_db(...)
[optional] get_allocator(...).allocate(plan_id)
return get_plan(plan_id)
```

`get_planner` (`base.py`) supports:

- `PlanningStrategy.MONOLITHIC` → `MonolithicPlanner`
- `PlanningStrategy.DAG` → `DAGPlanner`
- `PlanningStrategy.BIG_DAG` → `BigDAGPlanner`
- `PlanningStrategy.MANUAL_PLAN` → raises `ValueError` (handled earlier in service)

There is **no** protobuf enum for Replanner.

## BasePlanner responsibilities

| Concern | Method / field |
|---------|----------------|
| Fleet context | `_load_capabilities`, `_get_agent_context_string` |
| LLM output → DB | `save_plan_to_db` |
| Graph → unified Plan | `_convert_dag_to_plan` |
| Audit trail | `planning_prompts`, `planning_artifacts`, `server_logs` |

Saved plans store the requested `planning_strategy` and `allocation_strategy` enums even when allocation is deferred (`NONE`).

## Strategy comparison

| Strategy | LLM calls | Parallelism | Cross-goal deps |
|----------|-----------|-------------|-----------------|
| Monolithic | 1 | Minimal (sequential Plan) | Via ordering only |
| DAG | per goal | Within each goal DAG | Forbidden |
| Big DAG | 1 | Within unified DAG | Allowed |
| Replanner | 1 per recovery | Recovery segment sequential Plan | N/A (context-driven) |

Detailed operator guides live under `types/*/README.md`.

## Prompt and catalog conventions

Concrete planners under `types/` co-locate:

- `system.prompt` / `user.prompt`
- `summary.yaml` for dashboard catalog entries (ids 1–4 in current tree)

Runtime code reads prompts from disk; YAML summaries are documentation-only.

## Environment

- **`OPENAI_API_KEY`** required for all LLM planners in non-test CreatePlan.
- **`TESTING`** bypasses planner entirely (empty task list).

## Executor recovery

On replan policy, Executor constructs `Replanner(registry=...)` directly — not through `get_planner`. See `types/replanner/README.md`.

## Related modules

- Allocation after planning: `../allocators/`
- Shared schemas: `../formats/`
- Execution: `../executor/`
