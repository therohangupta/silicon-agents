# Coverage Agent (`coverage`)

This directory is the deployable microservice package for the **Coverage Agent** in the fleet **verification** stage (role `worker`).

## EDA responsibility

Coverage Agent class for the EDA chip-design agent fleet.

Charter from `config.yaml`: Write the coverage model from requirements, then analyze code, functional, and assertion coverage and list meaningful holes.

As a **worker**, this process executes bounded skills on isolated candidates and reports observations. Promotion and program-level tradeoffs stay with leads and humans.

## Identity and HTTP port

| Field | Value |
|-------|-------|
| Agent id | `coverage` |
| Stage | `verification` |
| Role | `worker` |
| Host | `host.docker.internal` |
| Port | **8220** (must match `Dockerfile` `EXPOSE`) |
| Health | `/health` |
| Execute | `/tasks/execute` |

## Boundaries

Hard limits from `config.yaml` `boundary`. The planner and `EdaAgent` enforce these even when a tool adapter could physically perform a forbidden action.

### May

- Write the coverage model on an isolated branch
- Read coverage databases
- Publish holes and suspected unreachable items

### May not

- Delete a coverpoint to raise a score
- Edit RTL
- Mark an item unreachable without evidence
- Promote a candidate onto the canonical baseline
- Approve a waiver or relax a hard requirement
- Treat its own summary as independent signoff

## Skills

Skills bind planner task ids to callables in `tools.py` (`module: tools`, `execution.mode: direct_function`).

| Skill id | Action | Callable | Description |
|----------|--------|----------|-------------|
| `write_functional_coverage_model` | `write_candidate` | `write_functional_coverage_model` | Write covergroups and bins from the requirements and interface contract. |
| `write_assertion_coverage_model` | `write_candidate` | `write_assertion_coverage_model` | Write assertion-coverage tracking for the property set. |
| `write_code_coverage_config` | `write_candidate` | `write_code_coverage_config` | Write the code-coverage configuration for this block. |
| `bind_covergroups` | `write_candidate` | `bind_covergroups` | Bind covergroups to the monitors in the isolated branch. |
| `read_coverage_database` | `read_reports` | `read_coverage_database` | Read the merged coverage database for one regression. |
| `merge_coverage_databases` | `submit_tool_job` | `merge_coverage_databases` | Merge coverage databases and return the combined score. |
| `analyze_code_coverage` | `read_reports` | `analyze_code_coverage` | Summarize line, toggle, and branch coverage. |
| `analyze_functional_coverage` | `read_reports` | `analyze_functional_coverage` | Summarize covergroup and bin coverage. |
| `analyze_assertion_coverage` | `read_reports` | `analyze_assertion_coverage` | Summarize which assertions fired. |
| `list_coverage_holes` | `publish_finding` | `list_coverage_holes` | List uncovered items with their requirement ids. |
| `list_suspected_unreachable` | `publish_finding` | `list_suspected_unreachable` | List items that look unreachable, with the evidence, without excluding them. |
| `diff_coverage_against_requirements` | `read_reports` | `diff_coverage_against_requirements` | List requirements that have no coverpoint. |
| `flag_coverage_exclusion` | `publish_finding` | `flag_coverage_exclusion` | Publish an exclusion that raises the score without a reviewed rationale. |
| `record_coverage_model_version` | `publish_finding` | `record_coverage_model_version` | Record the coverage model revision and the regression it was graded on. |

## Delegation

This agent declares **no** `delegates_to` entries. It executes its own `tools.py` skills when scheduled by a lead or the chip-flow orchestrator.

## Boot path

Every fleet agent shares the same linear startup so compose and local dev behave identically.

1. Container or shell runs `python server.py` (`deployment.dockerfile` / image `agentfleet/coverage:1.0`).
2. `server.py` prepends this directory to `sys.path`, imports `CoverageAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, CoverageAgent)`.
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
| `agent.py` | Defines `CoverageAgent`; loads sibling `config.yaml` into `spec`. |
| `server.py` | HTTP/ASGI bootstrap; exports FastAPI `app` for uvicorn. |
| `tools.py` | `@tool` skill callables; stable EDA operation contracts. |
| `config.yaml` | Fleet manifest (`apiVersion: agentfleet/v1`): boundaries, port, skills, memory, telemetry. |
| `Dockerfile` | Container image; `EXPOSE 8220`; `CMD python server.py`. |
| `requirements.txt` | FastAPI, uvicorn, pydantic, PyYAML for the HTTP surface. |
| `__init__.py` | Re-exports `CoverageAgent` for imports without starting HTTP. |
| `README.md` | This document. |

## Tool reference

### `write_functional_coverage_model` (`tools.write_functional_coverage_model`)

**Action:** `write_candidate`. Write covergroups and bins from the requirements and interface contract.

### `write_assertion_coverage_model` (`tools.write_assertion_coverage_model`)

**Action:** `write_candidate`. Write assertion-coverage tracking for the property set.

### `write_code_coverage_config` (`tools.write_code_coverage_config`)

**Action:** `write_candidate`. Write the code-coverage configuration for this block.

### `bind_covergroups` (`tools.bind_covergroups`)

**Action:** `write_candidate`. Bind covergroups to the monitors in the isolated branch.

### `read_coverage_database` (`tools.read_coverage_database`)

**Action:** `read_reports`. Read the merged coverage database for one regression.

### `merge_coverage_databases` (`tools.merge_coverage_databases`)

**Action:** `submit_tool_job`. Merge coverage databases and return the combined score.

### `analyze_code_coverage` (`tools.analyze_code_coverage`)

**Action:** `read_reports`. Summarize line, toggle, and branch coverage.

### `analyze_functional_coverage` (`tools.analyze_functional_coverage`)

**Action:** `read_reports`. Summarize covergroup and bin coverage.

### `analyze_assertion_coverage` (`tools.analyze_assertion_coverage`)

**Action:** `read_reports`. Summarize which assertions fired.

### `list_coverage_holes` (`tools.list_coverage_holes`)

**Action:** `publish_finding`. List uncovered items with their requirement ids.

### `list_suspected_unreachable` (`tools.list_suspected_unreachable`)

**Action:** `publish_finding`. List items that look unreachable, with the evidence, without excluding them.

### `diff_coverage_against_requirements` (`tools.diff_coverage_against_requirements`)

**Action:** `read_reports`. List requirements that have no coverpoint.

### `flag_coverage_exclusion` (`tools.flag_coverage_exclusion`)

**Action:** `publish_finding`. Publish an exclusion that raises the score without a reviewed rationale.

### `record_coverage_model_version` (`tools.record_coverage_model_version`)

**Action:** `publish_finding`. Record the coverage model revision and the regression it was graded on.

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
