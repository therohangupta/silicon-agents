# OSS EDA toolchain contract

`services/eda_toolchain` is the sole execution boundary for the agent fleet.
Agents submit named operations through `ToolchainAdapter`; they do not shell
out to Yosys, OpenSTA, or OpenROAD.

## Configuration and discovery

`domains/eda/toolchain.yaml` has two provider fields:

- `provider.implementation` selects the Python class, as `module:attribute`.
- `provider.config` is that class's own document. The HTTP host does not interpret it.

The current document is an ORFS profile because `implementation` points at `ORFSProvider`. Another tool vendor replaces both fields. Set `TOOLCHAIN_PROVIDER_CONFIG` to load a different file.

## Changing the design

Stay on `ORFSProvider` when the new design is still an OpenROAD-flow-scripts platform. Copy the design's own `config.mk` into the keys below and leave `implementation`, `binaries`, `version_arguments`, `limits`, `paths.workspace_root`, and `paths.orfs_root` alone.

| Key | Source |
|---|---|
| `paths.pdk_root` | `flow/platforms/<platform>/` |
| `paths.design_root` | directory that contains both the RTL and SDC paths below |
| `design.rtl` | Verilog path relative to `design_root` |
| `design.sdc` | SDC path relative to `design_root` |
| `design.top` | module name |
| `design.platform` | ORFS `PLATFORM` value |
| `design.pdn_tcl` | power-grid file relative to `design_root`, or `""` to use the platform default |
| `collateral.liberty` | liberty path relative to `pdk_root` |
| `collateral.tech_lef` | technology LEF path relative to `pdk_root` |
| `collateral.macro_lef` | standard-cell LEF path relative to `pdk_root` |
| `orfs_flow` | the variables that design's `config.mk` exports, using the same names |

`design.placement_site` must be present for this provider to load. The platform `config.mk` still supplies `PLACE_SITE` to the flow.

`GET /capabilities` reports the currently accepted operation names, installed
binary probes, ORFS targets, and the actual mounted PDK collateral. A planner
must call it before scheduling physical-design work, and must treat a false
binary or missing collateral result as a blocker rather than a passing result.

## Reproducible flow operations

The following operations invoke OpenROAD-flow-scripts (`make`) with a generated,
per-job configuration. Each target brings in its required predecessor targets.

- `run_synthesis` — Yosys synthesis and technology mapping.
- `run_floorplan` — floorplan, IO placement, tap/endcap, PDN, and early checks.
- `run_placement` — global placement, detailed placement, and placement repair.
- `run_cts` — clock-tree synthesis and post-CTS repair.
- `run_global_routing` — global route.
- `run_detailed_routing` — detailed route and antenna repair.
- `run_finish` — final reports.
- `run_gds` — GDS generation.
- `run_drc` — ORFS/KLayout physical DRC target, when supplied by the platform.
- `run_lvs` — ORFS/KLayout LVS target, when supplied by the platform.
- `run_full_orfs` — `all`, `gds`, `drc`, and `lvs` in one isolated run.
- `run_orfs_flow` — one explicitly selected target from the set returned by
  `/capabilities`.

Each response includes the immutable generated ORFS config, log, exit code,
job id, and workspace. `status=succeeded` means that target exited zero; it
does not mean a foundry has accepted a tapeout.

## Analysis and expert access

- `run_sta` performs mapped synthesis then OpenSTA with the selected SDC and
  returns WNS/TNS and the report.
- `run_yosys_script`, `run_opensta_script`, and `run_openroad_script` accept a
  Tcl/script payload for commands not represented by a stable stage contract.
  The job runs in its own workspace and does not permit Tcl commands that can
  spawn processes, load packages, open sockets/files, or source arbitrary
  scripts. This retains access to the installed tool's EDA command surface
  without making the sidecar an arbitrary-command service.

Use `design_path`, `sdc_path`, and `top` to select inputs under the configured
read-only design mount. The service rejects path traversal.

## Scope of the confidence claim

The active profile is the OpenROAD-flow-scripts Sky130hd GCD design. That
platform ships KLayout DRC and LVS decks, a standard-cell CDL, and the cell
GDS required to run those checks. A zero-exit result is still an open-PDK
engineering result, not a foundry tapeout signoff. Foundry signoff requires
the foundry PDK, licensed decks/tools where required, and the foundry's
acceptance criteria.
