# Independent DFT Validator (`dft_validator`)

This directory is the deployable microservice package for the **Independent DFT Validator** in the fleet **dft** stage (role `validator`).

## EDA responsibility

DFT Validator agent class (dft_validator).

Charter from `config.yaml`: Reproduce scan, fault-coverage, self-test, and test-mode checks and decide whether the DFT contract passes.

As a **validator**, this process independently grades gate evidence, audits waivers, and publishes pass/fail outcomes. It does not mutate design candidates on behalf of workers.

## Identity and HTTP port

| Field | Value |
|-------|-------|
| Agent id | `dft_validator` |
| Stage | `dft` |
| Role | `validator` |
| Host | `host.docker.internal` |
| Port | **8231** (must match `Dockerfile` `EXPOSE`) |
| Health | `/health` |
| Execute | `/tasks/execute` |

## Boundaries

Hard limits from `config.yaml` `boundary`. The planner and `EDAAgent` enforce these even when a tool adapter could physically perform a forbidden action.

### May

- Re-run critical DFT checks
- Read primary DFT reports
- Emit a gate

### May not

- Edit scan or patterns
- Waive a coverage miss
- Accept a summary in place of the report
- Promote a candidate onto the canonical baseline
- Approve a waiver or relax a hard requirement
- Treat its own summary as independent signoff

## Skills

Skills bind planner task ids to callables in `tools.py` (`module: tools`, `execution.mode: direct_function`).

| Skill id | Action | Callable | Description |
|----------|--------|----------|-------------|
| `read_dft_candidate_pin` | `read_reports` | `read_dft_candidate_pin` | Read the exact candidate and pattern set being graded. |
| `read_primary_dft_reports` | `read_reports` | `read_primary_dft_reports` | Read scan, ATPG, BIST, and test-mode reports from primary artifacts. |
| `check_dft_provenance` | `read_reports` | `check_dft_provenance` | Check DFT tool versions and recipes against the frozen flow. |
| `reproduce_scan_integrity` | `submit_tool_job` | `reproduce_scan_integrity` | Re-run scan connectivity and chain-integrity checks. |
| `reproduce_fault_coverage` | `submit_tool_job` | `reproduce_fault_coverage` | Re-run fault coverage for every required model. |
| `reproduce_bist_checks` | `submit_tool_job` | `reproduce_bist_checks` | Re-run MBIST and LBIST integration checks. |
| `reproduce_test_mode_timing` | `submit_tool_job` | `reproduce_test_mode_timing` | Re-run test-mode timing on the physical database. |
| `compare_dft_summary` | `read_reports` | `compare_dft_summary` | Compare the DFT lead's summary with the primary reports. |
| `audit_dft_untestables` | `read_reports` | `audit_dft_untestables` | Check that every untestable fault has a traced cause. |
| `emit_dft_gate` | `emit_gate` | `emit_dft_gate` | Record whether the DFT contract passed. |
| `publish_dft_gate_disagreement` | `publish_finding` | `publish_dft_gate_disagreement` | Publish a place where the summary and the primary report disagree. |
| `publish_missing_dft_input` | `publish_finding` | `publish_missing_dft_input` | Publish a report or fault model required for the gate that is absent. |

## Delegation

This agent declares **no** `delegates_to` entries. It executes its own `tools.py` skills when scheduled by a lead or the chip-flow orchestrator.

## Boot path

Every fleet agent shares the same linear startup so compose and local dev behave identically.

1. Container or shell runs `python server.py` (`deployment.dockerfile` / image `agentfleet/dft_validator:1.0`).
2. `server.py` prepends this directory to `sys.path`, imports `DftValidatorAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, DftValidatorAgent)`.
3. Importing `agent.py` sets `spec = EDAAgent.read_spec(<this directory>)`, loading `config.yaml` at class definition time.
4. Uvicorn serves FastAPI `app` on `connection.port` with `/health` and `/tasks/execute`.
5. On `/tasks/execute`, `EDAAgent.handle` assembles engineering-memory context (see `context` in YAML), journals the task, and dispatches the requested skill.
6. The skill callable in `tools.py` returns `tool_observation(...)`. With `backend.type: none`, observations are safe stubs (`not_run`) until `EDA_FRAMEWORK` or another adapter binds real engines.

## Related agents

- Stage index: [`../README.md`](../README.md) (dft specialists under `dft/`).
- Stage lead(s) that schedule this gate:
  - [`dft_lead`](../dft_lead/) (port **8225**)
- Sibling agents in this folder:
  - [`atpg_campaign`](../atpg_campaign/) — worker, port **8227**
  - [`dft_lead`](../dft_lead/) — lead, port **8225**
  - [`dft_physical_timing`](../dft_physical_timing/) — worker, port **8230**
  - [`mbist_lbist`](../mbist_lbist/) — worker, port **8229**
  - [`scan_insertion`](../scan_insertion/) — worker, port **8226**
  - [`testability_analysis`](../testability_analysis/) — worker, port **8228**
- Track overview: [`../README.md`](../README.md).

## Files in this directory

| File | Role |
|------|------|
| `agent.py` | Defines `DftValidatorAgent`; loads sibling `config.yaml` into `spec`. |
| `server.py` | HTTP/ASGI bootstrap; exports FastAPI `app` for uvicorn. |
| `tools.py` | `@tool` skill callables; stable EDA operation contracts. |
| `config.yaml` | Fleet manifest (`apiVersion: agentfleet/v1`): boundaries, port, skills, memory, telemetry. |
| `Dockerfile` | Container image; `EXPOSE 8231`; `CMD python server.py`. |
| `requirements.txt` | FastAPI, uvicorn, pydantic, PyYAML for the HTTP surface. |
| `__init__.py` | Re-exports `DftValidatorAgent` for imports without starting HTTP. |
| `README.md` | This document. |

## Tool reference

### `read_dft_candidate_pin` (`tools.read_dft_candidate_pin`)

**Action:** `read_reports`. Read the exact candidate and pattern set being graded.

### `read_primary_dft_reports` (`tools.read_primary_dft_reports`)

**Action:** `read_reports`. Read scan, ATPG, BIST, and test-mode reports from primary artifacts.

### `check_dft_provenance` (`tools.check_dft_provenance`)

**Action:** `read_reports`. Check DFT tool versions and recipes against the frozen flow.

### `reproduce_scan_integrity` (`tools.reproduce_scan_integrity`)

**Action:** `submit_tool_job`. Re-run scan connectivity and chain-integrity checks.

### `reproduce_fault_coverage` (`tools.reproduce_fault_coverage`)

**Action:** `submit_tool_job`. Re-run fault coverage for every required model.

### `reproduce_bist_checks` (`tools.reproduce_bist_checks`)

**Action:** `submit_tool_job`. Re-run MBIST and LBIST integration checks.

### `reproduce_test_mode_timing` (`tools.reproduce_test_mode_timing`)

**Action:** `submit_tool_job`. Re-run test-mode timing on the physical database.

### `compare_dft_summary` (`tools.compare_dft_summary`)

**Action:** `read_reports`. Compare the DFT lead's summary with the primary reports.

### `audit_dft_untestables` (`tools.audit_dft_untestables`)

**Action:** `read_reports`. Check that every untestable fault has a traced cause.

### `emit_dft_gate` (`tools.emit_dft_gate`)

**Action:** `emit_gate`. Record whether the DFT contract passed.

### `publish_dft_gate_disagreement` (`tools.publish_dft_gate_disagreement`)

**Action:** `publish_finding`. Publish a place where the summary and the primary report disagree.

### `publish_missing_dft_input` (`tools.publish_missing_dft_input`)

**Action:** `publish_finding`. Publish a report or fault model required for the gate that is absent.

## Runtime, memory, and context

- **Reliability:** task timeout 120s, max retries 1, on failure `replan`.
- **Execution:** `direct_function`, `max_tasks=1`.
- **Context include:** `requirements`, `interface_contracts`, `canonical_source`, `gates`, `open_findings`.
- **Context exclude:** `stale_candidates`, `unverified_agent_claims`.
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
