# Placement Lead (`placement_lead`)

This directory is the deployable microservice package for the **Placement Lead** in the fleet **placement** stage (role `lead`).

## EDA responsibility

Own standard-cell placement for one partition. Coordinate timing, congestion, power, and legalization, and recommend which candidate proceeds.

As a **lead**, this process publishes workflows, reads qualified upstream artifacts, opens child agent tasks, compares candidates, and recommends next steps. It does **not** promote the canonical baseline or act as independent signoff.

## Identity and HTTP port

| Field | Value |
|-------|-------|
| Agent id | `placement_lead` |
| Stage | `placement` |
| Role | `lead` |
| Host | `host.docker.internal` |
| Port | **8243** (must match `Dockerfile` `EXPOSE`) |
| Health | `/health` |
| Execute | `/tasks/execute` |

## Boundaries

Hard limits from `config.yaml` `boundary`. The planner and `EDAAgent` enforce these even when a tool adapter could physically perform a forbidden action.

### May

- Publish a placement workflow
- Read the qualified floorplan
- Request a human decision when candidates trade violations across corners

### May not

- Accept a candidate that only moves violations into another corner
- Promote a placement
- Promote a candidate onto the canonical baseline
- Approve a waiver or relax a hard requirement
- Treat its own summary as independent signoff

## Skills

Skills bind planner task ids to callables in `tools.py` (`module: tools`, `execution.mode: direct_function`).

| Skill id | Action | Callable | Description |
|----------|--------|----------|-------------|
| `plan_placement_trials` | `create_workflow` | `plan_placement_trials` | Emit the placement and evaluation workflow. |
| `request_placement_trial` | `create_workflow` | `request_placement_trial` | Open one isolated placement strategy. |
| `request_placement_evaluation` | `create_workflow` | `request_placement_evaluation` | Hand a candidate to the multi-corner evaluator. |
| `request_boundary_check` | `create_workflow` | `request_boundary_check` | Open a cross-partition boundary check. |
| `read_qualified_floorplan` | `read_reports` | `read_qualified_floorplan` | Read the floorplan this placement inherits. |
| `read_placement_metrics` | `read_reports` | `read_placement_metrics` | Read timing, congestion, power, and legality for each trial. |
| `read_corner_coverage` | `read_reports` | `read_corner_coverage` | Read which modes and corners each trial has been scored on. |
| `compare_placement_trials` | `read_reports` | `compare_placement_trials` | Rank trials that are legal in every required corner. |
| `recommend_placement_candidate` | `publish_finding` | `recommend_placement_candidate` | Record which legal candidate should advance. This does not promote it. |
| `flag_corner_shifted_violation` | `publish_finding` | `flag_corner_shifted_violation` | Publish a gain that moved a violation into another corner. |
| `record_placement_strategy` | `publish_finding` | `record_placement_strategy` | Record the next strategy after a plateau. |
| `request_placement_decision` | `request_human_decision` | `request_placement_decision` | Ask a human to choose among legal placements. |

## Delegation

This lead may open child workflows/tasks against:

- [`placement_experiment`](../placement_experiment/) — Placement Experiment Worker (port **8244**)
- [`placement_evaluator`](../placement_evaluator/) — Independent Multi-Corner Placement Evaluator (port **8245**)
- [`boundary_coordinator`](../boundary_coordinator/) — Cross-Partition Boundary Coordinator (port **8246**)

Delegation is declarative in `delegates_to`. The lead's `request_*` / `open_*` skills tell the orchestrator which child agent id and skill to schedule next; workers do not call each other directly over HTTP.

Independent validators configured for this agent:

- [`placement_evaluator`](../placement_evaluator/) (port **8245**)

## Boot path

Every fleet agent shares the same linear startup so compose and local dev behave identically.

1. Container or shell runs `python server.py` (`deployment.dockerfile` / image `agentfleet/placement_lead:1.0`).
2. `server.py` prepends this directory to `sys.path`, imports `PlacementLeadAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, PlacementLeadAgent)`.
3. Importing `agent.py` sets `spec = EDAAgent.read_spec(<this directory>)`, loading `config.yaml` at class definition time.
4. Uvicorn serves FastAPI `app` on `connection.port` with `/health` and `/tasks/execute`.
5. On `/tasks/execute`, `EDAAgent.handle` assembles engineering-memory context (see `context` in YAML), journals the task, and dispatches the requested skill.
6. The skill callable in `tools.py` returns `tool_observation(...)`. With `backend.type: none`, observations are safe stubs (`not_run`) until `EDA_FRAMEWORK` or another adapter binds real engines.

## Related agents

- Stage index: [`../README.md`](../README.md) (placement specialists under `placement/`).
- Program orchestrator:
  - [`chip_flow_lead`](../../../chip_flow_lead/) (port **8201**)
- Sibling agents in this folder:
  - [`boundary_coordinator`](../boundary_coordinator/) — worker, port **8246**
  - [`placement_evaluator`](../placement_evaluator/) — validator, port **8245**
  - [`placement_experiment`](../placement_experiment/) — worker, port **8244**
- Track overview: [`../../README.md`](../../README.md) (backend physical implementation).

## Files in this directory

| File | Role |
|------|------|
| `agent.py` | Defines `PlacementLeadAgent`; loads sibling `config.yaml` into `spec`. |
| `server.py` | HTTP/ASGI bootstrap; exports FastAPI `app` for uvicorn. |
| `tools.py` | `@tool` skill callables; stable EDA operation contracts. |
| `config.yaml` | Fleet manifest (`apiVersion: agentfleet/v1`): boundaries, port, skills, memory, telemetry. |
| `Dockerfile` | Container image; `EXPOSE 8243`; `CMD python server.py`. |
| `requirements.txt` | FastAPI, uvicorn, pydantic, PyYAML for the HTTP surface. |
| `__init__.py` | Re-exports `PlacementLeadAgent` for imports without starting HTTP. |
| `README.md` | This document. |

## Tool reference

### `plan_placement_trials` (`tools.plan_placement_trials`)

**Action:** `create_workflow`. Emit the placement and evaluation workflow.

Plan the set of placement experiment trials for this partition.

### `request_placement_trial` (`tools.request_placement_trial`)

**Action:** `create_workflow`. Open one isolated placement strategy.

Dispatch one placement experiment worker with a hypothesis.

### `request_placement_evaluation` (`tools.request_placement_evaluation`)

**Action:** `create_workflow`. Hand a candidate to the multi-corner evaluator.

Ask the multi-corner evaluator to grade a placement candidate.

### `request_boundary_check` (`tools.request_boundary_check`)

**Action:** `create_workflow`. Open a cross-partition boundary check.

Ask the boundary coordinator to check abutting partition interfaces.

### `read_qualified_floorplan` (`tools.read_qualified_floorplan`)

**Action:** `read_reports`. Read the floorplan this placement inherits.

Read the floorplan inputs that placement is allowed to consume.

### `read_placement_metrics` (`tools.read_placement_metrics`)

**Action:** `read_reports`. Read timing, congestion, power, and legality for each trial.

Read HPWL, density, congestion, and timing metrics for candidates.

### `read_corner_coverage` (`tools.read_corner_coverage`)

**Action:** `read_reports`. Read which modes and corners each trial has been scored on.

Read which PVT corners/modes have been evaluated.

### `compare_placement_trials` (`tools.compare_placement_trials`)

**Action:** `read_reports`. Rank trials that are legal in every required corner.

Compare placement trial metrics and evaluator grades.

### `recommend_placement_candidate` (`tools.recommend_placement_candidate`)

**Action:** `publish_finding`. Record which legal candidate should advance. This does not promote it.

Recommend which placement candidate should advance.

### `flag_corner_shifted_violation` (`tools.flag_corner_shifted_violation`)

**Action:** `publish_finding`. Publish a gain that moved a violation into another corner.

Finding: an apparent gain only moved violations to another corner.

### `record_placement_strategy` (`tools.record_placement_strategy`)

**Action:** `publish_finding`. Record the next strategy after a plateau.

Journal placement strategy and trial matrix for provenance.

### `request_placement_decision` (`tools.request_placement_decision`)

**Action:** `request_human_decision`. Ask a human to choose among legal placements.

Request an explicit decision on which placement proceeds.

## Runtime, memory, and context

- **Reliability:** task timeout 120s, max retries 1, on failure `replan`.
- **Execution:** `direct_function`, `max_tasks=1`.
- **Context include:** `gates`, `workflows`, `open_findings`, `decisions`, `experiments`.
- **Context exclude:** `stale_candidates`.
- **Token budget:** 80000.
- **Telemetry:** heartbeat every 5s; streams: skill_calls, artifacts.

## Operational notes

- **Promotion / signoff:** Boundaries forbid treating this agent's summary as independent signoff unless `role: validator` and the workflow explicitly schedules it.
- **Adapters:** Set `EDA_FRAMEWORK` / `backend.type` when wiring OpenROAD, Yosys, OpenSTA, simulators, or licensed signoff tools; until then skills return structured `not_run` observations.
- **Shared base:** Task handling lives in `domains/eda/runtime/agent.py`; HTTP wiring in `domains/eda/runtime/server.py`.
- **Telemetry:** See [`../../TELEMETRY.md`](../../TELEMETRY.md) (path may vary by depth) for fleet-wide observability conventions.

## How a newcomer should read this agent

1. Read `config.yaml` `metadata`, `boundary`, and `capabilities` for charter and limits.
2. Skim the skills table above, then open `tools.py` for parameter shapes.
3. Read `agent.py` and `server.py` only to confirm boot wiring.
4. Treat `Dockerfile` / `requirements.txt` as deployment detail.
