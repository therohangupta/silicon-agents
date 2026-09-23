# Dft stage agents

This directory groups **dft**-stage agents. Design-for-test: scan, ATPG, testability, MBIST/LBIST, and physical/timing handoff under a DFT lead and validator.

Each child folder is an independent HTTP microservice (`python server.py`) discovered via its `config.yaml`. Leads declare `delegates_to` worker ids; validators declare independent gates. Workers execute skills in `tools.py` and return observations until an EDA adapter is bound.

## Agents in this stage

| Agent | Role | Port | Package |
|-------|------|------|---------|
| DFT Lead (`dft_lead`) | `lead` | **8225** | [`dft_lead/`](dft_lead/) |
| Scan Insertion Agent (`scan_insertion`) | `worker` | **8226** | [`scan_insertion/`](scan_insertion/) |
| ATPG Campaign Agent (`atpg_campaign`) | `worker` | **8227** | [`atpg_campaign/`](atpg_campaign/) |
| Testability Analysis Agent (`testability_analysis`) | `worker` | **8228** | [`testability_analysis/`](testability_analysis/) |
| MBIST/LBIST Agent (`mbist_lbist`) | `worker` | **8229** | [`mbist_lbist/`](mbist_lbist/) |
| DFT Physical/Timing Coordination Agent (`dft_physical_timing`) | `worker` | **8230** | [`dft_physical_timing/`](dft_physical_timing/) |
| Independent DFT Validator (`dft_validator`) | `validator` | **8231** | [`dft_validator/`](dft_validator/) |

## Lead delegation graph

### `dft_lead` (port **8225**)

Own the block and chip test strategy. Decompose it into scan, ATPG, self-test, and physical-integration work, and coordinate closure against coverage, test time, area, power, and timing.

May schedule:
- [`scan_insertion`](scan_insertion/) — Scan Insertion Agent (**8226**)
- [`atpg_campaign`](atpg_campaign/) — ATPG Campaign Agent (**8227**)
- [`testability_analysis`](testability_analysis/) — Testability Analysis Agent (**8228**)
- [`mbist_lbist`](mbist_lbist/) — MBIST/LBIST Agent (**8229**)
- [`dft_physical_timing`](dft_physical_timing/) — DFT Physical/Timing Coordination Agent (**8230**)
- [`dft_validator`](dft_validator/) — Independent DFT Validator (**8231**)

Validators:
- `dft_validator`

## Suggested workflow (mental model)

1. **dft_lead** publishes DFT workflow across scan, logic BIST, and ATPG.
2. **testability_analysis** and **scan_insertion** prepare controllability/observability.
3. **atpg_campaign** and **mbist_lbist** expand pattern coverage.
4. **dft_physical_timing** and **dft_validator** gate handoff to backend signoff.

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

## Independent validators in this stage

- [`dft_validator`](dft_validator/) (port **8231**): Reproduce scan, fault-coverage, self-test, and test-mode checks and decide whether the DFT contract passes.

## Related documentation

- Parent track index: [`../README.md`](../README.md)
- Fleet agents tree: [`../README.md`](../README.md) or [`../../README.md`](../../README.md) depending on nesting.
- Shared agent runtime: `domains/eda/runtime/agent.py`, `domains/eda/runtime/server.py`.
- Telemetry conventions: [`../TELEMETRY.md`](../TELEMETRY.md) under `agents/`.

## Port map (quick reference)

- **8225** — `dft_lead` (lead)
- **8226** — `scan_insertion` (worker)
- **8227** — `atpg_campaign` (worker)
- **8228** — `testability_analysis` (worker)
- **8229** — `mbist_lbist` (worker)
- **8230** — `dft_physical_timing` (worker)
- **8231** — `dft_validator` (validator)

## Child agent charters

### [`dft_lead`](dft_lead/) (port **8225**, `lead`)

Own the block and chip test strategy. Decompose it into scan, ATPG, self-test, and physical-integration work, and coordinate closure against coverage, test time, area, power, and timing.

- **Skills in manifest:** 14 entries in `config.yaml` → `tools.py`.
- **Delegates to:** `scan_insertion`, `atpg_campaign`, `testability_analysis`, `mbist_lbist`, `dft_physical_timing`, `dft_validator`.

### [`scan_insertion`](scan_insertion/) (port **8226**, `worker`)

Insert scan chains, compression, test clocks, and lockup elements while preserving functional behavior, and produce a scan-connectivity report.

- **Skills in manifest:** 14 entries in `config.yaml` → `tools.py`.

### [`atpg_campaign`](atpg_campaign/) (port **8227**, `worker`)

Generate and analyze deterministic pattern campaigns across the required fault models.

- **Skills in manifest:** 14 entries in `config.yaml` → `tools.py`.

### [`testability_analysis`](testability_analysis/) (port **8228**, `worker`)

Find controllability and observability limits, X sources, and structures that block coverage, and propose a bounded change.

- **Skills in manifest:** 12 entries in `config.yaml` → `tools.py`.

### [`mbist_lbist`](mbist_lbist/) (port **8229**, `worker`)

Configure memory and logic BIST controllers, algorithms, repair, and diagnostic modes.

- **Skills in manifest:** 13 entries in `config.yaml` → `tools.py`.

### [`dft_physical_timing`](dft_physical_timing/) (port **8230**, `worker`)

Carry scan ordering, test clocks, congestion, and test-mode timing into physical design.

- **Skills in manifest:** 12 entries in `config.yaml` → `tools.py`.

### [`dft_validator`](dft_validator/) (port **8231**, `validator`)

Reproduce scan, fault-coverage, self-test, and test-mode checks and decide whether the DFT contract passes.

- **Skills in manifest:** 12 entries in `config.yaml` → `tools.py`.

## Findings, gates, and promotion

Workers publish **findings** and edit **candidates**; validators emit **gates**; leads **recommend** but do not promote the canonical baseline. Human promotion and waivers sit outside these agents and are routed through `chip_flow_lead` decisions.

Every child returns structured observations while `backend.type: none`; binding `EDA_FRAMEWORK` does not relax `boundary.may_not` rules.

## Scheduling hints

| If you need… | Start with… |
|--------------|-------------|
| Own the block and chip test strategy. Decompose it into scan, ATPG, self-test, and physica | `dft_lead` |
| Insert scan chains, compression, test clocks, and lockup elements while preserving functio | `scan_insertion` |
| Generate and analyze deterministic pattern campaigns across the required fault models. | `atpg_campaign` |
| Find controllability and observability limits, X sources, and structures that block covera | `testability_analysis` |
| Configure memory and logic BIST controllers, algorithms, repair, and diagnostic modes. | `mbist_lbist` |
| Carry scan ordering, test clocks, congestion, and test-mode timing into physical design. | `dft_physical_timing` |
| Reproduce scan, fault-coverage, self-test, and test-mode checks and decide whether the DFT | `dft_validator` |
