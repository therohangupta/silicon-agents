# Requirements Agent (`requirements`)

This directory is the deployable microservice package for the **Requirements Agent** in the fleet **architecture** stage (role `worker`).

## EDA responsibility

Requirements Agent — agent class entry point.

Charter from `config.yaml`: Convert product goals into traceable, measurable requirements and acceptance criteria.

As a **worker**, this process executes bounded skills on isolated candidates and reports observations. Promotion and program-level tradeoffs stay with leads and humans.

## Identity and HTTP port

| Field | Value |
|-------|-------|
| Agent id | `requirements` |
| Stage | `architecture` |
| Role | `worker` |
| Host | `host.docker.internal` |
| Port | **8202** (must match `Dockerfile` `EXPOSE`) |
| Health | `/health` |
| Execute | `/tasks/execute` |

## Boundaries

Hard limits from `config.yaml` `boundary`. The planner and `EdaAgent` enforce these even when a tool adapter could physically perform a forbidden action.

### May

- Read human design intent
- Write requirement records in an isolated draft
- Flag a goal that cannot be tested

### May not

- Change product intent
- Delete a requirement a human authored
- Promote a candidate onto the canonical baseline
- Approve a waiver or relax a hard requirement
- Treat its own summary as independent signoff

## Skills

Skills bind planner task ids to callables in `tools.py` (`module: tools`, `execution.mode: direct_function`).

| Skill id | Action | Callable | Description |
|----------|--------|----------|-------------|
| `extract_requirements` | `write_candidate` | `extract_requirements` | Turn design intent into requirement records with stable ids. |
| `assign_acceptance_criteria` | `write_candidate` | `assign_acceptance_criteria` | Attach a measurable check and a pass rule to one requirement. |
| `split_requirement` | `write_candidate` | `split_requirement` | Split one compound requirement into independently testable records. |
| `link_requirement_to_interface` | `write_candidate` | `link_requirement_to_interface` | Bind a requirement to the interface contract that carries it. |
| `link_requirement_to_check` | `write_candidate` | `link_requirement_to_check` | Bind a requirement to the test, assertion, or signoff check that closes it. |
| `record_requirement_assumption` | `write_candidate` | `record_requirement_assumption` | Record an assumption a requirement depends on, and who owns it. |
| `revise_requirement_draft` | `write_candidate` | `revise_requirement_draft` | Edit a draft requirement that has not been human-approved. |
| `trace_requirement` | `read_reports` | `trace_requirement` | List the design artifacts that claim to implement a requirement. |
| `diff_requirement_revisions` | `read_reports` | `diff_requirement_revisions` | Show what changed between two requirement revisions. |
| `list_unmapped_requirements` | `read_reports` | `list_unmapped_requirements` | List requirements with no implementing artifact and no closing check. |
| `flag_untestable_requirement` | `publish_finding` | `flag_untestable_requirement` | Publish a requirement that has no observable pass condition. |
| `flag_conflicting_requirements` | `publish_finding` | `flag_conflicting_requirements` | Publish two requirements that cannot both be true. |

## Delegation

This agent declares **no** `delegates_to` entries. It executes its own `tools.py` skills when scheduled by a lead or the chip-flow orchestrator.

## Boot path

Every fleet agent shares the same linear startup so compose and local dev behave identically.

1. Container or shell runs `python server.py` (`deployment.dockerfile` / image `agentfleet/requirements:1.0`).
2. `server.py` prepends this directory to `sys.path`, imports `RequirementsAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, RequirementsAgent)`.
3. Importing `agent.py` sets `spec = EdaAgent.read_spec(<this directory>)`, loading `config.yaml` at class definition time.
4. Uvicorn serves FastAPI `app` on `connection.port` with `/health` and `/tasks/execute`.
5. On `/tasks/execute`, `EdaAgent.handle` assembles engineering-memory context (see `context` in YAML), journals the task, and dispatches the requested skill.
6. The skill callable in `tools.py` returns `tool_observation(...)`. With `backend.type: none`, observations are safe stubs (`not_run`) until `EDA_FRAMEWORK` or another adapter binds real engines.

## Related agents

- Stage index: [`../README.md`](../README.md) (architecture specialists under `architecture/`).
- Stage lead(s) that delegate here:
  - [`architecture_lead`](../architecture_lead/) (port **8203**)
- Program orchestrator:
  - [`chip_flow_lead`](../../../chip_flow_lead/) (port **8201**)
- Sibling agents in this folder:
  - [`architecture_lead`](../architecture_lead/) — lead, port **8203**
  - [`interface`](../interface/) — worker, port **8205**
  - [`performance_modeling`](../performance_modeling/) — worker, port **8204**
  - [`power_area_estimation`](../power_area_estimation/) — worker, port **8206**
  - [`security_reliability`](../security_reliability/) — worker, port **8207**
- Track overview: [`../../README.md`](../../README.md) (frontend architecture, RTL, verification).

## Files in this directory

| File | Role |
|------|------|
| `agent.py` | Defines `RequirementsAgent`; loads sibling `config.yaml` into `spec`. |
| `server.py` | HTTP/ASGI bootstrap; exports FastAPI `app` for uvicorn. |
| `tools.py` | `@tool` skill callables; stable EDA operation contracts. |
| `config.yaml` | Fleet manifest (`apiVersion: agentfleet/v1`): boundaries, port, skills, memory, telemetry. |
| `Dockerfile` | Container image; `EXPOSE 8202`; `CMD python server.py`. |
| `requirements.txt` | FastAPI, uvicorn, pydantic, PyYAML for the HTTP surface. |
| `__init__.py` | Re-exports `RequirementsAgent` for imports without starting HTTP. |
| `README.md` | This document. |

## Tool reference

### `extract_requirements` (`tools.extract_requirements`)

**Action:** `write_candidate`. Turn design intent into requirement records with stable ids.

### `assign_acceptance_criteria` (`tools.assign_acceptance_criteria`)

**Action:** `write_candidate`. Attach a measurable check and a pass rule to one requirement.

### `split_requirement` (`tools.split_requirement`)

**Action:** `write_candidate`. Split one compound requirement into independently testable records.

### `link_requirement_to_interface` (`tools.link_requirement_to_interface`)

**Action:** `write_candidate`. Bind a requirement to the interface contract that carries it.

### `link_requirement_to_check` (`tools.link_requirement_to_check`)

**Action:** `write_candidate`. Bind a requirement to the test, assertion, or signoff check that closes it.

### `record_requirement_assumption` (`tools.record_requirement_assumption`)

**Action:** `write_candidate`. Record an assumption a requirement depends on, and who owns it.

### `revise_requirement_draft` (`tools.revise_requirement_draft`)

**Action:** `write_candidate`. Edit a draft requirement that has not been human-approved.

### `trace_requirement` (`tools.trace_requirement`)

**Action:** `read_reports`. List the design artifacts that claim to implement a requirement.

### `diff_requirement_revisions` (`tools.diff_requirement_revisions`)

**Action:** `read_reports`. Show what changed between two requirement revisions.

### `list_unmapped_requirements` (`tools.list_unmapped_requirements`)

**Action:** `read_reports`. List requirements with no implementing artifact and no closing check.

### `flag_untestable_requirement` (`tools.flag_untestable_requirement`)

**Action:** `publish_finding`. Publish a requirement that has no observable pass condition.

### `flag_conflicting_requirements` (`tools.flag_conflicting_requirements`)

**Action:** `publish_finding`. Publish two requirements that cannot both be true.

## Runtime, memory, and context

- **Reliability:** task timeout 120s, max retries 1, on failure `replan`.
- **Execution:** `direct_function`, `max_tasks=1`.
- **Context include:** `human_intent`, `requirements`, `interface_contracts`, `decisions`, `open_findings`.
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
