# Lab Procedure Agent (`lab_procedure`)

This directory is the deployable microservice package for the **Lab Procedure Agent** in the fleet **validation** stage (role `worker`).

## EDA responsibility

Lab Procedure agent class (lab_procedure).

Charter from `config.yaml`: Turn bring-up intent into a versioned procedure with prerequisites, safe bounds, expected observations, rollback, and human-approval points.

As a **worker**, this process executes bounded skills on isolated candidates and reports observations. Promotion and program-level tradeoffs stay with leads and humans.

## Identity and HTTP port

| Field | Value |
|-------|-------|
| Agent id | `lab_procedure` |
| Stage | `validation` |
| Role | `worker` |
| Host | `host.docker.internal` |
| Port | **8264** (must match `Dockerfile` `EXPOSE`) |
| Health | `/health` |
| Execute | `/tasks/execute` |

## Boundaries

Hard limits from `config.yaml` `boundary`. The planner and `EDAAgent` enforce these even when a tool adapter could physically perform a forbidden action.

### May

- Write a procedure draft
- List human approval points

### May not

- Run the procedure
- Widen a safety bound
- Promote a candidate onto the canonical baseline
- Approve a waiver or relax a hard requirement
- Treat its own summary as independent signoff

## Skills

Skills bind planner task ids to callables in `tools.py` (`module: tools`, `execution.mode: direct_function`).

| Skill id | Action | Callable | Description |
|----------|--------|----------|-------------|
| `draft_lab_procedure` | `write_candidate` | `draft_lab_procedure` | Write prerequisites, steps, expected observations, and rollback. |
| `write_procedure_prerequisites` | `write_candidate` | `write_procedure_prerequisites` | Write the setup that must be true before the first step. |
| `write_safe_operating_bounds` | `write_candidate` | `write_safe_operating_bounds` | Write voltage, current, and temperature bounds. Bounds may only be copied from an approved limit. |
| `write_expected_observations` | `write_candidate` | `write_expected_observations` | Write the measurements that mean the step passed. |
| `write_rollback_steps` | `write_candidate` | `write_rollback_steps` | Write how to return the bench to a safe state. |
| `write_approval_points` | `write_candidate` | `write_approval_points` | Mark the steps that require a human before they run. |
| `revise_procedure_draft` | `write_candidate` | `revise_procedure_draft` | Edit a draft that has not been approved. |
| `read_bringup_intent` | `read_reports` | `read_bringup_intent` | Read the bring-up intent this procedure implements. |
| `list_approval_points` | `read_reports` | `list_approval_points` | List the steps that require a human before they run. |
| `diff_procedure_revisions` | `read_reports` | `diff_procedure_revisions` | Show what changed between two procedure revisions. |
| `flag_missing_rollback` | `publish_finding` | `flag_missing_rollback` | Publish a procedure with no rollback. |
| `flag_widened_safety_bound` | `publish_finding` | `flag_widened_safety_bound` | Publish a draft whose bounds exceed the approved limit. |
| `record_procedure_version` | `publish_finding` | `record_procedure_version` | Record the procedure revision and the intent it traces to. |

## Delegation

This agent declares **no** `delegates_to` entries. It executes its own `tools.py` skills when scheduled by a lead or the chip-flow orchestrator.

## Boot path

Every fleet agent shares the same linear startup so compose and local dev behave identically.

1. Container or shell runs `python server.py` (`deployment.dockerfile` / image `agentfleet/lab_procedure:1.0`).
2. `server.py` prepends this directory to `sys.path`, imports `LabProcedureAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, LabProcedureAgent)`.
3. Importing `agent.py` sets `spec = EDAAgent.read_spec(<this directory>)`, loading `config.yaml` at class definition time.
4. Uvicorn serves FastAPI `app` on `connection.port` with `/health` and `/tasks/execute`.
5. On `/tasks/execute`, `EDAAgent.handle` assembles engineering-memory context (see `context` in YAML), journals the task, and dispatches the requested skill.
6. The skill callable in `tools.py` returns `tool_observation(...)`. With `backend.type: none`, observations are safe stubs (`not_run`) until `EDA_FRAMEWORK` or another adapter binds real engines.

## Related agents

- Stage index: [`../README.md`](../README.md) (validation specialists under `validation/`).
- Stage lead(s) that delegate here:
  - [`bringup_lead`](../bringup_lead/) (port **8263**)
- Sibling agents in this folder:
  - [`bringup_lead`](../bringup_lead/) — lead, port **8263**
  - [`characterization`](../characterization/) — worker, port **8268**
  - [`errata_drafting`](../errata_drafting/) — worker, port **8270**
  - [`failure_correlation`](../failure_correlation/) — worker, port **8269**
  - [`firmware_test_program`](../firmware_test_program/) — worker, port **8266**
  - [`instrument_control`](../instrument_control/) — worker, port **8265**
  - [`telemetry_log_analysis`](../telemetry_log_analysis/) — worker, port **8267**
- Track overview: [`../README.md`](../README.md).

## Files in this directory

| File | Role |
|------|------|
| `agent.py` | Defines `LabProcedureAgent`; loads sibling `config.yaml` into `spec`. |
| `server.py` | HTTP/ASGI bootstrap; exports FastAPI `app` for uvicorn. |
| `tools.py` | `@tool` skill callables; stable EDA operation contracts. |
| `config.yaml` | Fleet manifest (`apiVersion: agentfleet/v1`): boundaries, port, skills, memory, telemetry. |
| `Dockerfile` | Container image; `EXPOSE 8264`; `CMD python server.py`. |
| `requirements.txt` | FastAPI, uvicorn, pydantic, PyYAML for the HTTP surface. |
| `__init__.py` | Re-exports `LabProcedureAgent` for imports without starting HTTP. |
| `README.md` | This document. |

## Tool reference

### `draft_lab_procedure` (`tools.draft_lab_procedure`)

**Action:** `write_candidate`. Write prerequisites, steps, expected observations, and rollback.

### `write_procedure_prerequisites` (`tools.write_procedure_prerequisites`)

**Action:** `write_candidate`. Write the setup that must be true before the first step.

### `write_safe_operating_bounds` (`tools.write_safe_operating_bounds`)

**Action:** `write_candidate`. Write voltage, current, and temperature bounds. Bounds may only be copied from an approved limit.

### `write_expected_observations` (`tools.write_expected_observations`)

**Action:** `write_candidate`. Write the measurements that mean the step passed.

### `write_rollback_steps` (`tools.write_rollback_steps`)

**Action:** `write_candidate`. Write how to return the bench to a safe state.

### `write_approval_points` (`tools.write_approval_points`)

**Action:** `write_candidate`. Mark the steps that require a human before they run.

### `revise_procedure_draft` (`tools.revise_procedure_draft`)

**Action:** `write_candidate`. Edit a draft that has not been approved.

### `read_bringup_intent` (`tools.read_bringup_intent`)

**Action:** `read_reports`. Read the bring-up intent this procedure implements.

### `list_approval_points` (`tools.list_approval_points`)

**Action:** `read_reports`. List the steps that require a human before they run.

### `diff_procedure_revisions` (`tools.diff_procedure_revisions`)

**Action:** `read_reports`. Show what changed between two procedure revisions.

### `flag_missing_rollback` (`tools.flag_missing_rollback`)

**Action:** `publish_finding`. Publish a procedure with no rollback.

### `flag_widened_safety_bound` (`tools.flag_widened_safety_bound`)

**Action:** `publish_finding`. Publish a draft whose bounds exceed the approved limit.

### `record_procedure_version` (`tools.record_procedure_version`)

**Action:** `publish_finding`. Record the procedure revision and the intent it traces to.

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
- **Shared base:** Task handling lives in `domains/eda/runtime/agent.py`; HTTP wiring in `domains/eda/runtime/server.py`.
- **Telemetry:** See [`../../TELEMETRY.md`](../../TELEMETRY.md) (path may vary by depth) for fleet-wide observability conventions.

## How a newcomer should read this agent

1. Read `config.yaml` `metadata`, `boundary`, and `capabilities` for charter and limits.
2. Skim the skills table above, then open `tools.py` for parameter shapes.
3. Read `agent.py` and `server.py` only to confirm boot wiring.
4. Treat `Dockerfile` / `requirements.txt` as deployment detail.
