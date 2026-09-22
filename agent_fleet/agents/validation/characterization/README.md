# Characterization Agent (`characterization`)

This directory is the deployable microservice package for the **Characterization Agent** in the fleet **validation** stage (role `worker`).

## EDA responsibility

Characterization agent class (characterization).

Charter from `config.yaml`: Plan and execute voltage, frequency, temperature, and workload sweeps inside approved bounds, fit the operating envelope, and compare it with pre-silicon predictions.

As a **worker**, this process executes bounded skills on isolated candidates and reports observations. Promotion and program-level tradeoffs stay with leads and humans.

## Identity and HTTP port

| Field | Value |
|-------|-------|
| Agent id | `characterization` |
| Stage | `validation` |
| Role | `worker` |
| Host | `host.docker.internal` |
| Port | **8268** (must match `Dockerfile` `EXPOSE`) |
| Health | `/health` |
| Execute | `/tasks/execute` |

## Boundaries

Hard limits from `config.yaml` `boundary`. The planner and `EdaAgent` enforce these even when a tool adapter could physically perform a forbidden action.

### May

- Write a sweep plan
- Submit sweep points that sit inside approved bounds
- Publish an operating envelope

### May not

- Submit a point outside the approved bounds
- Drop an outlier to tighten a guardband
- Widen a safety bound
- Promote a candidate onto the canonical baseline
- Approve a waiver or relax a hard requirement
- Treat its own summary as independent signoff

## Skills

Skills bind planner task ids to callables in `tools.py` (`module: tools`, `execution.mode: direct_function`).

| Skill id | Action | Callable | Description |
|----------|--------|----------|-------------|
| `plan_pvt_sweep` | `write_candidate` | `plan_pvt_sweep` | Plan a voltage, frequency, temperature, and workload sweep. |
| `define_voltage_points` | `write_candidate` | `define_voltage_points` | Write the voltage points. Each point must sit inside the approved bound. |
| `define_frequency_points` | `write_candidate` | `define_frequency_points` | Write the frequency points. |
| `define_temperature_points` | `write_candidate` | `define_temperature_points` | Write the temperature points inside the approved bound. |
| `define_workload_points` | `write_candidate` | `define_workload_points` | Write the workloads the sweep will run. |
| `check_sweep_against_bounds` | `read_reports` | `check_sweep_against_bounds` | Check every point against the approved voltage, current, and temperature limits. |
| `submit_sweep_point` | `submit_tool_job` | `submit_sweep_point` | Submit one sweep point to the lab adapter. |
| `submit_sweep_batch` | `submit_tool_job` | `submit_sweep_batch` | Submit the approved points as one batch. |
| `read_sweep_measurements` | `read_reports` | `read_sweep_measurements` | Read measured shmoo and workload results, including outliers. |
| `fit_operating_envelope` | `publish_finding` | `fit_operating_envelope` | Fit the measured envelope and the guardband. Outliers stay in the fit. |
| `compare_with_presilicon` | `publish_finding` | `compare_with_presilicon` | Compare the measured distribution with the pre-silicon prediction. |
| `flag_sweep_outlier` | `publish_finding` | `flag_sweep_outlier` | Publish an outlier that the guardband must include. |
| `flag_out_of_bounds_point` | `publish_finding` | `flag_out_of_bounds_point` | Publish a requested point that sits outside the approved bounds. It must not be submitted. |
| `record_characterization_provenance` | `publish_finding` | `record_characterization_provenance` | Record the board, lot, points, and prediction revision. |

## Delegation

This agent declares **no** `delegates_to` entries. It executes its own `tools.py` skills when scheduled by a lead or the chip-flow orchestrator.

## Boot path

Every fleet agent shares the same linear startup so compose and local dev behave identically.

1. Container or shell runs `python server.py` (`deployment.dockerfile` / image `agentfleet/characterization:1.0`).
2. `server.py` prepends this directory to `sys.path`, imports `CharacterizationAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, CharacterizationAgent)`.
3. Importing `agent.py` sets `spec = EdaAgent.read_spec(<this directory>)`, loading `config.yaml` at class definition time.
4. Uvicorn serves FastAPI `app` on `connection.port` with `/health` and `/tasks/execute`.
5. On `/tasks/execute`, `EdaAgent.handle` assembles engineering-memory context (see `context` in YAML), journals the task, and dispatches the requested skill.
6. The skill callable in `tools.py` returns `tool_observation(...)`. With `backend.type: none`, observations are safe stubs (`not_run`) until `EDA_FRAMEWORK` or another adapter binds real engines.

## Related agents

- Stage index: [`../README.md`](../README.md) (validation specialists under `validation/`).
- Stage lead(s) that delegate here:
  - [`bringup_lead`](../bringup_lead/) (port **8263**)
- Sibling agents in this folder:
  - [`bringup_lead`](../bringup_lead/) — lead, port **8263**
  - [`errata_drafting`](../errata_drafting/) — worker, port **8270**
  - [`failure_correlation`](../failure_correlation/) — worker, port **8269**
  - [`firmware_test_program`](../firmware_test_program/) — worker, port **8266**
  - [`instrument_control`](../instrument_control/) — worker, port **8265**
  - [`lab_procedure`](../lab_procedure/) — worker, port **8264**
  - [`telemetry_log_analysis`](../telemetry_log_analysis/) — worker, port **8267**
- Track overview: [`../README.md`](../README.md).

## Files in this directory

| File | Role |
|------|------|
| `agent.py` | Defines `CharacterizationAgent`; loads sibling `config.yaml` into `spec`. |
| `server.py` | HTTP/ASGI bootstrap; exports FastAPI `app` for uvicorn. |
| `tools.py` | `@tool` skill callables; stable EDA operation contracts. |
| `config.yaml` | Fleet manifest (`apiVersion: agentfleet/v1`): boundaries, port, skills, memory, telemetry. |
| `Dockerfile` | Container image; `EXPOSE 8268`; `CMD python server.py`. |
| `requirements.txt` | FastAPI, uvicorn, pydantic, PyYAML for the HTTP surface. |
| `__init__.py` | Re-exports `CharacterizationAgent` for imports without starting HTTP. |
| `README.md` | This document. |

## Tool reference

### `plan_pvt_sweep` (`tools.plan_pvt_sweep`)

**Action:** `write_candidate`. Plan a voltage, frequency, temperature, and workload sweep.

### `define_voltage_points` (`tools.define_voltage_points`)

**Action:** `write_candidate`. Write the voltage points. Each point must sit inside the approved bound.

### `define_frequency_points` (`tools.define_frequency_points`)

**Action:** `write_candidate`. Write the frequency points.

### `define_temperature_points` (`tools.define_temperature_points`)

**Action:** `write_candidate`. Write the temperature points inside the approved bound.

### `define_workload_points` (`tools.define_workload_points`)

**Action:** `write_candidate`. Write the workloads the sweep will run.

### `check_sweep_against_bounds` (`tools.check_sweep_against_bounds`)

**Action:** `read_reports`. Check every point against the approved voltage, current, and temperature limits.

### `submit_sweep_point` (`tools.submit_sweep_point`)

**Action:** `submit_tool_job`. Submit one sweep point to the lab adapter.

### `submit_sweep_batch` (`tools.submit_sweep_batch`)

**Action:** `submit_tool_job`. Submit the approved points as one batch.

### `read_sweep_measurements` (`tools.read_sweep_measurements`)

**Action:** `read_reports`. Read measured shmoo and workload results, including outliers.

### `fit_operating_envelope` (`tools.fit_operating_envelope`)

**Action:** `publish_finding`. Fit the measured envelope and the guardband. Outliers stay in the fit.

### `compare_with_presilicon` (`tools.compare_with_presilicon`)

**Action:** `publish_finding`. Compare the measured distribution with the pre-silicon prediction.

### `flag_sweep_outlier` (`tools.flag_sweep_outlier`)

**Action:** `publish_finding`. Publish an outlier that the guardband must include.

### `flag_out_of_bounds_point` (`tools.flag_out_of_bounds_point`)

**Action:** `publish_finding`. Publish a requested point that sits outside the approved bounds. It must not be submitted.

### `record_characterization_provenance` (`tools.record_characterization_provenance`)

**Action:** `publish_finding`. Record the board, lot, points, and prediction revision.

## Runtime, memory, and context

- **Reliability:** task timeout 120s, max retries 1, on failure `replan`.
- **Execution:** `direct_function`, `max_tasks=1`.
- **Context include:** `experiments`, `gates`, `decisions`, `open_findings`, `canonical_source`.
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
