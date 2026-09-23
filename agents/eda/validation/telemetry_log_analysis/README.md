# Telemetry and Log-Analysis Agent (`telemetry_log_analysis`)

This directory is the deployable microservice package for the **Telemetry and Log-Analysis Agent** in the fleet **validation** stage (role `worker`).

## EDA responsibility

Telemetry / Log Analysis agent class (telemetry_log_analysis).

Charter from `config.yaml`: Normalize, correlate, search, and summarize firmware logs, counters, traces, and instrument captures while preserving links to the primary evidence.

As a **worker**, this process executes bounded skills on isolated candidates and reports observations. Promotion and program-level tradeoffs stay with leads and humans.

## Identity and HTTP port

| Field | Value |
|-------|-------|
| Agent id | `telemetry_log_analysis` |
| Stage | `validation` |
| Role | `worker` |
| Host | `host.docker.internal` |
| Port | **8267** (must match `Dockerfile` `EXPOSE`) |
| Health | `/health` |
| Execute | `/tasks/execute` |

## Boundaries

Hard limits from `config.yaml` `boundary`. The planner and `EDAAgent` enforce these even when a tool adapter could physically perform a forbidden action.

### May

- Read logs and captures
- Publish a correlation with links to the primary evidence

### May not

- Drop a capture that contradicts the summary
- Edit firmware
- Promote a candidate onto the canonical baseline
- Approve a waiver or relax a hard requirement
- Treat its own summary as independent signoff

## Skills

Skills bind planner task ids to callables in `tools.py` (`module: tools`, `execution.mode: direct_function`).

| Skill id | Action | Callable | Description |
|----------|--------|----------|-------------|
| `normalize_firmware_logs` | `read_reports` | `normalize_firmware_logs` | Normalize firmware logs into a common record. |
| `normalize_instrument_metadata` | `read_reports` | `normalize_instrument_metadata` | Normalize instrument captures and environmental metadata. |
| `read_hardware_counters` | `read_reports` | `read_hardware_counters` | Read hardware performance counters. |
| `read_trace_index` | `read_reports` | `read_trace_index` | Read the trace and capture index. |
| `search_logs` | `read_reports` | `search_logs` | Search normalized logs for one signature. |
| `correlate_traces` | `publish_finding` | `correlate_traces` | Correlate counters, traces, and environment metadata. |
| `align_logs_to_captures` | `read_reports` | `align_logs_to_captures` | Align firmware timestamps with instrument captures. |
| `summarize_session` | `publish_finding` | `summarize_session` | Summarize one lab session and link every claim to a primary capture. |
| `flag_contradictory_capture` | `publish_finding` | `flag_contradictory_capture` | Publish a capture that contradicts the session summary. |
| `flag_unlinked_summary_claim` | `publish_finding` | `flag_unlinked_summary_claim` | Publish a summary sentence with no primary evidence. |
| `record_telemetry_sources` | `publish_finding` | `record_telemetry_sources` | Record the log, counter, and capture refs included in an analysis. |
| `publish_telemetry_correlation` | `publish_finding` | `publish_telemetry_correlation` | Publish the correlation and its evidence refs. |

## Delegation

This agent declares **no** `delegates_to` entries. It executes its own `tools.py` skills when scheduled by a lead or the chip-flow orchestrator.

## Boot path

Every fleet agent shares the same linear startup so compose and local dev behave identically.

1. Container or shell runs `python server.py` (`deployment.dockerfile` / image `agentfleet/telemetry_log_analysis:1.0`).
2. `server.py` prepends this directory to `sys.path`, imports `TelemetryLogAnalysisAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, TelemetryLogAnalysisAgent)`.
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
  - [`lab_procedure`](../lab_procedure/) — worker, port **8264**
- Track overview: [`../README.md`](../README.md).

## Files in this directory

| File | Role |
|------|------|
| `agent.py` | Defines `TelemetryLogAnalysisAgent`; loads sibling `config.yaml` into `spec`. |
| `server.py` | HTTP/ASGI bootstrap; exports FastAPI `app` for uvicorn. |
| `tools.py` | `@tool` skill callables; stable EDA operation contracts. |
| `config.yaml` | Fleet manifest (`apiVersion: agentfleet/v1`): boundaries, port, skills, memory, telemetry. |
| `Dockerfile` | Container image; `EXPOSE 8267`; `CMD python server.py`. |
| `requirements.txt` | FastAPI, uvicorn, pydantic, PyYAML for the HTTP surface. |
| `__init__.py` | Re-exports `TelemetryLogAnalysisAgent` for imports without starting HTTP. |
| `README.md` | This document. |

## Tool reference

### `normalize_firmware_logs` (`tools.normalize_firmware_logs`)

**Action:** `read_reports`. Normalize firmware logs into a common record.

### `normalize_instrument_metadata` (`tools.normalize_instrument_metadata`)

**Action:** `read_reports`. Normalize instrument captures and environmental metadata.

### `read_hardware_counters` (`tools.read_hardware_counters`)

**Action:** `read_reports`. Read hardware performance counters.

### `read_trace_index` (`tools.read_trace_index`)

**Action:** `read_reports`. Read the trace and capture index.

### `search_logs` (`tools.search_logs`)

**Action:** `read_reports`. Search normalized logs for one signature.

### `correlate_traces` (`tools.correlate_traces`)

**Action:** `publish_finding`. Correlate counters, traces, and environment metadata.

### `align_logs_to_captures` (`tools.align_logs_to_captures`)

**Action:** `read_reports`. Align firmware timestamps with instrument captures.

### `summarize_session` (`tools.summarize_session`)

**Action:** `publish_finding`. Summarize one lab session and link every claim to a primary capture.

### `flag_contradictory_capture` (`tools.flag_contradictory_capture`)

**Action:** `publish_finding`. Publish a capture that contradicts the session summary.

### `flag_unlinked_summary_claim` (`tools.flag_unlinked_summary_claim`)

**Action:** `publish_finding`. Publish a summary sentence with no primary evidence.

### `record_telemetry_sources` (`tools.record_telemetry_sources`)

**Action:** `publish_finding`. Record the log, counter, and capture refs included in an analysis.

### `publish_telemetry_correlation` (`tools.publish_telemetry_correlation`)

**Action:** `publish_finding`. Publish the correlation and its evidence refs.

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
