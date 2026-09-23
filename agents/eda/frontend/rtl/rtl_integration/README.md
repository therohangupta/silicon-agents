# RTL Integration Agent (`rtl_integration`)

This directory is the deployable microservice package for the **RTL Integration Agent** in the fleet **rtl** stage (role `worker`).

## EDA responsibility

RTL Integration Agent — agent class entry point.

Charter from `config.yaml`: Merge compatible block candidates and mark stale downstream results.

As a **worker**, this process executes bounded skills on isolated candidates and reports observations. Promotion and program-level tradeoffs stay with leads and humans.

## Identity and HTTP port

| Field | Value |
|-------|-------|
| Agent id | `rtl_integration` |
| Stage | `rtl` |
| Role | `worker` |
| Host | `host.docker.internal` |
| Port | **8214** (must match `Dockerfile` `EXPOSE`) |
| Health | `/health` |
| Execute | `/tasks/execute` |

## Boundaries

Hard limits from `config.yaml` `boundary`. The planner and `EDAAgent` enforce these even when a tool adapter could physically perform a forbidden action.

### May

- Read qualified block candidates
- Write an integration candidate
- Mark downstream artifacts stale

### May not

- Merge a candidate that failed its block gate
- Overwrite a newer baseline silently
- Promote a candidate onto the canonical baseline
- Approve a waiver or relax a hard requirement
- Treat its own summary as independent signoff

## Skills

Skills bind planner task ids to callables in `tools.py` (`module: tools`, `execution.mode: direct_function`).

| Skill id | Action | Callable | Description |
|----------|--------|----------|-------------|
| `list_mergeable_candidates` | `read_reports` | `list_mergeable_candidates` | List block candidates whose local gates passed and whose baselines match. |
| `read_candidate_gate` | `read_reports` | `read_candidate_gate` | Read the local gate result for one block candidate. |
| `diff_candidates` | `read_reports` | `diff_candidates` | Show file overlap between two candidates before a merge. |
| `merge_block_candidates` | `write_candidate` | `merge_block_candidates` | Combine compatible block revisions into one integration candidate. |
| `resolve_merge_conflict` | `write_candidate` | `resolve_merge_conflict` | Apply one explicit resolution in the integration candidate. |
| `write_integration_manifest` | `write_candidate` | `write_integration_manifest` | Write the list of block revisions included in the integration candidate. |
| `compile_integration` | `submit_tool_job` | `compile_integration` | Compile the integrated candidate. |
| `mark_stale_downstream` | `publish_finding` | `mark_stale_downstream` | Record which synthesis and physical results a merge invalidates. |
| `flag_baseline_mismatch` | `publish_finding` | `flag_baseline_mismatch` | Publish a candidate whose baseline is no longer the integration parent. |
| `flag_failed_block_gate` | `publish_finding` | `flag_failed_block_gate` | Publish a candidate that was offered for merge without a passing local gate. |
| `flag_merge_conflict` | `publish_finding` | `flag_merge_conflict` | Publish files that cannot be merged automatically. |
| `record_integration_lineage` | `publish_finding` | `record_integration_lineage` | Publish the parent baseline and the block revisions inside the integration candidate. |

## Delegation

This agent declares **no** `delegates_to` entries. It executes its own `tools.py` skills when scheduled by a lead or the chip-flow orchestrator.

## Boot path

Every fleet agent shares the same linear startup so compose and local dev behave identically.

1. Container or shell runs `python server.py` (`deployment.dockerfile` / image `agentfleet/rtl_integration:1.0`).
2. `server.py` prepends this directory to `sys.path`, imports `RtlIntegrationAgent` from `agent.py`, and builds `AgentService.from_agent(config.yaml, RtlIntegrationAgent)`.
3. Importing `agent.py` sets `spec = EDAAgent.read_spec(<this directory>)`, loading `config.yaml` at class definition time.
4. Uvicorn serves FastAPI `app` on `connection.port` with `/health` and `/tasks/execute`.
5. On `/tasks/execute`, `EDAAgent.handle` assembles engineering-memory context (see `context` in YAML), journals the task, and dispatches the requested skill.
6. The skill callable in `tools.py` returns `tool_observation(...)`. With `backend.type: none`, observations are safe stubs (`not_run`) until `EDA_FRAMEWORK` or another adapter binds real engines.

## Related agents

- Stage index: [`../README.md`](../README.md) (rtl specialists under `rtl/`).
- Stage lead(s) that delegate here:
  - [`rtl_lead`](../rtl_lead/) (port **8208**)
- Sibling agents in this folder:
  - [`cdc_rdc`](../cdc_rdc/) — worker, port **8211**
  - [`clock_reset`](../clock_reset/) — worker, port **8210**
  - [`lint_quality`](../lint_quality/) — worker, port **8213**
  - [`low_power`](../low_power/) — worker, port **8212**
  - [`rtl_implementation`](../rtl_implementation/) — worker, port **8209**
  - [`rtl_lead`](../rtl_lead/) — lead, port **8208**
- Track overview: [`../../README.md`](../../README.md) (frontend architecture, RTL, verification).

## Files in this directory

| File | Role |
|------|------|
| `agent.py` | Defines `RtlIntegrationAgent`; loads sibling `config.yaml` into `spec`. |
| `server.py` | HTTP/ASGI bootstrap; exports FastAPI `app` for uvicorn. |
| `tools.py` | `@tool` skill callables; stable EDA operation contracts. |
| `config.yaml` | Fleet manifest (`apiVersion: agentfleet/v1`): boundaries, port, skills, memory, telemetry. |
| `Dockerfile` | Container image; `EXPOSE 8214`; `CMD python server.py`. |
| `requirements.txt` | FastAPI, uvicorn, pydantic, PyYAML for the HTTP surface. |
| `__init__.py` | Re-exports `RtlIntegrationAgent` for imports without starting HTTP. |
| `README.md` | This document. |

## Tool reference

### `list_mergeable_candidates` (`tools.list_mergeable_candidates`)

**Action:** `read_reports`. List block candidates whose local gates passed and whose baselines match.

### `read_candidate_gate` (`tools.read_candidate_gate`)

**Action:** `read_reports`. Read the local gate result for one block candidate.

### `diff_candidates` (`tools.diff_candidates`)

**Action:** `read_reports`. Show file overlap between two candidates before a merge.

### `merge_block_candidates` (`tools.merge_block_candidates`)

**Action:** `write_candidate`. Combine compatible block revisions into one integration candidate.

### `resolve_merge_conflict` (`tools.resolve_merge_conflict`)

**Action:** `write_candidate`. Apply one explicit resolution in the integration candidate.

### `write_integration_manifest` (`tools.write_integration_manifest`)

**Action:** `write_candidate`. Write the list of block revisions included in the integration candidate.

### `compile_integration` (`tools.compile_integration`)

**Action:** `submit_tool_job`. Compile the integrated candidate.

### `mark_stale_downstream` (`tools.mark_stale_downstream`)

**Action:** `publish_finding`. Record which synthesis and physical results a merge invalidates.

### `flag_baseline_mismatch` (`tools.flag_baseline_mismatch`)

**Action:** `publish_finding`. Publish a candidate whose baseline is no longer the integration parent.

### `flag_failed_block_gate` (`tools.flag_failed_block_gate`)

**Action:** `publish_finding`. Publish a candidate that was offered for merge without a passing local gate.

### `flag_merge_conflict` (`tools.flag_merge_conflict`)

**Action:** `publish_finding`. Publish files that cannot be merged automatically.

### `record_integration_lineage` (`tools.record_integration_lineage`)

**Action:** `publish_finding`. Publish the parent baseline and the block revisions inside the integration candidate.

## Runtime, memory, and context

- **Reliability:** task timeout 120s, max retries 1, on failure `replan`.
- **Execution:** `direct_function`, `max_tasks=1`.
- **Context include:** `requirements`, `interface_contracts`, `canonical_source`, `open_findings`, `experiments`.
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
