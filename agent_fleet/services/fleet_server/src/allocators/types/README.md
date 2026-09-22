# allocators/types

Concrete task-to-agent assignment strategies. Each directory contains `allocator.py` implementing `async allocate(plan_id)` plus optional prompts and `summary.yaml` catalog metadata.

## Factory mapping (CreatePlan and AllocatePlan)

`allocators.base.get_allocator(allocation_strategy, registry=...)` selects:

| `AllocationStrategy` | Directory | Class | Invoked from |
|----------------------|-----------|-------|--------------|
| `LP` | `lp/` | `LPAllocator` | CreatePlan (if not NONE), AllocatePlan |
| `LLM` | `llm/` | `LLMAllocator` | CreatePlan, AllocatePlan, Replanner (hard-coded) |
| `COST_BASED` | `cost_based/` | `CostBasedAllocator` | CreatePlan, AllocatePlan |
| `NONE` | — | — | **Do not call** factory; skip allocation |
| `MANUAL_ALLOCATION` | — | — | **Do not call** factory; UI assigns per task |

### CreatePlan sequence

After planning (or manual/test shell with tasks added later):

```text
if allocation_strategy != NONE:
    allocator = get_allocator(allocation_strategy, registry=...)
    await allocator.allocate(plan_id)
    update_plan(allocation_prompts, allocation_artifacts, server_logs)
```

When strategy is `NONE`, tasks remain without `agent_id` until `AllocatePlan` or manual assignment.

### AllocatePlan sequence

Always requires a populated plan:

```text
get_plan(plan_id) → must have task_ids
allocator = get_allocator(request.allocation_strategy, ...)
await allocator.allocate(plan_id)
update_plan(allocation_strategy=..., prompts, artifacts)
```

Use this RPC to defer allocation, change strategy, or re-run after editing tasks.

## Directory contract

| Artifact | LP | LLM | cost_based |
|----------|----|-----|------------|
| `allocator.py` | yes | yes | yes |
| `system.prompt` | no | yes | yes |
| `user.prompt` | no | yes | yes |
| `summary.yaml` | yes (`prompts: none`) | yes | yes |
| `README.md` | yes | yes | yes |

LLM-backed allocators load prompts via `BaseAllocator._load_prompt` from the co-located directory.

## Shared outputs

All successful paths:

1. Mutate task rows: `registry.update_task(task_id, agent_id=...)`.
2. Return `formats.Allocation` wrapping `AgentTask` list (annotations may still say `Dict[int, str]` historically).

CreatePlan persists allocator prompts/artifacts/logs on the plan when allocation runs.

## Choosing a strategy

| Priority | Strategy |
|----------|----------|
| Minimize max tasks per agent (deterministic) | `lp/` |
| Semantic fit of descriptions to agent roles | `llm/` |
| Respect DAG frontiers + reduce agent switching | `cost_based/` |
| Human-in-the-loop assignment | `MANUAL_ALLOCATION` (no allocator) |
| Plan first, assign later | CreatePlan with `NONE`, then `AllocatePlan` |

Planning strategy (Monolithic/DAG/Big DAG) does not constrain allocation enum — any pairing is valid at the API level, though cost_based pairs best with DAG-shaped task graphs.

## Requirements

- **LP**: PuLP installed; no OpenAI for allocation.
- **LLM / cost_based**: `OPENAI_API_KEY`.
- **All**: registered agents and tasks on the plan.

## Per-type documentation

- `lp/README.md` — ILP constraints and capability inference
- `llm/README.md` — single structured Allocation call
- `cost_based/README.md` — iterative frontier rounds

Parent package: `../README.md`.
