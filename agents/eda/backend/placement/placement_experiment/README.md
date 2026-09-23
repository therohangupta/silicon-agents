# Placement Experiment Worker (`placement_experiment`)

This directory is the deployable microservice package for the **Placement Experiment Worker** in the fleet **placement** stage (role `worker`).

## EDA responsibility

Tools for the Placement Experiment Worker.

Charter from `config.yaml`: Run one placement, legalization, buffering, and sizing strategy in an isolated workspace. Adapter target: OpenROAD global and detailed placement.

As a **worker**, this process executes bounded skills on isolated candidates and reports observations. Promotion and program-level tradeoffs stay with leads and humans.

## Identity and HTTP port

| Field | Value |
|-------|-------|
| Agent id | `placement_experiment` |
| Stage | `placement` |
| Role | `worker` |
| Host | `host.docker.internal` |
| Port | **8244** (must match `Dockerfile` `EXPOSE`) |
| Health | `/health` |
| Execute | `/tasks/execute` |

## Boundaries

Hard limits from `config.yaml` `boundary`. The planner and `EDAAgent` enforce these even when a tool adapter could physically perform a forbidden action.

### May

- Submit one placement job
- Write placement directives
- Return multi-metric results with tool version

### May not

- Edit the shared placement database
- Drop a mode from the report
- Promote a candidate onto the canonical baseline
- Approve a waiver or relax a hard requirement
- Treat its own summary as independent signoff

## Skills

Skills bind planner task ids to callables in `tools.py` (`module: tools`, `execution.mode: direct_function`).

| Skill id | Action | Callable | Description |
|----------|--------|----------|-------------|
| `write_placement_directives` | `write_candidate` | `write_placement_directives` | Write density, padding, and dont-use directives for this trial. |
| `set_placement_padding` | `write_candidate` | `set_placement_padding` | Set padding for one cell class. Adapter target: OpenROAD set_placement_padding. |
| `set_dont_use` | `write_candidate` | `set_dont_use` | Mark library cells this trial must not use. |
| `run_global_placement` | `submit_tool_job` | `run_global_placement` | Run global placement. Adapter target: OpenROAD global_placement. |
| `run_detailed_placement` | `submit_tool_job` | `run_detailed_placement` | Run detailed placement and legalization. Adapter target: OpenROAD detailed_placement. |
| `optimize_mirroring` | `submit_tool_job` | `optimize_mirroring` | Run mirror optimization. Adapter target: OpenROAD optimize_mirroring. |
| `improve_placement` | `submit_tool_job` | `improve_placement` | Run a detailed-placement improvement pass. |
| `repair_placement_design` | `submit_tool_job` | `repair_placement_design` | Insert buffers and resize on the isolated candidate. Adapter target: OpenROAD repair_design. |
| `repair_placement_timing` | `submit_tool_job` | `repair_placement_timing` | Run a timing repair pass on the isolated candidate. Adapter target: OpenROAD repair_timing. |
| `run_placement_trial` | `submit_tool_job` | `run_placement_trial` | Place, legalize, and size one candidate as a single job. |
| `check_placement_legality` | `submit_tool_job` | `check_placement_legality` | Check overlap, row alignment, and site rules. Adapter target: OpenROAD check_placement. |
| `summarize_placement_metrics` | `read_reports` | `summarize_placement_metrics` | Return timing, congestion, power, and legality for the trial. |
| `report_placement_wns` | `read_reports` | `report_placement_wns` | Report WNS and TNS for the modes this trial ran. |
| `report_placement_density` | `read_reports` | `report_placement_density` | Report density and overflow. |
| `write_placement_def` | `write_candidate` | `write_placement_def` | Write the placed DEF. |
| `record_placement_provenance` | `publish_finding` | `record_placement_provenance` | Record tool, version, directives, and modes actually run. |

## Delegation

This agent declares **no** `delegates_to` entries. It executes its own `tools.py` skills when scheduled by a lead or the chip-flow orchestrator.

## Boot path

Every fleet agent shares the same linear startup so compose and local dev behave identically.

1. Container or shell runs `python server.py` (`deployment.dockerfile` / image `agentfleet/placement_experiment:1.0`).
2. `server.py` prepends this directory to `sys.path`, imports `PlacementExperimentAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, PlacementExperimentAgent)`.
3. Importing `agent.py` sets `spec = EDAAgent.read_spec(<this directory>)`, loading `config.yaml` at class definition time.
4. Uvicorn serves FastAPI `app` on `connection.port` with `/health` and `/tasks/execute`.
5. On `/tasks/execute`, `EDAAgent.handle` assembles engineering-memory context (see `context` in YAML), journals the task, and dispatches the requested skill.
6. The skill callable in `tools.py` returns `tool_observation(...)`. With `backend.type: none`, observations are safe stubs (`not_run`) until `EDA_FRAMEWORK` or another adapter binds real engines.

## Related agents

- Stage index: [`../README.md`](../README.md) (placement specialists under `placement/`).
- Stage lead(s) that delegate here:
  - [`placement_lead`](../placement_lead/) (port **8243**)
- Sibling agents in this folder:
  - [`boundary_coordinator`](../boundary_coordinator/) — worker, port **8246**
  - [`placement_evaluator`](../placement_evaluator/) — validator, port **8245**
  - [`placement_lead`](../placement_lead/) — lead, port **8243**
- Track overview: [`../../README.md`](../../README.md) (backend physical implementation).

## Files in this directory

| File | Role |
|------|------|
| `agent.py` | Defines `PlacementExperimentAgent`; loads sibling `config.yaml` into `spec`. |
| `server.py` | HTTP/ASGI bootstrap; exports FastAPI `app` for uvicorn. |
| `tools.py` | `@tool` skill callables; stable EDA operation contracts. |
| `config.yaml` | Fleet manifest (`apiVersion: agentfleet/v1`): boundaries, port, skills, memory, telemetry. |
| `Dockerfile` | Container image; `EXPOSE 8244`; `CMD python server.py`. |
| `requirements.txt` | FastAPI, uvicorn, pydantic, PyYAML for the HTTP surface. |
| `__init__.py` | Re-exports `PlacementExperimentAgent` for imports without starting HTTP. |
| `README.md` | This document. |

## Tool reference

### `write_placement_directives` (`tools.write_placement_directives`)

**Action:** `write_candidate`. Write density, padding, and dont-use directives for this trial.

Write density/region/guide directives for this placement trial.

### `set_placement_padding` (`tools.set_placement_padding`)

**Action:** `write_candidate`. Set padding for one cell class. Adapter target: OpenROAD set_placement_padding.

Set cell padding that reserves white space for later buffering.

### `set_dont_use` (`tools.set_dont_use`)

**Action:** `write_candidate`. Mark library cells this trial must not use.

Mark library cells as dont-use for this trial's sizing/legalization.

### `run_global_placement` (`tools.run_global_placement`)

**Action:** `submit_tool_job`. Run global placement. Adapter target: OpenROAD global_placement.

Run coarse global placement (OpenROAD global_placement).

### `run_detailed_placement` (`tools.run_detailed_placement`)

**Action:** `submit_tool_job`. Run detailed placement and legalization. Adapter target: OpenROAD detailed_placement.

Run detailed placement into legal sites (OpenROAD detailed_placement).

### `optimize_mirroring` (`tools.optimize_mirroring`)

**Action:** `submit_tool_job`. Run mirror optimization. Adapter target: OpenROAD optimize_mirroring.

Optimize cell mirroring/orientation for timing or congestion.

### `improve_placement` (`tools.improve_placement`)

**Action:** `submit_tool_job`. Run a detailed-placement improvement pass.

Run incremental placement improvement passes.

### `repair_placement_design` (`tools.repair_placement_design`)

**Action:** `submit_tool_job`. Insert buffers and resize on the isolated candidate. Adapter target: OpenROAD repair_design.

Repair overlapping/illegal cells after placement.

### `repair_placement_timing` (`tools.repair_placement_timing`)

**Action:** `submit_tool_job`. Run a timing repair pass on the isolated candidate. Adapter target: OpenROAD repair_timing.

Buffer/size to repair placement-stage timing violations.

### `run_placement_trial` (`tools.run_placement_trial`)

**Action:** `submit_tool_job`. Place, legalize, and size one candidate as a single job.

Orchestrate one full placement trial recipe end-to-end.

### `check_placement_legality` (`tools.check_placement_legality`)

**Action:** `submit_tool_job`. Check overlap, row alignment, and site rules. Adapter target: OpenROAD check_placement.

Check that all cells are on-site and non-overlapping.

### `summarize_placement_metrics` (`tools.summarize_placement_metrics`)

**Action:** `read_reports`. Return timing, congestion, power, and legality for the trial.

Summarize HPWL, density, congestion proxies for the trial.

### `report_placement_wns` (`tools.report_placement_wns`)

**Action:** `read_reports`. Report WNS and TNS for the modes this trial ran.

Report worst negative slack at placement stage.

### `report_placement_density` (`tools.report_placement_density`)

**Action:** `read_reports`. Report density and overflow.

Report local and global density for the trial.

### `write_placement_def` (`tools.write_placement_def`)

**Action:** `write_candidate`. Write the placed DEF.

Write the placed DEF/ODB candidate artifact.

### `record_placement_provenance` (`tools.record_placement_provenance`)

**Action:** `publish_finding`. Record tool, version, directives, and modes actually run.

Record OpenROAD recipe and directives used.

## Runtime, memory, and context

- **Reliability:** task timeout 120s, max retries 1, on failure `replan`.
- **Execution:** `direct_function`, `max_tasks=1`.
- **Context include:** `canonical_source`, `open_findings`, `experiments`, `gates`, `decisions`.
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
