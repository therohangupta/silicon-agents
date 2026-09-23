# Generic fleet and EDA workflow boundary

> **Current architecture.** The terms below supersede the historical
> materializer terminology later in this document. Fleet owns one graph
> hierarchy: `DAGPlan` is the canonical proposed task graph and
> `WorkflowGraph(DAGPlan)` adds generic workflow metadata without creating a
> competing graph. `Planner` is the only component that persists symbolic
> dependencies. `Allocator` applies an `AllocationStrategy` to durable tasks.
> `AllocatedDAGPlan` is the executor projection with numeric task ids.
>
> EDA's `WorkflowSpec` is only a versioned lead-agent message. Its adapter
> returns the shared `WorkflowGraph`; EDA does not implement graph validation,
> task persistence, or agent assignment independently.

The design document requires planning, allocation, execution, and validation
to be separate decisions. This repository expresses that boundary as follows.

| Concern | Generic fleet SDK | EDA domain |
|---|---|---|
| Planning graph | `DAGPlan` is validated once; `WorkflowGraph` extends it | Lead `WorkflowSpec` chooses stage tasks, capabilities, and gates |
| Durable plan creation | `Planner` maps symbolic edges to persisted task ids | `to_fleet_workflow` maps `WorkflowTask` to generic nodes |
| Allocation | `Allocator` applies the selected allocation strategy | EDA can add PDK, license, data-locality, and candidate-conflict scores |
| Execution | Existing fleet executor dispatches allocated task DAGs and honors dependencies | `ToolchainAdapter` chooses an approved EDA operation and turns reports into observations |
| Validation | Fleet preserves task state and evidence | EDA validators define independent acceptance criteria and promotion gates |

## Workflow handoff

An EDA lead returns `eda.workflow/v1`; it does not execute children itself.
The caller obtains a fleet graph with `to_fleet_workflow`, then calls
`Planner.create_plan(...)`. The resulting
tasks use the existing allocation and `StartPlan` flow. This keeps `goal_id`
and plan ownership in the control plane rather than embedding fleet database
details in an agent response.

## OSS tool sidecar

`services/eda_toolchain` runs **Yosys, OpenSTA, and OpenROAD** on the **Nangate45**
collateral staged from `external/OpenROAD-flow-scripts` (see
`scripts/stage_nangate45_gcd.sh`). Agent skills such as `compile_candidate`,
`run_sta`, and `run_global_placement` call the sidecar through `ToolchainAdapter`.

On Apple Silicon the service uses `platform: linux/amd64` (QEMU) because upstream
OpenROAD images are amd64-only.

Setup and demo:

```bash
./scripts/stage_nangate45_gcd.sh
docker compose -f compose/docker-compose.eda.yml up --build -d
EDA_TOOLCHAIN_URL=http://127.0.0.1:8090 python scripts/demo_openroad_sta.py
```

Design: `tmp/gcd/gcd.v` + `constraint.sdc`. PDK: `tmp/pdk/nangate45/{lib,lef}`.
These flows are **engineering experiments**, not tapeout signoff — validators still
gate promotion per the design doc.
