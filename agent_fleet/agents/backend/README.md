# Backend (physical implementation) agents

Synthesis through signoff on placed/routed candidates.

## Stages in this track

- **[`clock/`](clock/)** — [`clock/README.md`](clock/README.md)
- **[`floorplan/`](floorplan/)** — [`floorplan/README.md`](floorplan/README.md)
- **[`placement/`](placement/)** — [`placement/README.md`](placement/README.md)
- **[`routing/`](routing/)** — [`routing/README.md`](routing/README.md)
- **[`signoff/`](signoff/)** — [`signoff/README.md`](signoff/README.md)
- **[`synthesis/`](synthesis/)** — [`synthesis/README.md`](synthesis/README.md)

## Agent inventory (this track)

| Port | Agent | Stage | Role |
|------|-------|-------|------|
| 8232 | [`synthesis_lead`](synthesis/synthesis_lead/) | `synthesis` | `lead` |
| 8233 | [`constraint_generation`](synthesis/constraint_generation/) | `synthesis` | `worker` |
| 8234 | [`synthesis_experiment`](synthesis/synthesis_experiment/) | `synthesis` | `worker` |
| 8235 | [`retiming_mapping`](synthesis/retiming_mapping/) | `synthesis` | `worker` |
| 8236 | [`equivalence`](synthesis/equivalence/) | `synthesis` | `worker` |
| 8237 | [`netlist_quality`](synthesis/netlist_quality/) | `synthesis` | `worker` |
| 8238 | [`floorplanning_lead`](floorplan/floorplanning_lead/) | `floorplan` | `lead` |
| 8239 | [`macro_placement`](floorplan/macro_placement/) | `floorplan` | `worker` |
| 8240 | [`pin_assignment`](floorplan/pin_assignment/) | `floorplan` | `worker` |
| 8241 | [`power_grid`](floorplan/power_grid/) | `floorplan` | `worker` |
| 8242 | [`early_congestion_timing`](floorplan/early_congestion_timing/) | `floorplan` | `worker` |
| 8243 | [`placement_lead`](placement/placement_lead/) | `placement` | `lead` |
| 8244 | [`placement_experiment`](placement/placement_experiment/) | `placement` | `worker` |
| 8245 | [`placement_evaluator`](placement/placement_evaluator/) | `placement` | `validator` |
| 8246 | [`boundary_coordinator`](placement/boundary_coordinator/) | `placement` | `worker` |
| 8247 | [`cts`](clock/cts/) | `clock` | `worker` |
| 8248 | [`clock_validation`](clock/clock_validation/) | `clock` | `validator` |
| 8249 | [`routing_lead`](routing/routing_lead/) | `routing` | `lead` |
| 8250 | [`global_routing`](routing/global_routing/) | `routing` | `worker` |
| 8251 | [`detailed_routing_repair`](routing/detailed_routing_repair/) | `routing` | `worker` |
| 8252 | [`si_noise_repair`](routing/si_noise_repair/) | `routing` | `worker` |
| 8253 | [`antenna_manufacturability`](routing/antenna_manufacturability/) | `routing` | `worker` |
| 8254 | [`extraction`](signoff/extraction/) | `signoff` | `worker` |
| 8255 | [`sta_lead`](signoff/sta_lead/) | `signoff` | `lead` |
| 8256 | [`timing_debug`](signoff/timing_debug/) | `signoff` | `worker` |
| 8257 | [`power_analysis`](signoff/power_analysis/) | `signoff` | `worker` |
| 8258 | [`ir_em`](signoff/ir_em/) | `signoff` | `worker` |
| 8259 | [`thermal_reliability`](signoff/thermal_reliability/) | `signoff` | `worker` |
| 8260 | [`drc_lvs`](signoff/drc_lvs/) | `signoff` | `worker` |
| 8261 | [`eco_lead`](signoff/eco_lead/) | `signoff` | `lead` |
| 8262 | [`signoff_validator`](signoff/signoff_validator/) | `signoff` | `validator` |

## End-to-end flow (within the track)

1. **synthesis** — constraints, mapping, equivalence, netlist quality.
2. **floorplan** → **placement** → **clock** → **routing** physical closure.
3. **signoff** — extraction, STA, power, IR/EM, thermal, DRC/LVS, ECO, independent validator.

## Stage leads and validators

| Stage | Lead (port) | Validator (port) |
|-------|-------------|------------------|
| synthesis | `synthesis_lead` (**8232**) | — |
| floorplan | `floorplanning_lead` (**8238**) | — |
| placement | `placement_lead` (**8243**) | `placement_evaluator` (**8245**) |
| clock | — | `clock_validation` (**8248**) |
| routing | `routing_lead` (**8249**) | — |
| signoff | `sta_lead` (**8255**), `eco_lead` (**8261**) | `signoff_validator` (**8262**) |

Ports **8232**–**8262** are reserved for backend agents in this tree. Each stage README documents delegation graphs and recommended scheduling order.

## Upstream / downstream neighbors

- **Upstream:** frontend RTL and constraints promoted by program decision (`chip_flow_lead`).
- **Downstream:** `dft/` and lab `validation/` consume signoff artifacts and pattern handoff after tapeout.

## Conventions

Each leaf folder matches the fleet microservice layout documented in [`../README.md`](../README.md).
Leads delegate via `delegates_to`; workers do not promote baselines.
HTTP ports are unique per agent; see each child `README.md` for skills and boundaries.

## Boot path (typical leaf)

1. `python server.py` in the agent directory (or Docker equivalent).
2. Orchestrator POST `/tasks/execute` with a skill id from `config.yaml`.
3. `tools.py` returns observations; engineering memory stores findings and candidate edits.

## Related

- [`../chip_flow_lead/`](../chip_flow_lead/) program orchestration.
- [`../README.md`](../README.md) full fleet port inventory.
- [`../TELEMETRY.md`](../TELEMETRY.md) observability conventions.
