# RTL Lead (`rtl_lead`)

This directory is the deployable microservice package for the **RTL Lead** in the fleet **rtl** stage (role `lead`).

## EDA responsibility

Plan implementation of one block and coordinate lint, clock, CDC, low-power, and integration checks.

As a **lead**, this process publishes workflows, reads qualified upstream artifacts, opens child agent tasks, compares candidates, and recommends next steps. It does **not** promote the canonical baseline or act as independent signoff.

## Identity and HTTP port

| Field | Value |
|-------|-------|
| Agent id | `rtl_lead` |
| Stage | `rtl` |
| Role | `lead` |
| Host | `host.docker.internal` |
| Port | **8208** (must match `Dockerfile` `EXPOSE`) |
| Health | `/health` |
| Execute | `/tasks/execute` |

## Boundaries

Hard limits from `config.yaml` `boundary`. The planner and `EdaAgent` enforce these even when a tool adapter could physically perform a forbidden action.

### May

- Read the block specification and architecture budgets
- Publish an implementation workflow for this block
- Send a finding back to architecture when the spec cannot be implemented

### May not

- Edit the canonical RTL directly
- Skip lint or CDC because a candidate simulates
- Promote a candidate onto the canonical baseline
- Approve a waiver or relax a hard requirement
- Treat its own summary as independent signoff

## Skills

Skills bind planner task ids to callables in `tools.py` (`module: tools`, `execution.mode: direct_function`).

| Skill id | Action | Callable | Description |
|----------|--------|----------|-------------|
| `plan_block_implementation` | `create_workflow` | `plan_block_implementation` | Emit the block workflow from spec through qualification. |
| `request_block_qualification` | `create_workflow` | `request_block_qualification` | Ask lint, clock, CDC, low-power, and integration checks to grade the current candidate. |
| `request_rtl_edit` | `create_workflow` | `request_rtl_edit` | Open one bounded RTL-edit task with a single hypothesis. |
| `request_integration` | `create_workflow` | `request_integration` | Open a merge of block candidates that have passed their local checks. |
| `read_block_spec` | `read_reports` | `read_block_spec` | Read the qualified specification and interface contracts for this block. |
| `read_candidate_status` | `read_reports` | `read_candidate_status` | Read lint, CDC, clock, and low-power status for the active candidate. |
| `read_open_rtl_findings` | `read_reports` | `read_open_rtl_findings` | Read findings still open against this block. |
| `recommend_rtl_candidate` | `publish_finding` | `recommend_rtl_candidate` | Record which isolated candidate should be handed to verification. This does not promote it. |
| `return_spec_gap` | `publish_finding` | `return_spec_gap` | Publish a finding when the specification cannot be implemented as written. |
| `flag_missing_block_check` | `publish_finding` | `flag_missing_block_check` | Publish a required lint, CDC, clock, or low-power check that has not run. |
| `record_block_handoff` | `publish_finding` | `record_block_handoff` | Record the candidate ref, checks, and open findings included in a handoff. |
| `request_verification_handoff` | `create_workflow` | `request_verification_handoff` | Open the verification workflow for a candidate that has passed basic compile and lint readiness. |

## Delegation

This lead may open child workflows/tasks against:

- [`rtl_implementation`](../rtl_implementation/) — RTL Implementation Agent (port **8209**)
- [`clock_reset`](../clock_reset/) — Clock/Reset Agent (port **8210**)
- [`cdc_rdc`](../cdc_rdc/) — CDC/RDC Agent (port **8211**)
- [`low_power`](../low_power/) — Low-Power Agent (port **8212**)
- [`lint_quality`](../lint_quality/) — Lint/Quality Agent (port **8213**)
- [`rtl_integration`](../rtl_integration/) — RTL Integration Agent (port **8214**)

Delegation is declarative in `delegates_to`. The lead's `request_*` / `open_*` skills tell the orchestrator which child agent id and skill to schedule next; workers do not call each other directly over HTTP.

Independent validators configured for this agent:

- [`verification_validator`](../../verification/verification_validator/) (port **8224**)

## Boot path

Every fleet agent shares the same linear startup so compose and local dev behave identically.

1. Container or shell runs `python server.py` (`deployment.dockerfile` / image `agentfleet/rtl_lead:1.0`).
2. `server.py` prepends this directory to `sys.path`, imports `RtlLeadAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, RtlLeadAgent)`.
3. Importing `agent.py` sets `spec = EdaAgent.read_spec(<this directory>)`, loading `config.yaml` at class definition time.
4. Uvicorn serves FastAPI `app` on `connection.port` with `/health` and `/tasks/execute`.
5. On `/tasks/execute`, `EdaAgent.handle` assembles engineering-memory context (see `context` in YAML), journals the task, and dispatches the requested skill.
6. The skill callable in `tools.py` returns `tool_observation(...)`. With `backend.type: none`, observations are safe stubs (`not_run`) until `EDA_FRAMEWORK` or another adapter binds real engines.

## Related agents

- Stage index: [`../README.md`](../README.md) (rtl specialists under `rtl/`).
- Program orchestrator:
  - [`chip_flow_lead`](../../../chip_flow_lead/) (port **8201**)
- Sibling agents in this folder:
  - [`cdc_rdc`](../cdc_rdc/) — worker, port **8211**
  - [`clock_reset`](../clock_reset/) — worker, port **8210**
  - [`lint_quality`](../lint_quality/) — worker, port **8213**
  - [`low_power`](../low_power/) — worker, port **8212**
  - [`rtl_implementation`](../rtl_implementation/) — worker, port **8209**
  - [`rtl_integration`](../rtl_integration/) — worker, port **8214**
- Track overview: [`../../README.md`](../../README.md) (frontend architecture, RTL, verification).

## Files in this directory

| File | Role |
|------|------|
| `agent.py` | Defines `RtlLeadAgent`; loads sibling `config.yaml` into `spec`. |
| `server.py` | HTTP/ASGI bootstrap; exports FastAPI `app` for uvicorn. |
| `tools.py` | `@tool` skill callables; stable EDA operation contracts. |
| `config.yaml` | Fleet manifest (`apiVersion: agentfleet/v1`): boundaries, port, skills, memory, telemetry. |
| `Dockerfile` | Container image; `EXPOSE 8208`; `CMD python server.py`. |
| `requirements.txt` | FastAPI, uvicorn, pydantic, PyYAML for the HTTP surface. |
| `__init__.py` | Re-exports `RtlLeadAgent` for imports without starting HTTP. |
| `README.md` | This document. |

## Tool reference

### `plan_block_implementation` (`tools.plan_block_implementation`)

**Action:** `create_workflow`. Emit the block workflow from spec through qualification.

### `request_block_qualification` (`tools.request_block_qualification`)

**Action:** `create_workflow`. Ask lint, clock, CDC, low-power, and integration checks to grade the current candidate.

### `request_rtl_edit` (`tools.request_rtl_edit`)

**Action:** `create_workflow`. Open one bounded RTL-edit task with a single hypothesis.

### `request_integration` (`tools.request_integration`)

**Action:** `create_workflow`. Open a merge of block candidates that have passed their local checks.

### `read_block_spec` (`tools.read_block_spec`)

**Action:** `read_reports`. Read the qualified specification and interface contracts for this block.

### `read_candidate_status` (`tools.read_candidate_status`)

**Action:** `read_reports`. Read lint, CDC, clock, and low-power status for the active candidate.

### `read_open_rtl_findings` (`tools.read_open_rtl_findings`)

**Action:** `read_reports`. Read findings still open against this block.

### `recommend_rtl_candidate` (`tools.recommend_rtl_candidate`)

**Action:** `publish_finding`. Record which isolated candidate should be handed to verification. This does not promote it.

### `return_spec_gap` (`tools.return_spec_gap`)

**Action:** `publish_finding`. Publish a finding when the specification cannot be implemented as written.

### `flag_missing_block_check` (`tools.flag_missing_block_check`)

**Action:** `publish_finding`. Publish a required lint, CDC, clock, or low-power check that has not run.

### `record_block_handoff` (`tools.record_block_handoff`)

**Action:** `publish_finding`. Record the candidate ref, checks, and open findings included in a handoff.

### `request_verification_handoff` (`tools.request_verification_handoff`)

**Action:** `create_workflow`. Open the verification workflow for a candidate that has passed basic compile and lint readiness.

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
- **Shared base:** Task handling lives in `domains/eda/agent.py`; HTTP wiring in `domains/eda/server.py`.
- **Telemetry:** See [`../../TELEMETRY.md`](../../TELEMETRY.md) (path may vary by depth) for fleet-wide observability conventions.

## How a newcomer should read this agent

1. Read `config.yaml` `metadata`, `boundary`, and `capabilities` for charter and limits.
2. Skim the skills table above, then open `tools.py` for parameter shapes.
3. Read `agent.py` and `server.py` only to confirm boot wiring.
4. Treat `Dockerfile` / `requirements.txt` as deployment detail.
