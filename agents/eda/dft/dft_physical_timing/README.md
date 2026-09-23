# DFT Physical/Timing Coordination Agent (`dft_physical_timing`)

This directory is the deployable microservice package for the **DFT Physical/Timing Coordination Agent** in the fleet **dft** stage (role `worker`).

## EDA responsibility

DFT Physical/Timing agent class (dft_physical_timing).

Charter from `config.yaml`: Carry scan ordering, test clocks, congestion, and test-mode timing into physical design.

As a **worker**, this process executes bounded skills on isolated candidates and reports observations. Promotion and program-level tradeoffs stay with leads and humans.

## Identity and HTTP port

| Field | Value |
|-------|-------|
| Agent id | `dft_physical_timing` |
| Stage | `dft` |
| Role | `worker` |
| Host | `host.docker.internal` |
| Port | **8230** (must match `Dockerfile` `EXPOSE`) |
| Health | `/health` |
| Execute | `/tasks/execute` |

## Boundaries

Hard limits from `config.yaml` `boundary`. The planner and `EDAAgent` enforce these even when a tool adapter could physically perform a forbidden action.

### May

- Read scan and placement data
- Write a scan-order and test-mode constraint proposal
- Publish test-mode timing and congestion findings

### May not

- Reorder scan in the canonical database
- Waive a test-mode timing violation
- Promote a candidate onto the canonical baseline
- Approve a waiver or relax a hard requirement
- Treat its own summary as independent signoff

## Skills

Skills bind planner task ids to callables in `tools.py` (`module: tools`, `execution.mode: direct_function`).

| Skill id | Action | Callable | Description |
|----------|--------|----------|-------------|
| `read_scan_order` | `read_reports` | `read_scan_order` | Read the current scan-chain order. |
| `read_test_mode_constraints` | `read_reports` | `read_test_mode_constraints` | Read test clocks, false paths, and case analysis for test mode. |
| `read_scan_congestion` | `read_reports` | `read_scan_congestion` | Read congestion along scan nets. |
| `propose_scan_chain_order` | `write_candidate` | `propose_scan_chain_order` | Write a proposed scan order that respects congestion and timing. This does not edit the canonical database. |
| `write_test_mode_sdc` | `write_candidate` | `write_test_mode_sdc` | Write test-mode clocks and exceptions as a constraint candidate. |
| `check_test_mode_timing` | `submit_tool_job` | `check_test_mode_timing` | Report test-mode setup, hold, and transition violations. |
| `check_test_mode_power` | `submit_tool_job` | `check_test_mode_power` | Report shift and capture power in the physical database. |
| `check_scan_routing_resource` | `read_reports` | `check_scan_routing_resource` | Report scan nets that cross congested regions. |
| `coordinate_scan_ordering` | `publish_finding` | `coordinate_scan_ordering` | Publish the proposed order and the congestion and timing evidence. |
| `flag_test_mode_timing_violation` | `publish_finding` | `flag_test_mode_timing_violation` | Publish a test-mode timing violation. This does not waive it. |
| `flag_scan_congestion` | `publish_finding` | `flag_scan_congestion` | Publish scan nets that need a physical change. |
| `record_dft_physical_handoff` | `publish_finding` | `record_dft_physical_handoff` | Record the scan order, test-mode SDC, and database revision handed to physical design. |

## Delegation

This agent declares **no** `delegates_to` entries. It executes its own `tools.py` skills when scheduled by a lead or the chip-flow orchestrator.

## Boot path

Every fleet agent shares the same linear startup so compose and local dev behave identically.

1. Container or shell runs `python server.py` (`deployment.dockerfile` / image `agentfleet/dft_physical_timing:1.0`).
2. `server.py` prepends this directory to `sys.path`, imports `DftPhysicalTimingAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, DftPhysicalTimingAgent)`.
3. Importing `agent.py` sets `spec = EDAAgent.read_spec(<this directory>)`, loading `config.yaml` at class definition time.
4. Uvicorn serves FastAPI `app` on `connection.port` with `/health` and `/tasks/execute`.
5. On `/tasks/execute`, `EDAAgent.handle` assembles engineering-memory context (see `context` in YAML), journals the task, and dispatches the requested skill.
6. The skill callable in `tools.py` returns `tool_observation(...)`. With `backend.type: none`, observations are safe stubs (`not_run`) until `EDA_FRAMEWORK` or another adapter binds real engines.

## Related agents

- Stage index: [`../README.md`](../README.md) (dft specialists under `dft/`).
- Stage lead(s) that delegate here:
  - [`dft_lead`](../dft_lead/) (port **8225**)
- Sibling agents in this folder:
  - [`atpg_campaign`](../atpg_campaign/) — worker, port **8227**
  - [`dft_lead`](../dft_lead/) — lead, port **8225**
  - [`dft_validator`](../dft_validator/) — validator, port **8231**
  - [`mbist_lbist`](../mbist_lbist/) — worker, port **8229**
  - [`scan_insertion`](../scan_insertion/) — worker, port **8226**
  - [`testability_analysis`](../testability_analysis/) — worker, port **8228**
- Track overview: [`../README.md`](../README.md).

## Files in this directory

| File | Role |
|------|------|
| `agent.py` | Defines `DftPhysicalTimingAgent`; loads sibling `config.yaml` into `spec`. |
| `server.py` | HTTP/ASGI bootstrap; exports FastAPI `app` for uvicorn. |
| `tools.py` | `@tool` skill callables; stable EDA operation contracts. |
| `config.yaml` | Fleet manifest (`apiVersion: agentfleet/v1`): boundaries, port, skills, memory, telemetry. |
| `Dockerfile` | Container image; `EXPOSE 8230`; `CMD python server.py`. |
| `requirements.txt` | FastAPI, uvicorn, pydantic, PyYAML for the HTTP surface. |
| `__init__.py` | Re-exports `DftPhysicalTimingAgent` for imports without starting HTTP. |
| `README.md` | This document. |

## Tool reference

### `read_scan_order` (`tools.read_scan_order`)

**Action:** `read_reports`. Read the current scan-chain order.

### `read_test_mode_constraints` (`tools.read_test_mode_constraints`)

**Action:** `read_reports`. Read test clocks, false paths, and case analysis for test mode.

### `read_scan_congestion` (`tools.read_scan_congestion`)

**Action:** `read_reports`. Read congestion along scan nets.

### `propose_scan_chain_order` (`tools.propose_scan_chain_order`)

**Action:** `write_candidate`. Write a proposed scan order that respects congestion and timing. This does not edit the canonical database.

### `write_test_mode_sdc` (`tools.write_test_mode_sdc`)

**Action:** `write_candidate`. Write test-mode clocks and exceptions as a constraint candidate.

### `check_test_mode_timing` (`tools.check_test_mode_timing`)

**Action:** `submit_tool_job`. Report test-mode setup, hold, and transition violations.

### `check_test_mode_power` (`tools.check_test_mode_power`)

**Action:** `submit_tool_job`. Report shift and capture power in the physical database.

### `check_scan_routing_resource` (`tools.check_scan_routing_resource`)

**Action:** `read_reports`. Report scan nets that cross congested regions.

### `coordinate_scan_ordering` (`tools.coordinate_scan_ordering`)

**Action:** `publish_finding`. Publish the proposed order and the congestion and timing evidence.

### `flag_test_mode_timing_violation` (`tools.flag_test_mode_timing_violation`)

**Action:** `publish_finding`. Publish a test-mode timing violation. This does not waive it.

### `flag_scan_congestion` (`tools.flag_scan_congestion`)

**Action:** `publish_finding`. Publish scan nets that need a physical change.

### `record_dft_physical_handoff` (`tools.record_dft_physical_handoff`)

**Action:** `publish_finding`. Record the scan order, test-mode SDC, and database revision handed to physical design.

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
