# allocators

Maps each task in a plan to a concrete **agent instance id** after tasks exist in the registry. Does not create tasks or modify dependency graphs — only sets `agent_id` on task rows.

## Entry points

| RPC / caller | When allocators run |
|--------------|---------------------|
| `CreatePlan` | After successful auto-plan save, if `allocation_strategy != NONE` |
| `AllocatePlan` | On demand for existing plans with tasks |
| `Replanner.replan` | Always uses `LLMAllocator` after recovery save (exception to enum) |

Skipped paths:

- `AllocationStrategy.NONE` — CreatePlan logs "Skipping allocation"; use AllocatePlan later.
- `AllocationStrategy.MANUAL_ALLOCATION` — operators assign via API/UI; `get_allocator` raises if called.

## Package exports

- `BaseAllocator`, `get_allocator`
- `LPAllocator`, `LLMAllocator`, `CostBasedAllocator`

## get_allocator mapping

Defined in `base.py`:

| Enum | Implementation |
|------|----------------|
| `LP` | PuLP min-max-load ILP |
| `LLM` | Single GPT-4o `Allocation` parse |
| `COST_BASED` | Iterative frontier + JSON agent→task maps |
| `NONE`, `MANUAL_ALLOCATION` | ValueError — guard in service before call |

## BaseAllocator

Constructors accept optional shared `AgentInstanceRegistry` from `FleetManagerService` (preferred) or `db_url` fallback.

Shared fields persisted onto plans:

- `allocation_prompts`
- `allocation_artifacts`
- `server_logs`

LLM subclasses use `_load_prompt("system"|"user")` from their type directory.

## CreatePlan vs AllocatePlan

**CreatePlan** chains planning + optional allocation in one transaction from the client's perspective:

1. Planner produces tasks.
2. If strategy not NONE, allocate immediately and merge logs into plan metadata.

**AllocatePlan** is for:

- Plans created with `NONE` or manual assignment partially done
- Re-running with a different strategy (e.g. switch LP → LLM)
- Re-allocation after task graph edits

AllocatePlan updates `allocation_strategy` on the plan row; CreatePlan sets it at creation time.

## Strategy selection (operator guide)

| Goal | Strategy |
|------|----------|
| Balanced workload, explicit caps/types | LP |
| Rich natural-language task/agent matching | LLM |
| DAG plans, minimize agent context switching | COST_BASED |
| Deferred assignment | NONE on create → AllocatePlan later |

Pairing with planners is flexible; common combos:

- Monolithic + LP — simple pipeline, balanced agents
- DAG + COST_BASED — parallel frontiers with sticky assignments
- Big DAG + LLM — complex graph, semantic agent fit

## Failure handling

- LP infeasible → empty allocation dict/object, error logged.
- LLM parse failure → empty return (LLM) or exception (cost_based round).
- StartPlan requires **full** allocation — partial assignment fails precondition.

## Dependencies

- LP: `pulp`
- LLM / cost_based: `OPENAI_API_KEY`

## Further reading

- Per-strategy: `types/README.md` and `types/*/README.md`
- Schemas: `../formats/README.md`
- gRPC: `../service.py` (`CreatePlan`, `AllocatePlan`)
