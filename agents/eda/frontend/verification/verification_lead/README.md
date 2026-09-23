# Verification Lead (`verification_lead`)

This directory is the deployable microservice package for the **Verification Lead** in the fleet **verification** stage (role `lead`).

## EDA responsibility

Verification Lead class for the EDA chip-design agent fleet.

Charter from `config.yaml`: Own the verification plan and closure workflow for one pinned RTL revision. Do not personally write every test or inspect every waveform.

As a **lead**, this process publishes workflows, reads qualified upstream artifacts, opens child agent tasks, compares candidates, and recommends next steps. It does **not** promote the canonical baseline or act as independent signoff.

## Identity and HTTP port

| Field | Value |
|-------|-------|
| Agent id | `verification_lead` |
| Stage | `verification` |
| Role | `lead` |
| Host | `host.docker.internal` |
| Port | **8215** (must match `Dockerfile` `EXPOSE`) |
| Health | `/health` |
| Execute | `/tasks/execute` |

## Boundaries

Hard limits from `config.yaml` `boundary`. The planner and `EDAAgent` enforce these even when a tool adapter could physically perform a forbidden action.

### May

- Read the specification, RTL candidate, and prior findings
- Publish a verification workflow and coverage-closure tasks
- Return UPSTREAM_CHANGE_REQUIRED when behavior is ambiguous
- Request a human decision for an exclusion or waiver

### May not

- Modify canonical RTL
- Waive a requirement
- Grade its own closure
- Promote a candidate onto the canonical baseline
- Approve a waiver or relax a hard requirement
- Treat its own summary as independent signoff

## Skills

Skills bind planner task ids to callables in `tools.py` (`module: tools`, `execution.mode: direct_function`).

| Skill id | Action | Callable | Description |
|----------|--------|----------|-------------|
| `build_verification_plan` | `create_workflow` | `build_verification_plan` | Emit the closure workflow for this RTL revision. |
| `request_uvm_environment` | `create_workflow` | `request_uvm_environment` | Open a task to build or update the UVM environment. |
| `request_reference_model` | `create_workflow` | `request_reference_model` | Open a task to build the behavioral reference model. |
| `request_formal_campaign` | `create_workflow` | `request_formal_campaign` | Open a formal proof task for the named properties. |
| `request_stimulus_for_holes` | `create_workflow` | `request_stimulus_for_holes` | Open stimulus work aimed at the listed coverage holes. |
| `request_regression_campaign` | `create_workflow` | `request_regression_campaign` | Open a regression for the current test manifest. |
| `request_failure_reproduction` | `create_workflow` | `request_failure_reproduction` | Open minimization for one failure cluster. |
| `request_independent_verification_gate` | `create_workflow` | `request_independent_verification_gate` | Hand the pinned candidate to the verification validator. |
| `read_verification_contract` | `read_reports` | `read_verification_contract` | Read the requirements, exclusions, and required checks for this candidate. |
| `read_coverage_summary` | `read_reports` | `read_coverage_summary` | Read code, functional, and assertion coverage for the current regression. |
| `read_failure_clusters` | `read_reports` | `read_failure_clusters` | Read clustered failures and their likely owners. |
| `read_regression_status` | `read_reports` | `read_regression_status` | Read pass, fail, and infrastructure-error counts for the campaign. |
| `publish_coverage_closure_gap` | `publish_finding` | `publish_coverage_closure_gap` | Publish holes that the current strategy has not closed. |
| `escalate_spec_ambiguity` | `publish_finding` | `escalate_spec_ambiguity` | Publish a finding when RTL and specification disagree. |
| `request_rtl_fix` | `publish_finding` | `request_rtl_fix` | Route a reproduced functional defect back to the RTL lead. |
| `record_verification_strategy_change` | `publish_finding` | `record_verification_strategy_change` | Record a change in how closure is searched after a plateau. |
| `request_verification_waiver` | `request_human_decision` | `request_verification_waiver` | Ask a human to approve or reject a verification exclusion. This agent cannot approve it. |
| `request_exclusion_decision` | `request_human_decision` | `request_exclusion_decision` | Ask a human whether an unreachable coverpoint may be excluded. |

## Delegation

This lead may open child workflows/tasks against:

- [`uvm_environment`](../uvm_environment/) — UVM Environment Agent (port **8216**)
- [`reference_model`](../reference_model/) — Reference Model Agent (port **8217**)
- [`assertion_formal`](../assertion_formal/) — Assertion/Formal Agent (port **8218**)
- [`stimulus`](../stimulus/) — Stimulus Agent (port **8219**)
- [`regression`](../regression/) — Regression Agent (port **8221**)
- [`coverage`](../coverage/) — Coverage Agent (port **8220**)
- [`failure_triage`](../failure_triage/) — Failure-Triage Agent (port **8222**)
- [`reproduction`](../reproduction/) — Reproduction Agent (port **8223**)
- [`verification_validator`](../verification_validator/) — Verification Validator (port **8224**)

Delegation is declarative in `delegates_to`. The lead's `request_*` / `open_*` skills tell the orchestrator which child agent id and skill to schedule next; workers do not call each other directly over HTTP.

Independent validators configured for this agent:

- [`verification_validator`](../verification_validator/) (port **8224**)

## Boot path

Every fleet agent shares the same linear startup so compose and local dev behave identically.

1. Container or shell runs `python server.py` (`deployment.dockerfile` / image `agentfleet/verification_lead:1.0`).
2. `server.py` prepends this directory to `sys.path`, imports `VerificationLeadAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, VerificationLeadAgent)`.
3. Importing `agent.py` sets `spec = EDAAgent.read_spec(<this directory>)`, loading `config.yaml` at class definition time.
4. Uvicorn serves FastAPI `app` on `connection.port` with `/health` and `/tasks/execute`.
5. On `/tasks/execute`, `EDAAgent.handle` assembles engineering-memory context (see `context` in YAML), journals the task, and dispatches the requested skill.
6. The skill callable in `tools.py` returns `tool_observation(...)`. With `backend.type: none`, observations are safe stubs (`not_run`) until `EDA_FRAMEWORK` or another adapter binds real engines.

## Related agents

- Stage index: [`../README.md`](../README.md) (verification specialists under `verification/`).
- Program orchestrator:
  - [`chip_flow_lead`](../../../chip_flow_lead/) (port **8201**)
- Sibling agents in this folder:
  - [`assertion_formal`](../assertion_formal/) — worker, port **8218**
  - [`coverage`](../coverage/) — worker, port **8220**
  - [`failure_triage`](../failure_triage/) — worker, port **8222**
  - [`reference_model`](../reference_model/) — worker, port **8217**
  - [`regression`](../regression/) — worker, port **8221**
  - [`reproduction`](../reproduction/) — worker, port **8223**
  - [`stimulus`](../stimulus/) — worker, port **8219**
  - [`uvm_environment`](../uvm_environment/) — worker, port **8216**
  - [`verification_validator`](../verification_validator/) — validator, port **8224**
- Track overview: [`../../README.md`](../../README.md) (frontend architecture, RTL, verification).

## Files in this directory

| File | Role |
|------|------|
| `agent.py` | Defines `VerificationLeadAgent`; loads sibling `config.yaml` into `spec`. |
| `server.py` | HTTP/ASGI bootstrap; exports FastAPI `app` for uvicorn. |
| `tools.py` | `@tool` skill callables; stable EDA operation contracts. |
| `config.yaml` | Fleet manifest (`apiVersion: agentfleet/v1`): boundaries, port, skills, memory, telemetry. |
| `Dockerfile` | Container image; `EXPOSE 8215`; `CMD python server.py`. |
| `requirements.txt` | FastAPI, uvicorn, pydantic, PyYAML for the HTTP surface. |
| `__init__.py` | Re-exports `VerificationLeadAgent` for imports without starting HTTP. |
| `README.md` | This document. |

## Tool reference

### `build_verification_plan` (`tools.build_verification_plan`)

**Action:** `create_workflow`. Emit the closure workflow for this RTL revision.

Emit the verification closure workflow for the pinned RTL revision.

### `request_uvm_environment` (`tools.request_uvm_environment`)

**Action:** `create_workflow`. Open a task to build or update the UVM environment.

Open a delegated task for the UVM Environment specialist.

### `request_reference_model` (`tools.request_reference_model`)

**Action:** `create_workflow`. Open a task to build the behavioral reference model.

Open a delegated task for the Reference Model specialist.

### `request_formal_campaign` (`tools.request_formal_campaign`)

**Action:** `create_workflow`. Open a formal proof task for the named properties.

Open a formal assertion campaign via the Assertion/Formal specialist.

### `request_stimulus_for_holes` (`tools.request_stimulus_for_holes`)

**Action:** `create_workflow`. Open stimulus work aimed at the listed coverage holes.

Open stimulus generation targeted at listed coverage holes.

### `request_regression_campaign` (`tools.request_regression_campaign`)

**Action:** `create_workflow`. Open a regression for the current test manifest.

Open a regression campaign over the current test manifest.

### `request_failure_reproduction` (`tools.request_failure_reproduction`)

**Action:** `create_workflow`. Open minimization for one failure cluster.

Open failure reproduction/minimization for one triage cluster.

### `request_independent_verification_gate` (`tools.request_independent_verification_gate`)

**Action:** `create_workflow`. Hand the pinned candidate to the verification validator.

Hand the pinned candidate to the independent Verification Validator.

### `read_verification_contract` (`tools.read_verification_contract`)

**Action:** `read_reports`. Read the requirements, exclusions, and required checks for this candidate.

Read the verification contract for the candidate.

### `read_coverage_summary` (`tools.read_coverage_summary`)

**Action:** `read_reports`. Read code, functional, and assertion coverage for the current regression.

Read the merged coverage summary for the current regression.

### `read_failure_clusters` (`tools.read_failure_clusters`)

**Action:** `read_reports`. Read clustered failures and their likely owners.

Read failure clusters and likely owners from triage.

### `read_regression_status` (`tools.read_regression_status`)

**Action:** `read_reports`. Read pass, fail, and infrastructure-error counts for the campaign.

Read pass/fail/infrastructure counts for the regression campaign.

### `publish_coverage_closure_gap` (`tools.publish_coverage_closure_gap`)

**Action:** `publish_finding`. Publish holes that the current strategy has not closed.

Publish a finding that coverage closure has plateaued with open holes.

### `escalate_spec_ambiguity` (`tools.escalate_spec_ambiguity`)

**Action:** `publish_finding`. Publish a finding when RTL and specification disagree.

Escalate when RTL behavior and the specification disagree.

### `request_rtl_fix` (`tools.request_rtl_fix`)

**Action:** `publish_finding`. Route a reproduced functional defect back to the RTL lead.

Route a reproduced functional defect to the RTL lead.

### `record_verification_strategy_change` (`tools.record_verification_strategy_change`)

**Action:** `publish_finding`. Record a change in how closure is searched after a plateau.

Record a verification strategy change after a coverage/debug plateau.

### `request_verification_waiver` (`tools.request_verification_waiver`)

**Action:** `request_human_decision`. Ask a human to approve or reject a verification exclusion. This agent cannot approve it.

Request a human decision on a verification waiver/exclusion.

### `request_exclusion_decision` (`tools.request_exclusion_decision`)

**Action:** `request_human_decision`. Ask a human whether an unreachable coverpoint may be excluded.

Request a human decision on excluding an unreachable coverpoint.

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
