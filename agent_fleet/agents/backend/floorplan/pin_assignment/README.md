# Pin-Assignment Agent (`pin_assignment`)

This directory is the deployable microservice package for the **Pin-Assignment Agent** in the fleet **floorplan** stage (role `worker`).

## EDA responsibility

Read interface, package, and bump constraints for this block.

Charter from `config.yaml`: Propose and validate block-pin locations, layers, ordering, and feedthroughs. Adapter target: OpenROAD pin placement.

As a **worker**, this process executes bounded skills on isolated candidates and reports observations. Promotion and program-level tradeoffs stay with leads and humans.

## Identity and HTTP port

| Field | Value |
|-------|-------|
| Agent id | `pin_assignment` |
| Stage | `floorplan` |
| Role | `worker` |
| Host | `host.docker.internal` |
| Port | **8240** (must match `Dockerfile` `EXPOSE`) |
| Health | `/health` |
| Execute | `/tasks/execute` |

## Boundaries

Hard limits from `config.yaml` `boundary`. The planner and `EdaAgent` enforce these even when a tool adapter could physically perform a forbidden action.

### May

- Write a pin assignment on an isolated candidate
- Report boundary density

### May not

- Move a package bump
- Ignore a feedthrough limit
- Promote a candidate onto the canonical baseline
- Approve a waiver or relax a hard requirement
- Treat its own summary as independent signoff

## Skills

Skills bind planner task ids to callables in `tools.py` (`module: tools`, `execution.mode: direct_function`).

| Skill id | Action | Callable | Description |
|----------|--------|----------|-------------|
| `read_pin_contract` | `read_reports` | `read_pin_contract` | Read interface, package, and bump constraints for this block. |
| `read_edge_capacity` | `read_reports` | `read_edge_capacity` | Read legal layers and track capacity on each edge. |
| `assign_pins` | `write_candidate` | `assign_pins` | Assign block pin locations, layers, and order. Adapter target: OpenROAD place_pins. |
| `assign_pin_layer` | `write_candidate` | `assign_pin_layer` | Set the layer of one pin or bus. |
| `order_bus_pins` | `write_candidate` | `order_bus_pins` | Set the order of one bus along an edge. |
| `place_feedthrough` | `write_candidate` | `place_feedthrough` | Add one feedthrough that the contract allows. |
| `write_pin_def` | `write_candidate` | `write_pin_def` | Write the pin section of the DEF. |
| `validate_pin_density` | `submit_tool_job` | `validate_pin_density` | Check boundary pin density against the contract. |
| `check_pin_track_alignment` | `submit_tool_job` | `check_pin_track_alignment` | Check that pins sit on legal tracks. |
| `check_pin_layer_rules` | `submit_tool_job` | `check_pin_layer_rules` | Check pin layers against the technology rules. |
| `estimate_pin_wirelength` | `read_reports` | `estimate_pin_wirelength` | Estimate wirelength from this pin assignment to the macros. |
| `flag_pin_density_violation` | `publish_finding` | `flag_pin_density_violation` | Publish an edge whose pin density exceeds the contract. |
| `flag_illegal_feedthrough` | `publish_finding` | `flag_illegal_feedthrough` | Publish a feedthrough the contract does not allow. |
| `record_pin_assignment` | `publish_finding` | `record_pin_assignment` | Record the pin DEF ref and the contract revision it was checked against. |

## Delegation

This agent declares **no** `delegates_to` entries. It executes its own `tools.py` skills when scheduled by a lead or the chip-flow orchestrator.

## Boot path

Every fleet agent shares the same linear startup so compose and local dev behave identically.

1. Container or shell runs `python server.py` (`deployment.dockerfile` / image `agentfleet/pin_assignment:1.0`).
2. `server.py` prepends this directory to `sys.path`, imports `PinAssignmentAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, PinAssignmentAgent)`.
3. Importing `agent.py` sets `spec = EdaAgent.read_spec(<this directory>)`, loading `config.yaml` at class definition time.
4. Uvicorn serves FastAPI `app` on `connection.port` with `/health` and `/tasks/execute`.
5. On `/tasks/execute`, `EdaAgent.handle` assembles engineering-memory context (see `context` in YAML), journals the task, and dispatches the requested skill.
6. The skill callable in `tools.py` returns `tool_observation(...)`. With `backend.type: none`, observations are safe stubs (`not_run`) until `EDA_FRAMEWORK` or another adapter binds real engines.

## Related agents

- Stage index: [`../README.md`](../README.md) (floorplan specialists under `floorplan/`).
- Stage lead(s) that delegate here:
  - [`floorplanning_lead`](../floorplanning_lead/) (port **8238**)
- Sibling agents in this folder:
  - [`early_congestion_timing`](../early_congestion_timing/) — worker, port **8242**
  - [`floorplanning_lead`](../floorplanning_lead/) — lead, port **8238**
  - [`macro_placement`](../macro_placement/) — worker, port **8239**
  - [`power_grid`](../power_grid/) — worker, port **8241**
- Track overview: [`../../README.md`](../../README.md) (backend physical implementation).

## Files in this directory

| File | Role |
|------|------|
| `agent.py` | Defines `PinAssignmentAgent`; loads sibling `config.yaml` into `spec`. |
| `server.py` | HTTP/ASGI bootstrap; exports FastAPI `app` for uvicorn. |
| `tools.py` | `@tool` skill callables; stable EDA operation contracts. |
| `config.yaml` | Fleet manifest (`apiVersion: agentfleet/v1`): boundaries, port, skills, memory, telemetry. |
| `Dockerfile` | Container image; `EXPOSE 8240`; `CMD python server.py`. |
| `requirements.txt` | FastAPI, uvicorn, pydantic, PyYAML for the HTTP surface. |
| `__init__.py` | Re-exports `PinAssignmentAgent` for imports without starting HTTP. |
| `README.md` | This document. |

## Tool reference

### `read_pin_contract` (`tools.read_pin_contract`)

**Action:** `read_reports`. Read interface, package, and bump constraints for this block.

### `read_edge_capacity` (`tools.read_edge_capacity`)

**Action:** `read_reports`. Read legal layers and track capacity on each edge.

### `assign_pins` (`tools.assign_pins`)

**Action:** `write_candidate`. Assign block pin locations, layers, and order. Adapter target: OpenROAD place_pins.

### `assign_pin_layer` (`tools.assign_pin_layer`)

**Action:** `write_candidate`. Set the layer of one pin or bus.

### `order_bus_pins` (`tools.order_bus_pins`)

**Action:** `write_candidate`. Set the order of one bus along an edge.

### `place_feedthrough` (`tools.place_feedthrough`)

**Action:** `write_candidate`. Add one feedthrough that the contract allows.

### `write_pin_def` (`tools.write_pin_def`)

**Action:** `write_candidate`. Write the pin section of the DEF.

### `validate_pin_density` (`tools.validate_pin_density`)

**Action:** `submit_tool_job`. Check boundary pin density against the contract.

### `check_pin_track_alignment` (`tools.check_pin_track_alignment`)

**Action:** `submit_tool_job`. Check that pins sit on legal tracks.

### `check_pin_layer_rules` (`tools.check_pin_layer_rules`)

**Action:** `submit_tool_job`. Check pin layers against the technology rules.

### `estimate_pin_wirelength` (`tools.estimate_pin_wirelength`)

**Action:** `read_reports`. Estimate wirelength from this pin assignment to the macros.

### `flag_pin_density_violation` (`tools.flag_pin_density_violation`)

**Action:** `publish_finding`. Publish an edge whose pin density exceeds the contract.

### `flag_illegal_feedthrough` (`tools.flag_illegal_feedthrough`)

**Action:** `publish_finding`. Publish a feedthrough the contract does not allow.

### `record_pin_assignment` (`tools.record_pin_assignment`)

**Action:** `publish_finding`. Record the pin DEF ref and the contract revision it was checked against.

## Runtime, memory, and context

- **Reliability:** task timeout 120s, max retries 1, on failure `replan`.
- **Execution:** `direct_function`, `max_tasks=1`.
- **Context include:** `canonical_source`, `open_findings`, `experiments`, `gates`, `decisions`.
- **Context exclude:** `stale_candidates`.
- **Token budget:** 80000.
- **Telemetry:** heartbeat every 5s; streams: skill_calls, artifacts.

## Operational notes

- **Promotion / signoff:** Boundaries forbid treating this agent's summary as independent signoff unless `role: validator` and the workflow explicitly schedules it.
- **Adapters:** Set `EDA_FRAMEWORK` / `backend.type` when wiring OpenROAD, Yosys, OpenSTA, simulators, or licensed signoff tools; until then skills return structured `not_run` observations.
- **Shared base:** Task handling lives in `domains/eda/agent.py`; HTTP wiring in `domains/eda/server.py`.
- **Telemetry:** See [`../../TELEMETRY.md`](../../TELEMETRY.md) (path may vary by depth) for fleet-wide observability conventions.

## How a newcomer should read this agent

1. Read `config.yaml` `metadata`, `boundary`, and `capabilities` for charter and limits.
2. Skim the skills table above, then open `tools.py` for parameter shapes.
3. Read `agent.py` and `server.py` only to confirm boot wiring.
4. Treat `Dockerfile` / `requirements.txt` as deployment detail.
