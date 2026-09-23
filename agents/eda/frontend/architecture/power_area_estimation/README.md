# Power/Area Estimation Agent (`power_area_estimation`)

This directory is the deployable microservice package for the **Power/Area Estimation Agent** in the fleet **architecture** stage (role `worker`).

## EDA responsibility

Power/Area Estimation Agent — agent class entry point.

Charter from `config.yaml`: Produce early power and area estimates with explicit uncertainty and assumptions.

As a **worker**, this process executes bounded skills on isolated candidates and reports observations. Promotion and program-level tradeoffs stay with leads and humans.

## Identity and HTTP port

| Field | Value |
|-------|-------|
| Agent id | `power_area_estimation` |
| Stage | `architecture` |
| Role | `worker` |
| Host | `host.docker.internal` |
| Port | **8206** (must match `Dockerfile` `EXPOSE`) |
| Health | `/health` |
| Execute | `/tasks/execute` |

## Boundaries

Hard limits from `config.yaml` `boundary`. The planner and `EDAAgent` enforce these even when a tool adapter could physically perform a forbidden action.

### May

- Read architecture budgets and activity assumptions
- Publish an estimate with its uncertainty

### May not

- Treat an early estimate as signoff power
- Hide the activity assumption
- Promote a candidate onto the canonical baseline
- Approve a waiver or relax a hard requirement
- Treat its own summary as independent signoff

## Skills

Skills bind planner task ids to callables in `tools.py` (`module: tools`, `execution.mode: direct_function`).

| Skill id | Action | Callable | Description |
|----------|--------|----------|-------------|
| `collect_estimation_inputs` | `read_reports` | `collect_estimation_inputs` | Read area models, activity, library, and utilization assumptions. |
| `write_estimation_assumptions` | `write_candidate` | `write_estimation_assumptions` | Write the activity, library, and utilization assumptions for one estimate. |
| `estimate_area` | `submit_tool_job` | `estimate_area` | Produce an early area estimate and its uncertainty. |
| `estimate_power` | `submit_tool_job` | `estimate_power` | Produce an early dynamic and leakage estimate and its uncertainty. |
| `estimate_ppa` | `submit_tool_job` | `estimate_ppa` | Produce a combined power, performance, and area estimate. |
| `sweep_utilization` | `submit_tool_job` | `sweep_utilization` | Rerun the estimate across a utilization range. |
| `read_estimate` | `read_reports` | `read_estimate` | Read one stored early estimate and its assumptions. |
| `compare_estimate_to_budget` | `read_reports` | `compare_estimate_to_budget` | Compare an estimate with the block power and area budgets. |
| `record_assumptions` | `publish_finding` | `record_assumptions` | Publish the assumptions behind an estimate so a later stage can reject a stale one. |
| `flag_budget_risk` | `publish_finding` | `flag_budget_risk` | Publish an estimate that crosses a budget inside its uncertainty band. |
| `flag_stale_estimate` | `publish_finding` | `flag_stale_estimate` | Publish an estimate whose architecture revision is no longer current. |
| `record_estimate_lineage` | `publish_finding` | `record_estimate_lineage` | Record the model, activity file, and library used for an estimate. |

## Delegation

This agent declares **no** `delegates_to` entries. It executes its own `tools.py` skills when scheduled by a lead or the chip-flow orchestrator.

## Boot path

Every fleet agent shares the same linear startup so compose and local dev behave identically.

1. Container or shell runs `python server.py` (`deployment.dockerfile` / image `agentfleet/power_area_estimation:1.0`).
2. `server.py` prepends this directory to `sys.path`, imports `PowerAreaEstimationAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, PowerAreaEstimationAgent)`.
3. Importing `agent.py` sets `spec = EDAAgent.read_spec(<this directory>)`, loading `config.yaml` at class definition time.
4. Uvicorn serves FastAPI `app` on `connection.port` with `/health` and `/tasks/execute`.
5. On `/tasks/execute`, `EDAAgent.handle` assembles engineering-memory context (see `context` in YAML), journals the task, and dispatches the requested skill.
6. The skill callable in `tools.py` returns `tool_observation(...)`. With `backend.type: none`, observations are safe stubs (`not_run`) until `EDA_FRAMEWORK` or another adapter binds real engines.

## Related agents

- Stage index: [`../README.md`](../README.md) (architecture specialists under `architecture/`).
- Stage lead(s) that delegate here:
  - [`architecture_lead`](../architecture_lead/) (port **8203**)
- Sibling agents in this folder:
  - [`architecture_lead`](../architecture_lead/) — lead, port **8203**
  - [`interface`](../interface/) — worker, port **8205**
  - [`performance_modeling`](../performance_modeling/) — worker, port **8204**
  - [`requirements`](../requirements/) — worker, port **8202**
  - [`security_reliability`](../security_reliability/) — worker, port **8207**
- Track overview: [`../../README.md`](../../README.md) (frontend architecture, RTL, verification).

## Files in this directory

| File | Role |
|------|------|
| `agent.py` | Defines `PowerAreaEstimationAgent`; loads sibling `config.yaml` into `spec`. |
| `server.py` | HTTP/ASGI bootstrap; exports FastAPI `app` for uvicorn. |
| `tools.py` | `@tool` skill callables; stable EDA operation contracts. |
| `config.yaml` | Fleet manifest (`apiVersion: agentfleet/v1`): boundaries, port, skills, memory, telemetry. |
| `Dockerfile` | Container image; `EXPOSE 8206`; `CMD python server.py`. |
| `requirements.txt` | FastAPI, uvicorn, pydantic, PyYAML for the HTTP surface. |
| `__init__.py` | Re-exports `PowerAreaEstimationAgent` for imports without starting HTTP. |
| `README.md` | This document. |

## Tool reference

### `collect_estimation_inputs` (`tools.collect_estimation_inputs`)

**Action:** `read_reports`. Read area models, activity, library, and utilization assumptions.

### `write_estimation_assumptions` (`tools.write_estimation_assumptions`)

**Action:** `write_candidate`. Write the activity, library, and utilization assumptions for one estimate.

### `estimate_area` (`tools.estimate_area`)

**Action:** `submit_tool_job`. Produce an early area estimate and its uncertainty.

### `estimate_power` (`tools.estimate_power`)

**Action:** `submit_tool_job`. Produce an early dynamic and leakage estimate and its uncertainty.

### `estimate_ppa` (`tools.estimate_ppa`)

**Action:** `submit_tool_job`. Produce a combined power, performance, and area estimate.

### `sweep_utilization` (`tools.sweep_utilization`)

**Action:** `submit_tool_job`. Rerun the estimate across a utilization range.

### `read_estimate` (`tools.read_estimate`)

**Action:** `read_reports`. Read one stored early estimate and its assumptions.

### `compare_estimate_to_budget` (`tools.compare_estimate_to_budget`)

**Action:** `read_reports`. Compare an estimate with the block power and area budgets.

### `record_assumptions` (`tools.record_assumptions`)

**Action:** `publish_finding`. Publish the assumptions behind an estimate so a later stage can reject a stale one.

### `flag_budget_risk` (`tools.flag_budget_risk`)

**Action:** `publish_finding`. Publish an estimate that crosses a budget inside its uncertainty band.

### `flag_stale_estimate` (`tools.flag_stale_estimate`)

**Action:** `publish_finding`. Publish an estimate whose architecture revision is no longer current.

### `record_estimate_lineage` (`tools.record_estimate_lineage`)

**Action:** `publish_finding`. Record the model, activity file, and library used for an estimate.

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
- **Shared base:** Task handling lives in `domains/eda/runtime/agent.py`; HTTP wiring in `domains/eda/runtime/server.py`.
- **Telemetry:** See [`../../TELEMETRY.md`](../../TELEMETRY.md) (path may vary by depth) for fleet-wide observability conventions.

## How a newcomer should read this agent

1. Read `config.yaml` `metadata`, `boundary`, and `capabilities` for charter and limits.
2. Skim the skills table above, then open `tools.py` for parameter shapes.
3. Read `agent.py` and `server.py` only to confirm boot wiring.
4. Treat `Dockerfile` / `requirements.txt` as deployment detail.
