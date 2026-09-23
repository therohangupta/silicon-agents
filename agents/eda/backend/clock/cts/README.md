# CTS Agent (`cts`)

This directory is the deployable microservice package for the **CTS Agent** in the fleet **clock** stage (role `worker`).

## EDA responsibility

Build and optimize a clock tree or mesh for the required modes and corners. Adapter target: OpenROAD clock_tree_synthesis.

As a **worker**, this process executes bounded skills on isolated candidates and reports observations. Promotion and program-level tradeoffs stay with leads and humans.

## Identity and HTTP port

| Field | Value |
|-------|-------|
| Agent id | `cts` |
| Stage | `clock` |
| Role | `worker` |
| Host | `host.docker.internal` |
| Port | **8247** (must match `Dockerfile` `EXPOSE`) |
| Health | `/health` |
| Execute | `/tasks/execute` |

## Boundaries

Hard limits from `config.yaml` `boundary`. The planner and `EDAAgent` enforce these even when a tool adapter could physically perform a forbidden action.

### May

- Submit clock-tree synthesis on an isolated candidate
- Write clock targets
- Report skew, insertion delay, transition, and power

### May not

- Edit the placement to hide skew
- Drop a test clock
- Promote a candidate onto the canonical baseline
- Approve a waiver or relax a hard requirement
- Treat its own summary as independent signoff

## Skills

Skills bind planner task ids to callables in `tools.py` (`module: tools`, `execution.mode: direct_function`).

| Skill id | Action | Callable | Description |
|----------|--------|----------|-------------|
| `read_clock_spec` | `read_reports` | `read_clock_spec` | Read clocks, generated clocks, targets, and test clocks. |
| `write_clock_transition_target` | `write_candidate` | `write_clock_transition_target` | Write the transition target for one clock. |
| `write_clock_skew_target` | `write_candidate` | `write_clock_skew_target` | Write the skew target for one clock. |
| `write_clock_sink_rules` | `write_candidate` | `write_clock_sink_rules` | Write sink clustering and buffer rules. |
| `build_clock_tree` | `submit_tool_job` | `build_clock_tree` | Run clock-tree synthesis for the required modes. Adapter target: OpenROAD clock_tree_synthesis. |
| `repair_clock_nets` | `submit_tool_job` | `repair_clock_nets` | Repair clock nets on the isolated candidate. Adapter target: OpenROAD repair_clock_nets. |
| `repair_clock_inverters` | `submit_tool_job` | `repair_clock_inverters` | Balance clock inverters on the isolated candidate. |
| `report_skew_and_insertion` | `read_reports` | `report_skew_and_insertion` | Report skew, insertion delay, transition, and power. |
| `report_clock_latency` | `read_reports` | `report_clock_latency` | Report latency by sink region. |
| `report_clock_transition` | `read_reports` | `report_clock_transition` | Report sinks over the transition limit. |
| `report_clock_power` | `read_reports` | `report_clock_power` | Report clock-network power. |
| `check_test_clock_built` | `read_reports` | `check_test_clock_built` | Check that every required test clock was built. |
| `write_cts_def` | `write_candidate` | `write_cts_def` | Write the clocked DEF. |
| `flag_dropped_test_clock` | `publish_finding` | `flag_dropped_test_clock` | Publish a required test clock that CTS did not build. |
| `record_cts_provenance` | `publish_finding` | `record_cts_provenance` | Record the CTS recipe, corners, and DEF ref. |

## Delegation

This agent declares **no** `delegates_to` entries. It executes its own `tools.py` skills when scheduled by a lead or the chip-flow orchestrator.

## Boot path

Every fleet agent shares the same linear startup so compose and local dev behave identically.

1. Container or shell runs `python server.py` (`deployment.dockerfile` / image `agentfleet/cts:1.0`).
2. `server.py` prepends this directory to `sys.path`, imports `CtsAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, CtsAgent)`.
3. Importing `agent.py` sets `spec = EDAAgent.read_spec(<this directory>)`, loading `config.yaml` at class definition time.
4. Uvicorn serves FastAPI `app` on `connection.port` with `/health` and `/tasks/execute`.
5. On `/tasks/execute`, `EDAAgent.handle` assembles engineering-memory context (see `context` in YAML), journals the task, and dispatches the requested skill.
6. The skill callable in `tools.py` returns `tool_observation(...)`. With `backend.type: none`, observations are safe stubs (`not_run`) until `EDA_FRAMEWORK` or another adapter binds real engines.

## Related agents

- Stage index: [`../README.md`](../README.md) (clock specialists under `clock/`).
- Program orchestrator:
  - [`chip_flow_lead`](../../../chip_flow_lead/) (port **8201**)
- Sibling agents in this folder:
  - [`clock_validation`](../clock_validation/) — validator, port **8248**
- Track overview: [`../../README.md`](../../README.md) (backend physical implementation).

## Files in this directory

| File | Role |
|------|------|
| `agent.py` | Defines `CtsAgent`; loads sibling `config.yaml` into `spec`. |
| `server.py` | HTTP/ASGI bootstrap; exports FastAPI `app` for uvicorn. |
| `tools.py` | `@tool` skill callables; stable EDA operation contracts. |
| `config.yaml` | Fleet manifest (`apiVersion: agentfleet/v1`): boundaries, port, skills, memory, telemetry. |
| `Dockerfile` | Container image; `EXPOSE 8247`; `CMD python server.py`. |
| `requirements.txt` | FastAPI, uvicorn, pydantic, PyYAML for the HTTP surface. |
| `__init__.py` | Re-exports `CtsAgent` for imports without starting HTTP. |
| `README.md` | This document. |

## Tool reference

### `read_clock_spec` (`tools.read_clock_spec`)

**Action:** `read_reports`. Read clocks, generated clocks, targets, and test clocks.

Read clocks, generated clocks, targets, and test clocks from constraints.

### `write_clock_transition_target` (`tools.write_clock_transition_target`)

**Action:** `write_candidate`. Write the transition target for one clock.

Write the max transition target for one clock network.

### `write_clock_skew_target` (`tools.write_clock_skew_target`)

**Action:** `write_candidate`. Write the skew target for one clock.

Write the skew target for one clock network.

### `write_clock_sink_rules` (`tools.write_clock_sink_rules`)

**Action:** `write_candidate`. Write sink clustering and buffer rules.

Write sink clustering and buffer/inverter rules for CTS.

### `build_clock_tree` (`tools.build_clock_tree`)

**Action:** `submit_tool_job`. Run clock-tree synthesis for the required modes. Adapter target: OpenROAD clock_tree_synthesis.

Run OpenROAD clock_tree_synthesis for the required modes.

### `repair_clock_nets` (`tools.repair_clock_nets`)

**Action:** `submit_tool_job`. Repair clock nets on the isolated candidate. Adapter target: OpenROAD repair_clock_nets.

Repair clock nets on the isolated candidate (OpenROAD repair_clock_nets).

### `repair_clock_inverters` (`tools.repair_clock_inverters`)

**Action:** `submit_tool_job`. Balance clock inverters on the isolated candidate.

Balance or fix clock inverter stages on the candidate.

### `report_skew_and_insertion` (`tools.report_skew_and_insertion`)

**Action:** `read_reports`. Report skew, insertion delay, transition, and power.

Report skew, insertion delay, transition, and clock power.

### `report_clock_latency` (`tools.report_clock_latency`)

**Action:** `read_reports`. Report latency by sink region.

Report latency by sink region for the built tree.

### `report_clock_transition` (`tools.report_clock_transition`)

**Action:** `read_reports`. Report sinks over the transition limit.

Report sinks still over the transition limit.

### `report_clock_power` (`tools.report_clock_power`)

**Action:** `read_reports`. Report clock-network power.

Report clock-network dynamic/leakage power.

### `check_test_clock_built` (`tools.check_test_clock_built`)

**Action:** `read_reports`. Check that every required test clock was built.

Check that every required DFT/test clock was constructed.

### `write_cts_def` (`tools.write_cts_def`)

**Action:** `write_candidate`. Write the clocked DEF.

Write the clocked DEF/ODB artifact after CTS.

### `flag_dropped_test_clock` (`tools.flag_dropped_test_clock`)

**Action:** `publish_finding`. Publish a required test clock that CTS did not build.

Finding: a required test clock was dropped from the tree.

### `record_cts_provenance` (`tools.record_cts_provenance`)

**Action:** `publish_finding`. Record the CTS recipe, corners, and DEF ref.

Record CTS recipe, targets, and tool versions.

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
- **Shared base:** Task handling lives in `domains/eda/runtime/agent.py`; HTTP wiring in `domains/eda/runtime/server.py`.
- **Telemetry:** See [`../../TELEMETRY.md`](../../TELEMETRY.md) (path may vary by depth) for fleet-wide observability conventions.

## How a newcomer should read this agent

1. Read `config.yaml` `metadata`, `boundary`, and `capabilities` for charter and limits.
2. Skim the skills table above, then open `tools.py` for parameter shapes.
3. Read `agent.py` and `server.py` only to confirm boot wiring.
4. Treat `Dockerfile` / `requirements.txt` as deployment detail.
