# Equivalence Agent (`equivalence`)

This directory is the deployable microservice package for the **Equivalence Agent** in the fleet **synthesis** stage (role `worker`).

## EDA responsibility

Write the compare setup, libraries, and black-box list. This does not edit either design.

Charter from `config.yaml`: Run and debug logical or sequential equivalence between RTL and a transformed implementation, and separate real divergence from setup or constraint problems. This is a check, not an independent gate.

As a **worker**, this process executes bounded skills on isolated candidates and reports observations. Promotion and program-level tradeoffs stay with leads and humans.

## Identity and HTTP port

| Field | Value |
|-------|-------|
| Agent id | `equivalence` |
| Stage | `synthesis` |
| Role | `worker` |
| Host | `host.docker.internal` |
| Port | **8236** (must match `Dockerfile` `EXPOSE`) |
| Health | `/health` |
| Execute | `/tasks/execute` |

## Boundaries

Hard limits from `config.yaml` `boundary`. The planner and `EDAAgent` enforce these even when a tool adapter could physically perform a forbidden action.

### May

- Submit an equivalence job
- Write compare setup on an isolated workspace
- Publish failing compare points

### May not

- Edit either design
- Map away a compare point to force a pass
- Emit a signoff gate
- Promote a candidate onto the canonical baseline
- Approve a waiver or relax a hard requirement
- Treat its own summary as independent signoff

## Skills

Skills bind planner task ids to callables in `tools.py` (`module: tools`, `execution.mode: direct_function`).

| Skill id | Action | Callable | Description |
|----------|--------|----------|-------------|
| `write_equivalence_setup` | `write_candidate` | `write_equivalence_setup` | Write the compare setup, libraries, and black-box list. This does not edit either design. |
| `write_compare_point_map` | `write_candidate` | `write_compare_point_map` | Write an explicit compare-point map. Every mapped-away point needs a justification. |
| `run_logical_equivalence` | `submit_tool_job` | `run_logical_equivalence` | Run combinational equivalence between RTL and the netlist. |
| `run_sequential_equivalence` | `submit_tool_job` | `run_sequential_equivalence` | Run sequential equivalence when retiming or restructuring moved state. |
| `read_failing_compare_points` | `read_reports` | `read_failing_compare_points` | Read compare points that failed. |
| `read_aborted_compare_points` | `read_reports` | `read_aborted_compare_points` | Read compare points the tool aborted. |
| `read_unmapped_points` | `read_reports` | `read_unmapped_points` | Read points present on only one side. |
| `classify_compare_points` | `publish_finding` | `classify_compare_points` | Separate functional mismatches from constraint or setup problems. |
| `trace_mismatch_cone` | `read_reports` | `trace_mismatch_cone` | Trace one failing compare point to the cone that diverges. |
| `flag_mapped_away_point` | `publish_finding` | `flag_mapped_away_point` | Publish a compare point removed from the map without justification. |
| `flag_setup_mismatch` | `publish_finding` | `flag_setup_mismatch` | Publish a failure caused by a missing clock, black box, or constraint. |
| `record_equivalence_tool_version` | `publish_finding` | `record_equivalence_tool_version` | Record the equivalence tool, version, and setup revision. |

## Delegation

This agent declares **no** `delegates_to` entries. It executes its own `tools.py` skills when scheduled by a lead or the chip-flow orchestrator.

## Boot path

Every fleet agent shares the same linear startup so compose and local dev behave identically.

1. Container or shell runs `python server.py` (`deployment.dockerfile` / image `agentfleet/equivalence:1.0`).
2. `server.py` prepends this directory to `sys.path`, imports `EquivalenceAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, EquivalenceAgent)`.
3. Importing `agent.py` sets `spec = EDAAgent.read_spec(<this directory>)`, loading `config.yaml` at class definition time.
4. Uvicorn serves FastAPI `app` on `connection.port` with `/health` and `/tasks/execute`.
5. On `/tasks/execute`, `EDAAgent.handle` assembles engineering-memory context (see `context` in YAML), journals the task, and dispatches the requested skill.
6. The skill callable in `tools.py` returns `tool_observation(...)`. With `backend.type: none`, observations are safe stubs (`not_run`) until `EDA_FRAMEWORK` or another adapter binds real engines.

## Related agents

- Stage index: [`../README.md`](../README.md) (synthesis specialists under `synthesis/`).
- Stage lead(s) that delegate here:
  - [`synthesis_lead`](../synthesis_lead/) (port **8232**)
- Sibling agents in this folder:
  - [`constraint_generation`](../constraint_generation/) — worker, port **8233**
  - [`netlist_quality`](../netlist_quality/) — worker, port **8237**
  - [`retiming_mapping`](../retiming_mapping/) — worker, port **8235**
  - [`synthesis_experiment`](../synthesis_experiment/) — worker, port **8234**
  - [`synthesis_lead`](../synthesis_lead/) — lead, port **8232**
- Track overview: [`../../README.md`](../../README.md) (backend physical implementation).

## Files in this directory

| File | Role |
|------|------|
| `agent.py` | Defines `EquivalenceAgent`; loads sibling `config.yaml` into `spec`. |
| `server.py` | HTTP/ASGI bootstrap; exports FastAPI `app` for uvicorn. |
| `tools.py` | `@tool` skill callables; stable EDA operation contracts. |
| `config.yaml` | Fleet manifest (`apiVersion: agentfleet/v1`): boundaries, port, skills, memory, telemetry. |
| `Dockerfile` | Container image; `EXPOSE 8236`; `CMD python server.py`. |
| `requirements.txt` | FastAPI, uvicorn, pydantic, PyYAML for the HTTP surface. |
| `__init__.py` | Re-exports `EquivalenceAgent` for imports without starting HTTP. |
| `README.md` | This document. |

## Tool reference

### `write_equivalence_setup` (`tools.write_equivalence_setup`)

**Action:** `write_candidate`. Write the compare setup, libraries, and black-box list. This does not edit either design.

### `write_compare_point_map` (`tools.write_compare_point_map`)

**Action:** `write_candidate`. Write an explicit compare-point map. Every mapped-away point needs a justification.

### `run_logical_equivalence` (`tools.run_logical_equivalence`)

**Action:** `submit_tool_job`. Run combinational equivalence between RTL and the netlist.

### `run_sequential_equivalence` (`tools.run_sequential_equivalence`)

**Action:** `submit_tool_job`. Run sequential equivalence when retiming or restructuring moved state.

### `read_failing_compare_points` (`tools.read_failing_compare_points`)

**Action:** `read_reports`. Read compare points that failed.

### `read_aborted_compare_points` (`tools.read_aborted_compare_points`)

**Action:** `read_reports`. Read compare points the tool aborted.

### `read_unmapped_points` (`tools.read_unmapped_points`)

**Action:** `read_reports`. Read points present on only one side.

### `classify_compare_points` (`tools.classify_compare_points`)

**Action:** `publish_finding`. Separate functional mismatches from constraint or setup problems.

### `trace_mismatch_cone` (`tools.trace_mismatch_cone`)

**Action:** `read_reports`. Trace one failing compare point to the cone that diverges.

### `flag_mapped_away_point` (`tools.flag_mapped_away_point`)

**Action:** `publish_finding`. Publish a compare point removed from the map without justification.

### `flag_setup_mismatch` (`tools.flag_setup_mismatch`)

**Action:** `publish_finding`. Publish a failure caused by a missing clock, black box, or constraint.

### `record_equivalence_tool_version` (`tools.record_equivalence_tool_version`)

**Action:** `publish_finding`. Record the equivalence tool, version, and setup revision.

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
