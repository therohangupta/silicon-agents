# DRC/LVS/ERC/DFM Agent (`drc_lvs`)

This directory is the deployable microservice package for the **DRC/LVS/ERC/DFM Agent** in the fleet **signoff** stage (role `worker`).

## EDA responsibility

Run and triage geometry, connectivity, electrical, density, and manufacturability checks, and separate real defects from setup errors.

As a **worker**, this process executes bounded skills on isolated candidates and reports observations. Promotion and program-level tradeoffs stay with leads and humans.

## Identity and HTTP port

| Field | Value |
|-------|-------|
| Agent id | `drc_lvs` |
| Stage | `signoff` |
| Role | `worker` |
| Host | `host.docker.internal` |
| Port | **8260** (must match `Dockerfile` `EXPOSE`) |
| Health | `/health` |
| Execute | `/tasks/execute` |

## Boundaries

Hard limits from `config.yaml` `boundary`. The planner and `EDAAgent` enforce these even when a tool adapter could physically perform a forbidden action.

### May

- Submit physical verification
- Read rule decks and waivers
- Cluster violations by likely cause

### May not

- Waive a violation
- Edit the layout
- Delete a marker
- Promote a candidate onto the canonical baseline
- Approve a waiver or relax a hard requirement
- Treat its own summary as independent signoff

## Skills

Skills bind planner task ids to callables in `tools.py` (`module: tools`, `execution.mode: direct_function`).

| Skill id | Action | Callable | Description |
|----------|--------|----------|-------------|
| `run_drc` | `submit_tool_job` | `run_drc` | Run design-rule checks. |
| `run_lvs` | `submit_tool_job` | `run_lvs` | Run layout-versus-schematic. |
| `run_erc` | `submit_tool_job` | `run_erc` | Run electrical-rule checks. |
| `run_density` | `submit_tool_job` | `run_density` | Run density checks. |
| `run_dfm` | `submit_tool_job` | `run_dfm` | Run manufacturability checks. |
| `read_drc_markers` | `read_reports` | `read_drc_markers` | Read DRC markers. |
| `read_lvs_discrepancies` | `read_reports` | `read_lvs_discrepancies` | Read shorts, opens, and device mismatches. |
| `read_erc_markers` | `read_reports` | `read_erc_markers` | Read electrical-rule markers. |
| `cluster_physical_violations` | `publish_finding` | `cluster_physical_violations` | Cluster violations and separate real defects from setup errors. |
| `separate_setup_errors` | `read_reports` | `separate_setup_errors` | List markers caused by a wrong rule deck, cell view, or window. |
| `flag_real_physical_defect` | `publish_finding` | `flag_real_physical_defect` | Publish a marker that is not a setup error and is not waived. |
| `record_physical_verification_deck` | `publish_finding` | `record_physical_verification_deck` | Record the rule deck, layout ref, and tool version. |

## Delegation

This agent declares **no** `delegates_to` entries. It executes its own `tools.py` skills when scheduled by a lead or the chip-flow orchestrator.

## Boot path

Every fleet agent shares the same linear startup so compose and local dev behave identically.

1. Container or shell runs `python server.py` (`deployment.dockerfile` / image `agentfleet/drc_lvs:1.0`).
2. `server.py` prepends this directory to `sys.path`, imports `DrcLvsAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, DrcLvsAgent)`.
3. Importing `agent.py` sets `spec = EDAAgent.read_spec(<this directory>)`, loading `config.yaml` at class definition time.
4. Uvicorn serves FastAPI `app` on `connection.port` with `/health` and `/tasks/execute`.
5. On `/tasks/execute`, `EDAAgent.handle` assembles engineering-memory context (see `context` in YAML), journals the task, and dispatches the requested skill.
6. The skill callable in `tools.py` returns `tool_observation(...)`. With `backend.type: none`, observations are safe stubs (`not_run`) until `EDA_FRAMEWORK` or another adapter binds real engines.

## Related agents

- Stage index: [`../README.md`](../README.md) (signoff specialists under `signoff/`).
- Stage lead(s) that delegate here:
  - [`eco_lead`](../eco_lead/) (port **8261**)
- Sibling agents in this folder:
  - [`eco_lead`](../eco_lead/) — lead, port **8261**
  - [`extraction`](../extraction/) — worker, port **8254**
  - [`ir_em`](../ir_em/) — worker, port **8258**
  - [`power_analysis`](../power_analysis/) — worker, port **8257**
  - [`signoff_validator`](../signoff_validator/) — validator, port **8262**
  - [`sta_lead`](../sta_lead/) — lead, port **8255**
  - [`thermal_reliability`](../thermal_reliability/) — worker, port **8259**
  - [`timing_debug`](../timing_debug/) — worker, port **8256**
- Track overview: [`../../README.md`](../../README.md) (backend physical implementation).

## Files in this directory

| File | Role |
|------|------|
| `agent.py` | Defines `DrcLvsAgent`; loads sibling `config.yaml` into `spec`. |
| `server.py` | HTTP/ASGI bootstrap; exports FastAPI `app` for uvicorn. |
| `tools.py` | `@tool` skill callables; stable EDA operation contracts. |
| `config.yaml` | Fleet manifest (`apiVersion: agentfleet/v1`): boundaries, port, skills, memory, telemetry. |
| `Dockerfile` | Container image; `EXPOSE 8260`; `CMD python server.py`. |
| `requirements.txt` | FastAPI, uvicorn, pydantic, PyYAML for the HTTP surface. |
| `__init__.py` | Re-exports `DrcLvsAgent` for imports without starting HTTP. |
| `README.md` | This document. |

## Tool reference

### `run_drc` (`tools.run_drc`)

**Action:** `submit_tool_job`. Run design-rule checks.

### `run_lvs` (`tools.run_lvs`)

**Action:** `submit_tool_job`. Run layout-versus-schematic.

### `run_erc` (`tools.run_erc`)

**Action:** `submit_tool_job`. Run electrical-rule checks.

### `run_density` (`tools.run_density`)

**Action:** `submit_tool_job`. Run density checks.

### `run_dfm` (`tools.run_dfm`)

**Action:** `submit_tool_job`. Run manufacturability checks.

### `read_drc_markers` (`tools.read_drc_markers`)

**Action:** `read_reports`. Read DRC markers.

### `read_lvs_discrepancies` (`tools.read_lvs_discrepancies`)

**Action:** `read_reports`. Read shorts, opens, and device mismatches.

### `read_erc_markers` (`tools.read_erc_markers`)

**Action:** `read_reports`. Read electrical-rule markers.

### `cluster_physical_violations` (`tools.cluster_physical_violations`)

**Action:** `publish_finding`. Cluster violations and separate real defects from setup errors.

### `separate_setup_errors` (`tools.separate_setup_errors`)

**Action:** `read_reports`. List markers caused by a wrong rule deck, cell view, or window.

### `flag_real_physical_defect` (`tools.flag_real_physical_defect`)

**Action:** `publish_finding`. Publish a marker that is not a setup error and is not waived.

### `record_physical_verification_deck` (`tools.record_physical_verification_deck`)

**Action:** `publish_finding`. Record the rule deck, layout ref, and tool version.

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
