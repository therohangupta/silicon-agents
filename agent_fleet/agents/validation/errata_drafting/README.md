# Errata and Issue-Drafting Agent (`errata_drafting`)

This directory is the deployable microservice package for the **Errata and Issue-Drafting Agent** in the fleet **validation** stage (role `worker`).

## EDA responsibility

Errata Drafting agent class (errata_drafting).

Charter from `config.yaml`: Draft a traceable internal issue or erratum with reproduction steps, affected configurations, evidence, severity, and proposed mitigations.

As a **worker**, this process executes bounded skills on isolated candidates and reports observations. Promotion and program-level tradeoffs stay with leads and humans.

## Identity and HTTP port

| Field | Value |
|-------|-------|
| Agent id | `errata_drafting` |
| Stage | `validation` |
| Role | `worker` |
| Host | `host.docker.internal` |
| Port | **8270** (must match `Dockerfile` `EXPOSE`) |
| Health | `/health` |
| Execute | `/tasks/execute` |

## Boundaries

Hard limits from `config.yaml` `boundary`. The planner and `EdaAgent` enforce these even when a tool adapter could physically perform a forbidden action.

### May

- Create a draft issue
- Cite primary evidence
- Write a draft erratum for human review

### May not

- Close the issue
- Publish customer errata without human approval
- Promote a candidate onto the canonical baseline
- Approve a waiver or relax a hard requirement
- Treat its own summary as independent signoff

## Skills

Skills bind planner task ids to callables in `tools.py` (`module: tools`, `execution.mode: direct_function`).

| Skill id | Action | Callable | Description |
|----------|--------|----------|-------------|
| `draft_issue` | `publish_finding` | `draft_issue` | Draft an internal issue with reproduction steps and evidence. |
| `draft_errata` | `write_candidate` | `draft_errata` | Draft an erratum record for human review. |
| `write_reproduction_steps` | `write_candidate` | `write_reproduction_steps` | Write the steps that reproduce the issue. |
| `write_affected_configurations` | `write_candidate` | `write_affected_configurations` | Write the revisions, modes, and conditions the issue affects. |
| `write_errata_severity` | `write_candidate` | `write_errata_severity` | Write the severity assessment and what it is based on. |
| `write_proposed_mitigation` | `write_candidate` | `write_proposed_mitigation` | Write a proposed workaround. This does not approve it. |
| `cite_primary_evidence` | `read_reports` | `cite_primary_evidence` | Attach the primary logs, waves, or measurements the draft relies on. |
| `read_source_finding` | `read_reports` | `read_source_finding` | Read the validated finding this draft is based on. |
| `diff_errata_drafts` | `read_reports` | `diff_errata_drafts` | Show what changed between two drafts. |
| `flag_errata_without_evidence` | `publish_finding` | `flag_errata_without_evidence` | Publish a draft whose claims have no primary evidence. |
| `flag_customer_release_attempt` | `publish_finding` | `flag_customer_release_attempt` | Publish a request to release customer errata that has no human approval. |
| `record_errata_lineage` | `publish_finding` | `record_errata_lineage` | Record the finding, evidence refs, and draft revision. |

## Delegation

This agent declares **no** `delegates_to` entries. It executes its own `tools.py` skills when scheduled by a lead or the chip-flow orchestrator.

## Boot path

Every fleet agent shares the same linear startup so compose and local dev behave identically.

1. Container or shell runs `python server.py` (`deployment.dockerfile` / image `agentfleet/errata_drafting:1.0`).
2. `server.py` prepends this directory to `sys.path`, imports `ErrataDraftingAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, ErrataDraftingAgent)`.
3. Importing `agent.py` sets `spec = EdaAgent.read_spec(<this directory>)`, loading `config.yaml` at class definition time.
4. Uvicorn serves FastAPI `app` on `connection.port` with `/health` and `/tasks/execute`.
5. On `/tasks/execute`, `EdaAgent.handle` assembles engineering-memory context (see `context` in YAML), journals the task, and dispatches the requested skill.
6. The skill callable in `tools.py` returns `tool_observation(...)`. With `backend.type: none`, observations are safe stubs (`not_run`) until `EDA_FRAMEWORK` or another adapter binds real engines.

## Related agents

- Stage index: [`../README.md`](../README.md) (validation specialists under `validation/`).
- Stage lead(s) that delegate here:
  - [`bringup_lead`](../bringup_lead/) (port **8263**)
- Sibling agents in this folder:
  - [`bringup_lead`](../bringup_lead/) — lead, port **8263**
  - [`characterization`](../characterization/) — worker, port **8268**
  - [`failure_correlation`](../failure_correlation/) — worker, port **8269**
  - [`firmware_test_program`](../firmware_test_program/) — worker, port **8266**
  - [`instrument_control`](../instrument_control/) — worker, port **8265**
  - [`lab_procedure`](../lab_procedure/) — worker, port **8264**
  - [`telemetry_log_analysis`](../telemetry_log_analysis/) — worker, port **8267**
- Track overview: [`../README.md`](../README.md).

## Files in this directory

| File | Role |
|------|------|
| `agent.py` | Defines `ErrataDraftingAgent`; loads sibling `config.yaml` into `spec`. |
| `server.py` | HTTP/ASGI bootstrap; exports FastAPI `app` for uvicorn. |
| `tools.py` | `@tool` skill callables; stable EDA operation contracts. |
| `config.yaml` | Fleet manifest (`apiVersion: agentfleet/v1`): boundaries, port, skills, memory, telemetry. |
| `Dockerfile` | Container image; `EXPOSE 8270`; `CMD python server.py`. |
| `requirements.txt` | FastAPI, uvicorn, pydantic, PyYAML for the HTTP surface. |
| `__init__.py` | Re-exports `ErrataDraftingAgent` for imports without starting HTTP. |
| `README.md` | This document. |

## Tool reference

### `draft_issue` (`tools.draft_issue`)

**Action:** `publish_finding`. Draft an internal issue with reproduction steps and evidence.

### `draft_errata` (`tools.draft_errata`)

**Action:** `write_candidate`. Draft an erratum record for human review.

### `write_reproduction_steps` (`tools.write_reproduction_steps`)

**Action:** `write_candidate`. Write the steps that reproduce the issue.

### `write_affected_configurations` (`tools.write_affected_configurations`)

**Action:** `write_candidate`. Write the revisions, modes, and conditions the issue affects.

### `write_errata_severity` (`tools.write_errata_severity`)

**Action:** `write_candidate`. Write the severity assessment and what it is based on.

### `write_proposed_mitigation` (`tools.write_proposed_mitigation`)

**Action:** `write_candidate`. Write a proposed workaround. This does not approve it.

### `cite_primary_evidence` (`tools.cite_primary_evidence`)

**Action:** `read_reports`. Attach the primary logs, waves, or measurements the draft relies on.

### `read_source_finding` (`tools.read_source_finding`)

**Action:** `read_reports`. Read the validated finding this draft is based on.

### `diff_errata_drafts` (`tools.diff_errata_drafts`)

**Action:** `read_reports`. Show what changed between two drafts.

### `flag_errata_without_evidence` (`tools.flag_errata_without_evidence`)

**Action:** `publish_finding`. Publish a draft whose claims have no primary evidence.

### `flag_customer_release_attempt` (`tools.flag_customer_release_attempt`)

**Action:** `publish_finding`. Publish a request to release customer errata that has no human approval.

### `record_errata_lineage` (`tools.record_errata_lineage`)

**Action:** `publish_finding`. Record the finding, evidence refs, and draft revision.

## Runtime, memory, and context

- **Reliability:** task timeout 120s, max retries 1, on failure `replan`.
- **Execution:** `direct_function`, `max_tasks=1`.
- **Context include:** `experiments`, `gates`, `decisions`, `open_findings`, `canonical_source`.
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
