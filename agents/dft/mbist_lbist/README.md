# MBIST/LBIST Agent (`mbist_lbist`)

This directory is the deployable microservice package for the **MBIST/LBIST Agent** in the fleet **dft** stage (role `worker`).

## EDA responsibility

Tool callables for the MBIST/LBIST agent (mbist_lbist).

Charter from `config.yaml`: Configure memory and logic BIST controllers, algorithms, repair, and diagnostic modes.

As a **worker**, this process executes bounded skills on isolated candidates and reports observations. Promotion and program-level tradeoffs stay with leads and humans.

## Identity and HTTP port

| Field | Value |
|-------|-------|
| Agent id | `mbist_lbist` |
| Stage | `dft` |
| Role | `worker` |
| Host | `host.docker.internal` |
| Port | **8229** (must match `Dockerfile` `EXPOSE`) |
| Health | `/health` |
| Execute | `/tasks/execute` |

## Boundaries

Hard limits from `config.yaml` `boundary`. The planner and `EdaAgent` enforce these even when a tool adapter could physically perform a forbidden action.

### May

- Edit BIST configuration on an isolated candidate
- Submit a BIST integration check

### May not

- Change the memory map
- Claim coverage without a BIST report
- Promote a candidate onto the canonical baseline
- Approve a waiver or relax a hard requirement
- Treat its own summary as independent signoff

## Skills

Skills bind planner task ids to callables in `tools.py` (`module: tools`, `execution.mode: direct_function`).

| Skill id | Action | Callable | Description |
|----------|--------|----------|-------------|
| `write_mbist_controller` | `write_candidate` | `write_mbist_controller` | Configure the MBIST controller for the memories in scope. |
| `write_mbist_algorithm` | `write_candidate` | `write_mbist_algorithm` | Select and write the March algorithm for each memory. |
| `write_memory_repair_interface` | `write_candidate` | `write_memory_repair_interface` | Write the repair interface and redundancy map. |
| `write_mbist_diagnostic_mode` | `write_candidate` | `write_mbist_diagnostic_mode` | Write the diagnostic mode that reports failing address and bit. |
| `write_lbist_controller` | `write_candidate` | `write_lbist_controller` | Configure the LBIST controller, PRPG, and MISR. |
| `write_lbist_seed` | `write_candidate` | `write_lbist_seed` | Write the LBIST seed set. |
| `bind_bist_to_memories` | `write_candidate` | `bind_bist_to_memories` | Bind controllers to the memory instances in the candidate. |
| `check_bist_integration` | `submit_tool_job` | `check_bist_integration` | Check that BIST ports, clocks, and resets integrate with the functional design. |
| `read_bist_coverage` | `read_reports` | `read_bist_coverage` | Read MBIST and LBIST coverage from the BIST report. |
| `read_bist_timing_constraints` | `read_reports` | `read_bist_timing_constraints` | Read the test-mode clocks and false paths BIST requires. |
| `flag_uncovered_memory` | `publish_finding` | `flag_uncovered_memory` | Publish a memory with no MBIST algorithm. |
| `flag_bist_integration_error` | `publish_finding` | `flag_bist_integration_error` | Publish a BIST port, clock, or reset that does not integrate. |
| `record_bist_configuration` | `publish_finding` | `record_bist_configuration` | Record algorithms, seeds, and the candidate they were applied to. |

## Delegation

This agent declares **no** `delegates_to` entries. It executes its own `tools.py` skills when scheduled by a lead or the chip-flow orchestrator.

## Boot path

Every fleet agent shares the same linear startup so compose and local dev behave identically.

1. Container or shell runs `python server.py` (`deployment.dockerfile` / image `agentfleet/mbist_lbist:1.0`).
2. `server.py` prepends this directory to `sys.path`, imports `MbistLbistAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, MbistLbistAgent)`.
3. Importing `agent.py` sets `spec = EdaAgent.read_spec(<this directory>)`, loading `config.yaml` at class definition time.
4. Uvicorn serves FastAPI `app` on `connection.port` with `/health` and `/tasks/execute`.
5. On `/tasks/execute`, `EdaAgent.handle` assembles engineering-memory context (see `context` in YAML), journals the task, and dispatches the requested skill.
6. The skill callable in `tools.py` returns `tool_observation(...)`. With `backend.type: none`, observations are safe stubs (`not_run`) until `EDA_FRAMEWORK` or another adapter binds real engines.

## Related agents

- Stage index: [`../README.md`](../README.md) (dft specialists under `dft/`).
- Stage lead(s) that delegate here:
  - [`dft_lead`](../dft_lead/) (port **8225**)
- Sibling agents in this folder:
  - [`atpg_campaign`](../atpg_campaign/) — worker, port **8227**
  - [`dft_lead`](../dft_lead/) — lead, port **8225**
  - [`dft_physical_timing`](../dft_physical_timing/) — worker, port **8230**
  - [`dft_validator`](../dft_validator/) — validator, port **8231**
  - [`scan_insertion`](../scan_insertion/) — worker, port **8226**
  - [`testability_analysis`](../testability_analysis/) — worker, port **8228**
- Track overview: [`../README.md`](../README.md).

## Files in this directory

| File | Role |
|------|------|
| `agent.py` | Defines `MbistLbistAgent`; loads sibling `config.yaml` into `spec`. |
| `server.py` | HTTP/ASGI bootstrap; exports FastAPI `app` for uvicorn. |
| `tools.py` | `@tool` skill callables; stable EDA operation contracts. |
| `config.yaml` | Fleet manifest (`apiVersion: agentfleet/v1`): boundaries, port, skills, memory, telemetry. |
| `Dockerfile` | Container image; `EXPOSE 8229`; `CMD python server.py`. |
| `requirements.txt` | FastAPI, uvicorn, pydantic, PyYAML for the HTTP surface. |
| `__init__.py` | Re-exports `MbistLbistAgent` for imports without starting HTTP. |
| `README.md` | This document. |

## Tool reference

### `write_mbist_controller` (`tools.write_mbist_controller`)

**Action:** `write_candidate`. Configure the MBIST controller for the memories in scope.

### `write_mbist_algorithm` (`tools.write_mbist_algorithm`)

**Action:** `write_candidate`. Select and write the March algorithm for each memory.

### `write_memory_repair_interface` (`tools.write_memory_repair_interface`)

**Action:** `write_candidate`. Write the repair interface and redundancy map.

### `write_mbist_diagnostic_mode` (`tools.write_mbist_diagnostic_mode`)

**Action:** `write_candidate`. Write the diagnostic mode that reports failing address and bit.

### `write_lbist_controller` (`tools.write_lbist_controller`)

**Action:** `write_candidate`. Configure the LBIST controller, PRPG, and MISR.

### `write_lbist_seed` (`tools.write_lbist_seed`)

**Action:** `write_candidate`. Write the LBIST seed set.

### `bind_bist_to_memories` (`tools.bind_bist_to_memories`)

**Action:** `write_candidate`. Bind controllers to the memory instances in the candidate.

### `check_bist_integration` (`tools.check_bist_integration`)

**Action:** `submit_tool_job`. Check that BIST ports, clocks, and resets integrate with the functional design.

### `read_bist_coverage` (`tools.read_bist_coverage`)

**Action:** `read_reports`. Read MBIST and LBIST coverage from the BIST report.

### `read_bist_timing_constraints` (`tools.read_bist_timing_constraints`)

**Action:** `read_reports`. Read the test-mode clocks and false paths BIST requires.

### `flag_uncovered_memory` (`tools.flag_uncovered_memory`)

**Action:** `publish_finding`. Publish a memory with no MBIST algorithm.

### `flag_bist_integration_error` (`tools.flag_bist_integration_error`)

**Action:** `publish_finding`. Publish a BIST port, clock, or reset that does not integrate.

### `record_bist_configuration` (`tools.record_bist_configuration`)

**Action:** `publish_finding`. Record algorithms, seeds, and the candidate they were applied to.

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
- **Shared base:** Task handling lives in `domains/eda/agent.py`; HTTP wiring in `domains/eda/server.py`.
- **Telemetry:** See [`../../TELEMETRY.md`](../../TELEMETRY.md) (path may vary by depth) for fleet-wide observability conventions.

## How a newcomer should read this agent

1. Read `config.yaml` `metadata`, `boundary`, and `capabilities` for charter and limits.
2. Skim the skills table above, then open `tools.py` for parameter shapes.
3. Read `agent.py` and `server.py` only to confirm boot wiring.
4. Treat `Dockerfile` / `requirements.txt` as deployment detail.
