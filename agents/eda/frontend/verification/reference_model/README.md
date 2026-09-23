# Reference Model Agent (`reference_model`)

This directory is the deployable microservice package for the **Reference Model Agent** in the fleet **verification** stage (role `worker`).

## EDA responsibility

Reference Model Agent class for the EDA chip-design agent fleet.

Charter from `config.yaml`: Produce an executable behavioral reference model from the specification.

As a **worker**, this process executes bounded skills on isolated candidates and reports observations. Promotion and program-level tradeoffs stay with leads and humans.

## Identity and HTTP port

| Field | Value |
|-------|-------|
| Agent id | `reference_model` |
| Stage | `verification` |
| Role | `worker` |
| Host | `host.docker.internal` |
| Port | **8217** (must match `Dockerfile` `EXPOSE`) |
| Health | `/health` |
| Execute | `/tasks/execute` |

## Boundaries

Hard limits from `config.yaml` `boundary`. The planner and `EDAAgent` enforce these even when a tool adapter could physically perform a forbidden action.

### May

- Read the specification
- Write a reference model on an isolated branch
- Run the model against its own directed checks

### May not

- Copy unreviewed RTL into the reference
- Change the spec to match the model
- Promote a candidate onto the canonical baseline
- Approve a waiver or relax a hard requirement
- Treat its own summary as independent signoff

## Skills

Skills bind planner task ids to callables in `tools.py` (`module: tools`, `execution.mode: direct_function`).

| Skill id | Action | Callable | Description |
|----------|--------|----------|-------------|
| `generate_reference_model` | `write_candidate` | `generate_reference_model` | Write a behavioral model that encodes the specification. |
| `write_model_ports` | `write_candidate` | `write_model_ports` | Write the model's ports from the interface contract. |
| `write_model_transactions` | `write_candidate` | `write_model_transactions` | Write legal transaction types and their fields. |
| `write_model_error_behavior` | `write_candidate` | `write_model_error_behavior` | Write how the model reports and recovers from illegal inputs. |
| `write_model_latency_rule` | `write_candidate` | `write_model_latency_rule` | Write the latency or ordering rule the model must obey. |
| `write_model_selfcheck` | `write_candidate` | `write_model_selfcheck` | Write directed checks that exercise the model without the DUT. |
| `read_model_specification` | `read_reports` | `read_model_specification` | Read the specification clauses this model claims to encode. |
| `diff_model_against_spec` | `read_reports` | `diff_model_against_spec` | List specification clauses the model does not yet encode. |
| `compile_reference_model` | `submit_tool_job` | `compile_reference_model` | Compile the reference model. |
| `run_model_selfcheck` | `submit_tool_job` | `run_model_selfcheck` | Run the model's own checks and return mismatches. |
| `flag_spec_hole_in_model` | `publish_finding` | `flag_spec_hole_in_model` | Publish a specification clause that cannot be encoded because it is ambiguous. |
| `record_reference_model_version` | `publish_finding` | `record_reference_model_version` | Record the model source, spec revision, and language. |

## Delegation

This agent declares **no** `delegates_to` entries. It executes its own `tools.py` skills when scheduled by a lead or the chip-flow orchestrator.

## Boot path

Every fleet agent shares the same linear startup so compose and local dev behave identically.

1. Container or shell runs `python server.py` (`deployment.dockerfile` / image `agentfleet/reference_model:1.0`).
2. `server.py` prepends this directory to `sys.path`, imports `ReferenceModelAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, ReferenceModelAgent)`.
3. Importing `agent.py` sets `spec = EDAAgent.read_spec(<this directory>)`, loading `config.yaml` at class definition time.
4. Uvicorn serves FastAPI `app` on `connection.port` with `/health` and `/tasks/execute`.
5. On `/tasks/execute`, `EDAAgent.handle` assembles engineering-memory context (see `context` in YAML), journals the task, and dispatches the requested skill.
6. The skill callable in `tools.py` returns `tool_observation(...)`. With `backend.type: none`, observations are safe stubs (`not_run`) until `EDA_FRAMEWORK` or another adapter binds real engines.

## Related agents

- Stage index: [`../README.md`](../README.md) (verification specialists under `verification/`).
- Stage lead(s) that delegate here:
  - [`verification_lead`](../verification_lead/) (port **8215**)
- Sibling agents in this folder:
  - [`assertion_formal`](../assertion_formal/) — worker, port **8218**
  - [`coverage`](../coverage/) — worker, port **8220**
  - [`failure_triage`](../failure_triage/) — worker, port **8222**
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
| `agent.py` | Defines `ReferenceModelAgent`; loads sibling `config.yaml` into `spec`. |
| `server.py` | HTTP/ASGI bootstrap; exports FastAPI `app` for uvicorn. |
| `tools.py` | `@tool` skill callables; stable EDA operation contracts. |
| `config.yaml` | Fleet manifest (`apiVersion: agentfleet/v1`): boundaries, port, skills, memory, telemetry. |
| `Dockerfile` | Container image; `EXPOSE 8217`; `CMD python server.py`. |
| `requirements.txt` | FastAPI, uvicorn, pydantic, PyYAML for the HTTP surface. |
| `__init__.py` | Re-exports `ReferenceModelAgent` for imports without starting HTTP. |
| `README.md` | This document. |

## Tool reference

### `generate_reference_model` (`tools.generate_reference_model`)

**Action:** `write_candidate`. Write a behavioral model that encodes the specification.

### `write_model_ports` (`tools.write_model_ports`)

**Action:** `write_candidate`. Write the model's ports from the interface contract.

### `write_model_transactions` (`tools.write_model_transactions`)

**Action:** `write_candidate`. Write legal transaction types and their fields.

### `write_model_error_behavior` (`tools.write_model_error_behavior`)

**Action:** `write_candidate`. Write how the model reports and recovers from illegal inputs.

### `write_model_latency_rule` (`tools.write_model_latency_rule`)

**Action:** `write_candidate`. Write the latency or ordering rule the model must obey.

### `write_model_selfcheck` (`tools.write_model_selfcheck`)

**Action:** `write_candidate`. Write directed checks that exercise the model without the DUT.

### `read_model_specification` (`tools.read_model_specification`)

**Action:** `read_reports`. Read the specification clauses this model claims to encode.

### `diff_model_against_spec` (`tools.diff_model_against_spec`)

**Action:** `read_reports`. List specification clauses the model does not yet encode.

### `compile_reference_model` (`tools.compile_reference_model`)

**Action:** `submit_tool_job`. Compile the reference model.

### `run_model_selfcheck` (`tools.run_model_selfcheck`)

**Action:** `submit_tool_job`. Run the model's own checks and return mismatches.

### `flag_spec_hole_in_model` (`tools.flag_spec_hole_in_model`)

**Action:** `publish_finding`. Publish a specification clause that cannot be encoded because it is ambiguous.

### `record_reference_model_version` (`tools.record_reference_model_version`)

**Action:** `publish_finding`. Record the model source, spec revision, and language.

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
