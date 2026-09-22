# Performance Modeling Agent (`performance_modeling`)

This directory is the deployable microservice package for the **Performance Modeling Agent** in the fleet **architecture** stage (role `worker`).

## EDA responsibility

Performance Modeling Agent — agent class entry point.

Charter from `config.yaml`: Model target workloads and bottlenecks, and report projected metrics with their assumptions.

As a **worker**, this process executes bounded skills on isolated candidates and reports observations. Promotion and program-level tradeoffs stay with leads and humans.

## Identity and HTTP port

| Field | Value |
|-------|-------|
| Agent id | `performance_modeling` |
| Stage | `architecture` |
| Role | `worker` |
| Host | `host.docker.internal` |
| Port | **8204** (must match `Dockerfile` `EXPOSE`) |
| Health | `/health` |
| Execute | `/tasks/execute` |

## Boundaries

Hard limits from `config.yaml` `boundary`. The planner and `EdaAgent` enforce these even when a tool adapter could physically perform a forbidden action.

### May

- Read workload descriptions and interface contracts
- Write a performance model into an isolated candidate
- Publish a bottleneck finding with the model artifact

### May not

- Change the requirement set
- Claim a projection is a measured result
- Promote a candidate onto the canonical baseline
- Approve a waiver or relax a hard requirement
- Treat its own summary as independent signoff

## Skills

Skills bind planner task ids to callables in `tools.py` (`module: tools`, `execution.mode: direct_function`).

| Skill id | Action | Callable | Description |
|----------|--------|----------|-------------|
| `characterize_workload` | `read_reports` | `characterize_workload` | Summarize traffic, data sizes, and latency bounds for one workload. |
| `write_performance_model` | `write_candidate` | `write_performance_model` | Write an executable performance model for one architecture candidate. |
| `set_model_assumption` | `write_candidate` | `set_model_assumption` | Record one assumption the model depends on. |
| `run_performance_model` | `submit_tool_job` | `run_performance_model` | Execute the bound performance model and record projected metrics. |
| `sweep_model_parameter` | `submit_tool_job` | `sweep_model_parameter` | Rerun the model over one parameter range. |
| `read_projected_metrics` | `read_reports` | `read_projected_metrics` | Read throughput, latency, and utilization from a model run. |
| `read_sensitivity` | `read_reports` | `read_sensitivity` | Read how a projected metric moves when one assumption changes. |
| `compare_model_to_requirement` | `read_reports` | `compare_model_to_requirement` | Compare projected metrics with the numeric requirement. |
| `report_bottlenecks` | `publish_finding` | `report_bottlenecks` | Publish the dominant throughput or latency limiters. |
| `report_model_uncertainty` | `publish_finding` | `report_model_uncertainty` | Publish which projections are sensitive to an unmeasured assumption. |
| `flag_model_requirement_miss` | `publish_finding` | `flag_model_requirement_miss` | Publish a requirement the model says the candidate misses. |
| `record_model_version` | `publish_finding` | `record_model_version` | Record the model source, inputs, and version used for a projection. |

## Delegation

This agent declares **no** `delegates_to` entries. It executes its own `tools.py` skills when scheduled by a lead or the chip-flow orchestrator.

## Boot path

Every fleet agent shares the same linear startup so compose and local dev behave identically.

1. Container or shell runs `python server.py` (`deployment.dockerfile` / image `agentfleet/performance_modeling:1.0`).
2. `server.py` prepends this directory to `sys.path`, imports `PerformanceModelingAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, PerformanceModelingAgent)`.
3. Importing `agent.py` sets `spec = EdaAgent.read_spec(<this directory>)`, loading `config.yaml` at class definition time.
4. Uvicorn serves FastAPI `app` on `connection.port` with `/health` and `/tasks/execute`.
5. On `/tasks/execute`, `EdaAgent.handle` assembles engineering-memory context (see `context` in YAML), journals the task, and dispatches the requested skill.
6. The skill callable in `tools.py` returns `tool_observation(...)`. With `backend.type: none`, observations are safe stubs (`not_run`) until `EDA_FRAMEWORK` or another adapter binds real engines.

## Related agents

- Stage index: [`../README.md`](../README.md) (architecture specialists under `architecture/`).
- Stage lead(s) that delegate here:
  - [`architecture_lead`](../architecture_lead/) (port **8203**)
- Sibling agents in this folder:
  - [`architecture_lead`](../architecture_lead/) — lead, port **8203**
  - [`interface`](../interface/) — worker, port **8205**
  - [`power_area_estimation`](../power_area_estimation/) — worker, port **8206**
  - [`requirements`](../requirements/) — worker, port **8202**
  - [`security_reliability`](../security_reliability/) — worker, port **8207**
- Track overview: [`../../README.md`](../../README.md) (frontend architecture, RTL, verification).

## Files in this directory

| File | Role |
|------|------|
| `agent.py` | Defines `PerformanceModelingAgent`; loads sibling `config.yaml` into `spec`. |
| `server.py` | HTTP/ASGI bootstrap; exports FastAPI `app` for uvicorn. |
| `tools.py` | `@tool` skill callables; stable EDA operation contracts. |
| `config.yaml` | Fleet manifest (`apiVersion: agentfleet/v1`): boundaries, port, skills, memory, telemetry. |
| `Dockerfile` | Container image; `EXPOSE 8204`; `CMD python server.py`. |
| `requirements.txt` | FastAPI, uvicorn, pydantic, PyYAML for the HTTP surface. |
| `__init__.py` | Re-exports `PerformanceModelingAgent` for imports without starting HTTP. |
| `README.md` | This document. |

## Tool reference

### `characterize_workload` (`tools.characterize_workload`)

**Action:** `read_reports`. Summarize traffic, data sizes, and latency bounds for one workload.

### `write_performance_model` (`tools.write_performance_model`)

**Action:** `write_candidate`. Write an executable performance model for one architecture candidate.

### `set_model_assumption` (`tools.set_model_assumption`)

**Action:** `write_candidate`. Record one assumption the model depends on.

### `run_performance_model` (`tools.run_performance_model`)

**Action:** `submit_tool_job`. Execute the bound performance model and record projected metrics.

### `sweep_model_parameter` (`tools.sweep_model_parameter`)

**Action:** `submit_tool_job`. Rerun the model over one parameter range.

### `read_projected_metrics` (`tools.read_projected_metrics`)

**Action:** `read_reports`. Read throughput, latency, and utilization from a model run.

### `read_sensitivity` (`tools.read_sensitivity`)

**Action:** `read_reports`. Read how a projected metric moves when one assumption changes.

### `compare_model_to_requirement` (`tools.compare_model_to_requirement`)

**Action:** `read_reports`. Compare projected metrics with the numeric requirement.

### `report_bottlenecks` (`tools.report_bottlenecks`)

**Action:** `publish_finding`. Publish the dominant throughput or latency limiters.

### `report_model_uncertainty` (`tools.report_model_uncertainty`)

**Action:** `publish_finding`. Publish which projections are sensitive to an unmeasured assumption.

### `flag_model_requirement_miss` (`tools.flag_model_requirement_miss`)

**Action:** `publish_finding`. Publish a requirement the model says the candidate misses.

### `record_model_version` (`tools.record_model_version`)

**Action:** `publish_finding`. Record the model source, inputs, and version used for a projection.

## Runtime, memory, and context

- **Reliability:** task timeout 120s, max retries 1, on failure `replan`.
- **Execution:** `direct_function`, `max_tasks=1`.
- **Context include:** `human_intent`, `requirements`, `interface_contracts`, `decisions`, `open_findings`.
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
