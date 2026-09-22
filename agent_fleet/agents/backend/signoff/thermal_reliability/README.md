# Thermal and Reliability Agent (`thermal_reliability`)

This directory is the deployable microservice package for the **Thermal and Reliability Agent** in the fleet **signoff** stage (role `worker`).

## EDA responsibility

Evaluate temperature, aging, variation, and reliability margins, and turn risks into constraints or an isolated physical change.

As a **worker**, this process executes bounded skills on isolated candidates and reports observations. Promotion and program-level tradeoffs stay with leads and humans.

## Identity and HTTP port

| Field | Value |
|-------|-------|
| Agent id | `thermal_reliability` |
| Stage | `signoff` |
| Role | `worker` |
| Host | `host.docker.internal` |
| Port | **8259** (must match `Dockerfile` `EXPOSE`) |
| Health | `/health` |
| Execute | `/tasks/execute` |

## Boundaries

Hard limits from `config.yaml` `boundary`. The planner and `EdaAgent` enforce these even when a tool adapter could physically perform a forbidden action.

### May

- Read thermal and aging reports
- Write a proposed constraint or an isolated physical change
- Publish a reliability finding

### May not

- Raise a temperature limit to pass
- Edit the package
- Edit the canonical database
- Promote a candidate onto the canonical baseline
- Approve a waiver or relax a hard requirement
- Treat its own summary as independent signoff

## Skills

Skills bind planner task ids to callables in `tools.py` (`module: tools`, `execution.mode: direct_function`).

| Skill id | Action | Callable | Description |
|----------|--------|----------|-------------|
| `read_thermal_map` | `read_reports` | `read_thermal_map` | Read the temperature distribution. |
| `evaluate_thermal_map` | `read_reports` | `evaluate_thermal_map` | Summarize hotspots and the power sources under them. |
| `read_aging_report` | `read_reports` | `read_aging_report` | Read aging and variation margins. |
| `evaluate_aging_margin` | `publish_finding` | `evaluate_aging_margin` | Report aging and variation margins that miss the requirement. |
| `read_reliability_limits` | `read_reports` | `read_reliability_limits` | Read the temperature, EM, and aging limits. |
| `write_thermal_constraint_proposal` | `write_candidate` | `write_thermal_constraint_proposal` | Write a proposed timing or placement constraint. This does not edit the canonical constraints. |
| `apply_thermal_physical_change` | `write_candidate` | `apply_thermal_physical_change` | Apply one physical change on an isolated candidate. |
| `check_thermal_feedback` | `submit_tool_job` | `check_thermal_feedback` | Check how the temperature map changes leakage and delay. |
| `compare_thermal_to_limit` | `read_reports` | `compare_thermal_to_limit` | Compare hotspot temperature with the limit. |
| `flag_hotspot_over_limit` | `publish_finding` | `flag_hotspot_over_limit` | Publish a hotspot over the temperature limit. |
| `flag_raised_thermal_limit` | `publish_finding` | `flag_raised_thermal_limit` | Publish an analysis that passed only because a limit was raised. |
| `record_thermal_provenance` | `publish_finding` | `record_thermal_provenance` | Record the thermal model, power map, and package assumption. |

## Delegation

This agent declares **no** `delegates_to` entries. It executes its own `tools.py` skills when scheduled by a lead or the chip-flow orchestrator.

## Boot path

Every fleet agent shares the same linear startup so compose and local dev behave identically.

1. Container or shell runs `python server.py` (`deployment.dockerfile` / image `agentfleet/thermal_reliability:1.0`).
2. `server.py` prepends this directory to `sys.path`, imports `ThermalReliabilityAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, ThermalReliabilityAgent)`.
3. Importing `agent.py` sets `spec = EdaAgent.read_spec(<this directory>)`, loading `config.yaml` at class definition time.
4. Uvicorn serves FastAPI `app` on `connection.port` with `/health` and `/tasks/execute`.
5. On `/tasks/execute`, `EdaAgent.handle` assembles engineering-memory context (see `context` in YAML), journals the task, and dispatches the requested skill.
6. The skill callable in `tools.py` returns `tool_observation(...)`. With `backend.type: none`, observations are safe stubs (`not_run`) until `EDA_FRAMEWORK` or another adapter binds real engines.

## Related agents

- Stage index: [`../README.md`](../README.md) (signoff specialists under `signoff/`).
- Sibling agents in this folder:
  - [`drc_lvs`](../drc_lvs/) — worker, port **8260**
  - [`eco_lead`](../eco_lead/) — lead, port **8261**
  - [`extraction`](../extraction/) — worker, port **8254**
  - [`ir_em`](../ir_em/) — worker, port **8258**
  - [`power_analysis`](../power_analysis/) — worker, port **8257**
  - [`signoff_validator`](../signoff_validator/) — validator, port **8262**
  - [`sta_lead`](../sta_lead/) — lead, port **8255**
  - [`timing_debug`](../timing_debug/) — worker, port **8256**
- Track overview: [`../../README.md`](../../README.md) (backend physical implementation).

## Files in this directory

| File | Role |
|------|------|
| `agent.py` | Defines `ThermalReliabilityAgent`; loads sibling `config.yaml` into `spec`. |
| `server.py` | HTTP/ASGI bootstrap; exports FastAPI `app` for uvicorn. |
| `tools.py` | `@tool` skill callables; stable EDA operation contracts. |
| `config.yaml` | Fleet manifest (`apiVersion: agentfleet/v1`): boundaries, port, skills, memory, telemetry. |
| `Dockerfile` | Container image; `EXPOSE 8259`; `CMD python server.py`. |
| `requirements.txt` | FastAPI, uvicorn, pydantic, PyYAML for the HTTP surface. |
| `__init__.py` | Re-exports `ThermalReliabilityAgent` for imports without starting HTTP. |
| `README.md` | This document. |

## Tool reference

### `read_thermal_map` (`tools.read_thermal_map`)

**Action:** `read_reports`. Read the temperature distribution.

### `evaluate_thermal_map` (`tools.evaluate_thermal_map`)

**Action:** `read_reports`. Summarize hotspots and the power sources under them.

### `read_aging_report` (`tools.read_aging_report`)

**Action:** `read_reports`. Read aging and variation margins.

### `evaluate_aging_margin` (`tools.evaluate_aging_margin`)

**Action:** `publish_finding`. Report aging and variation margins that miss the requirement.

### `read_reliability_limits` (`tools.read_reliability_limits`)

**Action:** `read_reports`. Read the temperature, EM, and aging limits.

### `write_thermal_constraint_proposal` (`tools.write_thermal_constraint_proposal`)

**Action:** `write_candidate`. Write a proposed timing or placement constraint. This does not edit the canonical constraints.

### `apply_thermal_physical_change` (`tools.apply_thermal_physical_change`)

**Action:** `write_candidate`. Apply one physical change on an isolated candidate.

### `check_thermal_feedback` (`tools.check_thermal_feedback`)

**Action:** `submit_tool_job`. Check how the temperature map changes leakage and delay.

### `compare_thermal_to_limit` (`tools.compare_thermal_to_limit`)

**Action:** `read_reports`. Compare hotspot temperature with the limit.

### `flag_hotspot_over_limit` (`tools.flag_hotspot_over_limit`)

**Action:** `publish_finding`. Publish a hotspot over the temperature limit.

### `flag_raised_thermal_limit` (`tools.flag_raised_thermal_limit`)

**Action:** `publish_finding`. Publish an analysis that passed only because a limit was raised.

### `record_thermal_provenance` (`tools.record_thermal_provenance`)

**Action:** `publish_finding`. Record the thermal model, power map, and package assumption.

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
