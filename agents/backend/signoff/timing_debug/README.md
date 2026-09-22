# Timing-Debug Agent (`timing_debug`)

This directory is the deployable microservice package for the **Timing-Debug Agent** in the fleet **signoff** stage (role `worker`).

## EDA responsibility

Run STA queries, classify setup, hold, recovery, removal, and clock failures, and trace them to a physical or logical cause. Adapter target: OpenSTA report_checks.

As a **worker**, this process executes bounded skills on isolated candidates and reports observations. Promotion and program-level tradeoffs stay with leads and humans.

## Identity and HTTP port

| Field | Value |
|-------|-------|
| Agent id | `timing_debug` |
| Stage | `signoff` |
| Role | `worker` |
| Host | `host.docker.internal` |
| Port | **8256** (must match `Dockerfile` `EXPOSE`) |
| Health | `/health` |
| Execute | `/tasks/execute` |

## Boundaries

Hard limits from `config.yaml` `boundary`. The planner and `EdaAgent` enforce these even when a tool adapter could physically perform a forbidden action.

### May

- Submit STA and path reports
- Publish a path-group diagnosis

### May not

- Edit the netlist
- Add a timing exception
- Promote a candidate onto the canonical baseline
- Approve a waiver or relax a hard requirement
- Treat its own summary as independent signoff

## Skills

Skills bind planner task ids to callables in `tools.py` (`module: tools`, `execution.mode: direct_function`).

| Skill id | Action | Callable | Description |
|----------|--------|----------|-------------|
| `run_sta` | `submit_tool_job` | `run_sta` | Run static timing for one mode and corner. Adapter target: OpenSTA. |
| `report_checks` | `submit_tool_job` | `report_checks` | Report timing checks. Adapter target: OpenSTA report_checks. |
| `report_wns` | `read_reports` | `report_wns` | Report worst negative slack. |
| `report_tns` | `read_reports` | `report_tns` | Report total negative slack. |
| `classify_timing_paths` | `read_reports` | `classify_timing_paths` | Group setup, hold, recovery, and removal violations. |
| `classify_clock_path_failures` | `read_reports` | `classify_clock_path_failures` | Group clock, pulse-width, and generated-clock failures. |
| `trace_path_cause` | `publish_finding` | `trace_path_cause` | Trace a path group to logic depth, placement, clock, or constraint. |
| `report_path_details` | `read_reports` | `report_path_details` | Report startpoint, endpoint, cells, and capacitance for one path. |
| `report_path_physical_span` | `read_reports` | `report_path_physical_span` | Report the placement span and layers of one path. |
| `diff_timing_against_baseline` | `read_reports` | `diff_timing_against_baseline` | Show paths that newly fail or newly pass. |
| `flag_unconstrained_endpoint` | `publish_finding` | `flag_unconstrained_endpoint` | Publish an endpoint with no timing check. |
| `record_sta_tool_version` | `publish_finding` | `record_sta_tool_version` | Record the STA tool, version, SPEF, and SDC. |

## Delegation

This agent declares **no** `delegates_to` entries. It executes its own `tools.py` skills when scheduled by a lead or the chip-flow orchestrator.

## Boot path

Every fleet agent shares the same linear startup so compose and local dev behave identically.

1. Container or shell runs `python server.py` (`deployment.dockerfile` / image `agentfleet/timing_debug:1.0`).
2. `server.py` prepends this directory to `sys.path`, imports `TimingDebugAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, TimingDebugAgent)`.
3. Importing `agent.py` sets `spec = EdaAgent.read_spec(<this directory>)`, loading `config.yaml` at class definition time.
4. Uvicorn serves FastAPI `app` on `connection.port` with `/health` and `/tasks/execute`.
5. On `/tasks/execute`, `EdaAgent.handle` assembles engineering-memory context (see `context` in YAML), journals the task, and dispatches the requested skill.
6. The skill callable in `tools.py` returns `tool_observation(...)`. With `backend.type: none`, observations are safe stubs (`not_run`) until `EDA_FRAMEWORK` or another adapter binds real engines.

## Related agents

- Stage index: [`../README.md`](../README.md) (signoff specialists under `signoff/`).
- Stage lead(s) that delegate here:
  - [`eco_lead`](../eco_lead/) (port **8261**)
  - [`sta_lead`](../sta_lead/) (port **8255**)
- Sibling agents in this folder:
  - [`drc_lvs`](../drc_lvs/) — worker, port **8260**
  - [`eco_lead`](../eco_lead/) — lead, port **8261**
  - [`extraction`](../extraction/) — worker, port **8254**
  - [`ir_em`](../ir_em/) — worker, port **8258**
  - [`power_analysis`](../power_analysis/) — worker, port **8257**
  - [`signoff_validator`](../signoff_validator/) — validator, port **8262**
  - [`sta_lead`](../sta_lead/) — lead, port **8255**
  - [`thermal_reliability`](../thermal_reliability/) — worker, port **8259**
- Track overview: [`../../README.md`](../../README.md) (backend physical implementation).

## Files in this directory

| File | Role |
|------|------|
| `agent.py` | Defines `TimingDebugAgent`; loads sibling `config.yaml` into `spec`. |
| `server.py` | HTTP/ASGI bootstrap; exports FastAPI `app` for uvicorn. |
| `tools.py` | `@tool` skill callables; stable EDA operation contracts. |
| `config.yaml` | Fleet manifest (`apiVersion: agentfleet/v1`): boundaries, port, skills, memory, telemetry. |
| `Dockerfile` | Container image; `EXPOSE 8256`; `CMD python server.py`. |
| `requirements.txt` | FastAPI, uvicorn, pydantic, PyYAML for the HTTP surface. |
| `__init__.py` | Re-exports `TimingDebugAgent` for imports without starting HTTP. |
| `README.md` | This document. |

## Tool reference

### `run_sta` (`tools.run_sta`)

**Action:** `submit_tool_job`. Run static timing for one mode and corner. Adapter target: OpenSTA.

### `report_checks` (`tools.report_checks`)

**Action:** `submit_tool_job`. Report timing checks. Adapter target: OpenSTA report_checks.

### `report_wns` (`tools.report_wns`)

**Action:** `read_reports`. Report worst negative slack.

### `report_tns` (`tools.report_tns`)

**Action:** `read_reports`. Report total negative slack.

### `classify_timing_paths` (`tools.classify_timing_paths`)

**Action:** `read_reports`. Group setup, hold, recovery, and removal violations.

### `classify_clock_path_failures` (`tools.classify_clock_path_failures`)

**Action:** `read_reports`. Group clock, pulse-width, and generated-clock failures.

### `trace_path_cause` (`tools.trace_path_cause`)

**Action:** `publish_finding`. Trace a path group to logic depth, placement, clock, or constraint.

### `report_path_details` (`tools.report_path_details`)

**Action:** `read_reports`. Report startpoint, endpoint, cells, and capacitance for one path.

### `report_path_physical_span` (`tools.report_path_physical_span`)

**Action:** `read_reports`. Report the placement span and layers of one path.

### `diff_timing_against_baseline` (`tools.diff_timing_against_baseline`)

**Action:** `read_reports`. Show paths that newly fail or newly pass.

### `flag_unconstrained_endpoint` (`tools.flag_unconstrained_endpoint`)

**Action:** `publish_finding`. Publish an endpoint with no timing check.

### `record_sta_tool_version` (`tools.record_sta_tool_version`)

**Action:** `publish_finding`. Record the STA tool, version, SPEF, and SDC.

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
- **Shared base:** Task handling lives in `domains/eda/agent.py`; HTTP wiring in `domains/eda/server.py`.
- **Telemetry:** See [`../../TELEMETRY.md`](../../TELEMETRY.md) (path may vary by depth) for fleet-wide observability conventions.

## How a newcomer should read this agent

1. Read `config.yaml` `metadata`, `boundary`, and `capabilities` for charter and limits.
2. Skim the skills table above, then open `tools.py` for parameter shapes.
3. Read `agent.py` and `server.py` only to confirm boot wiring.
4. Treat `Dockerfile` / `requirements.txt` as deployment detail.
