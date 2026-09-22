# Routing Lead (`routing_lead`)

This directory is the deployable microservice package for the **Routing Lead** in the fleet **routing** stage (role `lead`).

## EDA responsibility

Own global and detailed routing closure, including congestion, timing, signal integrity, antenna, and manufacturability.

As a **lead**, this process publishes workflows, reads qualified upstream artifacts, opens child agent tasks, compares candidates, and recommends next steps. It does **not** promote the canonical baseline or act as independent signoff.

## Identity and HTTP port

| Field | Value |
|-------|-------|
| Agent id | `routing_lead` |
| Stage | `routing` |
| Role | `lead` |
| Host | `host.docker.internal` |
| Port | **8249** (must match `Dockerfile` `EXPOSE`) |
| Health | `/health` |
| Execute | `/tasks/execute` |

## Boundaries

Hard limits from `config.yaml` `boundary`. The planner and `EdaAgent` enforce these even when a tool adapter could physically perform a forbidden action.

### May

- Publish a routing workflow
- Read the placed and clocked candidate
- Recommend which routed candidate advances

### May not

- Advance a routed database that failed antenna or SI checks
- Edit placement directly
- Promote a route
- Promote a candidate onto the canonical baseline
- Approve a waiver or relax a hard requirement
- Treat its own summary as independent signoff

## Skills

Skills bind planner task ids to callables in `tools.py` (`module: tools`, `execution.mode: direct_function`).

| Skill id | Action | Callable | Description |
|----------|--------|----------|-------------|
| `plan_routing_closure` | `create_workflow` | `plan_routing_closure` | Emit the routing and repair workflow. |
| `request_global_route_trial` | `create_workflow` | `request_global_route_trial` | Open one global-route experiment. |
| `request_detailed_route_repair` | `create_workflow` | `request_detailed_route_repair` | Open a localized detailed-route repair. |
| `request_si_repair` | `create_workflow` | `request_si_repair` | Open an SI repair for nets over the noise limit. |
| `request_antenna_repair` | `create_workflow` | `request_antenna_repair` | Open antenna and manufacturability repair. |
| `read_routing_status` | `read_reports` | `read_routing_status` | Read congestion, DRC, SI, antenna, and timing for each routed candidate. |
| `read_routing_acceptance` | `read_reports` | `read_routing_acceptance` | Read the DRC, SI, antenna, and timing criteria for advancement. |
| `compare_routed_candidates` | `read_reports` | `compare_routed_candidates` | Rank routed candidates that meet every hard check. |
| `recommend_routed_candidate` | `publish_finding` | `recommend_routed_candidate` | Record which routed candidate should advance to extraction. This does not promote it. |
| `flag_failed_route_check` | `publish_finding` | `flag_failed_route_check` | Publish a candidate that improved congestion and failed antenna, SI, or DRC. |
| `record_routing_strategy` | `publish_finding` | `record_routing_strategy` | Record the layer, cost, or repair change for the next trial. |
| `request_routing_decision` | `request_human_decision` | `request_routing_decision` | Ask a human to choose among routed candidates or to change a physical limit. |

## Delegation

This lead may open child workflows/tasks against:

- [`global_routing`](../global_routing/) — Global-Routing Experiment Agent (port **8250**)
- [`detailed_routing_repair`](../detailed_routing_repair/) — Detailed-Routing Repair Agent (port **8251**)
- [`si_noise_repair`](../si_noise_repair/) — SI/Noise Repair Agent (port **8252**)
- [`antenna_manufacturability`](../antenna_manufacturability/) — Antenna and Manufacturability Agent (port **8253**)

Delegation is declarative in `delegates_to`. The lead's `request_*` / `open_*` skills tell the orchestrator which child agent id and skill to schedule next; workers do not call each other directly over HTTP.

## Boot path

Every fleet agent shares the same linear startup so compose and local dev behave identically.

1. Container or shell runs `python server.py` (`deployment.dockerfile` / image `agentfleet/routing_lead:1.0`).
2. `server.py` prepends this directory to `sys.path`, imports `RoutingLeadAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, RoutingLeadAgent)`.
3. Importing `agent.py` sets `spec = EdaAgent.read_spec(<this directory>)`, loading `config.yaml` at class definition time.
4. Uvicorn serves FastAPI `app` on `connection.port` with `/health` and `/tasks/execute`.
5. On `/tasks/execute`, `EdaAgent.handle` assembles engineering-memory context (see `context` in YAML), journals the task, and dispatches the requested skill.
6. The skill callable in `tools.py` returns `tool_observation(...)`. With `backend.type: none`, observations are safe stubs (`not_run`) until `EDA_FRAMEWORK` or another adapter binds real engines.

## Related agents

- Stage index: [`../README.md`](../README.md) (routing specialists under `routing/`).
- Program orchestrator:
  - [`chip_flow_lead`](../../../chip_flow_lead/) (port **8201**)
- Sibling agents in this folder:
  - [`antenna_manufacturability`](../antenna_manufacturability/) — worker, port **8253**
  - [`detailed_routing_repair`](../detailed_routing_repair/) — worker, port **8251**
  - [`global_routing`](../global_routing/) — worker, port **8250**
  - [`si_noise_repair`](../si_noise_repair/) — worker, port **8252**
- Track overview: [`../../README.md`](../../README.md) (backend physical implementation).

## Files in this directory

| File | Role |
|------|------|
| `agent.py` | Defines `RoutingLeadAgent`; loads sibling `config.yaml` into `spec`. |
| `server.py` | HTTP/ASGI bootstrap; exports FastAPI `app` for uvicorn. |
| `tools.py` | `@tool` skill callables; stable EDA operation contracts. |
| `config.yaml` | Fleet manifest (`apiVersion: agentfleet/v1`): boundaries, port, skills, memory, telemetry. |
| `Dockerfile` | Container image; `EXPOSE 8249`; `CMD python server.py`. |
| `requirements.txt` | FastAPI, uvicorn, pydantic, PyYAML for the HTTP surface. |
| `__init__.py` | Re-exports `RoutingLeadAgent` for imports without starting HTTP. |
| `README.md` | This document. |

## Tool reference

### `plan_routing_closure` (`tools.plan_routing_closure`)

**Action:** `create_workflow`. Emit the routing and repair workflow.

Emit the child workflow that sequences global route, detailed repair, SI, and antenna work until routing closure.

### `request_global_route_trial` (`tools.request_global_route_trial`)

**Action:** `create_workflow`. Open one global-route experiment.

Ask the global-routing worker to run one coarse-route congestion experiment.

### `request_detailed_route_repair` (`tools.request_detailed_route_repair`)

**Action:** `create_workflow`. Open a localized detailed-route repair.

Ask detailed-routing repair to fix a localized DRC hotspot.

### `request_si_repair` (`tools.request_si_repair`)

**Action:** `create_workflow`. Open an SI repair for nets over the noise limit.

Ask SI/noise repair to fix aggressor/victim pairs over the noise limit.

### `request_antenna_repair` (`tools.request_antenna_repair`)

**Action:** `create_workflow`. Open antenna and manufacturability repair.

Ask antenna/manufacturability to clear process-antenna and density risks.

### `read_routing_status` (`tools.read_routing_status`)

**Action:** `read_reports`. Read congestion, DRC, SI, antenna, and timing for each routed candidate.

Read live congestion, DRC, SI, and antenna status for the routed candidate.

### `read_routing_acceptance` (`tools.read_routing_acceptance`)

**Action:** `read_reports`. Read the DRC, SI, antenna, and timing criteria for advancement.

Read whether acceptance gates for routing closure are satisfied.

### `compare_routed_candidates` (`tools.compare_routed_candidates`)

**Action:** `read_reports`. Rank routed candidates that meet every hard check.

Compare two routed candidates on congestion, DRC, SI, and timing.

### `recommend_routed_candidate` (`tools.recommend_routed_candidate`)

**Action:** `publish_finding`. Record which routed candidate should advance to extraction. This does not promote it.

Recommend which routed candidate should advance (does not promote itself).

### `flag_failed_route_check` (`tools.flag_failed_route_check`)

**Action:** `publish_finding`. Publish a candidate that improved congestion and failed antenna, SI, or DRC.

Publish a finding when a hard routing check failed.

### `record_routing_strategy` (`tools.record_routing_strategy`)

**Action:** `publish_finding`. Record the layer, cost, or repair change for the next trial.

Journal the routing strategy and worker assignment for provenance.

### `request_routing_decision` (`tools.request_routing_decision`)

**Action:** `request_human_decision`. Ask a human to choose among routed candidates or to change a physical limit.

Request an explicit human/lead decision on the routing candidate.

## Runtime, memory, and context

- **Reliability:** task timeout 120s, max retries 1, on failure `replan`.
- **Execution:** `direct_function`, `max_tasks=1`.
- **Context include:** `gates`, `workflows`, `open_findings`, `decisions`, `experiments`.
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
