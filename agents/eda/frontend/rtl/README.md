# Rtl stage agents

This directory groups **rtl**-stage agents. RTL implementation and integration: lint/quality, clock/reset, CDC/RDC, and low-power intent before handoff to synthesis.

Each child folder is an independent HTTP microservice (`python server.py`) discovered via its `config.yaml`. Leads declare `delegates_to` worker ids; validators declare independent gates. Workers execute skills in `tools.py` and return observations until an EDA adapter is bound.

## Agents in this stage

| Agent | Role | Port | Package |
|-------|------|------|---------|
| RTL Lead (`rtl_lead`) | `lead` | **8208** | [`rtl_lead/`](rtl_lead/) |
| RTL Implementation Agent (`rtl_implementation`) | `worker` | **8209** | [`rtl_implementation/`](rtl_implementation/) |
| Clock/Reset Agent (`clock_reset`) | `worker` | **8210** | [`clock_reset/`](clock_reset/) |
| CDC/RDC Agent (`cdc_rdc`) | `worker` | **8211** | [`cdc_rdc/`](cdc_rdc/) |
| Low-Power Agent (`low_power`) | `worker` | **8212** | [`low_power/`](low_power/) |
| Lint/Quality Agent (`lint_quality`) | `worker` | **8213** | [`lint_quality/`](lint_quality/) |
| RTL Integration Agent (`rtl_integration`) | `worker` | **8214** | [`rtl_integration/`](rtl_integration/) |

## Lead delegation graph

### `rtl_lead` (port **8208**)

Plan implementation of one block and coordinate lint, clock, CDC, low-power, and integration checks.

May schedule:
- [`rtl_implementation`](rtl_implementation/) — RTL Implementation Agent (**8209**)
- [`clock_reset`](clock_reset/) — Clock/Reset Agent (**8210**)
- [`cdc_rdc`](cdc_rdc/) — CDC/RDC Agent (**8211**)
- [`low_power`](low_power/) — Low-Power Agent (**8212**)
- [`lint_quality`](lint_quality/) — Lint/Quality Agent (**8213**)
- [`rtl_integration`](rtl_integration/) — RTL Integration Agent (**8214**)

Validators:
- `verification_validator`

## Suggested workflow (mental model)

1. **rtl_lead** coordinates implementation and integration workers.
2. **rtl_implementation** / **rtl_integration** own RTL edits on candidates.
3. **lint_quality**, **clock_reset**, **cdc_rdc**, and **low_power** close structural and power-intent checks.

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

- **8208** — `rtl_lead` (lead)
- **8209** — `rtl_implementation` (worker)
- **8210** — `clock_reset` (worker)
- **8211** — `cdc_rdc` (worker)
- **8212** — `low_power` (worker)
- **8213** — `lint_quality` (worker)
- **8214** — `rtl_integration` (worker)

## Child agent charters

### [`rtl_lead`](rtl_lead/) (port **8208**, `lead`)

Plan implementation of one block and coordinate lint, clock, CDC, low-power, and integration checks.

- **Skills in manifest:** 12 entries in `config.yaml` → `tools.py`.
- **Delegates to:** `rtl_implementation`, `clock_reset`, `cdc_rdc`, `low_power`, `lint_quality`, `rtl_integration`.

### [`rtl_implementation`](rtl_implementation/) (port **8209**, `worker`)

Make one bounded source change in an isolated branch and record the hypothesis it is testing.

- **Skills in manifest:** 12 entries in `config.yaml` → `tools.py`.

### [`clock_reset`](clock_reset/) (port **8210**, `worker`)

Check clocking, reset topology, and clock gating against the declared intent.

- **Skills in manifest:** 12 entries in `config.yaml` → `tools.py`.

### [`cdc_rdc`](cdc_rdc/) (port **8211**, `worker`)

Analyze clock and reset domain crossings and return evidence for a fix or a human waiver.

- **Skills in manifest:** 12 entries in `config.yaml` → `tools.py`.

### [`low_power`](low_power/) (port **8212**, `worker`)

Maintain power domains, isolation, retention, and UPF consistency.

- **Skills in manifest:** 12 entries in `config.yaml` → `tools.py`.

### [`lint_quality`](lint_quality/) (port **8213**, `worker`)

Detect structural, synthesis, style, and maintainability problems in a candidate.

- **Skills in manifest:** 12 entries in `config.yaml` → `tools.py`.

### [`rtl_integration`](rtl_integration/) (port **8214**, `worker`)

Merge compatible block candidates and mark stale downstream results.

- **Skills in manifest:** 12 entries in `config.yaml` → `tools.py`.

## Findings, gates, and promotion

Workers publish **findings** and edit **candidates**; validators emit **gates**; leads **recommend** but do not promote the canonical baseline. Human promotion and waivers sit outside these agents and are routed through `chip_flow_lead` decisions.

Every child returns structured observations while `backend.type: none`; binding `EDA_FRAMEWORK` does not relax `boundary.may_not` rules.

## Scheduling hints

| If you need… | Start with… |
|--------------|-------------|
| Plan implementation of one block and coordinate lint, clock, CDC, low-power, and integrati | `rtl_lead` |
| Make one bounded source change in an isolated branch and record the hypothesis it is testi | `rtl_implementation` |
| Check clocking, reset topology, and clock gating against the declared intent. | `clock_reset` |
| Analyze clock and reset domain crossings and return evidence for a fix or a human waiver. | `cdc_rdc` |
| Maintain power domains, isolation, retention, and UPF consistency. | `low_power` |
| Detect structural, synthesis, style, and maintainability problems in a candidate. | `lint_quality` |
| Merge compatible block candidates and mark stale downstream results. | `rtl_integration` |
