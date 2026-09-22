# Big DAG planner (unified cross-goal)

Produces **one `DAGPlan` spanning all goals** in a single GPT-4o call. Unlike `DAGPlanner`, `depends_on` may reference nodes belonging to different goals, enabling shared setup tasks, explicit handoffs, and cross-goal ordering constraints.

Implementation: `BigDAGPlanner` in `planner.py`.

## When Fleet Manager picks this strategy

`CreatePlan` selects Big DAG when the request carries `PlanningStrategy.BIG_DAG`:

1. `get_planner(BIG_DAG, registry=self.registry)` → `BigDAGPlanner`.
2. `plan_json = await planner.plan(goal_ids)`.
3. `plan_id = await planner.save_plan_to_db(...)`.
4. If `allocation_strategy != NONE`, `get_allocator(...).allocate(plan_id)`.

`AllocatePlan` never re-invokes Big DAG; it only re-runs allocation on an existing task graph.

## Suitable scenarios

| Prefer Big DAG when | Prefer per-goal DAG when |
|---------------------|--------------------------|
| Goal B logically depends on outputs of goal A | Goals are intentionally isolated teams or milestones |
| You want one holistic decomposition (chip flow, pipeline stages) | You prefer smaller, per-goal LLM contexts |
| Cross-goal edges reduce duplicate work | Debugging per-goal graphs separately is important |
| Agent types differ by stage and ordering spans goals | Cross-goal coupling is accidental, not desired |

`summary.yaml` (id `3`) documents chip-design-style examples (`requirements` → `rtl_implementation`).

## Directory layout

| File | Role |
|------|------|
| `planner.py` | Single LLM call, parse `DAGPlan`, convert to `Plan` |
| `system.prompt` | Unified DAG role, cross-goal dependency rules |
| `user.prompt` | `{goals_context}` (all goals) + `{agent_context}` |
| `summary.yaml` | Catalog metadata and multi-goal example nodes |
| `__init__.py` | Re-exports `BigDAGPlanner` |

## Planning pipeline

1. Validate and load all goals into a multi-goal context block (same pattern as Monolithic user context).
2. Load capabilities and agent summary string.
3. Format system + user prompts; store on `planning_prompts`.
4. One OpenAI parse with `response_format=DAGPlan`.
5. Validate nodes as `DAGNode` list; log total node count and goal count.
6. Fill `planning_artifacts.dag_structure` with nodes and derived edges for UI.
7. `_convert_dag_to_plan(big_dag_plan)` → Plan JSON for `save_plan_to_db`.

### Node id conventions

Prompts typically use short ids (`node0`, `node1`) because there is only one graph. Each node still carries an explicit `goal_id` for traceability and allocator hints via optional `agent_type`.

## Execution interaction

After allocation, `Executor` builds `AllocatedDAGPlan` from **database task ids**, not planner string node ids. Big DAG's cross-goal edges become integer `depends_on` on registry tasks, so the Kahn scheduler honors global ordering.

Parallelism exists wherever the unified DAG has multiple ready nodes with satisfied dependencies.

## Trade-offs

| Aspect | Big DAG | DAG (per goal) |
|--------|---------|----------------|
| LLM calls | 1 | len(goal_ids) |
| Context size | All goals in one prompt | Smaller per-goal prompts |
| Cross-goal deps | Allowed | Forbidden |
| Failure blast radius | Whole graph in one response | Per-goal retry possible (manual) |

## Failure modes

- Empty `goal_ids` → `ValueError`.
- Unparseable LLM JSON → `ValueError("Failed to parse LLM response")`.
- Cycles in the model output may break conversion or execution; prompts emphasize acyclicity.

## Requirements

- `OPENAI_API_KEY`.
- Registered agents for capability loading.

## Related reading

- Per-goal isolation: `../dag/README.md`.
- Sequential fallback: `../monolithic/README.md`.
- Formats: `formats/README.md`.
