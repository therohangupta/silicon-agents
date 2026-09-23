# DFT Lead (`dft_lead`)

This directory is the deployable microservice package for the **DFT Lead** in the fleet **dft** stage (role `lead`).

## EDA responsibility

Tool callables for the DFT Lead agent (dft_lead).

Charter from `config.yaml`: Own the block and chip test strategy. Decompose it into scan, ATPG, self-test, and physical-integration work, and coordinate closure against coverage, test time, area, power, and timing.

As a **lead**, this process publishes workflows, reads qualified upstream artifacts, opens child agent tasks, compares candidates, and recommends next steps. It does **not** promote the canonical baseline or act as independent signoff.

## Identity and HTTP port

| Field | Value |
|-------|-------|
| Agent id | `dft_lead` |
| Stage | `dft` |
| Role | `lead` |
| Host | `host.docker.internal` |
| Port | **8225** (must match `Dockerfile` `EXPOSE`) |
| Health | `/health` |
| Execute | `/tasks/execute` |

## Boundaries

Hard limits from `config.yaml` `boundary`. The planner and `EDAAgent` enforce these even when a tool adapter could physically perform a forbidden action.

### May

- Publish a DFT workflow
- Read RTL and test requirements
- Request a human decision on a coverage miss

### May not

- Edit functional RTL to chase coverage without a finding
- Waive fault coverage
- Promote a candidate onto the canonical baseline
- Approve a waiver or relax a hard requirement
- Treat its own summary as independent signoff

## Skills

Skills bind planner task ids to callables in `tools.py` (`module: tools`, `execution.mode: direct_function`).

| Skill id | Action | Callable | Description |
|----------|--------|----------|-------------|
| `plan_dft_closure` | `create_workflow` | `plan_dft_closure` | Emit the DFT workflow for this revision. |
| `request_scan_insertion` | `create_workflow` | `request_scan_insertion` | Open scan insertion for this RTL candidate. |
| `request_atpg_campaign` | `create_workflow` | `request_atpg_campaign` | Open an ATPG campaign for the required fault models. |
| `request_testability_analysis` | `create_workflow` | `request_testability_analysis` | Open testability analysis against the latest ATPG report. |
| `request_bist_configuration` | `create_workflow` | `request_bist_configuration` | Open MBIST or LBIST configuration for the memories and logic in scope. |
| `request_dft_physical_timing` | `create_workflow` | `request_dft_physical_timing` | Open the handoff of scan and test-mode constraints into physical design. |
| `request_dft_gate` | `create_workflow` | `request_dft_gate` | Hand the candidate to the independent DFT validator. |
| `read_dft_requirements` | `read_reports` | `read_dft_requirements` | Read fault-coverage, test-time, area, power, and timing requirements. |
| `read_dft_status` | `read_reports` | `read_dft_status` | Read scan, ATPG, BIST, and test-mode timing status. |
| `read_fault_coverage_summary` | `read_reports` | `read_fault_coverage_summary` | Read coverage by fault model. |
| `report_dft_gap` | `publish_finding` | `report_dft_gap` | Publish a coverage, test-time, or timing gap the strategy cannot close. |
| `route_testability_finding` | `publish_finding` | `route_testability_finding` | Route a testability finding to RTL or architecture. |
| `record_dft_strategy_change` | `publish_finding` | `record_dft_strategy_change` | Record a change in fault model, compression, or pattern budget. |
| `request_dft_coverage_decision` | `request_human_decision` | `request_dft_coverage_decision` | Ask a human to accept or reject a coverage miss. This agent cannot waive it. |

## Delegation

This lead may open child workflows/tasks against:

- [`scan_insertion`](../scan_insertion/) — Scan Insertion Agent (port **8226**)
- [`atpg_campaign`](../atpg_campaign/) — ATPG Campaign Agent (port **8227**)
- [`testability_analysis`](../testability_analysis/) — Testability Analysis Agent (port **8228**)
- [`mbist_lbist`](../mbist_lbist/) — MBIST/LBIST Agent (port **8229**)
- [`dft_physical_timing`](../dft_physical_timing/) — DFT Physical/Timing Coordination Agent (port **8230**)
- [`dft_validator`](../dft_validator/) — Independent DFT Validator (port **8231**)

Delegation is declarative in `delegates_to`. The lead's `request_*` / `open_*` skills tell the orchestrator which child agent id and skill to schedule next; workers do not call each other directly over HTTP.

Independent validators configured for this agent:

- [`dft_validator`](../dft_validator/) (port **8231**)

## Boot path

Every fleet agent shares the same linear startup so compose and local dev behave identically.

1. Container or shell runs `python server.py` (`deployment.dockerfile` / image `agentfleet/dft_lead:1.0`).
2. `server.py` prepends this directory to `sys.path`, imports `DftLeadAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, DftLeadAgent)`.
3. Importing `agent.py` sets `spec = EDAAgent.read_spec(<this directory>)`, loading `config.yaml` at class definition time.
4. Uvicorn serves FastAPI `app` on `connection.port` with `/health` and `/tasks/execute`.
5. On `/tasks/execute`, `EDAAgent.handle` assembles engineering-memory context (see `context` in YAML), journals the task, and dispatches the requested skill.
6. The skill callable in `tools.py` returns `tool_observation(...)`. With `backend.type: none`, observations are safe stubs (`not_run`) until `EDA_FRAMEWORK` or another adapter binds real engines.

## Related agents

- Stage index: [`../README.md`](../README.md) (dft specialists under `dft/`).
- Program orchestrator:
  - [`chip_flow_lead`](../../chip_flow_lead/) (port **8201**)
- Sibling agents in this folder:
  - [`atpg_campaign`](../atpg_campaign/) — worker, port **8227**
  - [`dft_physical_timing`](../dft_physical_timing/) — worker, port **8230**
  - [`dft_validator`](../dft_validator/) — validator, port **8231**
  - [`mbist_lbist`](../mbist_lbist/) — worker, port **8229**
  - [`scan_insertion`](../scan_insertion/) — worker, port **8226**
  - [`testability_analysis`](../testability_analysis/) — worker, port **8228**
- Track overview: [`../README.md`](../README.md).

## Files in this directory

| File | Role |
|------|------|
| `agent.py` | Defines `DftLeadAgent`; loads sibling `config.yaml` into `spec`. |
| `server.py` | HTTP/ASGI bootstrap; exports FastAPI `app` for uvicorn. |
| `tools.py` | `@tool` skill callables; stable EDA operation contracts. |
| `config.yaml` | Fleet manifest (`apiVersion: agentfleet/v1`): boundaries, port, skills, memory, telemetry. |
| `Dockerfile` | Container image; `EXPOSE 8225`; `CMD python server.py`. |
| `requirements.txt` | FastAPI, uvicorn, pydantic, PyYAML for the HTTP surface. |
| `__init__.py` | Re-exports `DftLeadAgent` for imports without starting HTTP. |
| `README.md` | This document. |

## Tool reference

### `plan_dft_closure` (`tools.plan_dft_closure`)

**Action:** `create_workflow`. Emit the DFT workflow for this revision.

### `request_scan_insertion` (`tools.request_scan_insertion`)

**Action:** `create_workflow`. Open scan insertion for this RTL candidate.

### `request_atpg_campaign` (`tools.request_atpg_campaign`)

**Action:** `create_workflow`. Open an ATPG campaign for the required fault models.

### `request_testability_analysis` (`tools.request_testability_analysis`)

**Action:** `create_workflow`. Open testability analysis against the latest ATPG report.

### `request_bist_configuration` (`tools.request_bist_configuration`)

**Action:** `create_workflow`. Open MBIST or LBIST configuration for the memories and logic in scope.

### `request_dft_physical_timing` (`tools.request_dft_physical_timing`)

**Action:** `create_workflow`. Open the handoff of scan and test-mode constraints into physical design.

### `request_dft_gate` (`tools.request_dft_gate`)

**Action:** `create_workflow`. Hand the candidate to the independent DFT validator.

### `read_dft_requirements` (`tools.read_dft_requirements`)

**Action:** `read_reports`. Read fault-coverage, test-time, area, power, and timing requirements.

### `read_dft_status` (`tools.read_dft_status`)

**Action:** `read_reports`. Read scan, ATPG, BIST, and test-mode timing status.

### `read_fault_coverage_summary` (`tools.read_fault_coverage_summary`)

**Action:** `read_reports`. Read coverage by fault model.

### `report_dft_gap` (`tools.report_dft_gap`)

**Action:** `publish_finding`. Publish a coverage, test-time, or timing gap the strategy cannot close.

### `route_testability_finding` (`tools.route_testability_finding`)

**Action:** `publish_finding`. Route a testability finding to RTL or architecture.

### `record_dft_strategy_change` (`tools.record_dft_strategy_change`)

**Action:** `publish_finding`. Record a change in fault model, compression, or pattern budget.

### `request_dft_coverage_decision` (`tools.request_dft_coverage_decision`)

**Action:** `request_human_decision`. Ask a human to accept or reject a coverage miss. This agent cannot waive it.

## Runtime, memory, and context

- **Reliability:** task timeout 120s, max retries 1, on failure `replan`.
- **Execution:** `direct_function`, `max_tasks=1`.
- **Context include:** `gates`, `workflows`, `open_findings`, `decisions`, `experiments`.
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
