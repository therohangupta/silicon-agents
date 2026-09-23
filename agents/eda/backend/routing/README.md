# Routing stage agents

This directory groups **routing**-stage agents. Global and detailed routing plus SI/noise and antenna/manufacturability repair under a routing lead.

Each child folder is an independent HTTP microservice (`python server.py`) discovered via its `config.yaml`. Leads declare `delegates_to` worker ids; validators declare independent gates. Workers execute skills in `tools.py` and return observations until an EDA adapter is bound.

## Agents in this stage

| Agent | Role | Port | Package |
|-------|------|------|---------|
| Routing Lead (`routing_lead`) | `lead` | **8249** | [`routing_lead/`](routing_lead/) |
| Global-Routing Experiment Agent (`global_routing`) | `worker` | **8250** | [`global_routing/`](global_routing/) |
| Detailed-Routing Repair Agent (`detailed_routing_repair`) | `worker` | **8251** | [`detailed_routing_repair/`](detailed_routing_repair/) |
| SI/Noise Repair Agent (`si_noise_repair`) | `worker` | **8252** | [`si_noise_repair/`](si_noise_repair/) |
| Antenna and Manufacturability Agent (`antenna_manufacturability`) | `worker` | **8253** | [`antenna_manufacturability/`](antenna_manufacturability/) |

## Lead delegation graph

### `routing_lead` (port **8249**)

Own global and detailed routing closure, including congestion, timing, signal integrity, antenna, and manufacturability.

May schedule:
- [`global_routing`](global_routing/) — Global-Routing Experiment Agent (**8250**)
- [`detailed_routing_repair`](detailed_routing_repair/) — Detailed-Routing Repair Agent (**8251**)
- [`si_noise_repair`](si_noise_repair/) — SI/Noise Repair Agent (**8252**)
- [`antenna_manufacturability`](antenna_manufacturability/) — Antenna and Manufacturability Agent (**8253**)

## Suggested workflow (mental model)

1. **routing_lead** owns global/detailed closure for the partition.
2. **global_routing** allocates tracks and guides.
3. **detailed_routing_repair** fixes DRC/antenna violations locally.
4. **si_noise_repair** and **antenna_manufacturability** address coupling and process rules.

## Shared package layout (every child)

| File | Role |
|------|------|
| `config.yaml` | Manifest: identity, boundaries, port, skills, memory, telemetry, context. |
| `agent.py` | Thin `EDAAgent` subclass loading sibling YAML into `spec`. |
| `tools.py` | Skill contracts returning `tool_observation` until adapters bind. |
| `server.py` | `AgentService` FastAPI bootstrap (`/health`, `/tasks/execute`). |
| `Dockerfile` / `requirements.txt` | Container and Python deps for the HTTP surface. |
| `README.md` | Per-agent charter, skills, boundaries, boot path, and related agents. |

## Boot path (all children)

1. Compose or `python server.py` starts the container/process.
2. `server.py` loads `config.yaml` and the agent class into `AgentService`.
3. Orchestrator (or a lead's delegated workflow) POSTs to `/tasks/execute` with a skill id.
4. `EDAAgent.handle` journals, assembles context, and invokes the matching `tools.py` callable.
5. Observations and findings land in engineering memory and telemetry streams.

## Related documentation

- Parent track index: [`../README.md`](../README.md)
- Fleet agents tree: [`../README.md`](../README.md) or [`../../README.md`](../../README.md) depending on nesting.
- Shared agent runtime: `domains/eda/runtime/agent.py`, `domains/eda/runtime/server.py`.
- Telemetry conventions: [`../TELEMETRY.md`](../TELEMETRY.md) under `agents/`.

## Port map (quick reference)

- **8249** — `routing_lead` (lead)
- **8250** — `global_routing` (worker)
- **8251** — `detailed_routing_repair` (worker)
- **8252** — `si_noise_repair` (worker)
- **8253** — `antenna_manufacturability` (worker)

## Child agent charters

### [`routing_lead`](routing_lead/) (port **8249**, `lead`)

Own global and detailed routing closure, including congestion, timing, signal integrity, antenna, and manufacturability.

- **Skills in manifest:** 12 entries in `config.yaml` → `tools.py`.
- **Delegates to:** `global_routing`, `detailed_routing_repair`, `si_noise_repair`, `antenna_manufacturability`.

### [`global_routing`](global_routing/) (port **8250**, `worker`)

Explore layer use, track assignment, congestion relief, and topology using global-route feedback. Adapter target: OpenROAD global_route.

- **Skills in manifest:** 12 entries in `config.yaml` → `tools.py`.

### [`detailed_routing_repair`](detailed_routing_repair/) (port **8251**, `worker`)

Diagnose local shorts, opens, spacing, vias, and pin-access failures, apply the repair on an isolated candidate, and verify that clean regions stay clean. Adapter target: OpenROAD detailed_route.

- **Skills in manifest:** 16 entries in `config.yaml` → `tools.py`.

### [`si_noise_repair`](si_noise_repair/) (port **8252**, `worker`)

Analyze coupling, crosstalk, and glitches, apply a repair on an isolated candidate, and verify it against noise and timing limits.

- **Skills in manifest:** 13 entries in `config.yaml` → `tools.py`.

### [`antenna_manufacturability`](antenna_manufacturability/) (port **8253**, `worker`)

Detect antenna, via-reliability, density, and patterning risks, apply a fix on an isolated candidate, and check electrical side effects. Adapter target: OpenROAD repair_antennas.

- **Skills in manifest:** 14 entries in `config.yaml` → `tools.py`.

## Findings, gates, and promotion

Workers publish **findings** and edit **candidates**; validators emit **gates**; leads **recommend** but do not promote the canonical baseline. Human promotion and waivers sit outside these agents and are routed through `chip_flow_lead` decisions.

Every child returns structured observations while `backend.type: none`; binding `EDA_FRAMEWORK` does not relax `boundary.may_not` rules.

## Scheduling hints

| If you need… | Start with… |
|--------------|-------------|
| Own global and detailed routing closure, including congestion, timing, signal integrity, a | `routing_lead` |
| Explore layer use, track assignment, congestion relief, and topology using global-route fe | `global_routing` |
| Diagnose local shorts, opens, spacing, vias, and pin-access failures, apply the repair on  | `detailed_routing_repair` |
| Analyze coupling, crosstalk, and glitches, apply a repair on an isolated candidate, and ve | `si_noise_repair` |
| Detect antenna, via-reliability, density, and patterning risks, apply a fix on an isolated | `antenna_manufacturability` |
