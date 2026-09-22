# Placement stage agents

This directory groups **placement**-stage agents. Standard-cell placement: experiments, evaluation, and partition boundaries under a placement lead.

Each child folder is an independent HTTP microservice (`python server.py`) discovered via its `config.yaml`. Leads declare `delegates_to` worker ids; validators declare independent gates. Workers execute skills in `tools.py` and return observations until an EDA adapter is bound.

## Agents in this stage

| Agent | Role | Port | Package |
|-------|------|------|---------|
| Placement Lead (`placement_lead`) | `lead` | **8243** | [`placement_lead/`](placement_lead/) |
| Placement Experiment Worker (`placement_experiment`) | `worker` | **8244** | [`placement_experiment/`](placement_experiment/) |
| Independent Multi-Corner Placement Evaluator (`placement_evaluator`) | `validator` | **8245** | [`placement_evaluator/`](placement_evaluator/) |
| Cross-Partition Boundary Coordinator (`boundary_coordinator`) | `worker` | **8246** | [`boundary_coordinator/`](boundary_coordinator/) |

## Lead delegation graph

### `placement_lead` (port **8243**)

Own standard-cell placement for one partition. Coordinate timing, congestion, power, and legalization, and recommend which candidate proceeds.

May schedule:
- [`placement_experiment`](placement_experiment/) — Placement Experiment Worker (**8244**)
- [`placement_evaluator`](placement_evaluator/) — Independent Multi-Corner Placement Evaluator (**8245**)
- [`boundary_coordinator`](boundary_coordinator/) — Cross-Partition Boundary Coordinator (**8246**)

Validators:
- `placement_evaluator`

## Suggested workflow (mental model)

1. **placement_lead** reads the qualified floorplan and publishes placement workflow.
2. **placement_experiment** tries one-hypothesis placement edits on isolated candidates.
3. **placement_evaluator** scores timing, congestion, and power metrics.
4. **boundary_coordinator** keeps partition interfaces legal across experiments.

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

## Independent validators in this stage

- [`placement_evaluator`](placement_evaluator/) (port **8245**): Re-check a placement across required modes and corners, and reject a gain that only shifts violations.

## Related documentation

- Parent track index: [`../README.md`](../README.md)
- Fleet agents tree: [`../README.md`](../README.md) or [`../../README.md`](../../README.md) depending on nesting.
- Shared agent runtime: `domains/eda/agent.py`, `domains/eda/server.py`.
- Telemetry conventions: [`../TELEMETRY.md`](../TELEMETRY.md) under `agents/`.

## Port map (quick reference)

- **8243** — `placement_lead` (lead)
- **8244** — `placement_experiment` (worker)
- **8245** — `placement_evaluator` (validator)
- **8246** — `boundary_coordinator` (worker)

## Child agent charters

### [`placement_lead`](placement_lead/) (port **8243**, `lead`)

Own standard-cell placement for one partition. Coordinate timing, congestion, power, and legalization, and recommend which candidate proceeds.

- **Skills in manifest:** 12 entries in `config.yaml` → `tools.py`.
- **Delegates to:** `placement_experiment`, `placement_evaluator`, `boundary_coordinator`.

### [`placement_experiment`](placement_experiment/) (port **8244**, `worker`)

Run one placement, legalization, buffering, and sizing strategy in an isolated workspace. Adapter target: OpenROAD global and detailed placement.

- **Skills in manifest:** 16 entries in `config.yaml` → `tools.py`.

### [`placement_evaluator`](placement_evaluator/) (port **8245**, `validator`)

Re-check a placement across required modes and corners, and reject a gain that only shifts violations.

- **Skills in manifest:** 12 entries in `config.yaml` → `tools.py`.

### [`boundary_coordinator`](boundary_coordinator/) (port **8246**, `worker`)

Check timing budgets, interface pins, feedthroughs, routing channels, power continuity, clock interactions, and constraint consistency across partitions.

- **Skills in manifest:** 13 entries in `config.yaml` → `tools.py`.

## Findings, gates, and promotion

Workers publish **findings** and edit **candidates**; validators emit **gates**; leads **recommend** but do not promote the canonical baseline. Human promotion and waivers sit outside these agents and are routed through `chip_flow_lead` decisions.

Every child returns structured observations while `backend.type: none`; binding `EDA_FRAMEWORK` does not relax `boundary.may_not` rules.

## Scheduling hints

| If you need… | Start with… |
|--------------|-------------|
| Own standard-cell placement for one partition. Coordinate timing, congestion, power, and l | `placement_lead` |
| Run one placement, legalization, buffering, and sizing strategy in an isolated workspace.  | `placement_experiment` |
| Re-check a placement across required modes and corners, and reject a gain that only shifts | `placement_evaluator` |
| Check timing budgets, interface pins, feedthroughs, routing channels, power continuity, cl | `boundary_coordinator` |
