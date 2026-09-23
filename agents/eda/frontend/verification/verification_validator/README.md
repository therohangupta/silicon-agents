# Verification Validator (`verification_validator`)

This directory is the deployable microservice package for the **Verification Validator** in the fleet **verification** stage (role `validator`).

## EDA responsibility

Verification Validator class for the EDA chip-design agent fleet.

Charter from `config.yaml`: Independently decide whether the verification contract passes for one candidate.

As a **validator**, this process independently grades gate evidence, audits waivers, and publishes pass/fail outcomes. It does not mutate design candidates on behalf of workers.

## Identity and HTTP port

| Field | Value |
|-------|-------|
| Agent id | `verification_validator` |
| Stage | `verification` |
| Role | `validator` |
| Host | `host.docker.internal` |
| Port | **8224** (must match `Dockerfile` `EXPOSE`) |
| Health | `/health` |
| Execute | `/tasks/execute` |

## Boundaries

Hard limits from `config.yaml` `boundary`. The planner and `EDAAgent` enforce these even when a tool adapter could physically perform a forbidden action.

### May

- Read the pinned candidate and primary reports
- Re-run critical checks
- Emit a gate decision
- Publish missing inputs or a disagreement with the producing summary

### May not

- Edit the candidate
- Waive a failing property
- Accept the producing agent's summary in place of the report
- Promote a candidate onto the canonical baseline
- Approve a waiver or relax a hard requirement
- Treat its own summary as independent signoff

## Skills

Skills bind planner task ids to callables in `tools.py` (`module: tools`, `execution.mode: direct_function`).

| Skill id | Action | Callable | Description |
|----------|--------|----------|-------------|
| `read_pinned_verification_candidate` | `read_reports` | `read_pinned_verification_candidate` | Read the exact candidate revision being graded. |
| `read_primary_verification_reports` | `read_reports` | `read_primary_verification_reports` | Read simulation, formal, and coverage reports from primary artifacts. |
| `check_verification_provenance` | `read_reports` | `check_verification_provenance` | Check simulator, formal engine, and coverage-model versions against the frozen recipe. |
| `reproduce_critical_simulation` | `submit_tool_job` | `reproduce_critical_simulation` | Re-run the critical simulation checks. |
| `reproduce_critical_formal` | `submit_tool_job` | `reproduce_critical_formal` | Re-run the critical formal checks. |
| `reproduce_coverage_merge` | `submit_tool_job` | `reproduce_coverage_merge` | Re-merge coverage and compare it with the reported score. |
| `compare_verification_summary` | `read_reports` | `compare_verification_summary` | Compare the producing agent's summary with the primary reports. |
| `audit_verification_exclusions` | `read_reports` | `audit_verification_exclusions` | Check that every exclusion has an owner, scope, and rationale. |
| `list_missing_verification_inputs` | `read_reports` | `list_missing_verification_inputs` | List reports or recipe fields required for a gate that are absent. |
| `emit_verification_gate` | `emit_gate` | `emit_verification_gate` | Record whether the verification contract passed. A missing input fails the gate. |
| `publish_verification_disagreement` | `publish_finding` | `publish_verification_disagreement` | Publish a place where the summary and the primary report disagree. |
| `publish_missing_verification_input` | `publish_finding` | `publish_missing_verification_input` | Publish an input that blocks an independent grade. |

## Delegation

This agent declares **no** `delegates_to` entries. It executes its own `tools.py` skills when scheduled by a lead or the chip-flow orchestrator.

## Boot path

Every fleet agent shares the same linear startup so compose and local dev behave identically.

1. Container or shell runs `python server.py` (`deployment.dockerfile` / image `agentfleet/verification_validator:1.0`).
2. `server.py` prepends this directory to `sys.path`, imports `VerificationValidatorAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, VerificationValidatorAgent)`.
3. Importing `agent.py` sets `spec = EDAAgent.read_spec(<this directory>)`, loading `config.yaml` at class definition time.
4. Uvicorn serves FastAPI `app` on `connection.port` with `/health` and `/tasks/execute`.
5. On `/tasks/execute`, `EDAAgent.handle` assembles engineering-memory context (see `context` in YAML), journals the task, and dispatches the requested skill.
6. The skill callable in `tools.py` returns `tool_observation(...)`. With `backend.type: none`, observations are safe stubs (`not_run`) until `EDA_FRAMEWORK` or another adapter binds real engines.

## Related agents

- Stage index: [`../README.md`](../README.md) (verification specialists under `verification/`).
- Stage lead(s) that schedule this gate:
  - [`verification_lead`](../verification_lead/) (port **8215**)
- Sibling agents in this folder:
  - [`assertion_formal`](../assertion_formal/) — worker, port **8218**
  - [`coverage`](../coverage/) — worker, port **8220**
  - [`failure_triage`](../failure_triage/) — worker, port **8222**
  - [`reference_model`](../reference_model/) — worker, port **8217**
  - [`regression`](../regression/) — worker, port **8221**
  - [`reproduction`](../reproduction/) — worker, port **8223**
  - [`stimulus`](../stimulus/) — worker, port **8219**
  - [`uvm_environment`](../uvm_environment/) — worker, port **8216**
  - [`verification_lead`](../verification_lead/) — lead, port **8215**
- Track overview: [`../../README.md`](../../README.md) (frontend architecture, RTL, verification).

## Files in this directory

| File | Role |
|------|------|
| `agent.py` | Defines `VerificationValidatorAgent`; loads sibling `config.yaml` into `spec`. |
| `server.py` | HTTP/ASGI bootstrap; exports FastAPI `app` for uvicorn. |
| `tools.py` | `@tool` skill callables; stable EDA operation contracts. |
| `config.yaml` | Fleet manifest (`apiVersion: agentfleet/v1`): boundaries, port, skills, memory, telemetry. |
| `Dockerfile` | Container image; `EXPOSE 8224`; `CMD python server.py`. |
| `requirements.txt` | FastAPI, uvicorn, pydantic, PyYAML for the HTTP surface. |
| `__init__.py` | Re-exports `VerificationValidatorAgent` for imports without starting HTTP. |
| `README.md` | This document. |

## Tool reference

### `read_pinned_verification_candidate` (`tools.read_pinned_verification_candidate`)

**Action:** `read_reports`. Read the exact candidate revision being graded.

### `read_primary_verification_reports` (`tools.read_primary_verification_reports`)

**Action:** `read_reports`. Read simulation, formal, and coverage reports from primary artifacts.

### `check_verification_provenance` (`tools.check_verification_provenance`)

**Action:** `read_reports`. Check simulator, formal engine, and coverage-model versions against the frozen recipe.

### `reproduce_critical_simulation` (`tools.reproduce_critical_simulation`)

**Action:** `submit_tool_job`. Re-run the critical simulation checks.

### `reproduce_critical_formal` (`tools.reproduce_critical_formal`)

**Action:** `submit_tool_job`. Re-run the critical formal checks.

### `reproduce_coverage_merge` (`tools.reproduce_coverage_merge`)

**Action:** `submit_tool_job`. Re-merge coverage and compare it with the reported score.

### `compare_verification_summary` (`tools.compare_verification_summary`)

**Action:** `read_reports`. Compare the producing agent's summary with the primary reports.

### `audit_verification_exclusions` (`tools.audit_verification_exclusions`)

**Action:** `read_reports`. Check that every exclusion has an owner, scope, and rationale.

### `list_missing_verification_inputs` (`tools.list_missing_verification_inputs`)

**Action:** `read_reports`. List reports or recipe fields required for a gate that are absent.

### `emit_verification_gate` (`tools.emit_verification_gate`)

**Action:** `emit_gate`. Record whether the verification contract passed. A missing input fails the gate.

### `publish_verification_disagreement` (`tools.publish_verification_disagreement`)

**Action:** `publish_finding`. Publish a place where the summary and the primary report disagree.

### `publish_missing_verification_input` (`tools.publish_missing_verification_input`)

**Action:** `publish_finding`. Publish an input that blocks an independent grade.

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
