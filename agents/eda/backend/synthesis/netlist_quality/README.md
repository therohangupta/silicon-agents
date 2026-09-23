# Netlist Quality Agent (`netlist_quality`)

This directory is the deployable microservice package for the **Netlist Quality Agent** in the fleet **synthesis** stage (role `worker`).

## EDA responsibility

Check loops, undriven logic, high fanout, and unmapped cells.

Charter from `config.yaml`: Inspect a netlist for structural defects, high fanout, loops, poor mappings, congestion risks, DFT incompatibilities, and suspicious QoR regressions.

As a **worker**, this process executes bounded skills on isolated candidates and reports observations. Promotion and program-level tradeoffs stay with leads and humans.

## Identity and HTTP port

| Field | Value |
|-------|-------|
| Agent id | `netlist_quality` |
| Stage | `synthesis` |
| Role | `worker` |
| Host | `host.docker.internal` |
| Port | **8237** (must match `Dockerfile` `EXPOSE`) |
| Health | `/health` |
| Execute | `/tasks/execute` |

## Boundaries

Hard limits from `config.yaml` `boundary`. The planner and `EDAAgent` enforce these even when a tool adapter could physically perform a forbidden action.

### May

- Read the netlist and QoR report
- Submit structural checks
- Publish structural findings

### May not

- Edit the netlist
- Ignore a combinational loop
- Promote a candidate onto the canonical baseline
- Approve a waiver or relax a hard requirement
- Treat its own summary as independent signoff

## Skills

Skills bind planner task ids to callables in `tools.py` (`module: tools`, `execution.mode: direct_function`).

| Skill id | Action | Callable | Description |
|----------|--------|----------|-------------|
| `inspect_netlist_structure` | `submit_tool_job` | `inspect_netlist_structure` | Check loops, undriven logic, high fanout, and unmapped cells. |
| `check_high_fanout_nets` | `read_reports` | `check_high_fanout_nets` | List nets over the fanout limit. |
| `check_undriven_and_unused` | `read_reports` | `check_undriven_and_unused` | List undriven, unused, and multiply driven nets. |
| `check_unmapped_cells` | `read_reports` | `check_unmapped_cells` | List cells with no library mapping. |
| `check_dont_use_violations` | `read_reports` | `check_dont_use_violations` | List cells the library contract marks dont-use. |
| `check_dft_scan_compatibility` | `read_reports` | `check_dft_scan_compatibility` | Check that scan cells and test clocks survived synthesis. |
| `check_congestion_risk_cells` | `read_reports` | `check_congestion_risk_cells` | List mappings that are likely to congest placement. |
| `read_qor_baseline` | `read_reports` | `read_qor_baseline` | Read the baseline QoR this netlist is compared with. |
| `flag_qor_regressions` | `publish_finding` | `flag_qor_regressions` | Publish QoR regressions against the recorded baseline. |
| `flag_combinational_loop_in_netlist` | `publish_finding` | `flag_combinational_loop_in_netlist` | Publish a combinational loop. |
| `flag_dft_incompatible_netlist` | `publish_finding` | `flag_dft_incompatible_netlist` | Publish a netlist that dropped scan or test clocks. |
| `record_netlist_quality_evidence` | `publish_finding` | `record_netlist_quality_evidence` | Record the netlist ref and the checks that ran. |

## Delegation

This agent declares **no** `delegates_to` entries. It executes its own `tools.py` skills when scheduled by a lead or the chip-flow orchestrator.

## Boot path

Every fleet agent shares the same linear startup so compose and local dev behave identically.

1. Container or shell runs `python server.py` (`deployment.dockerfile` / image `agentfleet/netlist_quality:1.0`).
2. `server.py` prepends this directory to `sys.path`, imports `NetlistQualityAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, NetlistQualityAgent)`.
3. Importing `agent.py` sets `spec = EDAAgent.read_spec(<this directory>)`, loading `config.yaml` at class definition time.
4. Uvicorn serves FastAPI `app` on `connection.port` with `/health` and `/tasks/execute`.
5. On `/tasks/execute`, `EDAAgent.handle` assembles engineering-memory context (see `context` in YAML), journals the task, and dispatches the requested skill.
6. The skill callable in `tools.py` returns `tool_observation(...)`. With `backend.type: none`, observations are safe stubs (`not_run`) until `EDA_FRAMEWORK` or another adapter binds real engines.

## Related agents

- Stage index: [`../README.md`](../README.md) (synthesis specialists under `synthesis/`).
- Stage lead(s) that delegate here:
  - [`synthesis_lead`](../synthesis_lead/) (port **8232**)
- Sibling agents in this folder:
  - [`constraint_generation`](../constraint_generation/) — worker, port **8233**
  - [`equivalence`](../equivalence/) — worker, port **8236**
  - [`retiming_mapping`](../retiming_mapping/) — worker, port **8235**
  - [`synthesis_experiment`](../synthesis_experiment/) — worker, port **8234**
  - [`synthesis_lead`](../synthesis_lead/) — lead, port **8232**
- Track overview: [`../../README.md`](../../README.md) (backend physical implementation).

## Files in this directory

| File | Role |
|------|------|
| `agent.py` | Defines `NetlistQualityAgent`; loads sibling `config.yaml` into `spec`. |
| `server.py` | HTTP/ASGI bootstrap; exports FastAPI `app` for uvicorn. |
| `tools.py` | `@tool` skill callables; stable EDA operation contracts. |
| `config.yaml` | Fleet manifest (`apiVersion: agentfleet/v1`): boundaries, port, skills, memory, telemetry. |
| `Dockerfile` | Container image; `EXPOSE 8237`; `CMD python server.py`. |
| `requirements.txt` | FastAPI, uvicorn, pydantic, PyYAML for the HTTP surface. |
| `__init__.py` | Re-exports `NetlistQualityAgent` for imports without starting HTTP. |
| `README.md` | This document. |

## Tool reference

### `inspect_netlist_structure` (`tools.inspect_netlist_structure`)

**Action:** `submit_tool_job`. Check loops, undriven logic, high fanout, and unmapped cells.

### `check_high_fanout_nets` (`tools.check_high_fanout_nets`)

**Action:** `read_reports`. List nets over the fanout limit.

### `check_undriven_and_unused` (`tools.check_undriven_and_unused`)

**Action:** `read_reports`. List undriven, unused, and multiply driven nets.

### `check_unmapped_cells` (`tools.check_unmapped_cells`)

**Action:** `read_reports`. List cells with no library mapping.

### `check_dont_use_violations` (`tools.check_dont_use_violations`)

**Action:** `read_reports`. List cells the library contract marks dont-use.

### `check_dft_scan_compatibility` (`tools.check_dft_scan_compatibility`)

**Action:** `read_reports`. Check that scan cells and test clocks survived synthesis.

### `check_congestion_risk_cells` (`tools.check_congestion_risk_cells`)

**Action:** `read_reports`. List mappings that are likely to congest placement.

### `read_qor_baseline` (`tools.read_qor_baseline`)

**Action:** `read_reports`. Read the baseline QoR this netlist is compared with.

### `flag_qor_regressions` (`tools.flag_qor_regressions`)

**Action:** `publish_finding`. Publish QoR regressions against the recorded baseline.

### `flag_combinational_loop_in_netlist` (`tools.flag_combinational_loop_in_netlist`)

**Action:** `publish_finding`. Publish a combinational loop.

### `flag_dft_incompatible_netlist` (`tools.flag_dft_incompatible_netlist`)

**Action:** `publish_finding`. Publish a netlist that dropped scan or test clocks.

### `record_netlist_quality_evidence` (`tools.record_netlist_quality_evidence`)

**Action:** `publish_finding`. Record the netlist ref and the checks that ran.

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
