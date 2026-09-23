# Instrument-Control Agent (`instrument_control`)

This directory is the deployable microservice package for the **Instrument-Control Agent** in the fleet **validation** stage (role `worker`).

## EDA responsibility

Instrument Control agent class (instrument_control).

Charter from `config.yaml`: Operate approved instruments through a typed safety-enforcing adapter and record every command and measurement.

As a **worker**, this process executes bounded skills on isolated candidates and reports observations. Promotion and program-level tradeoffs stay with leads and humans.

## Identity and HTTP port

| Field | Value |
|-------|-------|
| Agent id | `instrument_control` |
| Stage | `validation` |
| Role | `worker` |
| Host | `host.docker.internal` |
| Port | **8265** (must match `Dockerfile` `EXPOSE`) |
| Health | `/health` |
| Execute | `/tasks/execute` |

## Boundaries

Hard limits from `config.yaml` `boundary`. The planner and `EDAAgent` enforce these even when a tool adapter could physically perform a forbidden action.

### May

- Submit an approved procedure inside its safe bounds
- Record measurements

### May not

- Exceed a configured limit
- Run a procedure that has no approval-point record
- Widen a limit
- Promote a candidate onto the canonical baseline
- Approve a waiver or relax a hard requirement
- Treat its own summary as independent signoff

## Skills

Skills bind planner task ids to callables in `tools.py` (`module: tools`, `execution.mode: direct_function`).

| Skill id | Action | Callable | Description |
|----------|--------|----------|-------------|
| `run_instrument_procedure` | `submit_tool_job` | `run_instrument_procedure` | Execute one approved procedure through the lab adapter. |
| `arm_power_supply` | `submit_tool_job` | `arm_power_supply` | Set a power supply inside the approved voltage and current limits. |
| `capture_oscilloscope` | `submit_tool_job` | `capture_oscilloscope` | Capture one oscilloscope waveform inside the approved setup. |
| `capture_logic_analyzer` | `submit_tool_job` | `capture_logic_analyzer` | Capture one logic-analyzer trace. |
| `set_thermal_setpoint` | `submit_tool_job` | `set_thermal_setpoint` | Set a thermal chamber or plate inside the approved temperature limit. |
| `read_instrument_state` | `read_reports` | `read_instrument_state` | Read the live state of one instrument. |
| `read_procedure_approval` | `read_reports` | `read_procedure_approval` | Read the approval record required before this procedure runs. |
| `check_command_against_bounds` | `read_reports` | `check_command_against_bounds` | Check a command against the approved voltage, current, and temperature limits. |
| `record_instrument_command` | `publish_finding` | `record_instrument_command` | Record the command, instrument, limits, and operator approval ref. |
| `record_measurement` | `publish_finding` | `record_measurement` | Store the measurement with board, voltage, temperature, and instrument state. |
| `flag_command_over_limit` | `publish_finding` | `flag_command_over_limit` | Publish a command that would exceed a configured limit. The adapter must not run it. |
| `flag_unapproved_procedure` | `publish_finding` | `flag_unapproved_procedure` | Publish a run requested without an approval-point record. |
| `record_instrument_session` | `publish_finding` | `record_instrument_session` | Record every command and measurement in this session. |

## Delegation

This agent declares **no** `delegates_to` entries. It executes its own `tools.py` skills when scheduled by a lead or the chip-flow orchestrator.

## Boot path

Every fleet agent shares the same linear startup so compose and local dev behave identically.

1. Container or shell runs `python server.py` (`deployment.dockerfile` / image `agentfleet/instrument_control:1.0`).
2. `server.py` prepends this directory to `sys.path`, imports `InstrumentControlAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, InstrumentControlAgent)`.
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
  - [`lab_procedure`](../lab_procedure/) — worker, port **8264**
  - [`telemetry_log_analysis`](../telemetry_log_analysis/) — worker, port **8267**
- Track overview: [`../README.md`](../README.md).

## Files in this directory

| File | Role |
|------|------|
| `agent.py` | Defines `InstrumentControlAgent`; loads sibling `config.yaml` into `spec`. |
| `server.py` | HTTP/ASGI bootstrap; exports FastAPI `app` for uvicorn. |
| `tools.py` | `@tool` skill callables; stable EDA operation contracts. |
| `config.yaml` | Fleet manifest (`apiVersion: agentfleet/v1`): boundaries, port, skills, memory, telemetry. |
| `Dockerfile` | Container image; `EXPOSE 8265`; `CMD python server.py`. |
| `requirements.txt` | FastAPI, uvicorn, pydantic, PyYAML for the HTTP surface. |
| `__init__.py` | Re-exports `InstrumentControlAgent` for imports without starting HTTP. |
| `README.md` | This document. |

## Tool reference

### `run_instrument_procedure` (`tools.run_instrument_procedure`)

**Action:** `submit_tool_job`. Execute one approved procedure through the lab adapter.

### `arm_power_supply` (`tools.arm_power_supply`)

**Action:** `submit_tool_job`. Set a power supply inside the approved voltage and current limits.

### `capture_oscilloscope` (`tools.capture_oscilloscope`)

**Action:** `submit_tool_job`. Capture one oscilloscope waveform inside the approved setup.

### `capture_logic_analyzer` (`tools.capture_logic_analyzer`)

**Action:** `submit_tool_job`. Capture one logic-analyzer trace.

### `set_thermal_setpoint` (`tools.set_thermal_setpoint`)

**Action:** `submit_tool_job`. Set a thermal chamber or plate inside the approved temperature limit.

### `read_instrument_state` (`tools.read_instrument_state`)

**Action:** `read_reports`. Read the live state of one instrument.

### `read_procedure_approval` (`tools.read_procedure_approval`)

**Action:** `read_reports`. Read the approval record required before this procedure runs.

### `check_command_against_bounds` (`tools.check_command_against_bounds`)

**Action:** `read_reports`. Check a command against the approved voltage, current, and temperature limits.

### `record_instrument_command` (`tools.record_instrument_command`)

**Action:** `publish_finding`. Record the command, instrument, limits, and operator approval ref.

### `record_measurement` (`tools.record_measurement`)

**Action:** `publish_finding`. Store the measurement with board, voltage, temperature, and instrument state.

### `flag_command_over_limit` (`tools.flag_command_over_limit`)

**Action:** `publish_finding`. Publish a command that would exceed a configured limit. The adapter must not run it.

### `flag_unapproved_procedure` (`tools.flag_unapproved_procedure`)

**Action:** `publish_finding`. Publish a run requested without an approval-point record.

### `record_instrument_session` (`tools.record_instrument_session`)

**Action:** `publish_finding`. Record every command and measurement in this session.

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
