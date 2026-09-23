# Constraint Generation and Validation Agent (`constraint_generation`)

This directory is the deployable microservice package for the **Constraint Generation and Validation Agent** in the fleet **synthesis** stage (role `worker`).

## EDA responsibility

Constraint Generation and Validation agent module.

Charter from `config.yaml`: Create and audit clocks, generated clocks, I/O delays, uncertainties, exceptions, operating modes, and environment assumptions.

As a **worker**, this process executes bounded skills on isolated candidates and reports observations. Promotion and program-level tradeoffs stay with leads and humans.

## Identity and HTTP port

| Field | Value |
|-------|-------|
| Agent id | `constraint_generation` |
| Stage | `synthesis` |
| Role | `worker` |
| Host | `host.docker.internal` |
| Port | **8233** (must match `Dockerfile` `EXPOSE`) |
| Health | `/health` |
| Execute | `/tasks/execute` |

## Boundaries

Hard limits from `config.yaml` `boundary`. The planner and `EDAAgent` enforce these even when a tool adapter could physically perform a forbidden action.

### May

- Write constraints on an isolated candidate
- Audit exceptions
- Submit a constraint check

### May not

- Add a false path to hide a violation
- Edit RTL
- Promote a candidate onto the canonical baseline
- Approve a waiver or relax a hard requirement
- Treat its own summary as independent signoff

## Skills

Skills bind planner task ids to callables in `tools.py` (`module: tools`, `execution.mode: direct_function`).

| Skill id | Action | Callable | Description |
|----------|--------|----------|-------------|
| `write_create_clock` | `write_candidate` | `write_create_clock` | Write create_clock constraints for the declared clocks. |
| `write_generated_clock` | `write_candidate` | `write_generated_clock` | Write create_generated_clock for one derived or gated clock. |
| `write_input_delay` | `write_candidate` | `write_input_delay` | Write set_input_delay for one port group. |
| `write_output_delay` | `write_candidate` | `write_output_delay` | Write set_output_delay for one port group. |
| `write_clock_uncertainty` | `write_candidate` | `write_clock_uncertainty` | Write setup and hold uncertainty for one clock. |
| `write_clock_groups` | `write_candidate` | `write_clock_groups` | Write asynchronous or logically exclusive clock groups. |
| `write_false_path` | `write_candidate` | `write_false_path` | Write a false path only with the justification that makes it legal. |
| `write_multicycle_path` | `write_candidate` | `write_multicycle_path` | Write a multicycle path with its architectural latency. |
| `write_case_analysis` | `write_candidate` | `write_case_analysis` | Write set_case_analysis for one operating mode. |
| `write_sdc` | `write_candidate` | `write_sdc` | Write the SDC file for this candidate. |
| `audit_constraints` | `submit_tool_job` | `audit_constraints` | Flag missing, contradictory, or unjustified exceptions. |
| `check_clocks_exist_in_netlist` | `read_reports` | `check_clocks_exist_in_netlist` | Check that every constrained clock exists in the candidate. |
| `read_constraint_exceptions` | `read_reports` | `read_constraint_exceptions` | Read false paths, multicycle paths, and case analysis. |
| `flag_unjustified_exception` | `publish_finding` | `flag_unjustified_exception` | Publish an exception that has no architectural justification. |
| `flag_missing_clock` | `publish_finding` | `flag_missing_clock` | Publish a declared clock with no create_clock. |
| `record_constraint_lineage` | `publish_finding` | `record_constraint_lineage` | Record the SDC revision, mode list, and RTL revision. |

## Delegation

This agent declares **no** `delegates_to` entries. It executes its own `tools.py` skills when scheduled by a lead or the chip-flow orchestrator.

## Boot path

Every fleet agent shares the same linear startup so compose and local dev behave identically.

1. Container or shell runs `python server.py` (`deployment.dockerfile` / image `agentfleet/constraint_generation:1.0`).
2. `server.py` prepends this directory to `sys.path`, imports `ConstraintGenerationAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, ConstraintGenerationAgent)`.
3. Importing `agent.py` sets `spec = EDAAgent.read_spec(<this directory>)`, loading `config.yaml` at class definition time.
4. Uvicorn serves FastAPI `app` on `connection.port` with `/health` and `/tasks/execute`.
5. On `/tasks/execute`, `EDAAgent.handle` assembles engineering-memory context (see `context` in YAML), journals the task, and dispatches the requested skill.
6. The skill callable in `tools.py` returns `tool_observation(...)`. With `backend.type: none`, observations are safe stubs (`not_run`) until `EDA_FRAMEWORK` or another adapter binds real engines.

## Related agents

- Stage index: [`../README.md`](../README.md) (synthesis specialists under `synthesis/`).
- Stage lead(s) that delegate here:
  - [`synthesis_lead`](../synthesis_lead/) (port **8232**)
- Sibling agents in this folder:
  - [`equivalence`](../equivalence/) — worker, port **8236**
  - [`netlist_quality`](../netlist_quality/) — worker, port **8237**
  - [`retiming_mapping`](../retiming_mapping/) — worker, port **8235**
  - [`synthesis_experiment`](../synthesis_experiment/) — worker, port **8234**
  - [`synthesis_lead`](../synthesis_lead/) — lead, port **8232**
- Track overview: [`../../README.md`](../../README.md) (backend physical implementation).

## Files in this directory

| File | Role |
|------|------|
| `agent.py` | Defines `ConstraintGenerationAgent`; loads sibling `config.yaml` into `spec`. |
| `server.py` | HTTP/ASGI bootstrap; exports FastAPI `app` for uvicorn. |
| `tools.py` | `@tool` skill callables; stable EDA operation contracts. |
| `config.yaml` | Fleet manifest (`apiVersion: agentfleet/v1`): boundaries, port, skills, memory, telemetry. |
| `Dockerfile` | Container image; `EXPOSE 8233`; `CMD python server.py`. |
| `requirements.txt` | FastAPI, uvicorn, pydantic, PyYAML for the HTTP surface. |
| `__init__.py` | Re-exports `ConstraintGenerationAgent` for imports without starting HTTP. |
| `README.md` | This document. |

## Tool reference

### `write_create_clock` (`tools.write_create_clock`)

**Action:** `write_candidate`. Write create_clock constraints for the declared clocks.

### `write_generated_clock` (`tools.write_generated_clock`)

**Action:** `write_candidate`. Write create_generated_clock for one derived or gated clock.

### `write_input_delay` (`tools.write_input_delay`)

**Action:** `write_candidate`. Write set_input_delay for one port group.

### `write_output_delay` (`tools.write_output_delay`)

**Action:** `write_candidate`. Write set_output_delay for one port group.

### `write_clock_uncertainty` (`tools.write_clock_uncertainty`)

**Action:** `write_candidate`. Write setup and hold uncertainty for one clock.

### `write_clock_groups` (`tools.write_clock_groups`)

**Action:** `write_candidate`. Write asynchronous or logically exclusive clock groups.

### `write_false_path` (`tools.write_false_path`)

**Action:** `write_candidate`. Write a false path only with the justification that makes it legal.

### `write_multicycle_path` (`tools.write_multicycle_path`)

**Action:** `write_candidate`. Write a multicycle path with its architectural latency.

### `write_case_analysis` (`tools.write_case_analysis`)

**Action:** `write_candidate`. Write set_case_analysis for one operating mode.

### `write_sdc` (`tools.write_sdc`)

**Action:** `write_candidate`. Write the SDC file for this candidate.

### `audit_constraints` (`tools.audit_constraints`)

**Action:** `submit_tool_job`. Flag missing, contradictory, or unjustified exceptions.

### `check_clocks_exist_in_netlist` (`tools.check_clocks_exist_in_netlist`)

**Action:** `read_reports`. Check that every constrained clock exists in the candidate.

### `read_constraint_exceptions` (`tools.read_constraint_exceptions`)

**Action:** `read_reports`. Read false paths, multicycle paths, and case analysis.

### `flag_unjustified_exception` (`tools.flag_unjustified_exception`)

**Action:** `publish_finding`. Publish an exception that has no architectural justification.

### `flag_missing_clock` (`tools.flag_missing_clock`)

**Action:** `publish_finding`. Publish a declared clock with no create_clock.

### `record_constraint_lineage` (`tools.record_constraint_lineage`)

**Action:** `publish_finding`. Record the SDC revision, mode list, and RTL revision.

## Runtime, memory, and context

- **Reliability:** task timeout 120s, max retries 1, on failure `replan`.
- **Execution:** `direct_function`, `max_tasks=1`.
- **Context include:** `canonical_source`, `open_findings`, `experiments`, `gates`, `decisions`.
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
