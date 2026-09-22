# Independent Signoff Validator (`signoff_validator`)

This directory is the deployable microservice package for the **Independent Signoff Validator** in the fleet **signoff** stage (role `validator`).

## EDA responsibility

Read primary signoff artifacts, reproduce critical checks, audit waivers, and decide whether every required gate passed.

As a **validator**, this process independently grades gate evidence, audits waivers, and publishes pass/fail outcomes. It does not mutate design candidates on behalf of workers.

## Identity and HTTP port

| Field | Value |
|-------|-------|
| Agent id | `signoff_validator` |
| Stage | `signoff` |
| Role | `validator` |
| Host | `host.docker.internal` |
| Port | **8262** (must match `Dockerfile` `EXPOSE`) |
| Health | `/health` |
| Execute | `/tasks/execute` |

## Boundaries

Hard limits from `config.yaml` `boundary`. The planner and `EdaAgent` enforce these even when a tool adapter could physically perform a forbidden action.

### May

- Read a frozen candidate and frozen recipes
- Reproduce critical checks
- Emit a signoff gate
- Publish missing inputs

### May not

- Modify the candidate
- Change a rule deck
- Suppress a violation
- Approve a waiver
- Release a tapeout package
- Promote a candidate onto the canonical baseline
- Approve a waiver or relax a hard requirement
- Treat its own summary as independent signoff

## Skills

Skills bind planner task ids to callables in `tools.py` (`module: tools`, `execution.mode: direct_function`).

| Skill id | Action | Callable | Description |
|----------|--------|----------|-------------|
| `read_frozen_signoff_candidate` | `read_reports` | `read_frozen_signoff_candidate` | Read the pinned candidate being graded. |
| `read_frozen_signoff_recipes` | `read_reports` | `read_frozen_signoff_recipes` | Read the frozen tool recipes and rule decks. |
| `read_primary_signoff_artifacts` | `read_reports` | `read_primary_signoff_artifacts` | Read timing, power, IR, DRC, LVS, and extraction artifacts. |
| `check_signoff_provenance` | `read_reports` | `check_signoff_provenance` | Check tool versions, SPEF, SDC, and rule decks against the frozen flow. |
| `reproduce_signoff_checks` | `submit_tool_job` | `reproduce_signoff_checks` | Re-run the critical signoff checks from primary artifacts. |
| `reproduce_signoff_sta` | `submit_tool_job` | `reproduce_signoff_sta` | Re-run static timing on the frozen SPEF and SDC. |
| `reproduce_signoff_drc_lvs` | `submit_tool_job` | `reproduce_signoff_drc_lvs` | Re-run DRC and LVS with the frozen rule deck. |
| `audit_waivers` | `read_reports` | `audit_waivers` | Check that every waiver has an owner, scope, and expiration. |
| `list_missing_signoff_inputs` | `read_reports` | `list_missing_signoff_inputs` | List required reports that are absent. |
| `compare_signoff_summary` | `read_reports` | `compare_signoff_summary` | Compare producing agents' summaries with the primary artifacts. |
| `emit_signoff_gate` | `emit_gate` | `emit_signoff_gate` | Record whether the signoff contract passed. A missing input fails the gate. |
| `publish_signoff_disagreement` | `publish_finding` | `publish_signoff_disagreement` | Publish a place where a summary and a primary artifact disagree. |
| `publish_missing_signoff_input` | `publish_finding` | `publish_missing_signoff_input` | Publish an input that blocks the signoff grade. |
| `publish_waiver_audit_gap` | `publish_finding` | `publish_waiver_audit_gap` | Publish a waiver that lacks an owner, scope, or expiration. |

## Delegation

This agent declares **no** `delegates_to` entries. It executes its own `tools.py` skills when scheduled by a lead or the chip-flow orchestrator.

## Boot path

Every fleet agent shares the same linear startup so compose and local dev behave identically.

1. Container or shell runs `python server.py` (`deployment.dockerfile` / image `agentfleet/signoff_validator:1.0`).
2. `server.py` prepends this directory to `sys.path`, imports `SignoffValidatorAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, SignoffValidatorAgent)`.
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
  - [`extraction`](../extraction/) — worker, port **8254**
  - [`ir_em`](../ir_em/) — worker, port **8258**
  - [`power_analysis`](../power_analysis/) — worker, port **8257**
  - [`sta_lead`](../sta_lead/) — lead, port **8255**
  - [`thermal_reliability`](../thermal_reliability/) — worker, port **8259**
  - [`timing_debug`](../timing_debug/) — worker, port **8256**
- Track overview: [`../../README.md`](../../README.md) (backend physical implementation).

## Files in this directory

| File | Role |
|------|------|
| `agent.py` | Defines `SignoffValidatorAgent`; loads sibling `config.yaml` into `spec`. |
| `server.py` | HTTP/ASGI bootstrap; exports FastAPI `app` for uvicorn. |
| `tools.py` | `@tool` skill callables; stable EDA operation contracts. |
| `config.yaml` | Fleet manifest (`apiVersion: agentfleet/v1`): boundaries, port, skills, memory, telemetry. |
| `Dockerfile` | Container image; `EXPOSE 8262`; `CMD python server.py`. |
| `requirements.txt` | FastAPI, uvicorn, pydantic, PyYAML for the HTTP surface. |
| `__init__.py` | Re-exports `SignoffValidatorAgent` for imports without starting HTTP. |
| `README.md` | This document. |

## Tool reference

### `read_frozen_signoff_candidate` (`tools.read_frozen_signoff_candidate`)

**Action:** `read_reports`. Read the pinned candidate being graded.

### `read_frozen_signoff_recipes` (`tools.read_frozen_signoff_recipes`)

**Action:** `read_reports`. Read the frozen tool recipes and rule decks.

### `read_primary_signoff_artifacts` (`tools.read_primary_signoff_artifacts`)

**Action:** `read_reports`. Read timing, power, IR, DRC, LVS, and extraction artifacts.

### `check_signoff_provenance` (`tools.check_signoff_provenance`)

**Action:** `read_reports`. Check tool versions, SPEF, SDC, and rule decks against the frozen flow.

### `reproduce_signoff_checks` (`tools.reproduce_signoff_checks`)

**Action:** `submit_tool_job`. Re-run the critical signoff checks from primary artifacts.

### `reproduce_signoff_sta` (`tools.reproduce_signoff_sta`)

**Action:** `submit_tool_job`. Re-run static timing on the frozen SPEF and SDC.

### `reproduce_signoff_drc_lvs` (`tools.reproduce_signoff_drc_lvs`)

**Action:** `submit_tool_job`. Re-run DRC and LVS with the frozen rule deck.

### `audit_waivers` (`tools.audit_waivers`)

**Action:** `read_reports`. Check that every waiver has an owner, scope, and expiration.

### `list_missing_signoff_inputs` (`tools.list_missing_signoff_inputs`)

**Action:** `read_reports`. List required reports that are absent.

### `compare_signoff_summary` (`tools.compare_signoff_summary`)

**Action:** `read_reports`. Compare producing agents' summaries with the primary artifacts.

### `emit_signoff_gate` (`tools.emit_signoff_gate`)

**Action:** `emit_gate`. Record whether the signoff contract passed. A missing input fails the gate.

### `publish_signoff_disagreement` (`tools.publish_signoff_disagreement`)

**Action:** `publish_finding`. Publish a place where a summary and a primary artifact disagree.

### `publish_missing_signoff_input` (`tools.publish_missing_signoff_input`)

**Action:** `publish_finding`. Publish an input that blocks the signoff grade.

### `publish_waiver_audit_gap` (`tools.publish_waiver_audit_gap`)

**Action:** `publish_finding`. Publish a waiver that lacks an owner, scope, or expiration.

## Runtime, memory, and context

- **Reliability:** task timeout 120s, max retries 1, on failure `replan`.
- **Execution:** `direct_function`, `max_tasks=1`.
- **Context include:** `requirements`, `interface_contracts`, `canonical_source`, `gates`, `open_findings`.
- **Context exclude:** `stale_candidates`, `unverified_agent_claims`.
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
