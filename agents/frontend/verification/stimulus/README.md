# Stimulus Agent (`stimulus`)

This directory is the deployable microservice package for the **Stimulus Agent** in the fleet **verification** stage (role `worker`).

## EDA responsibility

Stimulus Agent class for the EDA chip-design agent fleet.

Charter from `config.yaml`: Create directed tests and constrained-random sequences aimed at coverage holes.

As a **worker**, this process executes bounded skills on isolated candidates and reports observations. Promotion and program-level tradeoffs stay with leads and humans.

## Identity and HTTP port

| Field | Value |
|-------|-------|
| Agent id | `stimulus` |
| Stage | `verification` |
| Role | `worker` |
| Host | `host.docker.internal` |
| Port | **8219** (must match `Dockerfile` `EXPOSE`) |
| Health | `/health` |
| Execute | `/tasks/execute` |

## Boundaries

Hard limits from `config.yaml` `boundary`. The planner and `EdaAgent` enforce these even when a tool adapter could physically perform a forbidden action.

### May

- Write tests on an isolated branch
- Read coverage holes
- Compile the tests

### May not

- Edit RTL
- Constrain a test so it avoids a known failure
- Promote a candidate onto the canonical baseline
- Approve a waiver or relax a hard requirement
- Treat its own summary as independent signoff

## Skills

Skills bind planner task ids to callables in `tools.py` (`module: tools`, `execution.mode: direct_function`).

| Skill id | Action | Callable | Description |
|----------|--------|----------|-------------|
| `create_directed_tests` | `write_candidate` | `create_directed_tests` | Write directed tests for specific coverage holes. |
| `create_constrained_random_sequences` | `write_candidate` | `create_constrained_random_sequences` | Write constrained-random sequences from the interface contract. |
| `create_coverage_directed_sequence` | `write_candidate` | `create_coverage_directed_sequence` | Write a sequence whose constraints target one uncovered bin. |
| `write_seed_list` | `write_candidate` | `write_seed_list` | Write the seed list for this stimulus set. Do not drop a seed that previously failed. |
| `write_stimulus_constraints` | `write_candidate` | `write_stimulus_constraints` | Write legal constraints taken from the interface contract. |
| `read_coverage_holes` | `read_reports` | `read_coverage_holes` | Read the holes this stimulus is supposed to close. |
| `read_stimulus_contract` | `read_reports` | `read_stimulus_contract` | Read the interface constraints stimulus must obey. |
| `compile_stimulus` | `submit_tool_job` | `compile_stimulus` | Compile the new tests against the UVM environment. |
| `lint_stimulus_constraints` | `submit_tool_job` | `lint_stimulus_constraints` | Check that constraints do not exclude a known failing transaction. |
| `flag_failure_avoiding_constraint` | `publish_finding` | `flag_failure_avoiding_constraint` | Publish a constraint that removes a previously failing legal transaction. |
| `flag_unjustified_constraint` | `publish_finding` | `flag_unjustified_constraint` | Publish a constraint that is not backed by the interface contract. |
| `record_stimulus_intent` | `publish_finding` | `record_stimulus_intent` | Record which holes and requirements this stimulus set targets. |

## Delegation

This agent declares **no** `delegates_to` entries. It executes its own `tools.py` skills when scheduled by a lead or the chip-flow orchestrator.

## Boot path

Every fleet agent shares the same linear startup so compose and local dev behave identically.

1. Container or shell runs `python server.py` (`deployment.dockerfile` / image `agentfleet/stimulus:1.0`).
2. `server.py` prepends this directory to `sys.path`, imports `StimulusAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, StimulusAgent)`.
3. Importing `agent.py` sets `spec = EdaAgent.read_spec(<this directory>)`, loading `config.yaml` at class definition time.
4. Uvicorn serves FastAPI `app` on `connection.port` with `/health` and `/tasks/execute`.
5. On `/tasks/execute`, `EdaAgent.handle` assembles engineering-memory context (see `context` in YAML), journals the task, and dispatches the requested skill.
6. The skill callable in `tools.py` returns `tool_observation(...)`. With `backend.type: none`, observations are safe stubs (`not_run`) until `EDA_FRAMEWORK` or another adapter binds real engines.

## Related agents

- Stage index: [`../README.md`](../README.md) (verification specialists under `verification/`).
- Stage lead(s) that delegate here:
  - [`verification_lead`](../verification_lead/) (port **8215**)
- Sibling agents in this folder:
  - [`assertion_formal`](../assertion_formal/) — worker, port **8218**
  - [`coverage`](../coverage/) — worker, port **8220**
  - [`failure_triage`](../failure_triage/) — worker, port **8222**
  - [`reference_model`](../reference_model/) — worker, port **8217**
  - [`regression`](../regression/) — worker, port **8221**
  - [`reproduction`](../reproduction/) — worker, port **8223**
  - [`uvm_environment`](../uvm_environment/) — worker, port **8216**
  - [`verification_lead`](../verification_lead/) — lead, port **8215**
  - [`verification_validator`](../verification_validator/) — validator, port **8224**
- Track overview: [`../../README.md`](../../README.md) (frontend architecture, RTL, verification).

## Files in this directory

| File | Role |
|------|------|
| `agent.py` | Defines `StimulusAgent`; loads sibling `config.yaml` into `spec`. |
| `server.py` | HTTP/ASGI bootstrap; exports FastAPI `app` for uvicorn. |
| `tools.py` | `@tool` skill callables; stable EDA operation contracts. |
| `config.yaml` | Fleet manifest (`apiVersion: agentfleet/v1`): boundaries, port, skills, memory, telemetry. |
| `Dockerfile` | Container image; `EXPOSE 8219`; `CMD python server.py`. |
| `requirements.txt` | FastAPI, uvicorn, pydantic, PyYAML for the HTTP surface. |
| `__init__.py` | Re-exports `StimulusAgent` for imports without starting HTTP. |
| `README.md` | This document. |

## Tool reference

### `create_directed_tests` (`tools.create_directed_tests`)

**Action:** `write_candidate`. Write directed tests for specific coverage holes.

### `create_constrained_random_sequences` (`tools.create_constrained_random_sequences`)

**Action:** `write_candidate`. Write constrained-random sequences from the interface contract.

### `create_coverage_directed_sequence` (`tools.create_coverage_directed_sequence`)

**Action:** `write_candidate`. Write a sequence whose constraints target one uncovered bin.

### `write_seed_list` (`tools.write_seed_list`)

**Action:** `write_candidate`. Write the seed list for this stimulus set. Do not drop a seed that previously failed.

### `write_stimulus_constraints` (`tools.write_stimulus_constraints`)

**Action:** `write_candidate`. Write legal constraints taken from the interface contract.

### `read_coverage_holes` (`tools.read_coverage_holes`)

**Action:** `read_reports`. Read the holes this stimulus is supposed to close.

### `read_stimulus_contract` (`tools.read_stimulus_contract`)

**Action:** `read_reports`. Read the interface constraints stimulus must obey.

### `compile_stimulus` (`tools.compile_stimulus`)

**Action:** `submit_tool_job`. Compile the new tests against the UVM environment.

### `lint_stimulus_constraints` (`tools.lint_stimulus_constraints`)

**Action:** `submit_tool_job`. Check that constraints do not exclude a known failing transaction.

### `flag_failure_avoiding_constraint` (`tools.flag_failure_avoiding_constraint`)

**Action:** `publish_finding`. Publish a constraint that removes a previously failing legal transaction.

### `flag_unjustified_constraint` (`tools.flag_unjustified_constraint`)

**Action:** `publish_finding`. Publish a constraint that is not backed by the interface contract.

### `record_stimulus_intent` (`tools.record_stimulus_intent`)

**Action:** `publish_finding`. Record which holes and requirements this stimulus set targets.

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
- **Shared base:** Task handling lives in `domains/eda/agent.py`; HTTP wiring in `domains/eda/server.py`.
- **Telemetry:** See [`../../TELEMETRY.md`](../../TELEMETRY.md) (path may vary by depth) for fleet-wide observability conventions.

## How a newcomer should read this agent

1. Read `config.yaml` `metadata`, `boundary`, and `capabilities` for charter and limits.
2. Skim the skills table above, then open `tools.py` for parameter shapes.
3. Read `agent.py` and `server.py` only to confirm boot wiring.
4. Treat `Dockerfile` / `requirements.txt` as deployment detail.
