# Backend Signoff stage agents

This directory groups **signoff**-stage agents. Tapeout readiness: extraction, MMMC STA, power, IR/EM, thermal/reliability, DRC/LVS, ECO planning, and an independent signoff validator.

Each child folder is an independent HTTP microservice (`python server.py`) discovered via its `config.yaml`. Leads declare `delegates_to` worker ids; validators declare independent gates. Workers execute skills in `tools.py` and return observations until an EDA adapter is bound.

## Agents in this stage

| Agent | Role | Port | Package |
|-------|------|------|---------|
| Extraction Agent (`extraction`) | `worker` | **8254** | [`extraction/`](extraction/) |
| STA Lead (`sta_lead`) | `lead` | **8255** | [`sta_lead/`](sta_lead/) |
| Timing-Debug Agent (`timing_debug`) | `worker` | **8256** | [`timing_debug/`](timing_debug/) |
| Power-Analysis Agent (`power_analysis`) | `worker` | **8257** | [`power_analysis/`](power_analysis/) |
| IR/EM Agent (`ir_em`) | `worker` | **8258** | [`ir_em/`](ir_em/) |
| Thermal and Reliability Agent (`thermal_reliability`) | `worker` | **8259** | [`thermal_reliability/`](thermal_reliability/) |
| DRC/LVS/ERC/DFM Agent (`drc_lvs`) | `worker` | **8260** | [`drc_lvs/`](drc_lvs/) |
| ECO Lead (`eco_lead`) | `lead` | **8261** | [`eco_lead/`](eco_lead/) |
| Independent Signoff Validator (`signoff_validator`) | `validator` | **8262** | [`signoff_validator/`](signoff_validator/) |

## Lead delegation graph

### `sta_lead` (port **8255**)

Own multi-mode multi-corner static timing. Classify failures, trace causes, and coordinate bounded repairs.

May schedule:
- [`timing_debug`](timing_debug/) — Timing-Debug Agent (**8256**)

### `eco_lead` (port **8261**)

Plan a late functional, timing, power, or physical change. Minimize disruption, preserve equivalence, and name every check the change invalidates.

May schedule:
- [`rtl_implementation`](rtl_implementation/) — RTL Implementation Agent (**8209**)
- [`equivalence`](equivalence/) — Equivalence Agent (**8236**)
- [`timing_debug`](timing_debug/) — Timing-Debug Agent (**8256**)
- [`drc_lvs`](drc_lvs/) — DRC/LVS/ERC/DFM Agent (**8260**)

## Suggested workflow (mental model)

1. **extraction** produces SPEF corners from the routed design.
2. **timing_debug** and **sta_lead** close MMMC timing on SPEF + SDC.
3. **power_analysis**, **ir_em**, and **thermal_reliability** stress power, grid, and aging.
4. **drc_lvs** triages geometry, connectivity, and DFM against the rule deck.
5. **eco_lead** plans the smallest change when a finding needs RTL or physical edit.
6. **signoff_validator** audits evidence and waivers before tapeout promotion.

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

- [`signoff_validator`](signoff_validator/) (port **8262**): Read primary signoff artifacts, reproduce critical checks, audit waivers, and decide whether every required gate passed.

## Related documentation

- Parent track index: [`../README.md`](../README.md)
- Fleet agents tree: [`../README.md`](../README.md) or [`../../README.md`](../../README.md) depending on nesting.
- Shared agent runtime: `domains/eda/runtime/agent.py`, `domains/eda/runtime/server.py`.
- Telemetry conventions: [`../TELEMETRY.md`](../TELEMETRY.md) under `agents/`.

## Port map (quick reference)

- **8254** — `extraction` (worker)
- **8255** — `sta_lead` (lead)
- **8256** — `timing_debug` (worker)
- **8257** — `power_analysis` (worker)
- **8258** — `ir_em` (worker)
- **8259** — `thermal_reliability` (worker)
- **8260** — `drc_lvs` (worker)
- **8261** — `eco_lead` (lead)
- **8262** — `signoff_validator` (validator)

## Child agent charters

### [`extraction`](extraction/) (port **8254**, `worker`)

Produce versioned parasitic models from the routed design and record completeness and corner configuration. Adapter target: OpenROAD estimate_parasitics, then a signoff extractor behind the same operations.

- **Skills in manifest:** 12 entries in `config.yaml` → `tools.py`.

### [`sta_lead`](sta_lead/) (port **8255**, `lead`)

Own multi-mode multi-corner static timing. Classify failures, trace causes, and coordinate bounded repairs.

- **Skills in manifest:** 12 entries in `config.yaml` → `tools.py`.
- **Delegates to:** `timing_debug`.

### [`timing_debug`](timing_debug/) (port **8256**, `worker`)

Run STA queries, classify setup, hold, recovery, removal, and clock failures, and trace them to a physical or logical cause. Adapter target: OpenSTA report_checks.

- **Skills in manifest:** 12 entries in `config.yaml` → `tools.py`.

### [`power_analysis`](power_analysis/) (port **8257**, `worker`)

Estimate vector-based or vectorless dynamic power, leakage, and clock power, and compare them with the block budget. Adapter target: OpenROAD report_power, then a signoff power tool.

- **Skills in manifest:** 12 entries in `config.yaml` → `tools.py`.

### [`ir_em`](ir_em/) (port **8258**, `worker`)

Analyze static and dynamic voltage drop and current density, localize weak regions, and apply a grid or placement repair on an isolated candidate with a timing and routing check.

- **Skills in manifest:** 13 entries in `config.yaml` → `tools.py`.

### [`thermal_reliability`](thermal_reliability/) (port **8259**, `worker`)

Evaluate temperature, aging, variation, and reliability margins, and turn risks into constraints or an isolated physical change.

- **Skills in manifest:** 12 entries in `config.yaml` → `tools.py`.

### [`drc_lvs`](drc_lvs/) (port **8260**, `worker`)

Run and triage geometry, connectivity, electrical, density, and manufacturability checks, and separate real defects from setup errors.

- **Skills in manifest:** 12 entries in `config.yaml` → `tools.py`.

### [`eco_lead`](eco_lead/) (port **8261**, `lead`)

Plan a late functional, timing, power, or physical change. Minimize disruption, preserve equivalence, and name every check the change invalidates.

- **Skills in manifest:** 12 entries in `config.yaml` → `tools.py`.
- **Delegates to:** `rtl_implementation`, `equivalence`, `timing_debug`, `drc_lvs`.

### [`signoff_validator`](signoff_validator/) (port **8262**, `validator`)

Read primary signoff artifacts, reproduce critical checks, audit waivers, and decide whether every required gate passed.

- **Skills in manifest:** 14 entries in `config.yaml` → `tools.py`.

## Findings, gates, and promotion

Workers publish **findings** and edit **candidates**; validators emit **gates**; leads **recommend** but do not promote the canonical baseline. Human promotion and waivers sit outside these agents and are routed through `chip_flow_lead` decisions.

Every child returns structured observations while `backend.type: none`; binding `EDA_FRAMEWORK` does not relax `boundary.may_not` rules.

## Cross-stage handoffs

- **eco_lead** may reach frontend `rtl_implementation` and backend `equivalence` when a late ECO demands RTL or netlist re-proof.
- **extraction** consumes routed layout from **routing**; SPEF feeds **sta_lead** and **power_analysis**.
- Upstream **clock_validation** gate should pass before treating routing timing as trustworthy.

## Scheduling hints

| If you need… | Start with… |
|--------------|-------------|
| Produce versioned parasitic models from the routed design and record completeness and corn | `extraction` |
| Own multi-mode multi-corner static timing. Classify failures, trace causes, and coordinate | `sta_lead` |
| Run STA queries, classify setup, hold, recovery, removal, and clock failures, and trace th | `timing_debug` |
| Estimate vector-based or vectorless dynamic power, leakage, and clock power, and compare t | `power_analysis` |
| Analyze static and dynamic voltage drop and current density, localize weak regions, and ap | `ir_em` |
| Evaluate temperature, aging, variation, and reliability margins, and turn risks into const | `thermal_reliability` |
| Run and triage geometry, connectivity, electrical, density, and manufacturability checks,  | `drc_lvs` |
| Plan a late functional, timing, power, or physical change. Minimize disruption, preserve e | `eco_lead` |
| Read primary signoff artifacts, reproduce critical checks, audit waivers, and decide wheth | `signoff_validator` |
