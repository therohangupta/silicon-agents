# Power-Grid Agent (`power_grid`)

This directory is the deployable microservice package for the **Power-Grid Agent** in the fleet **floorplan** stage (role `worker`).

## EDA responsibility

Read domains, supplies, and macro power pins.

Charter from `config.yaml`: Design rings, straps, rails, vias, and macro connections against IR, electromigration, and routing-resource limits. Adapter target: OpenROAD PDN generation.

As a **worker**, this process executes bounded skills on isolated candidates and reports observations. Promotion and program-level tradeoffs stay with leads and humans.

## Identity and HTTP port

| Field | Value |
|-------|-------|
| Agent id | `power_grid` |
| Stage | `floorplan` |
| Role | `worker` |
| Host | `host.docker.internal` |
| Port | **8241** (must match `Dockerfile` `EXPOSE`) |
| Health | `/health` |
| Execute | `/tasks/execute` |

## Boundaries

Hard limits from `config.yaml` `boundary`. The planner and `EDAAgent` enforce these even when a tool adapter could physically perform a forbidden action.

### May

- Write a power-grid candidate
- Submit an early IR check

### May not

- Remove straps to clear congestion without publishing the IR impact
- Edit the package
- Promote a candidate onto the canonical baseline
- Approve a waiver or relax a hard requirement
- Treat its own summary as independent signoff

## Skills

Skills bind planner task ids to callables in `tools.py` (`module: tools`, `execution.mode: direct_function`).

| Skill id | Action | Callable | Description |
|----------|--------|----------|-------------|
| `read_power_domains` | `read_reports` | `read_power_domains` | Read domains, supplies, and macro power pins. |
| `read_current_budget` | `read_reports` | `read_current_budget` | Read the activity assumption and current budget. |
| `write_pdn_spec` | `write_candidate` | `write_pdn_spec` | Write the power-grid specification for rings, straps, rails, and vias. |
| `propose_power_grid` | `write_candidate` | `propose_power_grid` | Build rings, straps, rails, and macro connections. Adapter target: OpenROAD pdngen. |
| `add_power_ring` | `write_candidate` | `add_power_ring` | Add a core or domain ring. |
| `add_power_straps` | `write_candidate` | `add_power_straps` | Add straps on a named layer and pitch. |
| `add_rails` | `write_candidate` | `add_rails` | Add standard-cell rails. |
| `connect_macro_power` | `write_candidate` | `connect_macro_power` | Connect macro power pins to the grid. |
| `write_pdn_def` | `write_candidate` | `write_pdn_def` | Write the power-grid geometry into the candidate. |
| `evaluate_ir_em_proxy` | `submit_tool_job` | `evaluate_ir_em_proxy` | Estimate IR drop and electromigration against the activity assumption. |
| `estimate_grid_routing_resource` | `read_reports` | `estimate_grid_routing_resource` | Estimate the tracks the grid consumes. |
| `flag_ir_over_budget` | `publish_finding` | `flag_ir_over_budget` | Publish a region whose IR proxy exceeds the budget. |
| `flag_strap_congestion_tradeoff` | `publish_finding` | `flag_strap_congestion_tradeoff` | Publish a strap removal and the IR impact that must be accepted with it. |
| `record_pdn_recipe` | `publish_finding` | `record_pdn_recipe` | Record the PDN spec, pitch, and activity file. |

## Delegation

This agent declares **no** `delegates_to` entries. It executes its own `tools.py` skills when scheduled by a lead or the chip-flow orchestrator.

## Boot path

Every fleet agent shares the same linear startup so compose and local dev behave identically.

1. Container or shell runs `python server.py` (`deployment.dockerfile` / image `agentfleet/power_grid:1.0`).
2. `server.py` prepends this directory to `sys.path`, imports `PowerGridAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, PowerGridAgent)`.
3. Importing `agent.py` sets `spec = EDAAgent.read_spec(<this directory>)`, loading `config.yaml` at class definition time.
4. Uvicorn serves FastAPI `app` on `connection.port` with `/health` and `/tasks/execute`.
5. On `/tasks/execute`, `EDAAgent.handle` assembles engineering-memory context (see `context` in YAML), journals the task, and dispatches the requested skill.
6. The skill callable in `tools.py` returns `tool_observation(...)`. With `backend.type: none`, observations are safe stubs (`not_run`) until `EDA_FRAMEWORK` or another adapter binds real engines.

## Related agents

- Stage index: [`../README.md`](../README.md) (floorplan specialists under `floorplan/`).
- Stage lead(s) that delegate here:
  - [`floorplanning_lead`](../floorplanning_lead/) (port **8238**)
- Sibling agents in this folder:
  - [`early_congestion_timing`](../early_congestion_timing/) — worker, port **8242**
  - [`floorplanning_lead`](../floorplanning_lead/) — lead, port **8238**
  - [`macro_placement`](../macro_placement/) — worker, port **8239**
  - [`pin_assignment`](../pin_assignment/) — worker, port **8240**
- Track overview: [`../../README.md`](../../README.md) (backend physical implementation).

## Files in this directory

| File | Role |
|------|------|
| `agent.py` | Defines `PowerGridAgent`; loads sibling `config.yaml` into `spec`. |
| `server.py` | HTTP/ASGI bootstrap; exports FastAPI `app` for uvicorn. |
| `tools.py` | `@tool` skill callables; stable EDA operation contracts. |
| `config.yaml` | Fleet manifest (`apiVersion: agentfleet/v1`): boundaries, port, skills, memory, telemetry. |
| `Dockerfile` | Container image; `EXPOSE 8241`; `CMD python server.py`. |
| `requirements.txt` | FastAPI, uvicorn, pydantic, PyYAML for the HTTP surface. |
| `__init__.py` | Re-exports `PowerGridAgent` for imports without starting HTTP. |
| `README.md` | This document. |

## Tool reference

### `read_power_domains` (`tools.read_power_domains`)

**Action:** `read_reports`. Read domains, supplies, and macro power pins.

### `read_current_budget` (`tools.read_current_budget`)

**Action:** `read_reports`. Read the activity assumption and current budget.

### `write_pdn_spec` (`tools.write_pdn_spec`)

**Action:** `write_candidate`. Write the power-grid specification for rings, straps, rails, and vias.

### `propose_power_grid` (`tools.propose_power_grid`)

**Action:** `write_candidate`. Build rings, straps, rails, and macro connections. Adapter target: OpenROAD pdngen.

### `add_power_ring` (`tools.add_power_ring`)

**Action:** `write_candidate`. Add a core or domain ring.

### `add_power_straps` (`tools.add_power_straps`)

**Action:** `write_candidate`. Add straps on a named layer and pitch.

### `add_rails` (`tools.add_rails`)

**Action:** `write_candidate`. Add standard-cell rails.

### `connect_macro_power` (`tools.connect_macro_power`)

**Action:** `write_candidate`. Connect macro power pins to the grid.

### `write_pdn_def` (`tools.write_pdn_def`)

**Action:** `write_candidate`. Write the power-grid geometry into the candidate.

### `evaluate_ir_em_proxy` (`tools.evaluate_ir_em_proxy`)

**Action:** `submit_tool_job`. Estimate IR drop and electromigration against the activity assumption.

### `estimate_grid_routing_resource` (`tools.estimate_grid_routing_resource`)

**Action:** `read_reports`. Estimate the tracks the grid consumes.

### `flag_ir_over_budget` (`tools.flag_ir_over_budget`)

**Action:** `publish_finding`. Publish a region whose IR proxy exceeds the budget.

### `flag_strap_congestion_tradeoff` (`tools.flag_strap_congestion_tradeoff`)

**Action:** `publish_finding`. Publish a strap removal and the IR impact that must be accepted with it.

### `record_pdn_recipe` (`tools.record_pdn_recipe`)

**Action:** `publish_finding`. Record the PDN spec, pitch, and activity file.

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
