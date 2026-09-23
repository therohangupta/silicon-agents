# Macro-Placement Experiment Worker (`macro_placement`)

This directory is the deployable microservice package for the **Macro-Placement Experiment Worker** in the fleet **floorplan** stage (role `worker`).

## EDA responsibility

Macro-Placement Experiment Worker agent module.

Charter from `config.yaml`: Generate and score one isolated macro placement under halo, channel, orientation, and connectivity limits. Adapter target: OpenROAD initialize_floorplan and macro placement.

As a **worker**, this process executes bounded skills on isolated candidates and reports observations. Promotion and program-level tradeoffs stay with leads and humans.

## Identity and HTTP port

| Field | Value |
|-------|-------|
| Agent id | `macro_placement` |
| Stage | `floorplan` |
| Role | `worker` |
| Host | `host.docker.internal` |
| Port | **8239** (must match `Dockerfile` `EXPOSE`) |
| Health | `/health` |
| Execute | `/tasks/execute` |

## Boundaries

Hard limits from `config.yaml` `boundary`. The planner and `EDAAgent` enforce these even when a tool adapter could physically perform a forbidden action.

### May

- Write one macro placement candidate
- Submit a legality check

### May not

- Edit the shared physical database
- Move a macro into a keepout
- Promote a candidate onto the canonical baseline
- Approve a waiver or relax a hard requirement
- Treat its own summary as independent signoff

## Skills

Skills bind planner task ids to callables in `tools.py` (`module: tools`, `execution.mode: direct_function`).

| Skill id | Action | Callable | Description |
|----------|--------|----------|-------------|
| `initialize_floorplan` | `write_candidate` | `initialize_floorplan` | Create the die, core, rows, and sites for this candidate. Adapter target: OpenROAD initialize_floorplan. |
| `read_macro_inventory` | `read_reports` | `read_macro_inventory` | Read macros, abstracts, and orientation limits. |
| `read_floorplan_keepouts` | `read_reports` | `read_floorplan_keepouts` | Read blockages, halos, and manufacturing keepouts. |
| `place_macros` | `write_candidate` | `place_macros` | Place macros for one candidate. Adapter target: OpenROAD macro placement. |
| `set_macro_halo` | `write_candidate` | `set_macro_halo` | Set the halo around one macro. |
| `set_macro_orientation` | `write_candidate` | `set_macro_orientation` | Set a legal orientation for one macro. |
| `set_macro_channel` | `write_candidate` | `set_macro_channel` | Set the channel width between two macros. |
| `check_macro_overlaps` | `submit_tool_job` | `check_macro_overlaps` | Check macros for overlap. |
| `check_macro_channels` | `submit_tool_job` | `check_macro_channels` | Check channel widths against the routing requirement. |
| `check_macro_keepouts` | `submit_tool_job` | `check_macro_keepouts` | Check that no macro sits in a keepout. |
| `score_macro_connectivity` | `read_reports` | `score_macro_connectivity` | Score flyline length and macro-to-macro connectivity. |
| `write_floorplan_def` | `write_candidate` | `write_floorplan_def` | Write the floorplan DEF for this candidate. |
| `generate_macro_placement` | `write_candidate` | `generate_macro_placement` | Place macros and write the candidate in one step when the hypothesis is a full placement. |
| `score_macro_placement` | `read_reports` | `score_macro_placement` | Score halo, channel, orientation, and connectivity. |
| `flag_keepout_violation` | `publish_finding` | `flag_keepout_violation` | Publish a macro that entered a keepout. |
| `record_macro_placement_metrics` | `publish_finding` | `record_macro_placement_metrics` | Record utilization, flylines, and the OpenROAD recipe id. |

## Delegation

This agent declares **no** `delegates_to` entries. It executes its own `tools.py` skills when scheduled by a lead or the chip-flow orchestrator.

## Boot path

Every fleet agent shares the same linear startup so compose and local dev behave identically.

1. Container or shell runs `python server.py` (`deployment.dockerfile` / image `agentfleet/macro_placement:1.0`).
2. `server.py` prepends this directory to `sys.path`, imports `MacroPlacementAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, MacroPlacementAgent)`.
3. Importing `agent.py` sets `spec = EDAAgent.read_spec(<this directory>)`, loading `config.yaml` at class definition time.
4. Uvicorn serves FastAPI `app` on `connection.port` with `/health` and `/tasks/execute`.
5. On `/tasks/execute`, `EDAAgent.handle` assembles engineering-memory context (see `context` in YAML), journals the task, and dispatches the requested skill.
6. The skill callable in `tools.py` returns `tool_observation(...)`. With `backend.type: none`, observations are safe stubs (`not_run`) until `EDA_FRAMEWORK` or another adapter binds real engines.

## Related agents

- Stage index: [`../README.md`](../README.md) (floorplan specialists under `floorplan/`).
- Stage lead(s) that delegate here:
  - [`floorplanning_lead`](../floorplanning_lead/) (port **8238**)
- Sibling agents in this folder:
  - [`early_congestion_timing`](../early_congestion_timing/) — worker, port **8242**
  - [`floorplanning_lead`](../floorplanning_lead/) — lead, port **8238**
  - [`pin_assignment`](../pin_assignment/) — worker, port **8240**
  - [`power_grid`](../power_grid/) — worker, port **8241**
- Track overview: [`../../README.md`](../../README.md) (backend physical implementation).

## Files in this directory

| File | Role |
|------|------|
| `agent.py` | Defines `MacroPlacementAgent`; loads sibling `config.yaml` into `spec`. |
| `server.py` | HTTP/ASGI bootstrap; exports FastAPI `app` for uvicorn. |
| `tools.py` | `@tool` skill callables; stable EDA operation contracts. |
| `config.yaml` | Fleet manifest (`apiVersion: agentfleet/v1`): boundaries, port, skills, memory, telemetry. |
| `Dockerfile` | Container image; `EXPOSE 8239`; `CMD python server.py`. |
| `requirements.txt` | FastAPI, uvicorn, pydantic, PyYAML for the HTTP surface. |
| `__init__.py` | Re-exports `MacroPlacementAgent` for imports without starting HTTP. |
| `README.md` | This document. |

## Tool reference

### `initialize_floorplan` (`tools.initialize_floorplan`)

**Action:** `write_candidate`. Create the die, core, rows, and sites for this candidate. Adapter target: OpenROAD initialize_floorplan.

### `read_macro_inventory` (`tools.read_macro_inventory`)

**Action:** `read_reports`. Read macros, abstracts, and orientation limits.

### `read_floorplan_keepouts` (`tools.read_floorplan_keepouts`)

**Action:** `read_reports`. Read blockages, halos, and manufacturing keepouts.

### `place_macros` (`tools.place_macros`)

**Action:** `write_candidate`. Place macros for one candidate. Adapter target: OpenROAD macro placement.

### `set_macro_halo` (`tools.set_macro_halo`)

**Action:** `write_candidate`. Set the halo around one macro.

### `set_macro_orientation` (`tools.set_macro_orientation`)

**Action:** `write_candidate`. Set a legal orientation for one macro.

### `set_macro_channel` (`tools.set_macro_channel`)

**Action:** `write_candidate`. Set the channel width between two macros.

### `check_macro_overlaps` (`tools.check_macro_overlaps`)

**Action:** `submit_tool_job`. Check macros for overlap.

### `check_macro_channels` (`tools.check_macro_channels`)

**Action:** `submit_tool_job`. Check channel widths against the routing requirement.

### `check_macro_keepouts` (`tools.check_macro_keepouts`)

**Action:** `submit_tool_job`. Check that no macro sits in a keepout.

### `score_macro_connectivity` (`tools.score_macro_connectivity`)

**Action:** `read_reports`. Score flyline length and macro-to-macro connectivity.

### `write_floorplan_def` (`tools.write_floorplan_def`)

**Action:** `write_candidate`. Write the floorplan DEF for this candidate.

### `generate_macro_placement` (`tools.generate_macro_placement`)

**Action:** `write_candidate`. Place macros and write the candidate in one step when the hypothesis is a full placement.

### `score_macro_placement` (`tools.score_macro_placement`)

**Action:** `read_reports`. Score halo, channel, orientation, and connectivity.

### `flag_keepout_violation` (`tools.flag_keepout_violation`)

**Action:** `publish_finding`. Publish a macro that entered a keepout.

### `record_macro_placement_metrics` (`tools.record_macro_placement_metrics`)

**Action:** `publish_finding`. Record utilization, flylines, and the OpenROAD recipe id.

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
- **Shared base:** Task handling lives in `domains/eda/runtime/agent.py`; HTTP wiring in `domains/eda/runtime/server.py`.
- **Telemetry:** See [`../../TELEMETRY.md`](../../TELEMETRY.md) (path may vary by depth) for fleet-wide observability conventions.

## How a newcomer should read this agent

1. Read `config.yaml` `metadata`, `boundary`, and `capabilities` for charter and limits.
2. Skim the skills table above, then open `tools.py` for parameter shapes.
3. Read `agent.py` and `server.py` only to confirm boot wiring.
4. Treat `Dockerfile` / `requirements.txt` as deployment detail.
