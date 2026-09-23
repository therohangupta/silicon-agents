# ATPG Campaign Agent (`atpg_campaign`)

This directory is the deployable microservice package for the **ATPG Campaign Agent** in the fleet **dft** stage (role `worker`).

## EDA responsibility

ATPG Campaign agent class (atpg_campaign).

Charter from `config.yaml`: Generate and analyze deterministic pattern campaigns across the required fault models.

As a **worker**, this process executes bounded skills on isolated candidates and reports observations. Promotion and program-level tradeoffs stay with leads and humans.

## Identity and HTTP port

| Field | Value |
|-------|-------|
| Agent id | `atpg_campaign` |
| Stage | `dft` |
| Role | `worker` |
| Host | `host.docker.internal` |
| Port | **8227** (must match `Dockerfile` `EXPOSE`) |
| Health | `/health` |
| Execute | `/tasks/execute` |

## Boundaries

Hard limits from `config.yaml` `boundary`. The planner and `EDAAgent` enforce these even when a tool adapter could physically perform a forbidden action.

### May

- Submit an ATPG job
- Write pattern budgets
- Publish fault coverage, pattern count, and test power

### May not

- Drop a fault model from the contract
- Edit RTL
- Promote a candidate onto the canonical baseline
- Approve a waiver or relax a hard requirement
- Treat its own summary as independent signoff

## Skills

Skills bind planner task ids to callables in `tools.py` (`module: tools`, `execution.mode: direct_function`).

| Skill id | Action | Callable | Description |
|----------|--------|----------|-------------|
| `write_fault_model_list` | `write_candidate` | `write_fault_model_list` | Write the fault models this campaign must cover. Do not omit a required model. |
| `write_pattern_budget` | `write_candidate` | `write_pattern_budget` | Write the pattern-count and tester-time budget. |
| `generate_stuck_at_patterns` | `submit_tool_job` | `generate_stuck_at_patterns` | Generate stuck-at patterns. |
| `generate_transition_patterns` | `submit_tool_job` | `generate_transition_patterns` | Generate transition-delay patterns. |
| `generate_path_delay_patterns` | `submit_tool_job` | `generate_path_delay_patterns` | Generate path-delay patterns for the listed paths. |
| `generate_iddq_patterns` | `submit_tool_job` | `generate_iddq_patterns` | Generate IDDQ patterns when the contract requires them. |
| `read_fault_coverage` | `read_reports` | `read_fault_coverage` | Read coverage, untestable faults, and aborted faults by model. |
| `read_pattern_count` | `read_reports` | `read_pattern_count` | Read pattern count and estimated tester time. |
| `read_test_power` | `read_reports` | `read_test_power` | Read shift and capture power. |
| `compare_coverage_to_requirement` | `read_reports` | `compare_coverage_to_requirement` | Compare each fault model with its required coverage. |
| `analyze_fault_coverage` | `publish_finding` | `analyze_fault_coverage` | Publish coverage, pattern count, tester time, and test power. |
| `flag_dropped_fault_model` | `publish_finding` | `flag_dropped_fault_model` | Publish a campaign that omitted a required fault model. |
| `flag_test_power_over_budget` | `publish_finding` | `flag_test_power_over_budget` | Publish shift or capture power above the budget. |
| `record_atpg_tool_version` | `publish_finding` | `record_atpg_tool_version` | Record the ATPG tool, version, and fault-model settings. |

## Delegation

This agent declares **no** `delegates_to` entries. It executes its own `tools.py` skills when scheduled by a lead or the chip-flow orchestrator.

## Boot path

Every fleet agent shares the same linear startup so compose and local dev behave identically.

1. Container or shell runs `python server.py` (`deployment.dockerfile` / image `agentfleet/atpg_campaign:1.0`).
2. `server.py` prepends this directory to `sys.path`, imports `AtpgCampaignAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, AtpgCampaignAgent)`.
3. Importing `agent.py` sets `spec = EDAAgent.read_spec(<this directory>)`, loading `config.yaml` at class definition time.
4. Uvicorn serves FastAPI `app` on `connection.port` with `/health` and `/tasks/execute`.
5. On `/tasks/execute`, `EDAAgent.handle` assembles engineering-memory context (see `context` in YAML), journals the task, and dispatches the requested skill.
6. The skill callable in `tools.py` returns `tool_observation(...)`. With `backend.type: none`, observations are safe stubs (`not_run`) until `EDA_FRAMEWORK` or another adapter binds real engines.

## Related agents

- Stage index: [`../README.md`](../README.md) (dft specialists under `dft/`).
- Stage lead(s) that delegate here:
  - [`dft_lead`](../dft_lead/) (port **8225**)
- Sibling agents in this folder:
  - [`dft_lead`](../dft_lead/) — lead, port **8225**
  - [`dft_physical_timing`](../dft_physical_timing/) — worker, port **8230**
  - [`dft_validator`](../dft_validator/) — validator, port **8231**
  - [`mbist_lbist`](../mbist_lbist/) — worker, port **8229**
  - [`scan_insertion`](../scan_insertion/) — worker, port **8226**
  - [`testability_analysis`](../testability_analysis/) — worker, port **8228**
- Track overview: [`../README.md`](../README.md).

## Files in this directory

| File | Role |
|------|------|
| `agent.py` | Defines `AtpgCampaignAgent`; loads sibling `config.yaml` into `spec`. |
| `server.py` | HTTP/ASGI bootstrap; exports FastAPI `app` for uvicorn. |
| `tools.py` | `@tool` skill callables; stable EDA operation contracts. |
| `config.yaml` | Fleet manifest (`apiVersion: agentfleet/v1`): boundaries, port, skills, memory, telemetry. |
| `Dockerfile` | Container image; `EXPOSE 8227`; `CMD python server.py`. |
| `requirements.txt` | FastAPI, uvicorn, pydantic, PyYAML for the HTTP surface. |
| `__init__.py` | Re-exports `AtpgCampaignAgent` for imports without starting HTTP. |
| `README.md` | This document. |

## Tool reference

### `write_fault_model_list` (`tools.write_fault_model_list`)

**Action:** `write_candidate`. Write the fault models this campaign must cover. Do not omit a required model.

### `write_pattern_budget` (`tools.write_pattern_budget`)

**Action:** `write_candidate`. Write the pattern-count and tester-time budget.

### `generate_stuck_at_patterns` (`tools.generate_stuck_at_patterns`)

**Action:** `submit_tool_job`. Generate stuck-at patterns.

### `generate_transition_patterns` (`tools.generate_transition_patterns`)

**Action:** `submit_tool_job`. Generate transition-delay patterns.

### `generate_path_delay_patterns` (`tools.generate_path_delay_patterns`)

**Action:** `submit_tool_job`. Generate path-delay patterns for the listed paths.

### `generate_iddq_patterns` (`tools.generate_iddq_patterns`)

**Action:** `submit_tool_job`. Generate IDDQ patterns when the contract requires them.

### `read_fault_coverage` (`tools.read_fault_coverage`)

**Action:** `read_reports`. Read coverage, untestable faults, and aborted faults by model.

### `read_pattern_count` (`tools.read_pattern_count`)

**Action:** `read_reports`. Read pattern count and estimated tester time.

### `read_test_power` (`tools.read_test_power`)

**Action:** `read_reports`. Read shift and capture power.

### `compare_coverage_to_requirement` (`tools.compare_coverage_to_requirement`)

**Action:** `read_reports`. Compare each fault model with its required coverage.

### `analyze_fault_coverage` (`tools.analyze_fault_coverage`)

**Action:** `publish_finding`. Publish coverage, pattern count, tester time, and test power.

### `flag_dropped_fault_model` (`tools.flag_dropped_fault_model`)

**Action:** `publish_finding`. Publish a campaign that omitted a required fault model.

### `flag_test_power_over_budget` (`tools.flag_test_power_over_budget`)

**Action:** `publish_finding`. Publish shift or capture power above the budget.

### `record_atpg_tool_version` (`tools.record_atpg_tool_version`)

**Action:** `publish_finding`. Record the ATPG tool, version, and fault-model settings.

## Runtime, memory, and context

- **Reliability:** task timeout 120s, max retries 1, on failure `replan`.
- **Execution:** `direct_function`, `max_tasks=1`.
- **Context include:** `requirements`, `canonical_source`, `open_findings`, `gates`.
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
