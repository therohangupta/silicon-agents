# DAG planner (per-goal)

Generates a **separate directed acyclic graph for each goal**, then merges all `DAGNode` entries into one `DAGPlan` and converts to the unified `Plan` schema via `BasePlanner._convert_dag_to_plan`. Cross-goal dependency edges are forbidden by prompt design; node ids use a `goal{goal_id}_` prefix so merged graphs never collide.

Implementation: `DAGPlanner` in `planner.py`.

## When Fleet Manager picks this strategy

`CreatePlan` uses DAG when the client sends `PlanningStrategy.DAG`:

```
get_planner(DAG) → DAGPlanner(registry)
await planner.plan(goal_ids)
await planner.save_plan_to_db(...)
```

Same preconditions as other auto planners: not `MANUAL_PLAN`, non-empty `goal_ids`, planner not bypassed when `TESTING` is set.

`AllocatePlan` does not change the planning strategy; it only assigns agents to existing tasks using the requested `AllocationStrategy`.

## Suitable scenarios

| Prefer DAG when | Prefer Big DAG when |
|-----------------|---------------------|
| Goals are independent programs of work | Tasks in goal B should wait on artifacts from goal A |
| You want **N LLM calls** (one per goal) for isolation and debuggability | One coordinated graph is worth a single larger LLM call |
| Parallelism **within** a goal is enough | Shared setup / handoff tasks should appear once for all goals |
| Dashboard should show per-goal subgraphs in `planning_artifacts` | Cross-goal optimization (e.g. RTL depends on requirements) |

Catalog: `summary.yaml` (id `2`, per-goal isolation documented).

## Directory layout

| File | Role |
|------|------|
| `planner.py` | Loop per goal: LLM → `DAGPlan` JSON → validate `DAGNode` list → extend `all_nodes` |
| `system.prompt` | DAG rules, acyclicity, no cross-goal edges, node id conventions |
| `user.prompt` | Per-goal template: `{goal_id}`, `{goal_description}`, `{goal_prefix}`, `{agent_context}` |
| `summary.yaml` | Operator-facing description and example nodes |
| `__init__.py` | Re-exports `DAGPlanner` |

`planning_prompts` stores `system` plus `user_template` (actual user messages vary per goal).

## Planning pipeline

1. Load all goals; fail if any id is missing.
2. Initialize `planning_artifacts.goals` and empty `dag_structure`.
3. For **each goal**:
   - Set `goal_prefix = f"goal{goal_id}_"`.
   - Format `user.prompt` for that goal only.
   - Call OpenAI with `response_format=DAGPlan`.
   - Parse JSON, validate each node as `DAGNode`, append to `all_nodes`.
4. Build `DAGPlan(nodes=all_nodes)`.
5. Project nodes/edges into `planning_artifacts.dag_structure` (includes `agent_type` when present).
6. Return `super()._convert_dag_to_plan(combined_dag)` — string Plan JSON for persistence.

### DAG node schema (LLM output)

Each node (`formats.DAGNode`):

- `id` — string, must be unique after prefixing (e.g. `goal3_node0`).
- `description`, `goal_id`, `depends_on` (list of predecessor **node id strings**).
- Optional `agent_type` suggestion for allocators.

Conversion rewrites `depends_on` string ids into `dependency_task_ids` integer indices in the flat `Plan.tasks` list.

## Parallelism semantics

- **Within a goal**: tasks with empty or satisfied `depends_on` can run concurrently once allocated to different agents.
- **Across goals**: no edges; Executor may still run goals' ready tasks in parallel if agents are free.
- **Versus Monolithic**: DAG allows fork/join inside each goal; Monolithic forces a single global sequence.

## Cost and observability

- **One OpenAI call per goal** (linear in `len(goal_ids)`).
- Each successful parse logs node count per goal.
- Parse failures raise `ValueError` with goal id in the message → CreatePlan INTERNAL.

## Requirements

- `OPENAI_API_KEY` for production CreatePlan.
- At least one registered agent so `_load_capabilities()` succeeds (inherited from `BasePlanner`).

## Related reading

- Cross-goal graph: `../big_dag/README.md`.
- Sequential-only: `../monolithic/README.md`.
- Schema details: `formats/README.md` and `summary.yaml`.
