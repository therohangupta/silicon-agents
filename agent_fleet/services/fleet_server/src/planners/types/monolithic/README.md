# Monolithic planner

Generates a **single sequential `Plan`** for all requested goals in one GPT-4o structured call. Tasks may interleave across goals, but prompts instruct the model to avoid broad parallelism: dependencies typically form a chronological chain (each step builds on prior indices).

Implementation: `MonolithicPlanner` in `planner.py`, extending `BasePlanner`.

## When Fleet Manager picks this strategy

`CreatePlan` selects Monolithic when the client sets protobuf `PlanningStrategy.MONOLITHIC` on the request. The service flow is:

1. Reject empty `goal_ids` (auto-planning requires at least one goal).
2. Skip LLM when `TESTING` is truthy (empty plan shell only).
3. Call `get_planner(MONOLITHIC, registry=...)` → `MonolithicPlanner`.
4. Run `planner.plan(goal_ids)` then `save_plan_to_db(...)`.
5. Optionally run `get_allocator(...).allocate(plan_id)` if `allocation_strategy != NONE`.

Monolithic is **not** used by `AllocatePlan` (allocation only; planning already done).

Replanner and Executor recovery paths do **not** use Monolithic via `get_planner`; Replanner emits the same `Plan` schema but through `Replanner.replan()`.

## Suitable scenarios

| Prefer Monolithic when | Consider DAG / Big DAG instead when |
|------------------------|-------------------------------------|
| Strict ordering matters more than wall-clock parallelism | Independent sub-workstreams can run concurrently |
| Simple linear workflows (setup → act → verify) | Each goal has internal fork/join structure |
| You want one LLM call and predictable index-based deps | Goals must stay isolated (DAG) or share setup tasks (Big DAG) |
| Executor load is low or agent count is small | Many agents should work different branches at once |

Catalog metadata for dashboards lives in `summary.yaml` (id `1`, method `foundation model`).

## Directory layout

| File | Role |
|------|------|
| `planner.py` | `MonolithicPlanner.plan()` — goals, capabilities, OpenAI parse → `Plan` JSON string |
| `system.prompt` | Sequential planner role, feasibility rules, JSON task array shape |
| `user.prompt` | Template: `{goals_context}`, `{agent_context}` from registry |
| `summary.yaml` | Human description, output format, example Plan JSON (not loaded at runtime) |
| `__init__.py` | Re-exports `MonolithicPlanner` |

Prompt files include documentation headers; the loader reads the **entire** file into the LLM message.

## Planning pipeline (code path)

1. **Validate** `goal_ids` non-empty; load each goal from `AgentInstanceRegistry`.
2. **Context** — `_load_capabilities()` and `_get_agent_context_string()` so the model knows feasible agent types/capabilities (assignment still happens later in allocators).
3. **Prompts** — load `system.prompt` and format `user.prompt` with all goals and agent summary.
4. **Persist prompts** on `self.planning_prompts` for attachment to the plan row after save.
5. **LLM** — `client.beta.chat.completions.parse(..., response_format=Plan, model=gpt-4o, temperature=0.2)`.
6. **Artifacts** — `planning_artifacts` includes goals, capabilities, agent context, and `generated_plan` after the call.
7. **Return** Plan JSON string → `BasePlanner.save_plan_to_db` creates task rows and remaps `dependency_task_ids` from indices to database task ids.

Output schema (`formats.Plan` / `TaskPlanItem`):

- `description`, `goal_id`, `dependency_task_ids` (indices into the `tasks` array at planning time).
- Optional `agent_type` hint for allocators (not enforced by Monolithic itself).

## Prompt contract (summary)

**System** defines a sequential chronological planner: logical succession, capability feasibility, actionable steps, no per-task agent assignment, goals may interleave but remain sequential.

**User** supplies the goal block and registered agent capabilities/types so the model can avoid impossible steps.

See `summary.yaml` → `example_output` for a minimal three-task chain.

## Persistence and observability

After planning, `FleetManagerService.CreatePlan` stores:

- `planning_prompts` / `planning_artifacts` / `server_logs` from the planner instance (via `save_plan_to_db` and follow-up `update_plan` when allocation runs).

Monolithic performs **one** OpenAI call per plan creation (plus separate allocation calls if LP/LLM/COST_BASED is selected).

## Requirements and failure modes

- **`OPENAI_API_KEY`** must be set for non-test CreatePlan flows.
- Missing goals → `ValueError` → gRPC `INTERNAL` with "Planning failed".
- Invalid structured output → parse/validation errors from OpenAI or Pydantic during save.

## Related reading

- Parent factory: `planners/base.py` → `get_planner(PlanningStrategy.MONOLITHIC)`.
- Unified schemas: `formats/README.md`.
- Per-goal parallelism: `../dag/README.md`.
- Cross-goal dependencies: `../big_dag/README.md`.
