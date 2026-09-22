# Early Congestion and Timing Evaluator (`early_congestion_timing`)

This directory is the deployable microservice package for the **Early Congestion and Timing Evaluator** in the fleet **floorplan** stage (role `worker`).

## EDA responsibility

Early Congestion and Timing Evaluator agent module.

Charter from `config.yaml`: Estimate routability and timing before detailed placement and identify likely hotspots. Adapter targets: OpenROAD global placement, global route, and early timing reports.

As a **worker**, this process executes bounded skills on isolated candidates and reports observations. Promotion and program-level tradeoffs stay with leads and humans.

## Identity and HTTP port

| Field | Value |
|-------|-------|
| Agent id | `early_congestion_timing` |
| Stage | `floorplan` |
| Role | `worker` |
| Host | `host.docker.internal` |
| Port | **8242** (must match `Dockerfile` `EXPOSE`) |
| Health | `/health` |
| Execute | `/tasks/execute` |

## Boundaries

Hard limits from `config.yaml` `boundary`. The planner and `EdaAgent` enforce these even when a tool adapter could physically perform a forbidden action.

### May

- Submit trial placement and global route
- Read the floorplan candidate
- Publish hotspot evidence

### May not

- Treat the estimate as signoff timing
- Edit the floorplan it is scoring
- Promote a candidate onto the canonical baseline
- Approve a waiver or relax a hard requirement
- Treat its own summary as independent signoff

## Skills

Skills bind planner task ids to callables in `tools.py` (`module: tools`, `execution.mode: direct_function`).

| Skill id | Action | Callable | Description |
|----------|--------|----------|-------------|
| `run_trial_global_placement` | `submit_tool_job` | `run_trial_global_placement` | Run a trial global placement. Adapter target: OpenROAD global_placement. |
| `run_trial_global_route` | `submit_tool_job` | `run_trial_global_route` | Run a trial global route. Adapter target: OpenROAD global_route. |
| `estimate_routability` | `read_reports` | `estimate_routability` | Report congestion from the trial global route. |
| `estimate_early_timing` | `read_reports` | `estimate_early_timing` | Report early timing and the interfaces that dominate it. This is not signoff STA. |
| `read_congestion_map` | `read_reports` | `read_congestion_map` | Read congestion by layer and region. |
| `read_early_wns_tns` | `read_reports` | `read_early_wns_tns` | Read early WNS and TNS by path group. |
| `identify_congestion_hotspots` | `read_reports` | `identify_congestion_hotspots` | List regions over the congestion threshold. |
| `identify_critical_interfaces` | `read_reports` | `identify_critical_interfaces` | List interfaces that dominate early timing. |
| `compare_early_metrics` | `read_reports` | `compare_early_metrics` | Compare congestion and early timing across floorplan candidates. |
| `publish_routability_evidence` | `publish_finding` | `publish_routability_evidence` | Publish congestion and timing evidence that should guide a floorplan change. |
| `flag_early_timing_hotspot` | `publish_finding` | `flag_early_timing_hotspot` | Publish a path group that is already late before detailed placement. |
| `record_early_estimate_provenance` | `publish_finding` | `record_early_estimate_provenance` | Record the floorplan ref, recipe, and that these numbers are estimates. |

## Delegation

This agent declares **no** `delegates_to` entries. It executes its own `tools.py` skills when scheduled by a lead or the chip-flow orchestrator.

## Boot path

Every fleet agent shares the same linear startup so compose and local dev behave identically.

1. Container or shell runs `python server.py` (`deployment.dockerfile` / image `agentfleet/early_congestion_timing:1.0`).
2. `server.py` prepends this directory to `sys.path`, imports `EarlyCongestionTimingAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, EarlyCongestionTimingAgent)`.
3. Importing `agent.py` sets `spec = EdaAgent.read_spec(<this directory>)`, loading `config.yaml` at class definition time.
4. Uvicorn serves FastAPI `app` on `connection.port` with `/health` and `/tasks/execute`.
5. On `/tasks/execute`, `EdaAgent.handle` assembles engineering-memory context (see `context` in YAML), journals the task, and dispatches the requested skill.
6. The skill callable in `tools.py` returns `tool_observation(...)`. With `backend.type: none`, observations are safe stubs (`not_run`) until `EDA_FRAMEWORK` or another adapter binds real engines.

## Related agents

- Stage index: [`../README.md`](../README.md) (floorplan specialists under `floorplan/`).
- Stage lead(s) that delegate here:
  - [`floorplanning_lead`](../floorplanning_lead/) (port **8238**)
- Sibling agents in this folder:
  - [`floorplanning_lead`](../floorplanning_lead/) — lead, port **8238**
  - [`macro_placement`](../macro_placement/) — worker, port **8239**
  - [`pin_assignment`](../pin_assignment/) — worker, port **8240**
  - [`power_grid`](../power_grid/) — worker, port **8241**
- Track overview: [`../../README.md`](../../README.md) (backend physical implementation).

## Files in this directory

| File | Role |
|------|------|
| `agent.py` | Defines `EarlyCongestionTimingAgent`; loads sibling `config.yaml` into `spec`. |
| `server.py` | HTTP/ASGI bootstrap; exports FastAPI `app` for uvicorn. |
| `tools.py` | `@tool` skill callables; stable EDA operation contracts. |
| `config.yaml` | Fleet manifest (`apiVersion: agentfleet/v1`): boundaries, port, skills, memory, telemetry. |
| `Dockerfile` | Container image; `EXPOSE 8242`; `CMD python server.py`. |
| `requirements.txt` | FastAPI, uvicorn, pydantic, PyYAML for the HTTP surface. |
| `__init__.py` | Re-exports `EarlyCongestionTimingAgent` for imports without starting HTTP. |
| `README.md` | This document. |

## Tool reference

### `run_trial_global_placement` (`tools.run_trial_global_placement`)

**Action:** `submit_tool_job`. Run a trial global placement. Adapter target: OpenROAD global_placement.

### `run_trial_global_route` (`tools.run_trial_global_route`)

**Action:** `submit_tool_job`. Run a trial global route. Adapter target: OpenROAD global_route.

### `estimate_routability` (`tools.estimate_routability`)

**Action:** `read_reports`. Report congestion from the trial global route.

### `estimate_early_timing` (`tools.estimate_early_timing`)

**Action:** `read_reports`. Report early timing and the interfaces that dominate it. This is not signoff STA.

### `read_congestion_map` (`tools.read_congestion_map`)

**Action:** `read_reports`. Read congestion by layer and region.

### `read_early_wns_tns` (`tools.read_early_wns_tns`)

**Action:** `read_reports`. Read early WNS and TNS by path group.

### `identify_congestion_hotspots` (`tools.identify_congestion_hotspots`)

**Action:** `read_reports`. List regions over the congestion threshold.

### `identify_critical_interfaces` (`tools.identify_critical_interfaces`)

**Action:** `read_reports`. List interfaces that dominate early timing.

### `compare_early_metrics` (`tools.compare_early_metrics`)

**Action:** `read_reports`. Compare congestion and early timing across floorplan candidates.

### `publish_routability_evidence` (`tools.publish_routability_evidence`)

**Action:** `publish_finding`. Publish congestion and timing evidence that should guide a floorplan change.

### `flag_early_timing_hotspot` (`tools.flag_early_timing_hotspot`)

**Action:** `publish_finding`. Publish a path group that is already late before detailed placement.

### `record_early_estimate_provenance` (`tools.record_early_estimate_provenance`)

**Action:** `publish_finding`. Record the floorplan ref, recipe, and that these numbers are estimates.

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
- **Shared base:** Task handling lives in `domains/eda/agent.py`; HTTP wiring in `domains/eda/server.py`.
- **Telemetry:** See [`../../TELEMETRY.md`](../../TELEMETRY.md) (path may vary by depth) for fleet-wide observability conventions.

## How a newcomer should read this agent

1. Read `config.yaml` `metadata`, `boundary`, and `capabilities` for charter and limits.
2. Skim the skills table above, then open `tools.py` for parameter shapes.
3. Read `agent.py` and `server.py` only to confirm boot wiring.
4. Treat `Dockerfile` / `requirements.txt` as deployment detail.
