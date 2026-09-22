# Floorplan stage agents

This directory groups **floorplan**-stage agents. Floorplanning: macros, pins, PDN, and early congestion/timing proxies under a floorplanning lead before placement.

Each child folder is an independent HTTP microservice (`python server.py`) discovered via its `config.yaml`. Leads declare `delegates_to` worker ids; validators declare independent gates. Workers execute skills in `tools.py` and return observations until an EDA adapter is bound.

## Agents in this stage

| Agent | Role | Port | Package |
|-------|------|------|---------|
| Floorplanning Lead (`floorplanning_lead`) | `lead` | **8238** | [`floorplanning_lead/`](floorplanning_lead/) |
| Macro-Placement Experiment Worker (`macro_placement`) | `worker` | **8239** | [`macro_placement/`](macro_placement/) |
| Pin-Assignment Agent (`pin_assignment`) | `worker` | **8240** | [`pin_assignment/`](pin_assignment/) |
| Power-Grid Agent (`power_grid`) | `worker` | **8241** | [`power_grid/`](power_grid/) |
| Early Congestion and Timing Evaluator (`early_congestion_timing`) | `worker` | **8242** | [`early_congestion_timing/`](early_congestion_timing/) |

## Lead delegation graph

### `floorplanning_lead` (port **8238**)

Own macro, pin, power-grid, blockage, and utilization decisions for one partition, and recommend a candidate for placement.

May schedule:
- [`macro_placement`](macro_placement/) — Macro-Placement Experiment Worker (**8239**)
- [`pin_assignment`](pin_assignment/) — Pin-Assignment Agent (**8240**)
- [`power_grid`](power_grid/) — Power-Grid Agent (**8241**)
- [`early_congestion_timing`](early_congestion_timing/) — Early Congestion and Timing Evaluator (**8242**)

## Suggested workflow (mental model)

1. **floorplanning_lead** reads die/macro/package inputs and publishes exploration workflow.
2. **macro_placement** proposes macro arrays under halo/channel constraints.
3. **pin_assignment** aligns pins to the package contract.
4. **power_grid** builds early PDN candidates for IR feedback.
5. **early_congestion_timing** runs trial place/route proxies before handoff to placement.

## Shared package layout (every child)

| File | Role |
|------|------|
| `config.yaml` | Manifest: identity, boundaries, port, skills, memory, telemetry, context. |
| `agent.py` | Thin `EdaAgent` subclass loading sibling YAML into `spec`. |
| `tools.py` | Skill contracts returning `tool_observation` until adapters bind. |
| `server.py` | `AgentService` FastAPI bootstrap (`/health`, `/tasks/execute`). |
| `Dockerfile` / `requirements.txt` | Container and Python deps for the HTTP surface. |
| `README.md` | Per-agent charter, skills, boundaries, boot path, and related agents. |

## Boot path (all children)

1. Compose or `python server.py` starts the container/process.
2. `server.py` loads `config.yaml` and the agent class into `AgentService`.
3. Orchestrator (or a lead's delegated workflow) POSTs to `/tasks/execute` with a skill id.
4. `EdaAgent.handle` journals, assembles context, and invokes the matching `tools.py` callable.
5. Observations and findings land in engineering memory and telemetry streams.

## Related documentation

- Parent track index: [`../README.md`](../README.md)
- Fleet agents tree: [`../README.md`](../README.md) or [`../../README.md`](../../README.md) depending on nesting.
- Shared agent runtime: `domains/eda/agent.py`, `domains/eda/server.py`.
- Telemetry conventions: [`../TELEMETRY.md`](../TELEMETRY.md) under `agents/`.

## Port map (quick reference)

- **8238** — `floorplanning_lead` (lead)
- **8239** — `macro_placement` (worker)
- **8240** — `pin_assignment` (worker)
- **8241** — `power_grid` (worker)
- **8242** — `early_congestion_timing` (worker)

## Child agent charters

### [`floorplanning_lead`](floorplanning_lead/) (port **8238**, `lead`)

Own macro, pin, power-grid, blockage, and utilization decisions for one partition, and recommend a candidate for placement.

- **Skills in manifest:** 13 entries in `config.yaml` → `tools.py`.
- **Delegates to:** `macro_placement`, `pin_assignment`, `power_grid`, `early_congestion_timing`.

### [`macro_placement`](macro_placement/) (port **8239**, `worker`)

Generate and score one isolated macro placement under halo, channel, orientation, and connectivity limits. Adapter target: OpenROAD initialize_floorplan and macro placement.

- **Skills in manifest:** 16 entries in `config.yaml` → `tools.py`.

### [`pin_assignment`](pin_assignment/) (port **8240**, `worker`)

Propose and validate block-pin locations, layers, ordering, and feedthroughs. Adapter target: OpenROAD pin placement.

- **Skills in manifest:** 14 entries in `config.yaml` → `tools.py`.

### [`power_grid`](power_grid/) (port **8241**, `worker`)

Design rings, straps, rails, vias, and macro connections against IR, electromigration, and routing-resource limits. Adapter target: OpenROAD PDN generation.

- **Skills in manifest:** 14 entries in `config.yaml` → `tools.py`.

### [`early_congestion_timing`](early_congestion_timing/) (port **8242**, `worker`)

Estimate routability and timing before detailed placement and identify likely hotspots. Adapter targets: OpenROAD global placement, global route, and early timing reports.

- **Skills in manifest:** 12 entries in `config.yaml` → `tools.py`.

## Findings, gates, and promotion

Workers publish **findings** and edit **candidates**; validators emit **gates**; leads **recommend** but do not promote the canonical baseline. Human promotion and waivers sit outside these agents and are routed through `chip_flow_lead` decisions.

Every child returns structured observations while `backend.type: none`; binding `EDA_FRAMEWORK` does not relax `boundary.may_not` rules.

## Scheduling hints

| If you need… | Start with… |
|--------------|-------------|
| Own macro, pin, power-grid, blockage, and utilization decisions for one partition, and rec | `floorplanning_lead` |
| Generate and score one isolated macro placement under halo, channel, orientation, and conn | `macro_placement` |
| Propose and validate block-pin locations, layers, ordering, and feedthroughs. Adapter targ | `pin_assignment` |
| Design rings, straps, rails, vias, and macro connections against IR, electromigration, and | `power_grid` |
| Estimate routability and timing before detailed placement and identify likely hotspots. Ad | `early_congestion_timing` |
