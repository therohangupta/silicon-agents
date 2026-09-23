# Detailed-Routing Repair Agent (`detailed_routing_repair`)

This directory is the deployable microservice package for the **Detailed-Routing Repair Agent** in the fleet **routing** stage (role `worker`).

## EDA responsibility

Tools for the Detailed-Routing Repair Agent.

Charter from `config.yaml`: Diagnose local shorts, opens, spacing, vias, and pin-access failures, apply the repair on an isolated candidate, and verify that clean regions stay clean. Adapter target: OpenROAD detailed_route.

As a **worker**, this process executes bounded skills on isolated candidates and reports observations. Promotion and program-level tradeoffs stay with leads and humans.

## Identity and HTTP port

| Field | Value |
|-------|-------|
| Agent id | `detailed_routing_repair` |
| Stage | `routing` |
| Role | `worker` |
| Host | `host.docker.internal` |
| Port | **8251** (must match `Dockerfile` `EXPOSE`) |
| Health | `/health` |
| Execute | `/tasks/execute` |

## Boundaries

Hard limits from `config.yaml` `boundary`. The planner and `EDAAgent` enforce these even when a tool adapter could physically perform a forbidden action.

### May

- Read DRC for one region
- Apply a localized repair on an isolated candidate
- Submit an incremental detailed route and a region DRC check

### May not

- Reroute the whole design to fix one short
- Suppress a DRC
- Edit the canonical routed database
- Promote a candidate onto the canonical baseline
- Approve a waiver or relax a hard requirement
- Treat its own summary as independent signoff

## Skills

Skills bind planner task ids to callables in `tools.py` (`module: tools`, `execution.mode: direct_function`).

| Skill id | Action | Callable | Description |
|----------|--------|----------|-------------|
| `read_region_drc` | `read_reports` | `read_region_drc` | Read DRC markers for one region. |
| `cluster_route_shorts` | `read_reports` | `cluster_route_shorts` | Cluster short markers. |
| `cluster_route_opens` | `read_reports` | `cluster_route_opens` | Cluster open markers. |
| `cluster_route_spacing` | `read_reports` | `cluster_route_spacing` | Cluster spacing violations. |
| `cluster_via_violations` | `read_reports` | `cluster_via_violations` | Cluster via violations. |
| `cluster_pin_access_failures` | `read_reports` | `cluster_pin_access_failures` | Cluster pin-access failures. |
| `trace_violation_net` | `read_reports` | `trace_violation_net` | Trace one marker to its net and neighboring nets. |
| `propose_local_route_repair` | `publish_finding` | `propose_local_route_repair` | Publish a localized repair and its expected timing side effect. |
| `apply_local_route_repair` | `write_candidate` | `apply_local_route_repair` | Apply one localized repair on an isolated candidate. |
| `run_incremental_detailed_route` | `submit_tool_job` | `run_incremental_detailed_route` | Run detailed routing on the repaired region. Adapter target: OpenROAD detailed_route. |
| `verify_region_drc` | `submit_tool_job` | `verify_region_drc` | Re-run DRC on the repaired region and on the previously clean neighborhood. |
| `report_repair_timing_delta` | `read_reports` | `report_repair_timing_delta` | Report timing change caused by the repair. |
| `report_repair_wirelength_delta` | `read_reports` | `report_repair_wirelength_delta` | Report wirelength change caused by the repair. |
| `write_repaired_def` | `write_candidate` | `write_repaired_def` | Write the repaired DEF. |
| `flag_destabilized_clean_region` | `publish_finding` | `flag_destabilized_clean_region` | Publish a previously clean region that the repair made dirty. |
| `record_route_repair_provenance` | `publish_finding` | `record_route_repair_provenance` | Record the marker, the edit, and the verification report. |

## Delegation

This agent declares **no** `delegates_to` entries. It executes its own `tools.py` skills when scheduled by a lead or the chip-flow orchestrator.

## Boot path

Every fleet agent shares the same linear startup so compose and local dev behave identically.

1. Container or shell runs `python server.py` (`deployment.dockerfile` / image `agentfleet/detailed_routing_repair:1.0`).
2. `server.py` prepends this directory to `sys.path`, imports `DetailedRoutingRepairAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, DetailedRoutingRepairAgent)`.
3. Importing `agent.py` sets `spec = EDAAgent.read_spec(<this directory>)`, loading `config.yaml` at class definition time.
4. Uvicorn serves FastAPI `app` on `connection.port` with `/health` and `/tasks/execute`.
5. On `/tasks/execute`, `EDAAgent.handle` assembles engineering-memory context (see `context` in YAML), journals the task, and dispatches the requested skill.
6. The skill callable in `tools.py` returns `tool_observation(...)`. With `backend.type: none`, observations are safe stubs (`not_run`) until `EDA_FRAMEWORK` or another adapter binds real engines.

## Related agents

- Stage index: [`../README.md`](../README.md) (routing specialists under `routing/`).
- Stage lead(s) that delegate here:
  - [`routing_lead`](../routing_lead/) (port **8249**)
- Sibling agents in this folder:
  - [`antenna_manufacturability`](../antenna_manufacturability/) — worker, port **8253**
  - [`global_routing`](../global_routing/) — worker, port **8250**
  - [`routing_lead`](../routing_lead/) — lead, port **8249**
  - [`si_noise_repair`](../si_noise_repair/) — worker, port **8252**
- Track overview: [`../../README.md`](../../README.md) (backend physical implementation).

## Files in this directory

| File | Role |
|------|------|
| `agent.py` | Defines `DetailedRoutingRepairAgent`; loads sibling `config.yaml` into `spec`. |
| `server.py` | HTTP/ASGI bootstrap; exports FastAPI `app` for uvicorn. |
| `tools.py` | `@tool` skill callables; stable EDA operation contracts. |
| `config.yaml` | Fleet manifest (`apiVersion: agentfleet/v1`): boundaries, port, skills, memory, telemetry. |
| `Dockerfile` | Container image; `EXPOSE 8251`; `CMD python server.py`. |
| `requirements.txt` | FastAPI, uvicorn, pydantic, PyYAML for the HTTP surface. |
| `__init__.py` | Re-exports `DetailedRoutingRepairAgent` for imports without starting HTTP. |
| `README.md` | This document. |

## Tool reference

### `read_region_drc` (`tools.read_region_drc`)

**Action:** `read_reports`. Read DRC markers for one region.

Read design-rule check (DRC) markers inside one repair region.

### `cluster_route_shorts` (`tools.cluster_route_shorts`)

**Action:** `read_reports`. Cluster short markers.

Cluster short (metal-metal overlap) markers into repairable groups.

### `cluster_route_opens` (`tools.cluster_route_opens`)

**Action:** `read_reports`. Cluster open markers.

Cluster open (disconnected net) markers into repairable groups.

### `cluster_route_spacing` (`tools.cluster_route_spacing`)

**Action:** `read_reports`. Cluster spacing violations.

Cluster spacing/enclosure DRC markers into repairable groups.

### `cluster_via_violations` (`tools.cluster_via_violations`)

**Action:** `read_reports`. Cluster via violations.

Cluster via-related DRC (missing/illegal vias) into groups.

### `cluster_pin_access_failures` (`tools.cluster_pin_access_failures`)

**Action:** `read_reports`. Cluster pin-access failures.

Cluster pin-access failures where the router cannot exit a pin.

### `trace_violation_net` (`tools.trace_violation_net`)

**Action:** `read_reports`. Trace one marker to its net and neighboring nets.

Trace which net owns a DRC marker to scope the local repair.

### `propose_local_route_repair` (`tools.propose_local_route_repair`)

**Action:** `publish_finding`. Publish a localized repair and its expected timing side effect.

Propose a localized rip-up/reroute or via change without applying it yet.

### `apply_local_route_repair` (`tools.apply_local_route_repair`)

**Action:** `write_candidate`. Apply one localized repair on an isolated candidate.

Apply one local repair onto an isolated routed candidate.

### `run_incremental_detailed_route` (`tools.run_incremental_detailed_route`)

**Action:** `submit_tool_job`. Run detailed routing on the repaired region. Adapter target: OpenROAD detailed_route.

Run OpenROAD detailed_route incrementally on the repair region.

### `verify_region_drc` (`tools.verify_region_drc`)

**Action:** `submit_tool_job`. Re-run DRC on the repaired region and on the previously clean neighborhood.

Re-check DRC in the repaired region and neighboring clean regions.

### `report_repair_timing_delta` (`tools.report_repair_timing_delta`)

**Action:** `read_reports`. Report timing change caused by the repair.

Report setup/hold WNS/TNS change caused by the local repair.

### `report_repair_wirelength_delta` (`tools.report_repair_wirelength_delta`)

**Action:** `read_reports`. Report wirelength change caused by the repair.

Report wirelength change caused by the local repair.

### `write_repaired_def` (`tools.write_repaired_def`)

**Action:** `write_candidate`. Write the repaired DEF.

Write the repaired DEF/ODB artifact for the candidate.

### `flag_destabilized_clean_region` (`tools.flag_destabilized_clean_region`)

**Action:** `publish_finding`. Publish a previously clean region that the repair made dirty.

Finding: a previously clean region gained new DRC after repair.

### `record_route_repair_provenance` (`tools.record_route_repair_provenance`)

**Action:** `publish_finding`. Record the marker, the edit, and the verification report.

Record tools, regions, and recipes used for the repair.

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
