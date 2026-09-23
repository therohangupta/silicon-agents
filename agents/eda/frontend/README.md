# Frontend (pre-silicon) agents

Architecture, RTL, and verification specialists before tapeout handoff.

## Stages in this track

- **[`architecture/`](architecture/)** — [`architecture/README.md`](architecture/README.md)
- **[`rtl/`](rtl/)** — [`rtl/README.md`](rtl/README.md)
- **[`verification/`](verification/)** — [`verification/README.md`](verification/README.md)

## Agent inventory (this track)

| Port | Agent | Stage | Role |
|------|-------|-------|------|
| 8202 | [`requirements`](architecture/requirements/) | `architecture` | `worker` |
| 8203 | [`architecture_lead`](architecture/architecture_lead/) | `architecture` | `lead` |
| 8204 | [`performance_modeling`](architecture/performance_modeling/) | `architecture` | `worker` |
| 8205 | [`interface`](architecture/interface/) | `architecture` | `worker` |
| 8206 | [`power_area_estimation`](architecture/power_area_estimation/) | `architecture` | `worker` |
| 8207 | [`security_reliability`](architecture/security_reliability/) | `architecture` | `worker` |
| 8208 | [`rtl_lead`](rtl/rtl_lead/) | `rtl` | `lead` |
| 8209 | [`rtl_implementation`](rtl/rtl_implementation/) | `rtl` | `worker` |
| 8210 | [`clock_reset`](rtl/clock_reset/) | `rtl` | `worker` |
| 8211 | [`cdc_rdc`](rtl/cdc_rdc/) | `rtl` | `worker` |
| 8212 | [`low_power`](rtl/low_power/) | `rtl` | `worker` |
| 8213 | [`lint_quality`](rtl/lint_quality/) | `rtl` | `worker` |
| 8214 | [`rtl_integration`](rtl/rtl_integration/) | `rtl` | `worker` |
| 8215 | [`verification_lead`](verification/verification_lead/) | `verification` | `lead` |
| 8216 | [`uvm_environment`](verification/uvm_environment/) | `verification` | `worker` |
| 8217 | [`reference_model`](verification/reference_model/) | `verification` | `worker` |
| 8218 | [`assertion_formal`](verification/assertion_formal/) | `verification` | `worker` |
| 8219 | [`stimulus`](verification/stimulus/) | `verification` | `worker` |
| 8220 | [`coverage`](verification/coverage/) | `verification` | `worker` |
| 8221 | [`regression`](verification/regression/) | `verification` | `worker` |
| 8222 | [`failure_triage`](verification/failure_triage/) | `verification` | `worker` |
| 8223 | [`reproduction`](verification/reproduction/) | `verification` | `worker` |
| 8224 | [`verification_validator`](verification/verification_validator/) | `verification` | `validator` |

## End-to-end flow (within the track)

1. **architecture** — qualify requirements, interfaces, models, and budgets.
2. **rtl** — implement and integrate RTL; close lint, clock/reset, CDC/RDC, UPF.
3. **verification** — prove behavior with UVM/formal/coverage/regression; independent validator gates closure.
4. Handoff to **backend/synthesis** when the fleet promotes a qualified RTL baseline (program decision).

## Stage leads and validators

| Stage | Lead (port) | Validator (port) |
|-------|-------------|------------------|
| architecture | `architecture_lead` (**8203**) | — |
| rtl | `rtl_lead` (**8208**) | — |
| verification | `verification_lead` (**8215**) | `verification_validator` (**8224**) |

Leads own workflow publication and candidate comparison; validators emit independent gates. Workers (`8202`–`8214`, `8216`–`8223`) execute bounded skills on isolated drafts.

## Physical-design handoff

Qualified RTL and verification closure feed **backend/synthesis** (`synthesis_lead`, port **8232**). Until `chip_flow_lead` records a promotion decision, backend agents treat frontend artifacts as read-only upstream references.

Each leaf README documents EDA role, skills from `config.yaml`, HTTP port, boundaries, boot path, delegation, related agents, and a file table—read those before changing agent behavior.

Ports for this track span **8202**–**8224**; see the inventory table above for the authoritative mapping.

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
