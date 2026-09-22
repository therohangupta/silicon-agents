# LLM allocator (single-shot)

Assigns all tasks to agents in **one** GPT-4o structured call with `response_format=Allocation`. The model sees full task descriptions, goal ids, dependency task ids, agent types, and agent capabilities, then returns an `allocations` array persisted via `registry.update_task`.

Implementation: `LLMAllocator` in `allocator.py`.

## When Fleet Manager picks this strategy

### CreatePlan

When `allocation_strategy == AllocationStrategy.LLM` and planning produced tasks:

1. Planner completes and `save_plan_to_db` returns `plan_id`.
2. `get_allocator(LLM, registry=...)` → `LLMAllocator`.
3. `await allocator.allocate(plan_id)`.
4. Service calls `registry.update_plan` with `allocation_prompts`, `allocation_artifacts`, `server_logs`.

If `allocation_strategy == NONE`, this allocator is never invoked during CreatePlan.

### AllocatePlan

Primary path for plans created with `NONE` or `MANUAL_ALLOCATION`, or when operators change strategy:

- Requires existing tasks (`FAILED_PRECONDITION` if `task_ids` empty).
- Runs the same `allocate(plan_id)` pipeline and updates the plan's stored allocation strategy.

### Replanner (special case)

`Replanner.replan()` **always** instantiates `LLMAllocator` after saving a recovery plan, regardless of the original plan's `allocation_strategy`. CreatePlan/AllocatePlan enums do not control that path.

## Suitable scenarios

| Prefer LLM allocator when | Prefer LP when |
|---------------------------|----------------|
| Task text and agent roles need joint reasoning | Pure load balancing with hard capability constraints |
| Dependencies are informative but order is enforced at execution | You need guaranteed optimal min-max load |
| One-shot assignment is acceptable | You want zero OpenAI cost at allocation |

| Prefer LLM over cost_based when |
|---------------------------------|
| Plan is small and frontier iteration adds latency without benefit |
| Switching-cost optimization is unnecessary |

## Directory layout

| File | Role |
|------|------|
| `allocator.py` | Serialize tasks/agents, load prompts, OpenAI parse, DB updates |
| `system.prompt` | Allocator role, constraints, output JSON shape |
| `user.prompt` | `{task_descriptions}`, `{agent_descriptions}` JSON blobs |
| `summary.yaml` | Catalog id `2`, foundation model metadata |
| `__init__.py` | Re-exports `LLMAllocator` |

`BaseAllocator._load_prompt` resolves prompts next to the concrete allocator module path.

## Allocation pipeline

1. Verify plan exists; filter tasks for `plan_id`.
2. Build `task_descriptions` — string ids, description, goal_id, dependency list, optional agent_type.
3. Build `agent_descriptions` — agent_id, agent_type, capabilities string.
4. Format user prompt; store system+user in `allocation_prompts`.
5. Store inputs in `allocation_artifacts`.
6. OpenAI `parse(..., response_format=Allocation)`.
7. Parse JSON → `Allocation` with `AgentTask` entries.
8. `update_task` per assignment; append human-readable lines to `server_logs`.
9. Store `final_allocation` in artifacts.

## Output schema

```json
{
  "allocations": [
    {"task_id": 101, "agent_id": "agent-uuid-1"}
  ]
}
```

Matches `formats.Allocation` used as the structured output schema.

## Prompt contract (summary)

**System** — defines intelligent assignment: respect capabilities, types, dependencies as context (execution still serializes deps separately), optimize for goal completion.

**User** — embeds JSON arrays for tasks and agents produced by `allocate()` (see header comments in `user.prompt`).

## Failure modes

- Missing plan or agents → return `{}` (logged errors).
- Unparseable model output → return `{}` after logging raw content.
- Partial DB update failures logged per task in `server_logs`.

## Requirements

- `OPENAI_API_KEY`.
- Tasks must exist (CreatePlan after successful planning, or AllocatePlan on populated plan).

## Observability

CreatePlan and AllocatePlan persist prompts/artifacts on the plan row for dashboard replay. `server_logs` includes counts and per-assignment lines.

## Related reading

- Iterative frontier allocator: `../cost_based/README.md`.
- Optimal load split: `../lp/README.md`.
- Schemas: `formats/README.md`.
