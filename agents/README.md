# Agents tree

This directory holds every first-party chip-design specialist the fleet can schedule. Agents are discovered by scanning each leaf directory's `config.yaml` (gateway YAML scanner). `agents/__init__.py` is only a namespace marker—not a monolithic import path.

## Common per-agent file layout

| File | Role |
|------|------|
| `agent.py` | Concrete `EdaAgent` subclass; loads `spec` from sibling `config.yaml`. |
| `server.py` | HTTP bootstrap: `sys.path`, `AgentService`, FastAPI `app`. |
| `tools.py` | `@tool` skill callables → `tool_observation` until adapters bind. |
| `config.yaml` | Manifest: boundaries, delegation, ports, skills, memory, telemetry, context. |
| `Dockerfile` | Container running `python server.py`. |
| `requirements.txt` | FastAPI/uvicorn/pydantic/PyYAML. |
| `README.md` | Human guide (EDA role, skills, port, boundaries, boot, delegation). |

Boot order: container → `server.py` → `agent.py` + `config.yaml` → `/tasks/execute` → `tools.py`.

## Tracks

- **[`frontend/`](frontend/)** — see [`frontend/README.md`](frontend/README.md).
- **[`backend/`](backend/)** — see [`backend/README.md`](backend/README.md).
- **[`dft/`](dft/)** — see [`dft/README.md`](dft/README.md).
- **[`validation/`](validation/)** — see [`validation/README.md`](validation/README.md).
- **[`chip_flow_lead/`](chip_flow_lead/)** — program lead (port **8201**): milestones, cross-stage routing, human promotion gates.

## Agent inventory (by port)

| Port | Agent id | Stage | Role |
|------|----------|-------|------|
| 8201 | [`chip_flow_lead`](chip_flow_lead/) | `program` | `lead` |
| 8202 | [`requirements`](frontend/architecture/requirements/) | `architecture` | `worker` |
| 8203 | [`architecture_lead`](frontend/architecture/architecture_lead/) | `architecture` | `lead` |
| 8204 | [`performance_modeling`](frontend/architecture/performance_modeling/) | `architecture` | `worker` |
| 8205 | [`interface`](frontend/architecture/interface/) | `architecture` | `worker` |
| 8206 | [`power_area_estimation`](frontend/architecture/power_area_estimation/) | `architecture` | `worker` |
| 8207 | [`security_reliability`](frontend/architecture/security_reliability/) | `architecture` | `worker` |
| 8208 | [`rtl_lead`](frontend/rtl/rtl_lead/) | `rtl` | `lead` |
| 8209 | [`rtl_implementation`](frontend/rtl/rtl_implementation/) | `rtl` | `worker` |
| 8210 | [`clock_reset`](frontend/rtl/clock_reset/) | `rtl` | `worker` |
| 8211 | [`cdc_rdc`](frontend/rtl/cdc_rdc/) | `rtl` | `worker` |
| 8212 | [`low_power`](frontend/rtl/low_power/) | `rtl` | `worker` |
| 8213 | [`lint_quality`](frontend/rtl/lint_quality/) | `rtl` | `worker` |
| 8214 | [`rtl_integration`](frontend/rtl/rtl_integration/) | `rtl` | `worker` |
| 8215 | [`verification_lead`](frontend/verification/verification_lead/) | `verification` | `lead` |
| 8216 | [`uvm_environment`](frontend/verification/uvm_environment/) | `verification` | `worker` |
| 8217 | [`reference_model`](frontend/verification/reference_model/) | `verification` | `worker` |
| 8218 | [`assertion_formal`](frontend/verification/assertion_formal/) | `verification` | `worker` |
| 8219 | [`stimulus`](frontend/verification/stimulus/) | `verification` | `worker` |
| 8220 | [`coverage`](frontend/verification/coverage/) | `verification` | `worker` |
| 8221 | [`regression`](frontend/verification/regression/) | `verification` | `worker` |
| 8222 | [`failure_triage`](frontend/verification/failure_triage/) | `verification` | `worker` |
| 8223 | [`reproduction`](frontend/verification/reproduction/) | `verification` | `worker` |
| 8224 | [`verification_validator`](frontend/verification/verification_validator/) | `verification` | `validator` |
| 8225 | [`dft_lead`](dft/dft_lead/) | `dft` | `lead` |
| 8226 | [`scan_insertion`](dft/scan_insertion/) | `dft` | `worker` |
| 8227 | [`atpg_campaign`](dft/atpg_campaign/) | `dft` | `worker` |
| 8228 | [`testability_analysis`](dft/testability_analysis/) | `dft` | `worker` |
| 8229 | [`mbist_lbist`](dft/mbist_lbist/) | `dft` | `worker` |
| 8230 | [`dft_physical_timing`](dft/dft_physical_timing/) | `dft` | `worker` |
| 8231 | [`dft_validator`](dft/dft_validator/) | `dft` | `validator` |
| 8232 | [`synthesis_lead`](backend/synthesis/synthesis_lead/) | `synthesis` | `lead` |
| 8233 | [`constraint_generation`](backend/synthesis/constraint_generation/) | `synthesis` | `worker` |
| 8234 | [`synthesis_experiment`](backend/synthesis/synthesis_experiment/) | `synthesis` | `worker` |
| 8235 | [`retiming_mapping`](backend/synthesis/retiming_mapping/) | `synthesis` | `worker` |
| 8236 | [`equivalence`](backend/synthesis/equivalence/) | `synthesis` | `worker` |
| 8237 | [`netlist_quality`](backend/synthesis/netlist_quality/) | `synthesis` | `worker` |
| 8238 | [`floorplanning_lead`](backend/floorplan/floorplanning_lead/) | `floorplan` | `lead` |
| 8239 | [`macro_placement`](backend/floorplan/macro_placement/) | `floorplan` | `worker` |
| 8240 | [`pin_assignment`](backend/floorplan/pin_assignment/) | `floorplan` | `worker` |
| 8241 | [`power_grid`](backend/floorplan/power_grid/) | `floorplan` | `worker` |
| 8242 | [`early_congestion_timing`](backend/floorplan/early_congestion_timing/) | `floorplan` | `worker` |
| 8243 | [`placement_lead`](backend/placement/placement_lead/) | `placement` | `lead` |
| 8244 | [`placement_experiment`](backend/placement/placement_experiment/) | `placement` | `worker` |
| 8245 | [`placement_evaluator`](backend/placement/placement_evaluator/) | `placement` | `validator` |
| 8246 | [`boundary_coordinator`](backend/placement/boundary_coordinator/) | `placement` | `worker` |
| 8247 | [`cts`](backend/clock/cts/) | `clock` | `worker` |
| 8248 | [`clock_validation`](backend/clock/clock_validation/) | `clock` | `validator` |
| 8249 | [`routing_lead`](backend/routing/routing_lead/) | `routing` | `lead` |
| 8250 | [`global_routing`](backend/routing/global_routing/) | `routing` | `worker` |
| 8251 | [`detailed_routing_repair`](backend/routing/detailed_routing_repair/) | `routing` | `worker` |
| 8252 | [`si_noise_repair`](backend/routing/si_noise_repair/) | `routing` | `worker` |
| 8253 | [`antenna_manufacturability`](backend/routing/antenna_manufacturability/) | `routing` | `worker` |
| 8254 | [`extraction`](backend/signoff/extraction/) | `signoff` | `worker` |
| 8255 | [`sta_lead`](backend/signoff/sta_lead/) | `signoff` | `lead` |
| 8256 | [`timing_debug`](backend/signoff/timing_debug/) | `signoff` | `worker` |
| 8257 | [`power_analysis`](backend/signoff/power_analysis/) | `signoff` | `worker` |
| 8258 | [`ir_em`](backend/signoff/ir_em/) | `signoff` | `worker` |
| 8259 | [`thermal_reliability`](backend/signoff/thermal_reliability/) | `signoff` | `worker` |
| 8260 | [`drc_lvs`](backend/signoff/drc_lvs/) | `signoff` | `worker` |
| 8261 | [`eco_lead`](backend/signoff/eco_lead/) | `signoff` | `lead` |
| 8262 | [`signoff_validator`](backend/signoff/signoff_validator/) | `signoff` | `validator` |
| 8263 | [`bringup_lead`](validation/bringup_lead/) | `validation` | `lead` |
| 8264 | [`lab_procedure`](validation/lab_procedure/) | `validation` | `worker` |
| 8265 | [`instrument_control`](validation/instrument_control/) | `validation` | `worker` |
| 8266 | [`firmware_test_program`](validation/firmware_test_program/) | `validation` | `worker` |
| 8267 | [`telemetry_log_analysis`](validation/telemetry_log_analysis/) | `validation` | `worker` |
| 8268 | [`characterization`](validation/characterization/) | `validation` | `worker` |
| 8269 | [`failure_correlation`](validation/failure_correlation/) | `validation` | `worker` |
| 8270 | [`errata_drafting`](validation/errata_drafting/) | `validation` | `worker` |

## Telemetry

See [`TELEMETRY.md`](TELEMETRY.md) for heartbeats, skill-call streams, and optional high-rate adapters.

## Related docs

- Shared base class: `domains/eda/agent.py`.
- Fleet YAML: `fleets/` and `config/platform.yaml`.
