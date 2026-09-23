# CDC/RDC Agent (`cdc_rdc`)

This directory is the deployable microservice package for the **CDC/RDC Agent** in the fleet **rtl** stage (role `worker`).

## EDA responsibility

Analyze clock and reset domain crossings and return evidence for a fix or a human waiver.

As a **worker**, this process executes bounded skills on isolated candidates and reports observations. Promotion and program-level tradeoffs stay with leads and humans.

## Identity and HTTP port

| Field | Value |
|-------|-------|
| Agent id | `cdc_rdc` |
| Stage | `rtl` |
| Role | `worker` |
| Host | `host.docker.internal` |
| Port | **8211** (must match `Dockerfile` `EXPOSE`) |
| Health | `/health` |
| Execute | `/tasks/execute` |

## Boundaries

Hard limits from `config.yaml` `boundary`. The planner and `EDAAgent` enforce these even when a tool adapter could physically perform a forbidden action.

### May

- Read RTL and clock intent
- Propose a synchronizer or an unsigned waiver record
- Edit a synchronizer on an isolated candidate

### May not

- Approve the waiver
- Delete a crossing from the report
- Promote a candidate onto the canonical baseline
- Approve a waiver or relax a hard requirement
- Treat its own summary as independent signoff

## Skills

Skills bind planner task ids to callables in `tools.py` (`module: tools`, `execution.mode: direct_function`).

| Skill id | Action | Callable | Description |
|----------|--------|----------|-------------|
| `analyze_cdc` | `submit_tool_job` | `analyze_cdc` | List clock-domain crossings and their synchronizers. |
| `analyze_rdc` | `submit_tool_job` | `analyze_rdc` | List reset-domain crossings. |
| `read_cdc_report` | `read_reports` | `read_cdc_report` | Read a CDC report and its waiver candidates. |
| `read_rdc_report` | `read_reports` | `read_rdc_report` | Read an RDC report. |
| `classify_crossing` | `read_reports` | `classify_crossing` | Classify one crossing as synchronized, unsynchronized, or waived-pending. |
| `trace_crossing_path` | `read_reports` | `trace_crossing_path` | Trace the source and destination registers of one crossing. |
| `write_synchronizer` | `write_candidate` | `write_synchronizer` | Add one synchronizer on an isolated candidate. |
| `write_waiver_proposal` | `write_candidate` | `write_waiver_proposal` | Write an unsigned waiver proposal with scope and rationale. It is not approved. |
| `check_reconvergence` | `submit_tool_job` | `check_reconvergence` | Check reconvergent crossings that a single synchronizer does not cover. |
| `propose_waiver_or_fix` | `publish_finding` | `propose_waiver_or_fix` | Publish either a bounded RTL fix or an unsigned waiver proposal. |
| `flag_unsynchronized_crossing` | `publish_finding` | `flag_unsynchronized_crossing` | Publish a crossing that has no synchronizer and no waiver proposal. |
| `record_cdc_tool_version` | `publish_finding` | `record_cdc_tool_version` | Record the CDC/RDC tool, version, and rule set used. |

## Delegation

This agent declares **no** `delegates_to` entries. It executes its own `tools.py` skills when scheduled by a lead or the chip-flow orchestrator.

## Boot path

Every fleet agent shares the same linear startup so compose and local dev behave identically.

1. Container or shell runs `python server.py` (`deployment.dockerfile` / image `agentfleet/cdc_rdc:1.0`).
2. `server.py` prepends this directory to `sys.path`, imports `CdcRdcAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, CdcRdcAgent)`.
3. Importing `agent.py` sets `spec = EDAAgent.read_spec(<this directory>)`, loading `config.yaml` at class definition time.
4. Uvicorn serves FastAPI `app` on `connection.port` with `/health` and `/tasks/execute`.
5. On `/tasks/execute`, `EDAAgent.handle` assembles engineering-memory context (see `context` in YAML), journals the task, and dispatches the requested skill.
6. The skill callable in `tools.py` returns `tool_observation(...)`. With `backend.type: none`, observations are safe stubs (`not_run`) until `EDA_FRAMEWORK` or another adapter binds real engines.

## Related agents

- Stage index: [`../README.md`](../README.md) (rtl specialists under `rtl/`).
- Stage lead(s) that delegate here:
  - [`rtl_lead`](../rtl_lead/) (port **8208**)
- Sibling agents in this folder:
  - [`clock_reset`](../clock_reset/) — worker, port **8210**
  - [`lint_quality`](../lint_quality/) — worker, port **8213**
  - [`low_power`](../low_power/) — worker, port **8212**
  - [`rtl_implementation`](../rtl_implementation/) — worker, port **8209**
  - [`rtl_integration`](../rtl_integration/) — worker, port **8214**
  - [`rtl_lead`](../rtl_lead/) — lead, port **8208**
- Track overview: [`../../README.md`](../../README.md) (frontend architecture, RTL, verification).

## Files in this directory

| File | Role |
|------|------|
| `agent.py` | Defines `CdcRdcAgent`; loads sibling `config.yaml` into `spec`. |
| `server.py` | HTTP/ASGI bootstrap; exports FastAPI `app` for uvicorn. |
| `tools.py` | `@tool` skill callables; stable EDA operation contracts. |
| `config.yaml` | Fleet manifest (`apiVersion: agentfleet/v1`): boundaries, port, skills, memory, telemetry. |
| `Dockerfile` | Container image; `EXPOSE 8211`; `CMD python server.py`. |
| `requirements.txt` | FastAPI, uvicorn, pydantic, PyYAML for the HTTP surface. |
| `__init__.py` | Re-exports `CdcRdcAgent` for imports without starting HTTP. |
| `README.md` | This document. |

## Tool reference

### `analyze_cdc` (`tools.analyze_cdc`)

**Action:** `submit_tool_job`. List clock-domain crossings and their synchronizers.

### `analyze_rdc` (`tools.analyze_rdc`)

**Action:** `submit_tool_job`. List reset-domain crossings.

### `read_cdc_report` (`tools.read_cdc_report`)

**Action:** `read_reports`. Read a CDC report and its waiver candidates.

### `read_rdc_report` (`tools.read_rdc_report`)

**Action:** `read_reports`. Read an RDC report.

### `classify_crossing` (`tools.classify_crossing`)

**Action:** `read_reports`. Classify one crossing as synchronized, unsynchronized, or waived-pending.

### `trace_crossing_path` (`tools.trace_crossing_path`)

**Action:** `read_reports`. Trace the source and destination registers of one crossing.

### `write_synchronizer` (`tools.write_synchronizer`)

**Action:** `write_candidate`. Add one synchronizer on an isolated candidate.

### `write_waiver_proposal` (`tools.write_waiver_proposal`)

**Action:** `write_candidate`. Write an unsigned waiver proposal with scope and rationale. It is not approved.

### `check_reconvergence` (`tools.check_reconvergence`)

**Action:** `submit_tool_job`. Check reconvergent crossings that a single synchronizer does not cover.

### `propose_waiver_or_fix` (`tools.propose_waiver_or_fix`)

**Action:** `publish_finding`. Publish either a bounded RTL fix or an unsigned waiver proposal.

### `flag_unsynchronized_crossing` (`tools.flag_unsynchronized_crossing`)

**Action:** `publish_finding`. Publish a crossing that has no synchronizer and no waiver proposal.

### `record_cdc_tool_version` (`tools.record_cdc_tool_version`)

**Action:** `publish_finding`. Record the CDC/RDC tool, version, and rule set used.

## Runtime, memory, and context

- **Reliability:** task timeout 120s, max retries 1, on failure `replan`.
- **Execution:** `direct_function`, `max_tasks=1`.
- **Context include:** `requirements`, `interface_contracts`, `canonical_source`, `open_findings`, `experiments`.
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
