# Cost-based allocator (iterative frontier)

Assigns tasks **round by round** along the plan's dependency graph. Each round, the LLM maps agents to at most one **frontier** task (dependencies already assigned), using `previous_task_id` per agent to bias against expensive context switching.

Implementation: `CostBasedAllocator` in `allocator.py`. Catalog: `summary.yaml` (id `3`, `method_type: hybrid`).

## When Fleet Manager picks this strategy

### CreatePlan

Selected when the client sets `AllocationStrategy.COST_BASED` on `CreatePlanRequest`:

```
if allocation_strategy != NONE:
    allocator = get_allocator(COST_BASED, registry=...)
    await allocator.allocate(plan_id)
```

Runs immediately after planning unless `TESTING` bypass left an empty task list (nothing to allocate).

### AllocatePlan

Use to apply cost-based assignment to a plan that was created with `NONE`, `MANUAL_ALLOCATION`, or to **replace** a prior LP/LLM assignment:

- Validates plan exists and `task_ids` non-empty.
- Updates stored `allocation_strategy` on the plan row after success.

Replanner does **not** use cost_based today — recovery hard-codes `LLMAllocator`.

## Suitable scenarios

| Prefer cost_based when | Prefer LLM single-shot when |
|------------------------|-----------------------------|
| DAG-shaped plans with parallel frontiers | Small plans where one batch assignment suffices |
| Agent continuity reduces handoff cost (same specialist) | You want minimal OpenAI round trips |
| Assignment order should respect deps during allocation | Dependencies are weak hints only |

| Prefer cost_based over LP when |
|--------------------------------|
| Capability matching needs LLM interpretation of descriptions |
| Switching cost is not modeled in ILP objective |

## Directory layout

| File | Role |
|------|------|
| `allocator.py` | Frontier loop, per-round OpenAI JSON object, DB writes |
| `system.prompt` | Iterative cost-aware allocation role |
| `user.prompt` | `{available_tasks}`, `{agent_descriptions}` with `previous_task_id` |
| `summary.yaml` | Behavioral steps and output shape documentation |
| `__init__.py` | Re-exports `CostBasedAllocator` |

## Algorithm

1. Load plan tasks and agents; build `dependency_map[task_id] → set(dep ids)` from `dependency_task_ids` or legacy `dependencies`.
2. Initialize `assigned_tasks`, `agent_states[agent_id] → last task_id or None`.
3. **Loop** until no frontier tasks:
   - Frontier = unassigned tasks whose dependencies ⊆ `assigned_tasks`.
   - Serialize frontier tasks and agents (include `previous_task_id`).
   - Load/format prompts; call OpenAI with `response_format={"type": "json_object"}`.
   - Parse `agent_id → task_id` mapping; skip null assignments.
   - Record assignments, update `assigned_tasks` and agent states.
   - Break if a round assigns nothing (infinite-loop guard).
4. **Fallback** — remaining unassigned tasks go to the first agent in list (logged warning).
5. Persist all pairs; return `Allocation`.

Unlike `LLMAllocator`, prompts are reloaded every round (not stored once on `allocation_prompts` in the loop — operators may see fewer persisted prompt snapshots unless extended).

## Output shape per round

Model returns a JSON object mapping agent id strings to task id strings/integers. Final envelope still `Allocation` with full list of `AgentTask`.

## Trade-offs

| | cost_based | llm | lp |
|---|------------|-----|-----|
| OpenAI calls | O(rounds) | 1 | 0 |
| Respects dep order at assign time | Yes | No | No |
| Switching cost signal | Yes (`previous_task_id`) | Implicit | N/A |
| Deterministic | No | No | Yes (given caps) |

## Failure modes

- Missing plan/agents → `{}`.
- JSON parse error in a round → **raises** (CreatePlan/AllocatePlan → INTERNAL).
- Fallback may assign incapable agents if frontier stalls — monitor logs for warnings.

## Requirements

- `OPENAI_API_KEY`.
- Tasks should have consistent `dependency_task_ids` from planner save for correct frontiers.

## Related reading

- Single-shot allocation: `../llm/README.md`.
- Load-balanced ILP: `../lp/README.md`.
- Executor enforces deps at run time regardless: `executor/README.md`.
