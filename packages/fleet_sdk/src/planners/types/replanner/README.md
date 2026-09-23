# Replanner (Executor recovery)

Builds a **new recovery `Plan`** after a task failure when execution policy requests replanning. This is **not** wired through `get_planner` or normal `CreatePlan` strategy selection — the Executor constructs `Replanner` directly inside `_handle_task_failure`.

Standard `Replanner.plan(goal_ids)` always raises `NotImplementedError`; callers must use `replan(...)`.

## When Fleet Manager / Executor picks this path

| Entry point | Behavior |
|-------------|----------|
| `CreatePlan` | Does **not** select Replanner. Use MONOLITHIC, DAG, BIG_DAG, or MANUAL_PLAN. |
| `AllocatePlan` | Unrelated to Replanner. |
| `StartPlan` → `Executor` | On task failure, if reliability `on_failure == "replan"` (or agent signals replan), Executor calls `Replanner.replan(...)`. |

Replanner flow (from `planner.py`):

1. Load original plan, goals, strategies, ordered task ids.
2. Summarize completed, failed, and pending tasks plus failure message.
3. Include agent assignment snapshot from Executor's `agent_task_assignments`.
4. GPT-4o structured `Plan` recovery segment.
5. `save_plan_to_db` with **original** `planning_strategy`, `allocation_strategy`, and `goal_ids`.
6. **Always** runs `LLMAllocator.allocate(new_plan_id)` (hard-coded, not the plan's stored allocation enum).
7. Returns `new_plan_id`; Executor sets `self.plan_id` and `self.replan = True` to rebuild queues.

## Suitable scenarios

Use replanning (via Executor policy) when:

- Transient failures should produce an alternate task sequence rather than aborting the whole plan.
- New information from an agent invalidates remaining steps but original goals still apply.
- Operators want automatic recovery without manual `CreatePlan` from the dashboard.

Avoid relying on replan for:

- Systematic capability gaps (fix agents or replan manually with a different allocation strategy).
- Cases where you need LP/COST_BASED on recovery — Replanner currently forces LLM allocation.

Catalog: `summary.yaml` (id `4`, recovery Plan same schema as Monolithic).

## Directory layout

| File | Role |
|------|------|
| `planner.py` | `Replanner.replan(plan_id, failed_task_id, failure_message, agent_task_assignments)` |
| `system.prompt` | Recovery specialist role |
| `user.prompt` | Failure context, completed/pending task summaries, agent state |
| `summary.yaml` | Documentation example recovery chain |
| `__init__.py` | Re-exports `Replanner` |

## Context assembled for the LLM

Replanner gathers rich state from the registry:

- Original plan metadata and ordered tasks.
- Which tasks completed vs failed vs not yet started relative to `failed_task_id`.
- Agent capability context (same helpers as `BasePlanner`).
- Failure message from the agent run.

Prompts are stored on `planning_prompts`; artifacts capture goals and generated recovery JSON.

## Output and persistence

- Response validated as `Plan` (index-based `dependency_task_ids`).
- New plan row linked to original goals/strategies.
- Immediate LLM allocation assigns every new task before Executor resumes.

**Important:** Recovery allocation ignores `original_allocation_strategy` at runtime today — implementation imports `LLMAllocator` explicitly after save.

## Comparison to CreatePlan Monolithic

Both emit `Plan` JSON, but:

- Replanner conditions on execution history and failure, not greenfield goals only.
- Replanner creates a **new** plan id mid-flight; CreatePlan creates the initial plan.
- Replanner allocates inside `replan()`; CreatePlan allocates in `FleetManagerService` after save.

## Failure modes

- Missing original plan or tasks → `ValueError`.
- Invalid LLM JSON → `ValueError` with decode/validation details.
- Allocation failure leaves a saved but possibly unassigned plan; Executor behavior depends on subsequent allocation checks.

## Requirements

- `OPENAI_API_KEY` for both replan LLM and bundled LLM allocator.
- Working registry shared with Executor (injected `registry`).

## Related reading

- Executor scheduling and failure policies: `executor/README.md`.
- LLM allocation details: `../../allocators/types/llm/README.md`.
- Plan schema: `formats/README.md`.
