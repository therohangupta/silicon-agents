# Architecture stage agents

This directory groups **architecture**-stage agents. Pre-RTL architecture: requirements, interfaces, performance models, power/area estimates, and security/reliability studies roll up to an architecture lead that recommends block budgets—not informal conclusions.

Each child folder is an independent HTTP microservice (`python server.py`) discovered via its `config.yaml`. Leads declare `delegates_to` worker ids; validators declare independent gates. Workers execute skills in `tools.py` and return observations until an EDA adapter is bound.

## Agents in this stage

| Agent | Role | Port | Package |
|-------|------|------|---------|
| Requirements Agent (`requirements`) | `worker` | **8202** | [`requirements/`](requirements/) |
| Architecture Lead (`architecture_lead`) | `lead` | **8203** | [`architecture_lead/`](architecture_lead/) |
| Performance Modeling Agent (`performance_modeling`) | `worker` | **8204** | [`performance_modeling/`](performance_modeling/) |
| Interface Agent (`interface`) | `worker` | **8205** | [`interface/`](interface/) |
| Power/Area Estimation Agent (`power_area_estimation`) | `worker` | **8206** | [`power_area_estimation/`](power_area_estimation/) |
| Security/Reliability Agent (`security_reliability`) | `worker` | **8207** | [`security_reliability/`](security_reliability/) |

## Lead delegation graph

### `architecture_lead` (port **8203**)

Own decomposition and high-level tradeoffs. Select a qualified architecture revision with block budgets, not an informal conclusion.

May schedule:
- [`requirements`](requirements/) — Requirements Agent (**8202**)
- [`performance_modeling`](performance_modeling/) — Performance Modeling Agent (**8204**)
- [`interface`](interface/) — Interface Agent (**8205**)
- [`power_area_estimation`](power_area_estimation/) — Power/Area Estimation Agent (**8206**)
- [`security_reliability`](security_reliability/) — Security/Reliability Agent (**8207**)

## Suggested workflow (mental model)

1. **architecture_lead** decomposes the chip and sets block budgets.
2. Workers (**requirements**, **interface**, **performance_modeling**, **power_area_estimation**, **security_reliability**) produce evidence on isolated drafts.
3. The lead recommends a qualified architecture revision; RTL does not start from an untested intent.

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

- **8202** — `requirements` (worker)
- **8203** — `architecture_lead` (lead)
- **8204** — `performance_modeling` (worker)
- **8205** — `interface` (worker)
- **8206** — `power_area_estimation` (worker)
- **8207** — `security_reliability` (worker)

## Child agent charters

### [`requirements`](requirements/) (port **8202**, `worker`)

Convert product goals into traceable, measurable requirements and acceptance criteria.

- **Skills in manifest:** 12 entries in `config.yaml` → `tools.py`.

### [`architecture_lead`](architecture_lead/) (port **8203**, `lead`)

Own decomposition and high-level tradeoffs. Select a qualified architecture revision with block budgets, not an informal conclusion.

- **Skills in manifest:** 12 entries in `config.yaml` → `tools.py`.
- **Delegates to:** `requirements`, `performance_modeling`, `interface`, `power_area_estimation`, `security_reliability`.

### [`performance_modeling`](performance_modeling/) (port **8204**, `worker`)

Model target workloads and bottlenecks, and report projected metrics with their assumptions.

- **Skills in manifest:** 12 entries in `config.yaml` → `tools.py`.

### [`interface`](interface/) (port **8205**, `worker`)

Define inter-block protocols and contracts, including the assertions those contracts imply.

- **Skills in manifest:** 12 entries in `config.yaml` → `tools.py`.

### [`power_area_estimation`](power_area_estimation/) (port **8206**, `worker`)

Produce early power and area estimates with explicit uncertainty and assumptions.

- **Skills in manifest:** 12 entries in `config.yaml` → `tools.py`.

### [`security_reliability`](security_reliability/) (port **8207**, `worker`)

Define threat, safety, isolation, and reliability obligations, and the verification tasks they require.

- **Skills in manifest:** 12 entries in `config.yaml` → `tools.py`.

## Findings, gates, and promotion

Workers publish **findings** and edit **candidates**; validators emit **gates**; leads **recommend** but do not promote the canonical baseline. Human promotion and waivers sit outside these agents and are routed through `chip_flow_lead` decisions.

Every child returns structured observations while `backend.type: none`; binding `EDA_FRAMEWORK` does not relax `boundary.may_not` rules.

## Scheduling hints

| If you need… | Start with… |
|--------------|-------------|
| Convert product goals into traceable, measurable requirements and acceptance criteria. | `requirements` |
| Own decomposition and high-level tradeoffs. Select a qualified architecture revision with  | `architecture_lead` |
| Model target workloads and bottlenecks, and report projected metrics with their assumption | `performance_modeling` |
| Define inter-block protocols and contracts, including the assertions those contracts imply | `interface` |
| Produce early power and area estimates with explicit uncertainty and assumptions. | `power_area_estimation` |
| Define threat, safety, isolation, and reliability obligations, and the verification tasks  | `security_reliability` |
