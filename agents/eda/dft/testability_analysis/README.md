# Testability Analysis Agent (`testability_analysis`)

This directory is the deployable microservice package for the **Testability Analysis Agent** in the fleet **dft** stage (role `worker`).

## EDA responsibility

Testability Analysis agent class (testability_analysis).

Charter from `config.yaml`: Find controllability and observability limits, X sources, and structures that block coverage, and propose a bounded change.

As a **worker**, this process executes bounded skills on isolated candidates and reports observations. Promotion and program-level tradeoffs stay with leads and humans.

## Identity and HTTP port

| Field | Value |
|-------|-------|
| Agent id | `testability_analysis` |
| Stage | `dft` |
| Role | `worker` |
| Host | `host.docker.internal` |
| Port | **8228** (must match `Dockerfile` `EXPOSE`) |
| Health | `/health` |
| Execute | `/tasks/execute` |

## Boundaries

Hard limits from `config.yaml` `boundary`. The planner and `EDAAgent` enforce these even when a tool adapter could physically perform a forbidden action.

### May

- Read RTL and ATPG reports
- Write a proposal for a bounded RTL, constraint, or DFT change

### May not

- Apply the RTL change on the design candidate
- Mark faults untestable without evidence
- Promote a candidate onto the canonical baseline
- Approve a waiver or relax a hard requirement
- Treat its own summary as independent signoff

## Skills

Skills bind planner task ids to callables in `tools.py` (`module: tools`, `execution.mode: direct_function`).

| Skill id | Action | Callable | Description |
|----------|--------|----------|-------------|
| `read_atpg_untestables` | `read_reports` | `read_atpg_untestables` | Read faults the ATPG tool marked untestable. |
| `find_x_sources` | `read_reports` | `find_x_sources` | List X sources that block controllability or observability. |
| `find_uncontrollable_logic` | `read_reports` | `find_uncontrollable_logic` | List logic with no controllable path from a scan cell or primary input. |
| `find_unobservable_logic` | `read_reports` | `find_unobservable_logic` | List logic with no observable path to a scan cell or primary output. |
| `trace_blocked_fault` | `read_reports` | `trace_blocked_fault` | Trace one untestable fault to the structure that blocks it. |
| `classify_untestable_cause` | `read_reports` | `classify_untestable_cause` | Classify a blocked fault as X, black box, constraint, or architecture. |
| `write_testability_proposal` | `write_candidate` | `write_testability_proposal` | Write a bounded RTL, constraint, or DFT-architecture proposal. This does not edit the design candidate. |
| `estimate_coverage_recovery` | `read_reports` | `estimate_coverage_recovery` | Estimate how many faults the proposal would recover. |
| `propose_testability_change` | `publish_finding` | `propose_testability_change` | Publish the proposal, the faults it targets, and who must apply it. |
| `flag_unjustified_untestable` | `publish_finding` | `flag_unjustified_untestable` | Publish a fault marked untestable without a traced cause. |
| `flag_blackbox_coverage_hole` | `publish_finding` | `flag_blackbox_coverage_hole` | Publish a black box that hides required faults. |
| `record_testability_evidence` | `publish_finding` | `record_testability_evidence` | Record the ATPG report and RTL revision this analysis used. |

## Delegation

This agent declares **no** `delegates_to` entries. It executes its own `tools.py` skills when scheduled by a lead or the chip-flow orchestrator.

## Boot path

Every fleet agent shares the same linear startup so compose and local dev behave identically.

1. Container or shell runs `python server.py` (`deployment.dockerfile` / image `agentfleet/testability_analysis:1.0`).
2. `server.py` prepends this directory to `sys.path`, imports `TestabilityAnalysisAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, TestabilityAnalysisAgent)`.
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
  - [`dft_physical_timing`](../dft_physical_timing/) — worker, port **8230**
  - [`dft_validator`](../dft_validator/) — validator, port **8231**
  - [`mbist_lbist`](../mbist_lbist/) — worker, port **8229**
  - [`scan_insertion`](../scan_insertion/) — worker, port **8226**
- Track overview: [`../README.md`](../README.md).

## Files in this directory

| File | Role |
|------|------|
| `agent.py` | Defines `TestabilityAnalysisAgent`; loads sibling `config.yaml` into `spec`. |
| `server.py` | HTTP/ASGI bootstrap; exports FastAPI `app` for uvicorn. |
| `tools.py` | `@tool` skill callables; stable EDA operation contracts. |
| `config.yaml` | Fleet manifest (`apiVersion: agentfleet/v1`): boundaries, port, skills, memory, telemetry. |
| `Dockerfile` | Container image; `EXPOSE 8228`; `CMD python server.py`. |
| `requirements.txt` | FastAPI, uvicorn, pydantic, PyYAML for the HTTP surface. |
| `__init__.py` | Re-exports `TestabilityAnalysisAgent` for imports without starting HTTP. |
| `README.md` | This document. |

## Tool reference

### `read_atpg_untestables` (`tools.read_atpg_untestables`)

**Action:** `read_reports`. Read faults the ATPG tool marked untestable.

### `find_x_sources` (`tools.find_x_sources`)

**Action:** `read_reports`. List X sources that block controllability or observability.

### `find_uncontrollable_logic` (`tools.find_uncontrollable_logic`)

**Action:** `read_reports`. List logic with no controllable path from a scan cell or primary input.

### `find_unobservable_logic` (`tools.find_unobservable_logic`)

**Action:** `read_reports`. List logic with no observable path to a scan cell or primary output.

### `trace_blocked_fault` (`tools.trace_blocked_fault`)

**Action:** `read_reports`. Trace one untestable fault to the structure that blocks it.

### `classify_untestable_cause` (`tools.classify_untestable_cause`)

**Action:** `read_reports`. Classify a blocked fault as X, black box, constraint, or architecture.

### `write_testability_proposal` (`tools.write_testability_proposal`)

**Action:** `write_candidate`. Write a bounded RTL, constraint, or DFT-architecture proposal. This does not edit the design candidate.

### `estimate_coverage_recovery` (`tools.estimate_coverage_recovery`)

**Action:** `read_reports`. Estimate how many faults the proposal would recover.

### `propose_testability_change` (`tools.propose_testability_change`)

**Action:** `publish_finding`. Publish the proposal, the faults it targets, and who must apply it.

### `flag_unjustified_untestable` (`tools.flag_unjustified_untestable`)

**Action:** `publish_finding`. Publish a fault marked untestable without a traced cause.

### `flag_blackbox_coverage_hole` (`tools.flag_blackbox_coverage_hole`)

**Action:** `publish_finding`. Publish a black box that hides required faults.

### `record_testability_evidence` (`tools.record_testability_evidence`)

**Action:** `publish_finding`. Record the ATPG report and RTL revision this analysis used.

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
