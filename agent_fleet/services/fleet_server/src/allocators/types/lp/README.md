# LP allocator (linear programming)

Assigns every task in a plan to exactly one agent by solving a **PuLP integer linear program**. Objective: minimize the maximum number of tasks assigned to any single agent (`max_load`), subject to capability subset constraints and optional `agent_type` matching.

Implementation: `LPAllocator` in `allocator.py`. **No LLM prompts** — `summary.yaml` lists `prompts: none`.

## When Fleet Manager picks this strategy

### CreatePlan

After a planner saves tasks, if `allocation_strategy == AllocationStrategy.LP`:

```python
allocator = get_allocator(LP, registry=self.registry)
await allocator.allocate(plan_id)
```

Skipped when `allocation_strategy == NONE` or `MANUAL_ALLOCATION` (service must not call `get_allocator` for those enums).

### AllocatePlan

Re-runs allocation on an **existing** plan with tasks:

```python
allocator = get_allocator(request.allocation_strategy, ...)
await allocator.allocate(plan_id)
await registry.update_plan(..., allocation_strategy=..., allocation_artifacts=...)
```

Use AllocatePlan to switch from NONE/manual to LP, or to re-balance after task edits.

## Suitable scenarios

| Prefer LP when | Prefer LLM / cost_based when |
|----------------|------------------------------|
| Fair load balancing is the primary goal | Task text requires semantic matching beyond caps/types |
| Capabilities and types are well-defined on tasks/agents | Dependencies should influence assignment order during allocation |
| You want deterministic, reproducible assignments | Switching-cost / agent continuity matters mid-plan |
| No OpenAI cost for allocation step | Heuristic capability inference from descriptions is insufficient |

## Algorithm (from `allocator.py`)

1. **Load** plan, filter tasks by `plan_id`, list all agents.
2. **Capability map** — `agent_caps[agent_id] = set(capabilities)`.
3. **Task requirements** — use `required_capabilities` when set; else infer from description keywords (`navigate`, `pick`, `place`, etc.) for legacy demos.
4. **Fallback agent** — agent with the largest capability set when inference yields empty caps.
5. **Decision variables** — binary `x[task_id, agent_id]`.
6. **Constraints**:
   - Each task assigned to exactly one agent.
   - Zero assignment when agent type mismatches task `agent_type` (when specified).
   - Zero assignment when `task_caps ⊄ agent_caps`.
   - Special fallback-only routing for untyped tasks with empty inferred caps.
   - Per-agent task count ≤ `max_load`.
7. **Solve** with PuLP default (CBC). If not `Optimal`, log and return `{}`.
8. **Persist** each chosen pair via `registry.update_task(task_id, agent_id=...)`.
9. **Return** `Allocation(allocations=[AgentTask(...)])`.

## Output schema

Uses `formats.Allocation` / `AgentTask` (`task_id`, `agent_id`). Historical type hints say `Dict[int, str]` but runtime returns the Pydantic object.

## Artifacts and logging

`LPAllocator` does not populate `allocation_prompts` (no prompts). `server_logs` may remain empty unless extended; CreatePlan still attempts to persist allocator logs when present.

## Operational notes

- **Infeasible ILP** — no agent satisfies type+capability for a task → empty return; plan stays unallocated or partially assigned from a prior run.
- **Heuristic inference** — keyword scan on descriptions is demo-oriented; production tasks should set `required_capabilities` and `agent_type` explicitly.
- **Dependencies** — LP does **not** read task dependency order; Executor enforces order at run time. For allocation order aware of DAG frontiers, use `cost_based`.

## Dependencies

- Python package `pulp` (declared in fleet server requirements).
- No `OPENAI_API_KEY` for allocation itself (planner may still need it).

## Catalog metadata

See `summary.yaml` (id `1`, `method_type: algorithmic`, example behavior bullets).

## Related reading

- Factory: `allocators/base.py` → `get_allocator(AllocationStrategy.LP)`.
- Single-shot semantic allocation: `../llm/README.md`.
- Frontier + switching cost: `../cost_based/README.md`.
