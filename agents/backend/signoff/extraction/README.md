# Extraction Agent (`extraction`)

This directory is the deployable microservice package for the **Extraction Agent** in the fleet **signoff** stage (role `worker`).

## EDA responsibility

Produce versioned parasitic models from the routed design and record completeness and corner configuration. Adapter target: OpenROAD estimate_parasitics, then a signoff extractor behind the same operations.

As a **worker**, this process executes bounded skills on isolated candidates and reports observations. Promotion and program-level tradeoffs stay with leads and humans.

## Identity and HTTP port

| Field | Value |
|-------|-------|
| Agent id | `extraction` |
| Stage | `signoff` |
| Role | `worker` |
| Host | `host.docker.internal` |
| Port | **8254** (must match `Dockerfile` `EXPOSE`) |
| Health | `/health` |
| Execute | `/tasks/execute` |

## Boundaries

Hard limits from `config.yaml` `boundary`. The planner and `EdaAgent` enforce these even when a tool adapter could physically perform a forbidden action.

### May

- Submit extraction
- Write the corner configuration
- Publish RC artifact references

### May not

- Edit the routed design
- Drop a required corner
- Promote a candidate onto the canonical baseline
- Approve a waiver or relax a hard requirement
- Treat its own summary as independent signoff

## Skills

Skills bind planner task ids to callables in `tools.py` (`module: tools`, `execution.mode: direct_function`).

| Skill id | Action | Callable | Description |
|----------|--------|----------|-------------|
| `read_required_extraction_corners` | `read_reports` | `read_required_extraction_corners` | Read the corners extraction must produce. |
| `write_extraction_config` | `write_candidate` | `write_extraction_config` | Write the extraction configuration and corner list. |
| `extract_parasitics` | `submit_tool_job` | `extract_parasitics` | Extract parasitics for the configured corners. Adapter target: OpenROAD estimate_parasitics or the bound extractor. |
| `write_spef` | `submit_tool_job` | `write_spef` | Write the SPEF for one corner. |
| `validate_extraction_corners` | `read_reports` | `validate_extraction_corners` | Check that every required corner was extracted. |
| `check_extraction_completeness` | `read_reports` | `check_extraction_completeness` | Check for missing nets, layers, and couplings. |
| `check_spef_header` | `read_reports` | `check_spef_header` | Check design name, units, and divider in the SPEF header. |
| `compare_spef_to_routed_nets` | `read_reports` | `compare_spef_to_routed_nets` | Compare extracted nets with the routed netlist. |
| `read_extraction_log` | `read_reports` | `read_extraction_log` | Read the extraction log and warnings. |
| `flag_missing_extraction_corner` | `publish_finding` | `flag_missing_extraction_corner` | Publish a required corner that was not extracted. |
| `flag_incomplete_extraction` | `publish_finding` | `flag_incomplete_extraction` | Publish missing nets or couplings. |
| `record_extraction_provenance` | `publish_finding` | `record_extraction_provenance` | Record the extractor, version, rule deck, and SPEF refs. |

## Delegation

This agent declares **no** `delegates_to` entries. It executes its own `tools.py` skills when scheduled by a lead or the chip-flow orchestrator.

## Boot path

Every fleet agent shares the same linear startup so compose and local dev behave identically.

1. Container or shell runs `python server.py` (`deployment.dockerfile` / image `agentfleet/extraction:1.0`).
2. `server.py` prepends this directory to `sys.path`, imports `ExtractionAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, ExtractionAgent)`.
3. Importing `agent.py` sets `spec = EdaAgent.read_spec(<this directory>)`, loading `config.yaml` at class definition time.
4. Uvicorn serves FastAPI `app` on `connection.port` with `/health` and `/tasks/execute`.
5. On `/tasks/execute`, `EdaAgent.handle` assembles engineering-memory context (see `context` in YAML), journals the task, and dispatches the requested skill.
6. The skill callable in `tools.py` returns `tool_observation(...)`. With `backend.type: none`, observations are safe stubs (`not_run`) until `EDA_FRAMEWORK` or another adapter binds real engines.

## Related agents

- Stage index: [`../README.md`](../README.md) (signoff specialists under `signoff/`).
- Program orchestrator:
  - [`chip_flow_lead`](../../../chip_flow_lead/) (port **8201**)
- Sibling agents in this folder:
  - [`drc_lvs`](../drc_lvs/) — worker, port **8260**
  - [`eco_lead`](../eco_lead/) — lead, port **8261**
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
| `agent.py` | Defines `ExtractionAgent`; loads sibling `config.yaml` into `spec`. |
| `server.py` | HTTP/ASGI bootstrap; exports FastAPI `app` for uvicorn. |
| `tools.py` | `@tool` skill callables; stable EDA operation contracts. |
| `config.yaml` | Fleet manifest (`apiVersion: agentfleet/v1`): boundaries, port, skills, memory, telemetry. |
| `Dockerfile` | Container image; `EXPOSE 8254`; `CMD python server.py`. |
| `requirements.txt` | FastAPI, uvicorn, pydantic, PyYAML for the HTTP surface. |
| `__init__.py` | Re-exports `ExtractionAgent` for imports without starting HTTP. |
| `README.md` | This document. |

## Tool reference

### `read_required_extraction_corners` (`tools.read_required_extraction_corners`)

**Action:** `read_reports`. Read the corners extraction must produce.

### `write_extraction_config` (`tools.write_extraction_config`)

**Action:** `write_candidate`. Write the extraction configuration and corner list.

### `extract_parasitics` (`tools.extract_parasitics`)

**Action:** `submit_tool_job`. Extract parasitics for the configured corners. Adapter target: OpenROAD estimate_parasitics or the bound extractor.

### `write_spef` (`tools.write_spef`)

**Action:** `submit_tool_job`. Write the SPEF for one corner.

### `validate_extraction_corners` (`tools.validate_extraction_corners`)

**Action:** `read_reports`. Check that every required corner was extracted.

### `check_extraction_completeness` (`tools.check_extraction_completeness`)

**Action:** `read_reports`. Check for missing nets, layers, and couplings.

### `check_spef_header` (`tools.check_spef_header`)

**Action:** `read_reports`. Check design name, units, and divider in the SPEF header.

### `compare_spef_to_routed_nets` (`tools.compare_spef_to_routed_nets`)

**Action:** `read_reports`. Compare extracted nets with the routed netlist.

### `read_extraction_log` (`tools.read_extraction_log`)

**Action:** `read_reports`. Read the extraction log and warnings.

### `flag_missing_extraction_corner` (`tools.flag_missing_extraction_corner`)

**Action:** `publish_finding`. Publish a required corner that was not extracted.

### `flag_incomplete_extraction` (`tools.flag_incomplete_extraction`)

**Action:** `publish_finding`. Publish missing nets or couplings.

### `record_extraction_provenance` (`tools.record_extraction_provenance`)

**Action:** `publish_finding`. Record the extractor, version, rule deck, and SPEF refs.

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
