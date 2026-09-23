# STA Lead (`sta_lead`)

This directory is the deployable microservice package for the **STA Lead** in the fleet **signoff** stage (role `lead`).

## EDA responsibility

Own multi-mode multi-corner static timing. Classify failures, trace causes, and coordinate bounded repairs.

As a **lead**, this process publishes workflows, reads qualified upstream artifacts, opens child agent tasks, compares candidates, and recommends next steps. It does **not** promote the canonical baseline or act as independent signoff.

## Identity and HTTP port

| Field | Value |
|-------|-------|
| Agent id | `sta_lead` |
| Stage | `signoff` |
| Role | `lead` |
| Host | `host.docker.internal` |
| Port | **8255** (must match `Dockerfile` `EXPOSE`) |
| Health | `/health` |
| Execute | `/tasks/execute` |

## Boundaries

Hard limits from `config.yaml` `boundary`. The planner and `EDAAgent` enforce these even when a tool adapter could physically perform a forbidden action.

### May

- Publish a timing-debug workflow
- Read extracted parasitics and constraints
- Request a human decision on a timing tradeoff

### May not

- Change a constraint to close timing
- Accept a single-corner report as signoff
- Promote a timing ECO
- Promote a candidate onto the canonical baseline
- Approve a waiver or relax a hard requirement
- Treat its own summary as independent signoff

## Skills

Skills bind planner task ids to callables in `tools.py` (`module: tools`, `execution.mode: direct_function`).

| Skill id | Action | Callable | Description |
|----------|--------|----------|-------------|
| `plan_timing_closure` | `create_workflow` | `plan_timing_closure` | Emit the timing-debug workflow for the open violations. |
| `request_path_group_debug` | `create_workflow` | `request_path_group_debug` | Open debug for one path group and check type. |
| `request_timing_corner_sweep` | `create_workflow` | `request_timing_corner_sweep` | Open STA across the required modes and corners. |
| `read_mmmc_status` | `read_reports` | `read_mmmc_status` | Read which modes and corners have reports. |
| `read_worst_paths` | `read_reports` | `read_worst_paths` | Read the worst setup and hold paths. |
| `read_timing_constraints_in_force` | `read_reports` | `read_timing_constraints_in_force` | Read the constraints the current STA used. |
| `request_timing_repair` | `publish_finding` | `request_timing_repair` | Send a classified path group to the owner who can change it. |
| `flag_single_corner_signoff` | `publish_finding` | `flag_single_corner_signoff` | Publish a signoff claim that is missing a required corner. |
| `flag_constraint_edit_request` | `publish_finding` | `flag_constraint_edit_request` | Publish a proposed constraint edit so a human can judge it. This agent does not apply it. |
| `record_timing_strategy` | `publish_finding` | `record_timing_strategy` | Record which path group the next repair will target. |
| `recommend_timing_candidate` | `publish_finding` | `recommend_timing_candidate` | Record which repaired candidate should be rechecked. This does not promote it. |
| `request_timing_decision` | `request_human_decision` | `request_timing_decision` | Ask a human to accept a remaining violation or change a constraint. |

## Delegation

This lead may open child workflows/tasks against:

- [`timing_debug`](../timing_debug/) — Timing-Debug Agent (port **8256**)

Delegation is declarative in `delegates_to`. The lead's `request_*` / `open_*` skills tell the orchestrator which child agent id and skill to schedule next; workers do not call each other directly over HTTP.

## Boot path

Every fleet agent shares the same linear startup so compose and local dev behave identically.

1. Container or shell runs `python server.py` (`deployment.dockerfile` / image `agentfleet/sta_lead:1.0`).
2. `server.py` prepends this directory to `sys.path`, imports `StaLeadAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, StaLeadAgent)`.
3. Importing `agent.py` sets `spec = EDAAgent.read_spec(<this directory>)`, loading `config.yaml` at class definition time.
4. Uvicorn serves FastAPI `app` on `connection.port` with `/health` and `/tasks/execute`.
5. On `/tasks/execute`, `EDAAgent.handle` assembles engineering-memory context (see `context` in YAML), journals the task, and dispatches the requested skill.
6. The skill callable in `tools.py` returns `tool_observation(...)`. With `backend.type: none`, observations are safe stubs (`not_run`) until `EDA_FRAMEWORK` or another adapter binds real engines.

## Related agents

- Stage index: [`../README.md`](../README.md) (signoff specialists under `signoff/`).
- Program orchestrator:
  - [`chip_flow_lead`](../../../chip_flow_lead/) (port **8201**)
- Sibling agents in this folder:
  - [`drc_lvs`](../drc_lvs/) — worker, port **8260**
  - [`eco_lead`](../eco_lead/) — lead, port **8261**
  - [`extraction`](../extraction/) — worker, port **8254**
  - [`ir_em`](../ir_em/) — worker, port **8258**
  - [`power_analysis`](../power_analysis/) — worker, port **8257**
  - [`signoff_validator`](../signoff_validator/) — validator, port **8262**
  - [`thermal_reliability`](../thermal_reliability/) — worker, port **8259**
  - [`timing_debug`](../timing_debug/) — worker, port **8256**
- Track overview: [`../../README.md`](../../README.md) (backend physical implementation).

## Files in this directory

| File | Role |
|------|------|
| `agent.py` | Defines `StaLeadAgent`; loads sibling `config.yaml` into `spec`. |
| `server.py` | HTTP/ASGI bootstrap; exports FastAPI `app` for uvicorn. |
| `tools.py` | `@tool` skill callables; stable EDA operation contracts. |
| `config.yaml` | Fleet manifest (`apiVersion: agentfleet/v1`): boundaries, port, skills, memory, telemetry. |
| `Dockerfile` | Container image; `EXPOSE 8255`; `CMD python server.py`. |
| `requirements.txt` | FastAPI, uvicorn, pydantic, PyYAML for the HTTP surface. |
| `__init__.py` | Re-exports `StaLeadAgent` for imports without starting HTTP. |
| `README.md` | This document. |

## Tool reference

### `plan_timing_closure` (`tools.plan_timing_closure`)

**Action:** `create_workflow`. Emit the timing-debug workflow for the open violations.

### `request_path_group_debug` (`tools.request_path_group_debug`)

**Action:** `create_workflow`. Open debug for one path group and check type.

### `request_timing_corner_sweep` (`tools.request_timing_corner_sweep`)

**Action:** `create_workflow`. Open STA across the required modes and corners.

### `read_mmmc_status` (`tools.read_mmmc_status`)

**Action:** `read_reports`. Read which modes and corners have reports.

### `read_worst_paths` (`tools.read_worst_paths`)

**Action:** `read_reports`. Read the worst setup and hold paths.

### `read_timing_constraints_in_force` (`tools.read_timing_constraints_in_force`)

**Action:** `read_reports`. Read the constraints the current STA used.

### `request_timing_repair` (`tools.request_timing_repair`)

**Action:** `publish_finding`. Send a classified path group to the owner who can change it.

### `flag_single_corner_signoff` (`tools.flag_single_corner_signoff`)

**Action:** `publish_finding`. Publish a signoff claim that is missing a required corner.

### `flag_constraint_edit_request` (`tools.flag_constraint_edit_request`)

**Action:** `publish_finding`. Publish a proposed constraint edit so a human can judge it. This agent does not apply it.

### `record_timing_strategy` (`tools.record_timing_strategy`)

**Action:** `publish_finding`. Record which path group the next repair will target.

### `recommend_timing_candidate` (`tools.recommend_timing_candidate`)

**Action:** `publish_finding`. Record which repaired candidate should be rechecked. This does not promote it.

### `request_timing_decision` (`tools.request_timing_decision`)

**Action:** `request_human_decision`. Ask a human to accept a remaining violation or change a constraint.

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
