# Retiming and Mapping Agent (`retiming_mapping`)

This directory is the deployable microservice package for the **Retiming and Mapping Agent** in the fleet **synthesis** stage (role `worker`).

## EDA responsibility

Write the state-preserving retiming directive and the registers it may move.

Charter from `config.yaml`: Explore state-preserving retiming, logic restructuring, resource sharing, and technology mapping without violating architectural or verification contracts.

As a **worker**, this process executes bounded skills on isolated candidates and reports observations. Promotion and program-level tradeoffs stay with leads and humans.

## Identity and HTTP port

| Field | Value |
|-------|-------|
| Agent id | `retiming_mapping` |
| Stage | `synthesis` |
| Role | `worker` |
| Host | `host.docker.internal` |
| Port | **8235** (must match `Dockerfile` `EXPOSE`) |
| Health | `/health` |
| Execute | `/tasks/execute` |

## Boundaries

Hard limits from `config.yaml` `boundary`. The planner and `EDAAgent` enforce these even when a tool adapter could physically perform a forbidden action.

### May

- Submit a retiming or mapping experiment
- Write the experiment directive
- Publish the metric delta

### May not

- Retiming across a timing exception that changes observable latency
- Skip equivalence
- Promote a candidate onto the canonical baseline
- Approve a waiver or relax a hard requirement
- Treat its own summary as independent signoff

## Skills

Skills bind planner task ids to callables in `tools.py` (`module: tools`, `execution.mode: direct_function`).

| Skill id | Action | Callable | Description |
|----------|--------|----------|-------------|
| `write_retiming_directive` | `write_candidate` | `write_retiming_directive` | Write the state-preserving retiming directive and the registers it may move. |
| `write_mapping_directive` | `write_candidate` | `write_mapping_directive` | Write the technology-mapping objective and dont-use list. |
| `write_resource_sharing_directive` | `write_candidate` | `write_resource_sharing_directive` | Write which operators may share a resource. |
| `explore_retiming` | `submit_tool_job` | `explore_retiming` | Run one state-preserving retiming experiment. |
| `explore_restructuring` | `submit_tool_job` | `explore_restructuring` | Run one logic-restructuring experiment. |
| `explore_resource_sharing` | `submit_tool_job` | `explore_resource_sharing` | Run one resource-sharing experiment. |
| `explore_mapping` | `submit_tool_job` | `explore_mapping` | Run one technology-mapping alternative. |
| `read_latency_contract` | `read_reports` | `read_latency_contract` | Read observable latency the retiming must preserve. |
| `read_retiming_delta` | `read_reports` | `read_retiming_delta` | Read timing, area, and power deltas versus the parent netlist. |
| `check_observable_latency` | `read_reports` | `check_observable_latency` | Check that moved registers did not change an architectural latency. |
| `flag_latency_change` | `publish_finding` | `flag_latency_change` | Publish a retiming that changes an observable latency. |
| `flag_missing_equivalence_for_retime` | `publish_finding` | `flag_missing_equivalence_for_retime` | Publish a transformed netlist that has no equivalence job. |
| `record_retime_hypothesis` | `publish_finding` | `record_retime_hypothesis` | Record the hypothesis, directive, and parent netlist. |

## Delegation

This agent declares **no** `delegates_to` entries. It executes its own `tools.py` skills when scheduled by a lead or the chip-flow orchestrator.

## Boot path

Every fleet agent shares the same linear startup so compose and local dev behave identically.

1. Container or shell runs `python server.py` (`deployment.dockerfile` / image `agentfleet/retiming_mapping:1.0`).
2. `server.py` prepends this directory to `sys.path`, imports `RetimingMappingAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, RetimingMappingAgent)`.
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
  - [`equivalence`](../equivalence/) — worker, port **8236**
  - [`netlist_quality`](../netlist_quality/) — worker, port **8237**
  - [`synthesis_experiment`](../synthesis_experiment/) — worker, port **8234**
  - [`synthesis_lead`](../synthesis_lead/) — lead, port **8232**
- Track overview: [`../../README.md`](../../README.md) (backend physical implementation).

## Files in this directory

| File | Role |
|------|------|
| `agent.py` | Defines `RetimingMappingAgent`; loads sibling `config.yaml` into `spec`. |
| `server.py` | HTTP/ASGI bootstrap; exports FastAPI `app` for uvicorn. |
| `tools.py` | `@tool` skill callables; stable EDA operation contracts. |
| `config.yaml` | Fleet manifest (`apiVersion: agentfleet/v1`): boundaries, port, skills, memory, telemetry. |
| `Dockerfile` | Container image; `EXPOSE 8235`; `CMD python server.py`. |
| `requirements.txt` | FastAPI, uvicorn, pydantic, PyYAML for the HTTP surface. |
| `__init__.py` | Re-exports `RetimingMappingAgent` for imports without starting HTTP. |
| `README.md` | This document. |

## Tool reference

### `write_retiming_directive` (`tools.write_retiming_directive`)

**Action:** `write_candidate`. Write the state-preserving retiming directive and the registers it may move.

### `write_mapping_directive` (`tools.write_mapping_directive`)

**Action:** `write_candidate`. Write the technology-mapping objective and dont-use list.

### `write_resource_sharing_directive` (`tools.write_resource_sharing_directive`)

**Action:** `write_candidate`. Write which operators may share a resource.

### `explore_retiming` (`tools.explore_retiming`)

**Action:** `submit_tool_job`. Run one state-preserving retiming experiment.

### `explore_restructuring` (`tools.explore_restructuring`)

**Action:** `submit_tool_job`. Run one logic-restructuring experiment.

### `explore_resource_sharing` (`tools.explore_resource_sharing`)

**Action:** `submit_tool_job`. Run one resource-sharing experiment.

### `explore_mapping` (`tools.explore_mapping`)

**Action:** `submit_tool_job`. Run one technology-mapping alternative.

### `read_latency_contract` (`tools.read_latency_contract`)

**Action:** `read_reports`. Read observable latency the retiming must preserve.

### `read_retiming_delta` (`tools.read_retiming_delta`)

**Action:** `read_reports`. Read timing, area, and power deltas versus the parent netlist.

### `check_observable_latency` (`tools.check_observable_latency`)

**Action:** `read_reports`. Check that moved registers did not change an architectural latency.

### `flag_latency_change` (`tools.flag_latency_change`)

**Action:** `publish_finding`. Publish a retiming that changes an observable latency.

### `flag_missing_equivalence_for_retime` (`tools.flag_missing_equivalence_for_retime`)

**Action:** `publish_finding`. Publish a transformed netlist that has no equivalence job.

### `record_retime_hypothesis` (`tools.record_retime_hypothesis`)

**Action:** `publish_finding`. Record the hypothesis, directive, and parent netlist.

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
