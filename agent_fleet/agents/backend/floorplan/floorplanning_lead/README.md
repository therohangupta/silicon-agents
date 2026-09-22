# Floorplanning Lead (`floorplanning_lead`)

This directory is the deployable microservice package for the **Floorplanning Lead** in the fleet **floorplan** stage (role `lead`).

## EDA responsibility

Emit the floorplan workflow for this partition.

Charter from `config.yaml`: Own macro, pin, power-grid, blockage, and utilization decisions for one partition, and recommend a candidate for placement.

As a **lead**, this process publishes workflows, reads qualified upstream artifacts, opens child agent tasks, compares candidates, and recommends next steps. It does **not** promote the canonical baseline or act as independent signoff.

## Identity and HTTP port

| Field | Value |
|-------|-------|
| Agent id | `floorplanning_lead` |
| Stage | `floorplan` |
| Role | `lead` |
| Host | `host.docker.internal` |
| Port | **8238** (must match `Dockerfile` `EXPOSE`) |
| Health | `/health` |
| Execute | `/tasks/execute` |

## Boundaries

Hard limits from `config.yaml` `boundary`. The planner and `EdaAgent` enforce these even when a tool adapter could physically perform a forbidden action.

### May

- Publish a floorplan exploration workflow
- Read the netlist, constraints, and package contract
- Request an upstream decision when the floorplan is infeasible

### May not

- Edit RTL when the floorplan is infeasible
- Advance a candidate that breaks a hard physical limit
- Promote a floorplan
- Promote a candidate onto the canonical baseline
- Approve a waiver or relax a hard requirement
- Treat its own summary as independent signoff

## Skills

Skills bind planner task ids to callables in `tools.py` (`module: tools`, `execution.mode: direct_function`).

| Skill id | Action | Callable | Description |
|----------|--------|----------|-------------|
| `plan_floorplan_exploration` | `create_workflow` | `plan_floorplan_exploration` | Emit the floorplan workflow for this partition. |
| `request_macro_alternatives` | `create_workflow` | `request_macro_alternatives` | Open another macro-placement batch with one changed constraint. |
| `request_pin_assignment` | `create_workflow` | `request_pin_assignment` | Open pin assignment for the current macro candidate. |
| `request_power_grid` | `create_workflow` | `request_power_grid` | Open an early power-grid candidate. |
| `request_early_physical_estimate` | `create_workflow` | `request_early_physical_estimate` | Open trial placement, global route, and early timing. |
| `read_floorplan_inputs` | `read_reports` | `read_floorplan_inputs` | Read die, utilization, macros, constraints, and package contract. |
| `read_floorplan_metrics` | `read_reports` | `read_floorplan_metrics` | Read congestion, early timing, pin density, and IR proxy for each candidate. |
| `compare_floorplan_candidates` | `read_reports` | `compare_floorplan_candidates` | Rank candidates that satisfy hard physical limits. |
| `recommend_floorplan_candidate` | `publish_finding` | `recommend_floorplan_candidate` | Record which floorplan should advance to placement. This does not promote it. |
| `request_floorplan_upstream_change` | `publish_finding` | `request_floorplan_upstream_change` | Publish evidence when pin density or hierarchy makes the floorplan infeasible. |
| `flag_hard_physical_limit` | `publish_finding` | `flag_hard_physical_limit` | Publish a candidate that breaks a keepout, pin-density, or IR limit. |
| `record_floorplan_strategy` | `publish_finding` | `record_floorplan_strategy` | Record which physical variable the next batch will change. |
| `request_floorplan_decision` | `request_human_decision` | `request_floorplan_decision` | Ask a human to choose among feasible floorplans or to change an upstream contract. |

## Delegation

This lead may open child workflows/tasks against:

- [`macro_placement`](../macro_placement/) — Macro-Placement Experiment Worker (port **8239**)
- [`pin_assignment`](../pin_assignment/) — Pin-Assignment Agent (port **8240**)
- [`power_grid`](../power_grid/) — Power-Grid Agent (port **8241**)
- [`early_congestion_timing`](../early_congestion_timing/) — Early Congestion and Timing Evaluator (port **8242**)

Delegation is declarative in `delegates_to`. The lead's `request_*` / `open_*` skills tell the orchestrator which child agent id and skill to schedule next; workers do not call each other directly over HTTP.

## Boot path

Every fleet agent shares the same linear startup so compose and local dev behave identically.

1. Container or shell runs `python server.py` (`deployment.dockerfile` / image `agentfleet/floorplanning_lead:1.0`).
2. `server.py` prepends this directory to `sys.path`, imports `FloorplanningLeadAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, FloorplanningLeadAgent)`.
3. Importing `agent.py` sets `spec = EdaAgent.read_spec(<this directory>)`, loading `config.yaml` at class definition time.
4. Uvicorn serves FastAPI `app` on `connection.port` with `/health` and `/tasks/execute`.
5. On `/tasks/execute`, `EdaAgent.handle` assembles engineering-memory context (see `context` in YAML), journals the task, and dispatches the requested skill.
6. The skill callable in `tools.py` returns `tool_observation(...)`. With `backend.type: none`, observations are safe stubs (`not_run`) until `EDA_FRAMEWORK` or another adapter binds real engines.

## Related agents

- Stage index: [`../README.md`](../README.md) (floorplan specialists under `floorplan/`).
- Program orchestrator:
  - [`chip_flow_lead`](../../../chip_flow_lead/) (port **8201**)
- Sibling agents in this folder:
  - [`early_congestion_timing`](../early_congestion_timing/) — worker, port **8242**
  - [`macro_placement`](../macro_placement/) — worker, port **8239**
  - [`pin_assignment`](../pin_assignment/) — worker, port **8240**
  - [`power_grid`](../power_grid/) — worker, port **8241**
- Track overview: [`../../README.md`](../../README.md) (backend physical implementation).

## Files in this directory

| File | Role |
|------|------|
| `agent.py` | Defines `FloorplanningLeadAgent`; loads sibling `config.yaml` into `spec`. |
| `server.py` | HTTP/ASGI bootstrap; exports FastAPI `app` for uvicorn. |
| `tools.py` | `@tool` skill callables; stable EDA operation contracts. |
| `config.yaml` | Fleet manifest (`apiVersion: agentfleet/v1`): boundaries, port, skills, memory, telemetry. |
| `Dockerfile` | Container image; `EXPOSE 8238`; `CMD python server.py`. |
| `requirements.txt` | FastAPI, uvicorn, pydantic, PyYAML for the HTTP surface. |
| `__init__.py` | Re-exports `FloorplanningLeadAgent` for imports without starting HTTP. |
| `README.md` | This document. |

## Tool reference

### `plan_floorplan_exploration` (`tools.plan_floorplan_exploration`)

**Action:** `create_workflow`. Emit the floorplan workflow for this partition.

### `request_macro_alternatives` (`tools.request_macro_alternatives`)

**Action:** `create_workflow`. Open another macro-placement batch with one changed constraint.

### `request_pin_assignment` (`tools.request_pin_assignment`)

**Action:** `create_workflow`. Open pin assignment for the current macro candidate.

### `request_power_grid` (`tools.request_power_grid`)

**Action:** `create_workflow`. Open an early power-grid candidate.

### `request_early_physical_estimate` (`tools.request_early_physical_estimate`)

**Action:** `create_workflow`. Open trial placement, global route, and early timing.

### `read_floorplan_inputs` (`tools.read_floorplan_inputs`)

**Action:** `read_reports`. Read die, utilization, macros, constraints, and package contract.

### `read_floorplan_metrics` (`tools.read_floorplan_metrics`)

**Action:** `read_reports`. Read congestion, early timing, pin density, and IR proxy for each candidate.

### `compare_floorplan_candidates` (`tools.compare_floorplan_candidates`)

**Action:** `read_reports`. Rank candidates that satisfy hard physical limits.

### `recommend_floorplan_candidate` (`tools.recommend_floorplan_candidate`)

**Action:** `publish_finding`. Record which floorplan should advance to placement. This does not promote it.

### `request_floorplan_upstream_change` (`tools.request_floorplan_upstream_change`)

**Action:** `publish_finding`. Publish evidence when pin density or hierarchy makes the floorplan infeasible.

### `flag_hard_physical_limit` (`tools.flag_hard_physical_limit`)

**Action:** `publish_finding`. Publish a candidate that breaks a keepout, pin-density, or IR limit.

### `record_floorplan_strategy` (`tools.record_floorplan_strategy`)

**Action:** `publish_finding`. Record which physical variable the next batch will change.

### `request_floorplan_decision` (`tools.request_floorplan_decision`)

**Action:** `request_human_decision`. Ask a human to choose among feasible floorplans or to change an upstream contract.

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
- **Shared base:** Task handling lives in `domains/eda/agent.py`; HTTP wiring in `domains/eda/server.py`.
- **Telemetry:** See [`../../TELEMETRY.md`](../../TELEMETRY.md) (path may vary by depth) for fleet-wide observability conventions.

## How a newcomer should read this agent

1. Read `config.yaml` `metadata`, `boundary`, and `capabilities` for charter and limits.
2. Skim the skills table above, then open `tools.py` for parameter shapes.
3. Read `agent.py` and `server.py` only to confirm boot wiring.
4. Treat `Dockerfile` / `requirements.txt` as deployment detail.
