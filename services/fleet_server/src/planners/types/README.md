# planners/types

Concrete planning strategies shipped as **self-contained directories**. Each type owns its LLM prompts, optional catalog metadata, and a `planner.py` class registered through `planners.base.get_planner`.

## Factory mapping (CreatePlan)

`FleetManagerService.CreatePlan` calls `get_planner(planning_strategy, registry=...)` for automatic planning. The protobuf enum maps as follows:

| `PlanningStrategy` | Directory | Class | CreatePlan notes |
|--------------------|-----------|-------|------------------|
| `MONOLITHIC` | `monolithic/` | `MonolithicPlanner` | One sequential `Plan` for all goals |
| `DAG` | `dag/` | `DAGPlanner` | One `DAGPlan` LLM call per goal, merged |
| `BIG_DAG` | `big_dag/` | `BigDAGPlanner` | One unified cross-goal DAG |
| `MANUAL_PLAN` | — | — | **Not** via factory; empty plan shell in `service.py` |

`Replanner` lives here for packaging consistency but is **not** returned by `get_planner`. Executor imports it on failure (`replanner/`).

### CreatePlan branches that skip `get_planner`

1. **`MANUAL_PLAN`** — `registry.create_plan(..., task_ids=[])` immediately.
2. **`TESTING` env truthy** — empty plan with requested strategies, no LLM (integration tests).
3. **Missing `goal_ids`** on auto strategies → `INVALID_ARGUMENT`.

All other auto strategies require goals, run `plan()`, then `save_plan_to_db`.

## Standard directory contract

Every planner type directory includes:

| Artifact | Purpose |
|----------|---------|
| `planner.py` | Implements `async plan(goal_ids) -> str` (Plan JSON or converted Plan JSON) |
| `system.prompt` | LLM system message (may include maintainer documentation header) |
| `user.prompt` | Template with `{placeholders}` filled in code |
| `summary.yaml` | Dashboard/docs catalog — **not imported** by runtime |
| `README.md` | Strategy-specific operator guide |
| `__init__.py` | Public export for `planners.types` |

Replanner adds `replan(...)` and intentionally breaks `plan()`.

## Shared base behavior (`../base.py`)

All planners inherit `BasePlanner`:

- Load agent capabilities; fail if fleet empty.
- Build agent context string for prompts.
- `save_plan_to_db` — create plan row, tasks, remap dependency indices → task ids.
- `_convert_dag_to_plan` — used by DAG and Big DAG after LLM graph output.

Persisted on the plan record: `planning_prompts`, `planning_artifacts`, `server_logs`.

## Choosing a strategy (quick guide)

| Your workload | Start with |
|---------------|------------|
| Linear checklist across goals | `monolithic/` |
| Independent goals, parallel inside each | `dag/` |
| Shared prerequisites across goals | `big_dag/` |
| Mid-run failure recovery | `replanner/` (Executor-driven, not CreatePlan) |

Allocation is orthogonal — see `allocators/types/README.md`. CreatePlan can chain planner + allocator in one RPC when `allocation_strategy != NONE`.

## LLM and model settings

Planners use OpenAI `gpt-4o` with structured parse:

- Monolithic + Replanner → `response_format=Plan`
- DAG + Big DAG → `response_format=DAGPlan` then conversion

Temperature `0.2`, `max_tokens=4000` (see each `planner.py`).

## Further reading

- Package overview: `../README.md`
- Schemas: `../../formats/README.md`
- gRPC orchestration: `../../service.py` (`CreatePlan` docstring)

Per-type detail:

- `monolithic/README.md`
- `dag/README.md`
- `big_dag/README.md`
- `replanner/README.md`
