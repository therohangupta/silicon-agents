# Validation stage agents

This directory groups **validation**-stage agents. Post-silicon validation: lab bring-up, instruments, firmware test programs, telemetry, characterization, and errata under a bring-up lead.

Each child folder is an independent HTTP microservice (`python server.py`) discovered via its `config.yaml`. Leads declare `delegates_to` worker ids; validators declare independent gates. Workers execute skills in `tools.py` and return observations until an EDA adapter is bound.

## Agents in this stage

| Agent | Role | Port | Package |
|-------|------|------|---------|
| Bring-Up Lead (`bringup_lead`) | `lead` | **8263** | [`bringup_lead/`](bringup_lead/) |
| Lab Procedure Agent (`lab_procedure`) | `worker` | **8264** | [`lab_procedure/`](lab_procedure/) |
| Instrument-Control Agent (`instrument_control`) | `worker` | **8265** | [`instrument_control/`](instrument_control/) |
| Firmware and Test-Program Agent (`firmware_test_program`) | `worker` | **8266** | [`firmware_test_program/`](firmware_test_program/) |
| Telemetry and Log-Analysis Agent (`telemetry_log_analysis`) | `worker` | **8267** | [`telemetry_log_analysis/`](telemetry_log_analysis/) |
| Characterization Agent (`characterization`) | `worker` | **8268** | [`characterization/`](characterization/) |
| Failure-Correlation Agent (`failure_correlation`) | `worker` | **8269** | [`failure_correlation/`](failure_correlation/) |
| Errata and Issue-Drafting Agent (`errata_drafting`) | `worker` | **8270** | [`errata_drafting/`](errata_drafting/) |

## Lead delegation graph

### `bringup_lead` (port **8263**)

Own the path from first power-on to validated operation. Order safety checks and keep the bring-up decision record. Irreversible actions stay with a human.

May schedule:
- [`lab_procedure`](lab_procedure/) — Lab Procedure Agent (**8264**)
- [`instrument_control`](instrument_control/) — Instrument-Control Agent (**8265**)
- [`firmware_test_program`](firmware_test_program/) — Firmware and Test-Program Agent (**8266**)
- [`telemetry_log_analysis`](telemetry_log_analysis/) — Telemetry and Log-Analysis Agent (**8267**)
- [`characterization`](characterization/) — Characterization Agent (**8268**)
- [`failure_correlation`](failure_correlation/) — Failure-Correlation Agent (**8269**)
- [`errata_drafting`](errata_drafting/) — Errata and Issue-Drafting Agent (**8270**)

## Suggested workflow (mental model)

1. **bringup_lead** coordinates lab procedures and instrument access.
2. **firmware_test_program** and **lab_procedure** execute structured bring-up.
3. **instrument_control**, **telemetry_log_analysis**, and **characterization** capture silicon behavior.
4. **failure_correlation** and **errata_drafting** close the loop to architecture/RTL when needed.

## Shared package layout (every child)

| File | Role |
|------|------|
| `config.yaml` | Manifest: identity, boundaries, port, skills, memory, telemetry, context. |
| `agent.py` | Thin `EdaAgent` subclass loading sibling YAML into `spec`. |
| `tools.py` | Skill contracts returning `tool_observation` until adapters bind. |
| `server.py` | `AgentService` FastAPI bootstrap (`/health`, `/tasks/execute`). |
| `Dockerfile` / `requirements.txt` | Container and Python deps for the HTTP surface. |
| `README.md` | Per-agent charter, skills, boundaries, boot path, and related agents. |

## Boot path (all children)

1. Compose or `python server.py` starts the container/process.
2. `server.py` loads `config.yaml` and the agent class into `AgentService`.
3. Orchestrator (or a lead's delegated workflow) POSTs to `/tasks/execute` with a skill id.
4. `EdaAgent.handle` journals, assembles context, and invokes the matching `tools.py` callable.
5. Observations and findings land in engineering memory and telemetry streams.

## Related documentation

- Parent track index: [`../README.md`](../README.md)
- Fleet agents tree: [`../README.md`](../README.md) or [`../../README.md`](../../README.md) depending on nesting.
- Shared agent runtime: `domains/eda/agent.py`, `domains/eda/server.py`.
- Telemetry conventions: [`../TELEMETRY.md`](../TELEMETRY.md) under `agents/`.

## Port map (quick reference)

- **8263** — `bringup_lead` (lead)
- **8264** — `lab_procedure` (worker)
- **8265** — `instrument_control` (worker)
- **8266** — `firmware_test_program` (worker)
- **8267** — `telemetry_log_analysis` (worker)
- **8268** — `characterization` (worker)
- **8269** — `failure_correlation` (worker)
- **8270** — `errata_drafting` (worker)

## Child agent charters

### [`bringup_lead`](bringup_lead/) (port **8263**, `lead`)

Own the path from first power-on to validated operation. Order safety checks and keep the bring-up decision record. Irreversible actions stay with a human.

- **Skills in manifest:** 14 entries in `config.yaml` → `tools.py`.
- **Delegates to:** `lab_procedure`, `instrument_control`, `firmware_test_program`, `telemetry_log_analysis`, `characterization`, `failure_correlation`, `errata_drafting`.

### [`lab_procedure`](lab_procedure/) (port **8264**, `worker`)

Turn bring-up intent into a versioned procedure with prerequisites, safe bounds, expected observations, rollback, and human-approval points.

- **Skills in manifest:** 13 entries in `config.yaml` → `tools.py`.

### [`instrument_control`](instrument_control/) (port **8265**, `worker`)

Operate approved instruments through a typed safety-enforcing adapter and record every command and measurement.

- **Skills in manifest:** 13 entries in `config.yaml` → `tools.py`.

### [`firmware_test_program`](firmware_test_program/) (port **8266**, `worker`)

Draft and debug low-level firmware, diagnostics, boot flows, and test programs used to exercise silicon.

- **Skills in manifest:** 12 entries in `config.yaml` → `tools.py`.

### [`telemetry_log_analysis`](telemetry_log_analysis/) (port **8267**, `worker`)

Normalize, correlate, search, and summarize firmware logs, counters, traces, and instrument captures while preserving links to the primary evidence.

- **Skills in manifest:** 12 entries in `config.yaml` → `tools.py`.

### [`characterization`](characterization/) (port **8268**, `worker`)

Plan and execute voltage, frequency, temperature, and workload sweeps inside approved bounds, fit the operating envelope, and compare it with pre-silicon predictions.

- **Skills in manifest:** 14 entries in `config.yaml` → `tools.py`.

### [`failure_correlation`](failure_correlation/) (port **8269**, `worker`)

Correlate a silicon failure with simulation, formal, signoff, firmware, and manufacturing evidence, and name the earliest abstraction that reproduces it.

- **Skills in manifest:** 12 entries in `config.yaml` → `tools.py`.

### [`errata_drafting`](errata_drafting/) (port **8270**, `worker`)

Draft a traceable internal issue or erratum with reproduction steps, affected configurations, evidence, severity, and proposed mitigations.

- **Skills in manifest:** 12 entries in `config.yaml` → `tools.py`.

## Findings, gates, and promotion

Workers publish **findings** and edit **candidates**; validators emit **gates**; leads **recommend** but do not promote the canonical baseline. Human promotion and waivers sit outside these agents and are routed through `chip_flow_lead` decisions.

Every child returns structured observations while `backend.type: none`; binding `EDA_FRAMEWORK` does not relax `boundary.may_not` rules.

## Scheduling hints

| If you need… | Start with… |
|--------------|-------------|
| Own the path from first power-on to validated operation. Order safety checks and keep the  | `bringup_lead` |
| Turn bring-up intent into a versioned procedure with prerequisites, safe bounds, expected  | `lab_procedure` |
| Operate approved instruments through a typed safety-enforcing adapter and record every com | `instrument_control` |
| Draft and debug low-level firmware, diagnostics, boot flows, and test programs used to exe | `firmware_test_program` |
| Normalize, correlate, search, and summarize firmware logs, counters, traces, and instrumen | `telemetry_log_analysis` |
| Plan and execute voltage, frequency, temperature, and workload sweeps inside approved boun | `characterization` |
| Correlate a silicon failure with simulation, formal, signoff, firmware, and manufacturing  | `failure_correlation` |
| Draft a traceable internal issue or erratum with reproduction steps, affected configuratio | `errata_drafting` |
