# Power-Analysis Agent (`power_analysis`)

This directory is the deployable microservice package for the **Power-Analysis Agent** in the fleet **signoff** stage (role `worker`).

## EDA responsibility

Estimate vector-based or vectorless dynamic power, leakage, and clock power, and compare them with the block budget. Adapter target: OpenROAD report_power, then a signoff power tool.

As a **worker**, this process executes bounded skills on isolated candidates and reports observations. Promotion and program-level tradeoffs stay with leads and humans.

## Identity and HTTP port

| Field | Value |
|-------|-------|
| Agent id | `power_analysis` |
| Stage | `signoff` |
| Role | `worker` |
| Host | `host.docker.internal` |
| Port | **8257** (must match `Dockerfile` `EXPOSE`) |
| Health | `/health` |
| Execute | `/tasks/execute` |

## Boundaries

Hard limits from `config.yaml` `boundary`. The planner and `EDAAgent` enforce these even when a tool adapter could physically perform a forbidden action.

### May

- Submit a power analysis
- Read activity and the budget
- Publish the dominant contributors

### May not

- Change the activity file to meet the budget
- Edit RTL
- Promote a candidate onto the canonical baseline
- Approve a waiver or relax a hard requirement
- Treat its own summary as independent signoff

## Skills

Skills bind planner task ids to callables in `tools.py` (`module: tools`, `execution.mode: direct_function`).

| Skill id | Action | Callable | Description |
|----------|--------|----------|-------------|
| `read_power_budget` | `read_reports` | `read_power_budget` | Read the block and chip power budgets. |
| `read_activity_file` | `read_reports` | `read_activity_file` | Read the switching activity and its source. |
| `run_vector_power` | `submit_tool_job` | `run_vector_power` | Run vector-based power analysis. |
| `run_vectorless_power` | `submit_tool_job` | `run_vectorless_power` | Run vectorless power analysis. |
| `report_dynamic_power` | `read_reports` | `report_dynamic_power` | Report dynamic power. |
| `report_leakage_power` | `read_reports` | `report_leakage_power` | Report leakage power. |
| `report_clock_network_power` | `read_reports` | `report_clock_network_power` | Report clock-network power from the power analysis. |
| `identify_power_contributors` | `publish_finding` | `identify_power_contributors` | List the blocks and clocks that dominate power. |
| `compare_power_to_budget` | `read_reports` | `compare_power_to_budget` | Compare the estimate with the block and chip budgets. |
| `report_activity_uncertainty` | `read_reports` | `report_activity_uncertainty` | Report which power numbers move when activity changes. |
| `flag_power_over_budget` | `publish_finding` | `flag_power_over_budget` | Publish an estimate that crosses the budget. |
| `record_power_analysis_provenance` | `publish_finding` | `record_power_analysis_provenance` | Record the activity file, corner, and tool version. |

## Delegation

This agent declares **no** `delegates_to` entries. It executes its own `tools.py` skills when scheduled by a lead or the chip-flow orchestrator.

## Boot path

Every fleet agent shares the same linear startup so compose and local dev behave identically.

1. Container or shell runs `python server.py` (`deployment.dockerfile` / image `agentfleet/power_analysis:1.0`).
2. `server.py` prepends this directory to `sys.path`, imports `PowerAnalysisAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, PowerAnalysisAgent)`.
3. Importing `agent.py` sets `spec = EDAAgent.read_spec(<this directory>)`, loading `config.yaml` at class definition time.
4. Uvicorn serves FastAPI `app` on `connection.port` with `/health` and `/tasks/execute`.
5. On `/tasks/execute`, `EDAAgent.handle` assembles engineering-memory context (see `context` in YAML), journals the task, and dispatches the requested skill.
6. The skill callable in `tools.py` returns `tool_observation(...)`. With `backend.type: none`, observations are safe stubs (`not_run`) until `EDA_FRAMEWORK` or another adapter binds real engines.

## Related agents

- Stage index: [`../README.md`](../README.md) (signoff specialists under `signoff/`).
- Sibling agents in this folder:
  - [`drc_lvs`](../drc_lvs/) — worker, port **8260**
  - [`eco_lead`](../eco_lead/) — lead, port **8261**
  - [`extraction`](../extraction/) — worker, port **8254**
  - [`ir_em`](../ir_em/) — worker, port **8258**
  - [`signoff_validator`](../signoff_validator/) — validator, port **8262**
  - [`sta_lead`](../sta_lead/) — lead, port **8255**
  - [`thermal_reliability`](../thermal_reliability/) — worker, port **8259**
  - [`timing_debug`](../timing_debug/) — worker, port **8256**
- Track overview: [`../../README.md`](../../README.md) (backend physical implementation).

## Files in this directory

| File | Role |
|------|------|
| `agent.py` | Defines `PowerAnalysisAgent`; loads sibling `config.yaml` into `spec`. |
| `server.py` | HTTP/ASGI bootstrap; exports FastAPI `app` for uvicorn. |
| `tools.py` | `@tool` skill callables; stable EDA operation contracts. |
| `config.yaml` | Fleet manifest (`apiVersion: agentfleet/v1`): boundaries, port, skills, memory, telemetry. |
| `Dockerfile` | Container image; `EXPOSE 8257`; `CMD python server.py`. |
| `requirements.txt` | FastAPI, uvicorn, pydantic, PyYAML for the HTTP surface. |
| `__init__.py` | Re-exports `PowerAnalysisAgent` for imports without starting HTTP. |
| `README.md` | This document. |

## Tool reference

### `read_power_budget` (`tools.read_power_budget`)

**Action:** `read_reports`. Read the block and chip power budgets.

### `read_activity_file` (`tools.read_activity_file`)

**Action:** `read_reports`. Read the switching activity and its source.

### `run_vector_power` (`tools.run_vector_power`)

**Action:** `submit_tool_job`. Run vector-based power analysis.

### `run_vectorless_power` (`tools.run_vectorless_power`)

**Action:** `submit_tool_job`. Run vectorless power analysis.

### `report_dynamic_power` (`tools.report_dynamic_power`)

**Action:** `read_reports`. Report dynamic power.

### `report_leakage_power` (`tools.report_leakage_power`)

**Action:** `read_reports`. Report leakage power.

### `report_clock_network_power` (`tools.report_clock_network_power`)

**Action:** `read_reports`. Report clock-network power from the power analysis.

### `identify_power_contributors` (`tools.identify_power_contributors`)

**Action:** `publish_finding`. List the blocks and clocks that dominate power.

### `compare_power_to_budget` (`tools.compare_power_to_budget`)

**Action:** `read_reports`. Compare the estimate with the block and chip budgets.

### `report_activity_uncertainty` (`tools.report_activity_uncertainty`)

**Action:** `read_reports`. Report which power numbers move when activity changes.

### `flag_power_over_budget` (`tools.flag_power_over_budget`)

**Action:** `publish_finding`. Publish an estimate that crosses the budget.

### `record_power_analysis_provenance` (`tools.record_power_analysis_provenance`)

**Action:** `publish_finding`. Record the activity file, corner, and tool version.

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
