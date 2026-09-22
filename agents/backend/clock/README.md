# Clock stage agents

This directory groups **clock**-stage agents. Clock tree synthesis and independent clock validation before routing consumes skew/latency budgets.

Each child folder is an independent HTTP microservice (`python server.py`) discovered via its `config.yaml`. Leads declare `delegates_to` worker ids; validators declare independent gates. Workers execute skills in `tools.py` and return observations until an EDA adapter is bound.

## Agents in this stage

| Agent | Role | Port | Package |
|-------|------|------|---------|
| CTS Agent (`cts`) | `worker` | **8247** | [`cts/`](cts/) |
| Clock Validation Agent (`clock_validation`) | `validator` | **8248** | [`clock_validation/`](clock_validation/) |

## Suggested workflow (mental model)

1. **cts** builds/skews the clock tree toward latency/skew targets.
2. **clock_validation** independently checks reachability, generated clocks, gating, and limits before routing signoff.

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

- [`clock_validation`](clock_validation/) (port **8248**): Independently analyze clock reachability, generated clocks, gating, pulse width, skew, latency, transition, and mode coverage before routing.

## Related documentation

- Parent track index: [`../README.md`](../README.md)
- Fleet agents tree: [`../README.md`](../README.md) or [`../../README.md`](../../README.md) depending on nesting.
- Shared agent runtime: `domains/eda/agent.py`, `domains/eda/server.py`.
- Telemetry conventions: [`../TELEMETRY.md`](../TELEMETRY.md) under `agents/`.

## Port map (quick reference)

- **8247** — `cts` (worker)
- **8248** — `clock_validation` (validator)

## Child agent charters

### [`cts`](cts/) (port **8247**, `worker`)

Build and optimize a clock tree or mesh for the required modes and corners. Adapter target: OpenROAD clock_tree_synthesis.

- **Skills in manifest:** 15 entries in `config.yaml` → `tools.py`.

### [`clock_validation`](clock_validation/) (port **8248**, `validator`)

Independently analyze clock reachability, generated clocks, gating, pulse width, skew, latency, transition, and mode coverage before routing.

- **Skills in manifest:** 13 entries in `config.yaml` → `tools.py`.

## Findings, gates, and promotion

Workers publish **findings** and edit **candidates**; validators emit **gates**; leads **recommend** but do not promote the canonical baseline. Human promotion and waivers sit outside these agents and are routed through `chip_flow_lead` decisions.

Every child returns structured observations while `backend.type: none`; binding `EDA_FRAMEWORK` does not relax `boundary.may_not` rules.

## Scheduling hints

| If you need… | Start with… |
|--------------|-------------|
| Build and optimize a clock tree or mesh for the required modes and corners. Adapter target | `cts` |
| Independently analyze clock reachability, generated clocks, gating, pulse width, skew, lat | `clock_validation` |

## Upstream and downstream

- **Upstream:** qualified **placement** and floorplan clock regions (`placement_lead`, port **8243**).
- **Downstream:** **routing_lead** (port **8249**) assumes the clock validation gate passed before treating route timing as closed.
