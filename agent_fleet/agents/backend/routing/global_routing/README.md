# Global-Routing Experiment Agent (`global_routing`)

This directory is the deployable microservice package for the **Global-Routing Experiment Agent** in the fleet **routing** stage (role `worker`).

## EDA responsibility

Tools for the Global-Routing Experiment Agent.

Charter from `config.yaml`: Explore layer use, track assignment, congestion relief, and topology using global-route feedback. Adapter target: OpenROAD global_route.

As a **worker**, this process executes bounded skills on isolated candidates and reports observations. Promotion and program-level tradeoffs stay with leads and humans.

## Identity and HTTP port

| Field | Value |
|-------|-------|
| Agent id | `global_routing` |
| Stage | `routing` |
| Role | `worker` |
| Host | `host.docker.internal` |
| Port | **8250** (must match `Dockerfile` `EXPOSE`) |
| Health | `/health` |
| Execute | `/tasks/execute` |

## Boundaries

Hard limits from `config.yaml` `boundary`. The planner and `EdaAgent` enforce these even when a tool adapter could physically perform a forbidden action.

### May

- Submit one global-route experiment
- Write layer and adjustment directives
- Report congestion

### May not

- Edit the detailed route database
- Hide a congested layer
- Promote a candidate onto the canonical baseline
- Approve a waiver or relax a hard requirement
- Treat its own summary as independent signoff

## Skills

Skills bind planner task ids to callables in `tools.py` (`module: tools`, `execution.mode: direct_function`).

| Skill id | Action | Callable | Description |
|----------|--------|----------|-------------|
| `write_routing_layer_directive` | `write_candidate` | `write_routing_layer_directive` | Write the layers this experiment may use. Adapter target: OpenROAD set_routing_layers. |
| `write_layer_adjustment` | `write_candidate` | `write_layer_adjustment` | Write a congestion adjustment for one layer. |
| `write_global_route_guides_spec` | `write_candidate` | `write_global_route_guides_spec` | Write topology and buffering guidance for this trial. |
| `explore_global_route` | `submit_tool_job` | `explore_global_route` | Run one global-route experiment. Adapter target: OpenROAD global_route. |
| `report_global_congestion` | `read_reports` | `report_global_congestion` | Return congestion by layer and region. |
| `read_route_guides` | `read_reports` | `read_route_guides` | Read the route guides this trial produced. |
| `read_overflow_nets` | `read_reports` | `read_overflow_nets` | List nets with overflow. |
| `compare_congestion_to_baseline` | `read_reports` | `compare_congestion_to_baseline` | Compare congestion with the parent route. |
| `write_route_guides` | `write_candidate` | `write_route_guides` | Write the guide artifact for detailed routing. |
| `flag_hidden_congested_layer` | `publish_finding` | `flag_hidden_congested_layer` | Publish a report that omitted a layer over the congestion limit. |
| `flag_global_route_overflow` | `publish_finding` | `flag_global_route_overflow` | Publish regions that remain over the overflow limit. |
| `record_global_route_recipe` | `publish_finding` | `record_global_route_recipe` | Record layers, adjustments, and the OpenROAD recipe id. |

## Delegation

This agent declares **no** `delegates_to` entries. It executes its own `tools.py` skills when scheduled by a lead or the chip-flow orchestrator.

## Boot path

Every fleet agent shares the same linear startup so compose and local dev behave identically.

1. Container or shell runs `python server.py` (`deployment.dockerfile` / image `agentfleet/global_routing:1.0`).
2. `server.py` prepends this directory to `sys.path`, imports `GlobalRoutingAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, GlobalRoutingAgent)`.
3. Importing `agent.py` sets `spec = EdaAgent.read_spec(<this directory>)`, loading `config.yaml` at class definition time.
4. Uvicorn serves FastAPI `app` on `connection.port` with `/health` and `/tasks/execute`.
5. On `/tasks/execute`, `EdaAgent.handle` assembles engineering-memory context (see `context` in YAML), journals the task, and dispatches the requested skill.
6. The skill callable in `tools.py` returns `tool_observation(...)`. With `backend.type: none`, observations are safe stubs (`not_run`) until `EDA_FRAMEWORK` or another adapter binds real engines.

## Related agents

- Stage index: [`../README.md`](../README.md) (routing specialists under `routing/`).
- Stage lead(s) that delegate here:
  - [`routing_lead`](../routing_lead/) (port **8249**)
- Sibling agents in this folder:
  - [`antenna_manufacturability`](../antenna_manufacturability/) — worker, port **8253**
  - [`detailed_routing_repair`](../detailed_routing_repair/) — worker, port **8251**
  - [`routing_lead`](../routing_lead/) — lead, port **8249**
  - [`si_noise_repair`](../si_noise_repair/) — worker, port **8252**
- Track overview: [`../../README.md`](../../README.md) (backend physical implementation).

## Files in this directory

| File | Role |
|------|------|
| `agent.py` | Defines `GlobalRoutingAgent`; loads sibling `config.yaml` into `spec`. |
| `server.py` | HTTP/ASGI bootstrap; exports FastAPI `app` for uvicorn. |
| `tools.py` | `@tool` skill callables; stable EDA operation contracts. |
| `config.yaml` | Fleet manifest (`apiVersion: agentfleet/v1`): boundaries, port, skills, memory, telemetry. |
| `Dockerfile` | Container image; `EXPOSE 8250`; `CMD python server.py`. |
| `requirements.txt` | FastAPI, uvicorn, pydantic, PyYAML for the HTTP surface. |
| `__init__.py` | Re-exports `GlobalRoutingAgent` for imports without starting HTTP. |
| `README.md` | This document. |

## Tool reference

### `write_routing_layer_directive` (`tools.write_routing_layer_directive`)

**Action:** `write_candidate`. Write the layers this experiment may use. Adapter target: OpenROAD set_routing_layers.

Constrain which metal layers the GR trial may use (OpenROAD set_routing_layers).

### `write_layer_adjustment` (`tools.write_layer_adjustment`)

**Action:** `write_candidate`. Write a congestion adjustment for one layer.

Apply a per-layer congestion resource adjustment so GR avoids or favors a layer.

### `write_global_route_guides_spec` (`tools.write_global_route_guides_spec`)

**Action:** `write_candidate`. Write topology and buffering guidance for this trial.

Write topology/buffering guidance that shapes how GR builds guides.

### `explore_global_route` (`tools.explore_global_route`)

**Action:** `submit_tool_job`. Run one global-route experiment. Adapter target: OpenROAD global_route.

Submit one OpenROAD global_route experiment on an isolated candidate.

### `report_global_congestion` (`tools.report_global_congestion`)

**Action:** `read_reports`. Return congestion by layer and region.

Return overflow and demand/supply congestion by layer and GCell region.

### `read_route_guides` (`tools.read_route_guides`)

**Action:** `read_reports`. Read the route guides this trial produced.

Read the guide rectangles/tracks this GR trial produced for detailed routing.

### `read_overflow_nets` (`tools.read_overflow_nets`)

**Action:** `read_reports`. List nets with overflow.

List nets whose demand exceeds GR track capacity (overflow).

### `compare_congestion_to_baseline` (`tools.compare_congestion_to_baseline`)

**Action:** `read_reports`. Compare congestion with the parent route.

Diff congestion of this trial against the parent/baseline route.

### `write_route_guides` (`tools.write_route_guides`)

**Action:** `write_candidate`. Write the guide artifact for detailed routing.

Persist guide artifacts so detailed routing can follow them.

### `flag_hidden_congested_layer` (`tools.flag_hidden_congested_layer`)

**Action:** `publish_finding`. Publish a report that omitted a layer over the congestion limit.

Finding: a report omitted a layer that is still over the congestion limit.

### `flag_global_route_overflow` (`tools.flag_global_route_overflow`)

**Action:** `publish_finding`. Publish regions that remain over the overflow limit.

Finding: regions remain over the overflow limit after the trial.

### `record_global_route_recipe` (`tools.record_global_route_recipe`)

**Action:** `publish_finding`. Record layers, adjustments, and the OpenROAD recipe id.

Record layers, adjustments, and OpenROAD recipe id for provenance.

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
