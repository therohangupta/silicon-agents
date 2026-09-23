# Bring-Up Lead (`bringup_lead`)

This directory is the deployable microservice package for the **Bring-Up Lead** in the fleet **validation** stage (role `lead`).

## EDA responsibility

Bring-up Lead agent class (bringup_lead).

Charter from `config.yaml`: Own the path from first power-on to validated operation. Order safety checks and keep the bring-up decision record. Irreversible actions stay with a human.

As a **lead**, this process publishes workflows, reads qualified upstream artifacts, opens child agent tasks, compares candidates, and recommends next steps. It does **not** promote the canonical baseline or act as independent signoff.

## Identity and HTTP port

| Field | Value |
|-------|-------|
| Agent id | `bringup_lead` |
| Stage | `validation` |
| Role | `lead` |
| Host | `host.docker.internal` |
| Port | **8263** (must match `Dockerfile` `EXPOSE`) |
| Health | `/health` |
| Execute | `/tasks/execute` |

## Boundaries

Hard limits from `config.yaml` `boundary`. The planner and `EDAAgent` enforce these even when a tool adapter could physically perform a forbidden action.

### May

- Publish a bring-up workflow
- Read lab procedures and silicon findings
- Request a human decision before an irreversible or out-of-bounds action

### May not

- Authorize a destructive lab action
- Change a signoff waiver
- Widen a safety bound
- Promote a candidate onto the canonical baseline
- Approve a waiver or relax a hard requirement
- Treat its own summary as independent signoff

## Skills

Skills bind planner task ids to callables in `tools.py` (`module: tools`, `execution.mode: direct_function`).

| Skill id | Action | Callable | Description |
|----------|--------|----------|-------------|
| `plan_bringup` | `create_workflow` | `plan_bringup` | Emit the staged bring-up workflow with explicit approval points. |
| `request_lab_procedure` | `create_workflow` | `request_lab_procedure` | Open a versioned procedure for the next stage. |
| `request_instrument_run` | `create_workflow` | `request_instrument_run` | Open an instrument run of one approved procedure. |
| `request_firmware_change` | `create_workflow` | `request_firmware_change` | Open a firmware or test-program change. |
| `request_telemetry_review` | `create_workflow` | `request_telemetry_review` | Open log and trace review for the latest run. |
| `request_characterization_sweep` | `create_workflow` | `request_characterization_sweep` | Open a characterization sweep inside approved bounds. |
| `request_failure_correlation` | `create_workflow` | `request_failure_correlation` | Open correlation of a silicon symptom with pre-silicon evidence. |
| `request_errata_draft` | `create_workflow` | `request_errata_draft` | Open an errata draft for a validated finding. |
| `read_bringup_status` | `read_reports` | `read_bringup_status` | Read which stages have passed and which approval points are open. |
| `read_safety_bounds` | `read_reports` | `read_safety_bounds` | Read the voltage, current, and temperature bounds in force. |
| `record_bringup_decision` | `publish_finding` | `record_bringup_decision` | Record a human decision and the evidence it used. |
| `flag_skipped_safety_check` | `publish_finding` | `flag_skipped_safety_check` | Publish a stage that started before its safety check. |
| `request_bringup_decision` | `request_human_decision` | `request_bringup_decision` | Escalate an irreversible or out-of-bounds lab choice. |
| `request_destructive_action_decision` | `request_human_decision` | `request_destructive_action_decision` | Ask a human before a destructive or one-way lab action. |

## Delegation

This lead may open child workflows/tasks against:

- [`lab_procedure`](../lab_procedure/) — Lab Procedure Agent (port **8264**)
- [`instrument_control`](../instrument_control/) — Instrument-Control Agent (port **8265**)
- [`firmware_test_program`](../firmware_test_program/) — Firmware and Test-Program Agent (port **8266**)
- [`telemetry_log_analysis`](../telemetry_log_analysis/) — Telemetry and Log-Analysis Agent (port **8267**)
- [`characterization`](../characterization/) — Characterization Agent (port **8268**)
- [`failure_correlation`](../failure_correlation/) — Failure-Correlation Agent (port **8269**)
- [`errata_drafting`](../errata_drafting/) — Errata and Issue-Drafting Agent (port **8270**)

Delegation is declarative in `delegates_to`. The lead's `request_*` / `open_*` skills tell the orchestrator which child agent id and skill to schedule next; workers do not call each other directly over HTTP.

## Boot path

Every fleet agent shares the same linear startup so compose and local dev behave identically.

1. Container or shell runs `python server.py` (`deployment.dockerfile` / image `agentfleet/bringup_lead:1.0`).
2. `server.py` prepends this directory to `sys.path`, imports `BringupLeadAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, BringupLeadAgent)`.
3. Importing `agent.py` sets `spec = EDAAgent.read_spec(<this directory>)`, loading `config.yaml` at class definition time.
4. Uvicorn serves FastAPI `app` on `connection.port` with `/health` and `/tasks/execute`.
5. On `/tasks/execute`, `EDAAgent.handle` assembles engineering-memory context (see `context` in YAML), journals the task, and dispatches the requested skill.
6. The skill callable in `tools.py` returns `tool_observation(...)`. With `backend.type: none`, observations are safe stubs (`not_run`) until `EDA_FRAMEWORK` or another adapter binds real engines.

## Related agents

- Stage index: [`../README.md`](../README.md) (validation specialists under `validation/`).
- Program orchestrator:
  - [`chip_flow_lead`](../../chip_flow_lead/) (port **8201**)
- Sibling agents in this folder:
  - [`characterization`](../characterization/) — worker, port **8268**
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
| `agent.py` | Defines `BringupLeadAgent`; loads sibling `config.yaml` into `spec`. |
| `server.py` | HTTP/ASGI bootstrap; exports FastAPI `app` for uvicorn. |
| `tools.py` | `@tool` skill callables; stable EDA operation contracts. |
| `config.yaml` | Fleet manifest (`apiVersion: agentfleet/v1`): boundaries, port, skills, memory, telemetry. |
| `Dockerfile` | Container image; `EXPOSE 8263`; `CMD python server.py`. |
| `requirements.txt` | FastAPI, uvicorn, pydantic, PyYAML for the HTTP surface. |
| `__init__.py` | Re-exports `BringupLeadAgent` for imports without starting HTTP. |
| `README.md` | This document. |

## Tool reference

### `plan_bringup` (`tools.plan_bringup`)

**Action:** `create_workflow`. Emit the staged bring-up workflow with explicit approval points.

### `request_lab_procedure` (`tools.request_lab_procedure`)

**Action:** `create_workflow`. Open a versioned procedure for the next stage.

### `request_instrument_run` (`tools.request_instrument_run`)

**Action:** `create_workflow`. Open an instrument run of one approved procedure.

### `request_firmware_change` (`tools.request_firmware_change`)

**Action:** `create_workflow`. Open a firmware or test-program change.

### `request_telemetry_review` (`tools.request_telemetry_review`)

**Action:** `create_workflow`. Open log and trace review for the latest run.

### `request_characterization_sweep` (`tools.request_characterization_sweep`)

**Action:** `create_workflow`. Open a characterization sweep inside approved bounds.

### `request_failure_correlation` (`tools.request_failure_correlation`)

**Action:** `create_workflow`. Open correlation of a silicon symptom with pre-silicon evidence.

### `request_errata_draft` (`tools.request_errata_draft`)

**Action:** `create_workflow`. Open an errata draft for a validated finding.

### `read_bringup_status` (`tools.read_bringup_status`)

**Action:** `read_reports`. Read which stages have passed and which approval points are open.

### `read_safety_bounds` (`tools.read_safety_bounds`)

**Action:** `read_reports`. Read the voltage, current, and temperature bounds in force.

### `record_bringup_decision` (`tools.record_bringup_decision`)

**Action:** `publish_finding`. Record a human decision and the evidence it used.

### `flag_skipped_safety_check` (`tools.flag_skipped_safety_check`)

**Action:** `publish_finding`. Publish a stage that started before its safety check.

### `request_bringup_decision` (`tools.request_bringup_decision`)

**Action:** `request_human_decision`. Escalate an irreversible or out-of-bounds lab choice.

### `request_destructive_action_decision` (`tools.request_destructive_action_decision`)

**Action:** `request_human_decision`. Ask a human before a destructive or one-way lab action.

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
