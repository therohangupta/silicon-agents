# Synthesis stage agents

This directory groups **synthesis**-stage agents. Logic synthesis: constraints, mapping/retiming experiments, equivalence, and netlist quality under a synthesis lead before floorplan.

Each child folder is an independent HTTP microservice (`python server.py`) discovered via its `config.yaml`. Leads declare `delegates_to` worker ids; validators declare independent gates. Workers execute skills in `tools.py` and return observations until an EDA adapter is bound.

## Agents in this stage

| Agent | Role | Port | Package |
|-------|------|------|---------|
| Synthesis Lead (`synthesis_lead`) | `lead` | **8232** | [`synthesis_lead/`](synthesis_lead/) |
| Constraint Generation and Validation Agent (`constraint_generation`) | `worker` | **8233** | [`constraint_generation/`](constraint_generation/) |
| Synthesis Experiment Worker (`synthesis_experiment`) | `worker` | **8234** | [`synthesis_experiment/`](synthesis_experiment/) |
| Retiming and Mapping Agent (`retiming_mapping`) | `worker` | **8235** | [`retiming_mapping/`](retiming_mapping/) |
| Equivalence Agent (`equivalence`) | `worker` | **8236** | [`equivalence/`](equivalence/) |
| Netlist Quality Agent (`netlist_quality`) | `worker` | **8237** | [`netlist_quality/`](netlist_quality/) |

## Lead delegation graph

### `synthesis_lead` (port **8232**)

Own the RTL-to-netlist workflow. Define synthesis experiments and acceptance criteria, and recommend candidates that satisfy functional and PPA requirements.

May schedule:
- [`constraint_generation`](constraint_generation/) — Constraint Generation and Validation Agent (**8233**)
- [`synthesis_experiment`](synthesis_experiment/) — Synthesis Experiment Worker (**8234**)
- [`retiming_mapping`](retiming_mapping/) — Retiming and Mapping Agent (**8235**)
- [`equivalence`](equivalence/) — Equivalence Agent (**8236**)
- [`netlist_quality`](netlist_quality/) — Netlist Quality Agent (**8237**)

## Suggested workflow (mental model)

1. **synthesis_lead** owns netlist candidates entering floorplan.
2. **constraint_generation** prepares SDC/UPF inputs.
3. **synthesis_experiment** / **retiming_mapping** explore mapping choices.
4. **equivalence** and **netlist_quality** gate logical and structural quality.

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

- **8232** — `synthesis_lead` (lead)
- **8233** — `constraint_generation` (worker)
- **8234** — `synthesis_experiment` (worker)
- **8235** — `retiming_mapping` (worker)
- **8236** — `equivalence` (worker)
- **8237** — `netlist_quality` (worker)

## Child agent charters

### [`synthesis_lead`](synthesis_lead/) (port **8232**, `lead`)

Own the RTL-to-netlist workflow. Define synthesis experiments and acceptance criteria, and recommend candidates that satisfy functional and PPA requirements.

- **Skills in manifest:** 14 entries in `config.yaml` → `tools.py`.
- **Delegates to:** `constraint_generation`, `synthesis_experiment`, `retiming_mapping`, `equivalence`, `netlist_quality`.

### [`constraint_generation`](constraint_generation/) (port **8233**, `worker`)

Create and audit clocks, generated clocks, I/O delays, uncertainties, exceptions, operating modes, and environment assumptions.

- **Skills in manifest:** 16 entries in `config.yaml` → `tools.py`.

### [`synthesis_experiment`](synthesis_experiment/) (port **8234**, `worker`)

Run one isolated synthesis candidate and return QoR, runtime, warnings, and artifacts. Adapter targets are Yosys and, later, a licensed synthesizer behind the same operations.

- **Skills in manifest:** 19 entries in `config.yaml` → `tools.py`.

### [`retiming_mapping`](retiming_mapping/) (port **8235**, `worker`)

Explore state-preserving retiming, logic restructuring, resource sharing, and technology mapping without violating architectural or verification contracts.

- **Skills in manifest:** 13 entries in `config.yaml` → `tools.py`.

### [`equivalence`](equivalence/) (port **8236**, `worker`)

Run and debug logical or sequential equivalence between RTL and a transformed implementation, and separate real divergence from setup or constraint problems. This is a check, not an independent gate.

- **Skills in manifest:** 12 entries in `config.yaml` → `tools.py`.

### [`netlist_quality`](netlist_quality/) (port **8237**, `worker`)

Inspect a netlist for structural defects, high fanout, loops, poor mappings, congestion risks, DFT incompatibilities, and suspicious QoR regressions.

- **Skills in manifest:** 12 entries in `config.yaml` → `tools.py`.

## Findings, gates, and promotion

Workers publish **findings** and edit **candidates**; validators emit **gates**; leads **recommend** but do not promote the canonical baseline. Human promotion and waivers sit outside these agents and are routed through `chip_flow_lead` decisions.

Every child returns structured observations while `backend.type: none`; binding `EDA_FRAMEWORK` does not relax `boundary.may_not` rules.

## Scheduling hints

| If you need… | Start with… |
|--------------|-------------|
| Own the RTL-to-netlist workflow. Define synthesis experiments and acceptance criteria, and | `synthesis_lead` |
| Create and audit clocks, generated clocks, I/O delays, uncertainties, exceptions, operatin | `constraint_generation` |
| Run one isolated synthesis candidate and return QoR, runtime, warnings, and artifacts. Ada | `synthesis_experiment` |
| Explore state-preserving retiming, logic restructuring, resource sharing, and technology m | `retiming_mapping` |
| Run and debug logical or sequential equivalence between RTL and a transformed implementati | `equivalence` |
| Inspect a netlist for structural defects, high fanout, loops, poor mappings, congestion ri | `netlist_quality` |
