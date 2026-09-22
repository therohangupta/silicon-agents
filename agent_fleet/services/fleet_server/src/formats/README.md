# formats

Single module (`formats.py`) of **Pydantic models** shared by planners, allocators, and the Executor. Keeping schemas centralized ensures OpenAI structured outputs, DB persistence, and runtime dispatch agree on field names and types.

Do not invent ad-hoc dict shapes in strategy code — extend these models if new fields are required.

## Why two plan shapes (Plan vs DAGPlan)

| Stage | Model | Dependency representation |
|-------|-------|---------------------------|
| Monolithic / Replanner LLM output | `Plan` | Index-based `dependency_task_ids` into `tasks[]` |
| DAG / Big DAG LLM output | `DAGPlan` / `DAGNode` | String node ids in `depends_on` |
| After `save_plan_to_db` | Registry tasks | Integer `dependency_task_ids` → DB task ids |
| Executor scheduling | `AllocatedDAGPlan` | Integer `depends_on` task ids + `agent_id` |

`BasePlanner._convert_dag_to_plan` is the bridge from graph ids to index-based `Plan` before persistence.

## Model reference

### TaskPlanItem

One row in the unified planner output:

- `description` — agent-facing instruction
- `goal_id` — links to registry goal
- `dependency_task_ids` — **indices** at planning time
- `agent_type` — optional hint for allocators

### Plan

```python
class Plan(BaseModel):
    tasks: List[TaskPlanItem]
```

Used as OpenAI `response_format` for Monolithic and Replanner. Validated before task rows are created.

### DAGNode / DAGPlan

Graph-native planning:

- `DAGNode.id` — planner-local string (e.g. `goal2_node3`)
- `DAGNode.depends_on` — list of predecessor **node id strings**
- `DAGPlan.nodes` — flat node list; edges implied by `depends_on`

DAG and Big DAG planners validate LLM JSON into these models before conversion.

### AllocatedDAGNode / AllocatedDAGPlan

Executor-facing shape built in `Executor._generate_dag`:

- `task_id`, `agent_id` — concrete registry identifiers
- `depends_on` — prerequisite **task ids** (ints)
- Copied `description`, `goal_id` for logging and context

`Executor._get_agent_task_map` topologically sorts these nodes (Kahn) and splits work per agent.

### AgentTask / Allocation

Allocator output:

- `AgentTask`: `{task_id, agent_id}`
- `Allocation`: `{allocations: List[AgentTask]}`

OpenAI `response_format=Allocation` for LLM allocator. LP and cost_based construct the same envelope after solving.

## Data flow diagram

```text
Goals + strategy
       │
       ▼
  [Monolithic / Replanner] ──► Plan ──────────────┐
       │                                          │
  [DAG / Big DAG] ──► DAGPlan ──► convert ──► Plan ─┤
       │                                          │
       └──────────────────────────────────────────┤
                                                  ▼
                                         save_plan_to_db
                                                  │
                                                  ▼
                                    Registry tasks (int deps)
                                                  │
                    CreatePlan/AllocatePlan       │
                           │                      │
                           ▼                      │
                      Allocation                  │
                           │                      │
                           ▼                      ▼
                    agent_id on tasks    AllocatedDAGPlan
                                                  │
                                                  ▼
                                            Executor loop
```

## CreatePlan / AllocatePlan relationship

- **CreatePlan** never serializes these models directly to the client beyond what the registry/proto layer exposes; planners return JSON strings validated against `Plan` or `DAGPlan`.
- **AllocatePlan** consumes existing tasks (already `TaskPlanItem`-equivalent rows) and produces `Allocation` assignments — no change to Plan/DAGPlan schemas.

`allocation_strategy` does not alter format types; only which allocator class runs.

## LLM structured parse

Planners and LLM allocator pass Pydantic models to OpenAI `beta.chat.completions.parse`:

- Ensures JSON schema alignment with this module
- Reduces drift versus manual `json.loads` (though DAG planners still parse content strings for historical paths)

## Extension guidelines

When adding fields:

1. Update the Pydantic model in `formats.py`.
2. Update prompts / `summary.yaml` examples in the relevant `types/` directory.
3. Ensure `save_plan_to_db` or allocators persist new data if needed (may require registry/proto changes separately).

## Related reading

- Conversion logic: `planners/base.py` (`_convert_dag_to_plan`, `save_plan_to_db`)
- Executor builder: `executor/executor.py` (`_generate_dag`)
- Strategy docs: `planners/types/README.md`, `allocators/types/README.md`
