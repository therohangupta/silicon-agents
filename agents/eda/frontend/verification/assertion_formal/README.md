# Assertion/Formal Agent (`assertion_formal`)

This directory is the deployable microservice package for the **Assertion/Formal Agent** in the fleet **verification** stage (role `worker`).

## EDA responsibility

Assertion/Formal Agent class for the EDA chip-design agent fleet.

Charter from `config.yaml`: Create properties and assumptions, and submit formal proof tasks.

As a **worker**, this process executes bounded skills on isolated candidates and reports observations. Promotion and program-level tradeoffs stay with leads and humans.

## Identity and HTTP port

| Field | Value |
|-------|-------|
| Agent id | `assertion_formal` |
| Stage | `verification` |
| Role | `worker` |
| Host | `host.docker.internal` |
| Port | **8218** (must match `Dockerfile` `EXPOSE`) |
| Health | `/health` |
| Execute | `/tasks/execute` |

## Boundaries

Hard limits from `config.yaml` `boundary`. The planner and `EDAAgent` enforce these even when a tool adapter could physically perform a forbidden action.

### May

- Write assertions on an isolated branch
- Submit a formal job
- Classify counterexamples

### May not

- Add an assumption that hides a failure
- Edit RTL
- Approve a waiver
- Promote a candidate onto the canonical baseline
- Approve a waiver or relax a hard requirement
- Treat its own summary as independent signoff

## Skills

Skills bind planner task ids to callables in `tools.py` (`module: tools`, `execution.mode: direct_function`).

| Skill id | Action | Callable | Description |
|----------|--------|----------|-------------|
| `generate_assertions` | `write_candidate` | `generate_assertions` | Write properties for the named requirements. |
| `write_formal_assumptions` | `write_candidate` | `write_formal_assumptions` | Write environment assumptions. Each assumption cites the contract clause that justifies it. |
| `write_cover_properties` | `write_candidate` | `write_cover_properties` | Write cover properties for the legal scenarios the proof must reach. |
| `write_assertion_bind` | `write_candidate` | `write_assertion_bind` | Write the bind file that attaches properties to the candidate. |
| `read_formal_requirements` | `read_reports` | `read_formal_requirements` | Read the requirements this proof is responsible for. |
| `submit_formal` | `submit_tool_job` | `submit_formal` | Submit the property manifest to the bound formal engine. |
| `read_formal_results` | `read_reports` | `read_formal_results` | Read proven, cex, vacuous, and undetermined properties. |
| `classify_counterexample` | `read_reports` | `classify_counterexample` | Classify one counterexample as a design bug, a missing constraint, or an overconstraint. |
| `minimize_counterexample` | `submit_tool_job` | `minimize_counterexample` | Ask the formal engine for a shorter counterexample. |
| `flag_vacuous_property` | `publish_finding` | `flag_vacuous_property` | Publish a property that passes only because its antecedent is unreachable. |
| `flag_overconstraint` | `publish_finding` | `flag_overconstraint` | Publish an assumption that removes legal stimulus. |
| `record_formal_engine_version` | `publish_finding` | `record_formal_engine_version` | Record the formal engine, version, and proof settings. |

## Delegation

This agent declares **no** `delegates_to` entries. It executes its own `tools.py` skills when scheduled by a lead or the chip-flow orchestrator.

## Boot path

Every fleet agent shares the same linear startup so compose and local dev behave identically.

1. Container or shell runs `python server.py` (`deployment.dockerfile` / image `agentfleet/assertion_formal:1.0`).
2. `server.py` prepends this directory to `sys.path`, imports `AssertionFormalAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, AssertionFormalAgent)`.
3. Importing `agent.py` sets `spec = EDAAgent.read_spec(<this directory>)`, loading `config.yaml` at class definition time.
4. Uvicorn serves FastAPI `app` on `connection.port` with `/health` and `/tasks/execute`.
5. On `/tasks/execute`, `EDAAgent.handle` assembles engineering-memory context (see `context` in YAML), journals the task, and dispatches the requested skill.
6. The skill callable in `tools.py` returns `tool_observation(...)`. With `backend.type: none`, observations are safe stubs (`not_run`) until `EDA_FRAMEWORK` or another adapter binds real engines.

## Related agents

- Stage index: [`../README.md`](../README.md) (verification specialists under `verification/`).
- Stage lead(s) that delegate here:
  - [`verification_lead`](../verification_lead/) (port **8215**)
- Sibling agents in this folder:
  - [`coverage`](../coverage/) — worker, port **8220**
  - [`failure_triage`](../failure_triage/) — worker, port **8222**
  - [`reference_model`](../reference_model/) — worker, port **8217**
  - [`regression`](../regression/) — worker, port **8221**
  - [`reproduction`](../reproduction/) — worker, port **8223**
  - [`stimulus`](../stimulus/) — worker, port **8219**
  - [`uvm_environment`](../uvm_environment/) — worker, port **8216**
  - [`verification_lead`](../verification_lead/) — lead, port **8215**
  - [`verification_validator`](../verification_validator/) — validator, port **8224**
- Track overview: [`../../README.md`](../../README.md) (frontend architecture, RTL, verification).

## Files in this directory

| File | Role |
|------|------|
| `agent.py` | Defines `AssertionFormalAgent`; loads sibling `config.yaml` into `spec`. |
| `server.py` | HTTP/ASGI bootstrap; exports FastAPI `app` for uvicorn. |
| `tools.py` | `@tool` skill callables; stable EDA operation contracts. |
| `config.yaml` | Fleet manifest (`apiVersion: agentfleet/v1`): boundaries, port, skills, memory, telemetry. |
| `Dockerfile` | Container image; `EXPOSE 8218`; `CMD python server.py`. |
| `requirements.txt` | FastAPI, uvicorn, pydantic, PyYAML for the HTTP surface. |
| `__init__.py` | Re-exports `AssertionFormalAgent` for imports without starting HTTP. |
| `README.md` | This document. |

## Tool reference

### `generate_assertions` (`tools.generate_assertions`)

**Action:** `write_candidate`. Write properties for the named requirements.

### `write_formal_assumptions` (`tools.write_formal_assumptions`)

**Action:** `write_candidate`. Write environment assumptions. Each assumption cites the contract clause that justifies it.

### `write_cover_properties` (`tools.write_cover_properties`)

**Action:** `write_candidate`. Write cover properties for the legal scenarios the proof must reach.

### `write_assertion_bind` (`tools.write_assertion_bind`)

**Action:** `write_candidate`. Write the bind file that attaches properties to the candidate.

### `read_formal_requirements` (`tools.read_formal_requirements`)

**Action:** `read_reports`. Read the requirements this proof is responsible for.

### `submit_formal` (`tools.submit_formal`)

**Action:** `submit_tool_job`. Submit the property manifest to the bound formal engine.

### `read_formal_results` (`tools.read_formal_results`)

**Action:** `read_reports`. Read proven, cex, vacuous, and undetermined properties.

### `classify_counterexample` (`tools.classify_counterexample`)

**Action:** `read_reports`. Classify one counterexample as a design bug, a missing constraint, or an overconstraint.

### `minimize_counterexample` (`tools.minimize_counterexample`)

**Action:** `submit_tool_job`. Ask the formal engine for a shorter counterexample.

### `flag_vacuous_property` (`tools.flag_vacuous_property`)

**Action:** `publish_finding`. Publish a property that passes only because its antecedent is unreachable.

### `flag_overconstraint` (`tools.flag_overconstraint`)

**Action:** `publish_finding`. Publish an assumption that removes legal stimulus.

### `record_formal_engine_version` (`tools.record_formal_engine_version`)

**Action:** `publish_finding`. Record the formal engine, version, and proof settings.

## Runtime, memory, and context

- **Reliability:** task timeout 120s, max retries 1, on failure `replan`.
- **Execution:** `direct_function`, `max_tasks=1`.
- **Context include:** `requirements`, `interface_contracts`, `canonical_source`, `open_findings`, `experiments`, `decisions`.
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
