# IR/EM Agent (`ir_em`)

This directory is the deployable microservice package for the **IR/EM Agent** in the fleet **signoff** stage (role `worker`).

## EDA responsibility

Analyze static and dynamic voltage drop and current density, localize weak regions, and apply a grid or placement repair on an isolated candidate with a timing and routing check.

As a **worker**, this process executes bounded skills on isolated candidates and reports observations. Promotion and program-level tradeoffs stay with leads and humans.

## Identity and HTTP port

| Field | Value |
|-------|-------|
| Agent id | `ir_em` |
| Stage | `signoff` |
| Role | `worker` |
| Host | `host.docker.internal` |
| Port | **8258** (must match `Dockerfile` `EXPOSE`) |
| Health | `/health` |
| Execute | `/tasks/execute` |

## Boundaries

Hard limits from `config.yaml` `boundary`. The planner and `EDAAgent` enforce these even when a tool adapter could physically perform a forbidden action.

### May

- Submit an IR/EM analysis
- Apply a grid or placement repair on an isolated candidate
- Submit a timing and routing check of that repair

### May not

- Edit the canonical power grid
- Ignore a dynamic-drop window
- Claim a repair is closed without a timing and routing check
- Promote a candidate onto the canonical baseline
- Approve a waiver or relax a hard requirement
- Treat its own summary as independent signoff

## Skills

Skills bind planner task ids to callables in `tools.py` (`module: tools`, `execution.mode: direct_function`).

| Skill id | Action | Callable | Description |
|----------|--------|----------|-------------|
| `analyze_static_ir` | `submit_tool_job` | `analyze_static_ir` | Run static IR analysis. |
| `analyze_dynamic_ir` | `submit_tool_job` | `analyze_dynamic_ir` | Run dynamic IR analysis over the required windows. |
| `analyze_electromigration` | `submit_tool_job` | `analyze_electromigration` | Run current-density analysis. |
| `read_ir_map` | `read_reports` | `read_ir_map` | Read the voltage-drop map. |
| `read_em_violations` | `read_reports` | `read_em_violations` | Read electromigration violations. |
| `localize_grid_weakness` | `publish_finding` | `localize_grid_weakness` | Publish the weak regions and the current that causes them. |
| `propose_grid_repair` | `publish_finding` | `propose_grid_repair` | Publish a strap, via, or rail change. |
| `propose_ir_placement_repair` | `publish_finding` | `propose_ir_placement_repair` | Publish a placement change that reduces local current. |
| `apply_grid_repair` | `write_candidate` | `apply_grid_repair` | Apply one grid repair on an isolated candidate. |
| `verify_ir_after_repair` | `submit_tool_job` | `verify_ir_after_repair` | Re-run IR and EM on the repaired candidate. |
| `verify_ir_repair_timing_route` | `submit_tool_job` | `verify_ir_repair_timing_route` | Check timing and routing impact of the repair. |
| `flag_unchecked_ir_repair` | `publish_finding` | `flag_unchecked_ir_repair` | Publish a repair that has no timing or routing check. |
| `record_ir_em_provenance` | `publish_finding` | `record_ir_em_provenance` | Record the current source, windows, and tool version. |

## Delegation

This agent declares **no** `delegates_to` entries. It executes its own `tools.py` skills when scheduled by a lead or the chip-flow orchestrator.

## Boot path

Every fleet agent shares the same linear startup so compose and local dev behave identically.

1. Container or shell runs `python server.py` (`deployment.dockerfile` / image `agentfleet/ir_em:1.0`).
2. `server.py` prepends this directory to `sys.path`, imports `IrEmAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, IrEmAgent)`.
3. Importing `agent.py` sets `spec = EDAAgent.read_spec(<this directory>)`, loading `config.yaml` at class definition time.
4. Uvicorn serves FastAPI `app` on `connection.port` with `/health` and `/tasks/execute`.
5. On `/tasks/execute`, `EDAAgent.handle` assembles engineering-memory context (see `context` in YAML), journals the task, and dispatches the requested skill.
6. The skill callable in `tools.py` returns `tool_observation(...)`. With `backend.type: none`, observations are safe stubs (`not_run`) until `EDA_FRAMEWORK` or another adapter binds real engines.

## Related agents

- Stage index: [`../README.md`](../README.md) (signoff specialists under `signoff/`).
- Sibling agents in this folder:
  - [`drc_lvs`](../drc_lvs/) — worker, port **8260**
  - [`eco_lead`](../eco_lead/) — lead, port **8261**
  - [`extraction`](../extraction/) — worker, port **8254**
  - [`power_analysis`](../power_analysis/) — worker, port **8257**
  - [`signoff_validator`](../signoff_validator/) — validator, port **8262**
  - [`sta_lead`](../sta_lead/) — lead, port **8255**
  - [`thermal_reliability`](../thermal_reliability/) — worker, port **8259**
  - [`timing_debug`](../timing_debug/) — worker, port **8256**
- Track overview: [`../../README.md`](../../README.md) (backend physical implementation).

## Files in this directory

| File | Role |
|------|------|
| `agent.py` | Defines `IrEmAgent`; loads sibling `config.yaml` into `spec`. |
| `server.py` | HTTP/ASGI bootstrap; exports FastAPI `app` for uvicorn. |
| `tools.py` | `@tool` skill callables; stable EDA operation contracts. |
| `config.yaml` | Fleet manifest (`apiVersion: agentfleet/v1`): boundaries, port, skills, memory, telemetry. |
| `Dockerfile` | Container image; `EXPOSE 8258`; `CMD python server.py`. |
| `requirements.txt` | FastAPI, uvicorn, pydantic, PyYAML for the HTTP surface. |
| `__init__.py` | Re-exports `IrEmAgent` for imports without starting HTTP. |
| `README.md` | This document. |

## Tool reference

### `analyze_static_ir` (`tools.analyze_static_ir`)

**Action:** `submit_tool_job`. Run static IR analysis.

### `analyze_dynamic_ir` (`tools.analyze_dynamic_ir`)

**Action:** `submit_tool_job`. Run dynamic IR analysis over the required windows.

### `analyze_electromigration` (`tools.analyze_electromigration`)

**Action:** `submit_tool_job`. Run current-density analysis.

### `read_ir_map` (`tools.read_ir_map`)

**Action:** `read_reports`. Read the voltage-drop map.

### `read_em_violations` (`tools.read_em_violations`)

**Action:** `read_reports`. Read electromigration violations.

### `localize_grid_weakness` (`tools.localize_grid_weakness`)

**Action:** `publish_finding`. Publish the weak regions and the current that causes them.

### `propose_grid_repair` (`tools.propose_grid_repair`)

**Action:** `publish_finding`. Publish a strap, via, or rail change.

### `propose_ir_placement_repair` (`tools.propose_ir_placement_repair`)

**Action:** `publish_finding`. Publish a placement change that reduces local current.

### `apply_grid_repair` (`tools.apply_grid_repair`)

**Action:** `write_candidate`. Apply one grid repair on an isolated candidate.

### `verify_ir_after_repair` (`tools.verify_ir_after_repair`)

**Action:** `submit_tool_job`. Re-run IR and EM on the repaired candidate.

### `verify_ir_repair_timing_route` (`tools.verify_ir_repair_timing_route`)

**Action:** `submit_tool_job`. Check timing and routing impact of the repair.

### `flag_unchecked_ir_repair` (`tools.flag_unchecked_ir_repair`)

**Action:** `publish_finding`. Publish a repair that has no timing or routing check.

### `record_ir_em_provenance` (`tools.record_ir_em_provenance`)

**Action:** `publish_finding`. Record the current source, windows, and tool version.

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
