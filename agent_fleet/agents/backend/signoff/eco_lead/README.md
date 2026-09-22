# ECO Lead (`eco_lead`)

This directory is the deployable microservice package for the **ECO Lead** in the fleet **signoff** stage (role `lead`).

## EDA responsibility

Plan a late functional, timing, power, or physical change. Minimize disruption, preserve equivalence, and name every check the change invalidates.

As a **lead**, this process publishes workflows, reads qualified upstream artifacts, opens child agent tasks, compares candidates, and recommends next steps. It does **not** promote the canonical baseline or act as independent signoff.

## Identity and HTTP port

| Field | Value |
|-------|-------|
| Agent id | `eco_lead` |
| Stage | `signoff` |
| Role | `lead` |
| Host | `host.docker.internal` |
| Port | **8261** (must match `Dockerfile` `EXPOSE`) |
| Health | `/health` |
| Execute | `/tasks/execute` |

## Boundaries

Hard limits from `config.yaml` `boundary`. The planner and `EdaAgent` enforce these even when a tool adapter could physically perform a forbidden action.

### May

- Publish an ECO workflow
- Read the open finding and the current baseline
- Request a human decision before an ECO is applied

### May not

- Apply the ECO without equivalence when function changes
- Skip an impacted signoff check
- Promote the ECO
- Promote a candidate onto the canonical baseline
- Approve a waiver or relax a hard requirement
- Treat its own summary as independent signoff

## Skills

Skills bind planner task ids to callables in `tools.py` (`module: tools`, `execution.mode: direct_function`).

| Skill id | Action | Callable | Description |
|----------|--------|----------|-------------|
| `plan_eco` | `create_workflow` | `plan_eco` | Emit the smallest workflow that implements and revalidates one ECO. |
| `request_eco_rtl_edit` | `create_workflow` | `request_eco_rtl_edit` | Open one bounded RTL edit for a functional ECO. |
| `request_eco_equivalence` | `create_workflow` | `request_eco_equivalence` | Open equivalence for an ECO that changes logic. |
| `request_eco_timing` | `create_workflow` | `request_eco_timing` | Open timing on the paths the ECO can move. |
| `request_eco_physical_verification` | `create_workflow` | `request_eco_physical_verification` | Open DRC and LVS for a physical ECO. |
| `list_impacted_checks` | `read_reports` | `list_impacted_checks` | List the gates this ECO invalidates. |
| `read_eco_finding` | `read_reports` | `read_eco_finding` | Read the finding this ECO is supposed to close. |
| `read_eco_baseline` | `read_reports` | `read_eco_baseline` | Read the baseline the ECO must descend from. |
| `estimate_eco_disruption` | `read_reports` | `estimate_eco_disruption` | List files, nets, and path groups the ECO touches. |
| `flag_missing_eco_check` | `publish_finding` | `flag_missing_eco_check` | Publish an impacted check the workflow does not rerun. |
| `record_eco_scope` | `publish_finding` | `record_eco_scope` | Record the hypothesis, the baseline, and the checks that must rerun. |
| `request_eco_authorization` | `request_human_decision` | `request_eco_authorization` | Ask a human to authorize the ECO before it is applied. |

## Delegation

This lead may open child workflows/tasks against:

- [`rtl_implementation`](../../../frontend/rtl/rtl_implementation/) — RTL Implementation Agent (port **8209**)
- [`equivalence`](../../synthesis/equivalence/) — Equivalence Agent (port **8236**)
- [`timing_debug`](../timing_debug/) — Timing-Debug Agent (port **8256**)
- [`drc_lvs`](../drc_lvs/) — DRC/LVS/ERC/DFM Agent (port **8260**)

Delegation is declarative in `delegates_to`. The lead's `request_*` / `open_*` skills tell the orchestrator which child agent id and skill to schedule next; workers do not call each other directly over HTTP.

## Boot path

Every fleet agent shares the same linear startup so compose and local dev behave identically.

1. Container or shell runs `python server.py` (`deployment.dockerfile` / image `agentfleet/eco_lead:1.0`).
2. `server.py` prepends this directory to `sys.path`, imports `EcoLeadAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, EcoLeadAgent)`.
3. Importing `agent.py` sets `spec = EdaAgent.read_spec(<this directory>)`, loading `config.yaml` at class definition time.
4. Uvicorn serves FastAPI `app` on `connection.port` with `/health` and `/tasks/execute`.
5. On `/tasks/execute`, `EdaAgent.handle` assembles engineering-memory context (see `context` in YAML), journals the task, and dispatches the requested skill.
6. The skill callable in `tools.py` returns `tool_observation(...)`. With `backend.type: none`, observations are safe stubs (`not_run`) until `EDA_FRAMEWORK` or another adapter binds real engines.

## Related agents

- Stage index: [`../README.md`](../README.md) (signoff specialists under `signoff/`).
- Sibling agents in this folder:
  - [`drc_lvs`](../drc_lvs/) — worker, port **8260**
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
| `agent.py` | Defines `EcoLeadAgent`; loads sibling `config.yaml` into `spec`. |
| `server.py` | HTTP/ASGI bootstrap; exports FastAPI `app` for uvicorn. |
| `tools.py` | `@tool` skill callables; stable EDA operation contracts. |
| `config.yaml` | Fleet manifest (`apiVersion: agentfleet/v1`): boundaries, port, skills, memory, telemetry. |
| `Dockerfile` | Container image; `EXPOSE 8261`; `CMD python server.py`. |
| `requirements.txt` | FastAPI, uvicorn, pydantic, PyYAML for the HTTP surface. |
| `__init__.py` | Re-exports `EcoLeadAgent` for imports without starting HTTP. |
| `README.md` | This document. |

## Tool reference

### `plan_eco` (`tools.plan_eco`)

**Action:** `create_workflow`. Emit the smallest workflow that implements and revalidates one ECO.

### `request_eco_rtl_edit` (`tools.request_eco_rtl_edit`)

**Action:** `create_workflow`. Open one bounded RTL edit for a functional ECO.

### `request_eco_equivalence` (`tools.request_eco_equivalence`)

**Action:** `create_workflow`. Open equivalence for an ECO that changes logic.

### `request_eco_timing` (`tools.request_eco_timing`)

**Action:** `create_workflow`. Open timing on the paths the ECO can move.

### `request_eco_physical_verification` (`tools.request_eco_physical_verification`)

**Action:** `create_workflow`. Open DRC and LVS for a physical ECO.

### `list_impacted_checks` (`tools.list_impacted_checks`)

**Action:** `read_reports`. List the gates this ECO invalidates.

### `read_eco_finding` (`tools.read_eco_finding`)

**Action:** `read_reports`. Read the finding this ECO is supposed to close.

### `read_eco_baseline` (`tools.read_eco_baseline`)

**Action:** `read_reports`. Read the baseline the ECO must descend from.

### `estimate_eco_disruption` (`tools.estimate_eco_disruption`)

**Action:** `read_reports`. List files, nets, and path groups the ECO touches.

### `flag_missing_eco_check` (`tools.flag_missing_eco_check`)

**Action:** `publish_finding`. Publish an impacted check the workflow does not rerun.

### `record_eco_scope` (`tools.record_eco_scope`)

**Action:** `publish_finding`. Record the hypothesis, the baseline, and the checks that must rerun.

### `request_eco_authorization` (`tools.request_eco_authorization`)

**Action:** `request_human_decision`. Ask a human to authorize the ECO before it is applied.

## Runtime, memory, and context

- **Reliability:** task timeout 120s, max retries 1, on failure `replan`.
- **Execution:** `direct_function`, `max_tasks=1`.
- **Context include:** `gates`, `workflows`, `open_findings`, `decisions`, `experiments`.
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
